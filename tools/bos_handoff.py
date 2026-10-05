"""Return a supplied Worker Result to the existing BOS contract API.

This client creates no assignments, queue, approvals, claims, or review records.
Contract source: Bert-bos/bos-workforce-orchestrator at
8ae0d4bf0475006a7892280a1fcf87d4d5911f2c, schemas/worker-result-v1.schema.json
and src/dashboard-server.js. The bundled schema is an unchanged copy.
"""

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

API_ORIGIN = "https://bos-workforce-orchestrator.onrender.com"
WORKER_ID = "bos-worker"
MAX_BYTES = 2 * 1024 * 1024
SCHEMA_PATH = Path(__file__).parent / "schemas" / "worker-result-v1.schema.json"
IDENTIFIER = re.compile(r"[A-Za-z0-9._-]{3,128}")
RUNTIME_STATES = {
    "CREATED", "VALIDATED", "ROUTED", "APPROVED_FOR_EXECUTION", "CLAIMED",
    "WORKING", "REVIEW_READY", "QA_REJECTED", "BLOCKED", "RETRY_SCHEDULED",
    "COMPLETED", "RELEASED", "CANCELLED", "SUPERSEDED", "DEAD_LETTER",
}


class HandoffError(ValueError):
    """Safe error; never contains credentials or raw server response text."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _finite_number(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def _strict_json(data):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise HandoffError("Duplicate JSON properties are not allowed.")
            result[key] = value
        return result

    def reject_constant(_value):
        raise HandoffError("Non-finite JSON numbers are not allowed.")

    try:
        return json.loads(data, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise HandoffError("Invalid or ambiguous JSON payload.") from error


def _schema_validate(value, schema):
    types = schema.get("type", [])
    types = [types] if isinstance(types, str) else types
    checks = {
        "null": value is None,
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "boolean": isinstance(value, bool),
        "string": isinstance(value, str),
        "number": _finite_number(value),
    }
    if types and not any(checks.get(kind, False) for kind in types):
        raise HandoffError("Worker Result has a field with an invalid type.")
    if "const" in schema and value != schema["const"]:
        raise HandoffError("Worker Result uses an unsupported schema version.")
    if "enum" in schema and value not in schema["enum"]:
        raise HandoffError("Worker Result has an unsupported status.")
    if value is None:
        return
    if isinstance(value, str):
        length = len(value.encode("utf-16-le", errors="surrogatepass")) // 2
        if length < schema.get("minLength", 0) or length > schema.get("maxLength", math.inf):
            raise HandoffError("Worker Result contains a string outside the contract limits.")
        if schema.get("format") == "date-time":
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value, flags=re.IGNORECASE):
                raise HandoffError("Worker Result timestamps must be RFC 3339 values with a timezone.")
            try:
                datetime.datetime.fromisoformat(value.upper().replace("Z", "+00:00"))
            except ValueError as error:
                raise HandoffError("Worker Result contains an invalid timestamp.") from error
    if type(value) in (int, float) and value < schema.get("minimum", -math.inf):
        raise HandoffError("Worker Result contains a number outside the contract limits.")
    if isinstance(value, list):
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            raise HandoffError("Worker Result contains duplicate contract values.")
        for item in value:
            _schema_validate(item, schema.get("items", {}))
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if not set(schema.get("required", [])).issubset(value):
            raise HandoffError("Worker Result is missing required contract fields.")
        if schema.get("additionalProperties") is False and set(value) - set(properties):
            raise HandoffError("Worker Result contains fields outside the BOS contract.")
        for field, child in properties.items():
            if field in value:
                _schema_validate(value[field], child)


def validate_identifiers(task_id, job_id, attempt_id):
    if not all(isinstance(value, str) and IDENTIFIER.fullmatch(value) for value in (task_id, job_id, attempt_id)):
        raise HandoffError("Supply the existing BOS task ID, job ID, and current attempt ID.")


def validate_result(result, task_id, job_id, attempt_id):
    validate_identifiers(task_id, job_id, attempt_id)
    _schema_validate(result, _strict_json(SCHEMA_PATH.read_bytes()))
    if result["job_id"] != job_id or result["attempt_id"] != attempt_id:
        raise HandoffError("Worker Result does not match the supplied BOS job and attempt.")
    if result["worker_id"] != WORKER_ID:
        raise HandoffError("Worker Result must use the authenticated BOS worker identity.")
    reason = result["requires_bert_reason"]
    if (result["requires_bert"] and (not isinstance(reason, str) or not reason.strip())) or (not result["requires_bert"] and reason is not None):
        raise HandoffError("Worker Result requires-Bert reason is inconsistent.")
    if result["status"] in ("COMPLETED", "PARTIAL") and not result["evidence_refs"]:
        raise HandoffError("Review-ready Worker Results require evidence references.")
    return result


def read_result(path):
    try:
        with Path(path).open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
    except OSError as error:
        raise HandoffError("The supplied Worker Result file could not be read.") from error
    if len(data) > MAX_BYTES:
        raise HandoffError("Worker Result exceeds the return-client size limit.")
    return _strict_json(data)


class BosClient:
    def __init__(self, token=None, base_url=None, opener=None):
        origin = base_url if base_url is not None else os.environ.get("BOS_BASE_URL", API_ORIGIN)
        if origin not in (API_ORIGIN, API_ORIGIN + "/"):
            raise HandoffError("BOS_BASE_URL must use the approved HTTPS BOS origin.")
        self.origin = API_ORIGIN
        self.token = token if token is not None else os.environ.get("BOS_WORKER_KEY")
        if not self.token:
            raise HandoffError("Configure BOS_WORKER_KEY securely for the existing BOS return lane.")
        if not isinstance(self.token, str) or not self.token.isascii() or any(ord(char) < 33 or ord(char) == 127 for char in self.token):
            raise HandoffError("BOS_WORKER_KEY has an invalid format.")
        # Retain inherited proxy and TLS trust. Never send the key through redirects.
        self.opener = opener if opener is not None else build_opener(NoRedirects())

    def request(self, method, path, payload=None):
        data = json.dumps(payload, allow_nan=False).encode("utf-8") if payload is not None else None
        if data is not None and len(data) > MAX_BYTES:
            raise HandoffError("Worker Result exceeds the return-client size limit.")
        request = Request(self.origin + path, data=data, method=method, headers={
            "x-bos-key": self.token, "Accept": "application/json", "Content-Type": "application/json",
        })
        try:
            with self.opener.open(request, timeout=30) as response:
                if response.status < 200 or response.status >= 300:
                    raise HandoffError("BOS did not return a successful response.")
                body = response.read(MAX_BYTES + 1)
                if len(body) > MAX_BYTES:
                    raise HandoffError("BOS response exceeds the return-client size limit.")
                return _strict_json(body)
        except HTTPError as error:
            raise HandoffError(f"BOS request failed with HTTP {error.code}; verify authorization and existing job state.") from error
        except (URLError, OSError, ValueError) as error:
            raise HandoffError("BOS request could not be verified; check API network policy, proxy and TLS trust.") from error

    def handoff(self, task_id, job_id, attempt_id):
        validate_identifiers(task_id, job_id, attempt_id)
        snapshot = self.request("GET", "/api/contracts/status")
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("handoffs"), list):
            raise HandoffError("BOS did not return the documented contract status.")
        matches = [record for record in snapshot["handoffs"] if isinstance(record, dict) and record.get("task_id") == task_id]
        if len(matches) != 1 or matches[0].get("contract_job_id") != job_id:
            raise HandoffError("The supplied assignment is not an existing unique BOS contract job.")
        record = matches[0]
        if record.get("attempt_id") != attempt_id:
            raise HandoffError("The supplied attempt is no longer current in BOS.")
        if record.get("status") not in RUNTIME_STATES:
            raise HandoffError("BOS returned an unsupported runtime status.")
        return record

    def submit(self, task_id, job_id, attempt_id, result):
        validate_result(result, task_id, job_id, attempt_id)
        existing = self.handoff(task_id, job_id, attempt_id)
        # Reconcile an uncertain previous attempt using a read, never a duplicate POST.
        if existing.get("worker_result") == result:
            return receipt(existing, task_id, job_id, attempt_id, already_present=True)
        if existing.get("status") != "WORKING" or existing.get("claimed_by") != WORKER_ID:
            raise HandoffError("Only the existing WORKING assignment owned by this BOS worker can receive a result.")
        policy = existing.get("contract_cost_policy")
        if not isinstance(policy, dict) or not isinstance(policy.get("metered_calls_allowed"), bool) or not _finite_number(policy.get("max_job_usd")) or policy["max_job_usd"] < 0:
            raise HandoffError("The assignment's cost policy is missing or invalid.")
        if (not policy["metered_calls_allowed"] and result["spend_consumed"] != 0) or result["spend_consumed"] > policy["max_job_usd"]:
            raise HandoffError("Worker Result spend violates the existing BOS assignment.")
        try:
            response = self.request("POST", f"/api/contracts/{task_id}/result", result)
            if not isinstance(response, dict) or response.get("ok") is not True:
                raise HandoffError("BOS did not acknowledge the Worker Result.")
            observed = self.handoff(task_id, job_id, attempt_id)
        except HandoffError as error:
            raise HandoffError("Delivery is unverified. Read the existing BOS job before retrying; this client does not retry a result POST.") from error
        if observed.get("worker_result") != result:
            raise HandoffError("BOS result readback does not match. Reconcile the existing job before retrying.")
        return receipt(observed, task_id, job_id, attempt_id)


def receipt(record, task_id, job_id, attempt_id, already_present=False):
    return {"delivered": True, "verifiedByReadback": True, "alreadyPresent": already_present,
            "taskId": task_id, "jobId": job_id, "attemptId": attempt_id,
            "runtimeStatus": record["status"], "releaseAuthorized": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "status", "submit"))
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--attempt-id", required=True)
    parser.add_argument("--result", help="Complete existing BOS Worker Result v1 JSON file")
    args = parser.parse_args(argv)
    try:
        validate_identifiers(args.task_id, args.job_id, args.attempt_id)
        result = None
        if args.command in ("validate", "submit"):
            if not args.result:
                raise HandoffError("Supply --result for validation or submission.")
            result = validate_result(read_result(args.result), args.task_id, args.job_id, args.attempt_id)
        if args.command == "validate":
            output = {"schemaValid": True, "delivered": False, "liveAuthorityVerified": False}
        elif args.command == "status":
            record = BosClient().handoff(args.task_id, args.job_id, args.attempt_id)
            output = {"taskId": args.task_id, "jobId": args.job_id, "attemptId": args.attempt_id,
                      "runtimeStatus": record["status"], "delivered": False}
        else:
            output = BosClient().submit(args.task_id, args.job_id, args.attempt_id, result)
    except (HandoffError, OSError, UnicodeError):
        error = sys.exc_info()[1]
        print(str(error) if isinstance(error, HandoffError) else "BOS return-client configuration could not be read.", file=sys.stderr)
        return 1
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
