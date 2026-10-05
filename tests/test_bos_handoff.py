"""BOS return-client security checks and an existing-server local integration.

Set BOS_REFERENCE_DIR to a read-only BOS checkout to run the integration test.
It creates synthetic state only in a temporary directory and binds loopback.
"""

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import bos_handoff as bos

TASK = "handoff-synthetic-001"
JOB = "EP-BOS-SYNTHETIC-RETURN-TEST"
ATTEMPT = "attempt-synthetic-001"
KEY = "synthetic-local-worker-key"


def result_fixture(attempt=ATTEMPT):
    return {
        "schema_version": "1.0", "job_id": JOB, "attempt_id": attempt,
        "worker_id": "bos-worker", "status": "PARTIAL",
        "started_at": "2026-10-05T15:00:00Z", "finished_at": "2026-10-05T15:01:00Z",
        "exact_changes": ["Synthetic local integration only."], "files_changed": [],
        "commit_hashes": [], "tests_run": ["Synthetic existing-server return test"],
        "test_results": ["Local only"], "evidence_refs": ["synthetic:local-only"],
        "deployment_or_service_ids": [], "live_verification": None,
        "remaining_assumptions": [], "remaining_problems": [],
        "security_privacy_impact": "No production data or credentials.", "spend_consumed": 0,
        "rollback_state": "Temporary test state will be removed.",
        "recommended_next_action": "Independent QA remains required.",
        "requires_bert": False, "requires_bert_reason": None,
    }


def handoff_fixture(result=None, status="WORKING"):
    return {"task_id": TASK, "contract_job_id": JOB, "attempt_id": ATTEMPT,
            "status": status, "claimed_by": "bos-worker",
            "contract_cost_policy": {"metered_calls_allowed": False, "max_job_usd": 0},
            "worker_result": result}


class Response(io.BytesIO):
    status = 200


class ScriptedOpener:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def open(self, request, timeout):
        self.calls.append(request)
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return Response(json.dumps(reply).encode())


class ReturnClientTests(unittest.TestCase):
    def test_schema_is_identical_to_pinned_contract_if_reference_available(self):
        reference = Path(os.environ.get("BOS_REFERENCE_DIR", "/tmp/ep-reference-bos"))
        source = reference / "schemas" / "worker-result-v1.schema.json"
        if not source.exists():
            self.skipTest("Read-only BOS reference checkout unavailable")
        self.assertEqual(bos.SCHEMA_PATH.read_bytes(), source.read_bytes())

    def test_validation_does_not_require_network_or_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            path.write_text(json.dumps(result_fixture()))
            env = {key: value for key, value in os.environ.items() if key != "BOS_WORKER_KEY"}
            proc = subprocess.run([sys.executable, "-B", str(Path(bos.__file__)), "validate",
                                   "--task-id", TASK, "--job-id", JOB, "--attempt-id", ATTEMPT,
                                   "--result", str(path)], capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(json.loads(proc.stdout), {"schemaValid": True, "delivered": False, "liveAuthorityVerified": False})

    def test_incomplete_unbound_or_overbroad_result_is_rejected(self):
        for field, value in [("job_id", "another-job"), ("attempt_id", "stale-attempt"),
                             ("worker_id", "self-approved-reviewer"), ("spend_consumed", False),
                             ("evidence_refs", []), ("requires_bert_reason", "unexpected"),
                             ("started_at", "2026-10-05T15:00:00"), ("extra_field", "not allowed")]:
            result = result_fixture()
            result[field] = value
            with self.subTest(field=field), self.assertRaises(bos.HandoffError):
                bos.validate_result(result, TASK, JOB, ATTEMPT)
        result = result_fixture()
        del result["security_privacy_impact"]
        with self.assertRaises(bos.HandoffError):
            bos.validate_result(result, TASK, JOB, ATTEMPT)

    def test_identifier_and_origin_validation_prevents_credential_retargeting(self):
        for task in ["../review", "bad/id", "bad?path", "bad\nheader"]:
            with self.assertRaises(bos.HandoffError):
                bos.validate_identifiers(task, JOB, ATTEMPT)
        for origin in ["http://bos-workforce-orchestrator.onrender.com", "https://example.com",
                       bos.API_ORIGIN + "/elsewhere", bos.API_ORIGIN + ".example.com"]:
            with self.assertRaises(bos.HandoffError):
                bos.BosClient(KEY, base_url=origin)
        for key in ["has space", "bad\nheader", "bad\x7fheader"]:
            with self.assertRaises(bos.HandoffError):
                bos.BosClient(key)

    def test_ambiguous_or_nonfinite_json_is_rejected(self):
        for payload in [b'{"job_id":"one","job_id":"two"}', b'{"spend_consumed":NaN}', b'{"spend_consumed":Infinity}']:
            with self.assertRaises(bos.HandoffError):
                bos._strict_json(payload)
        result = result_fixture()
        result["spend_consumed"] = 10 ** 500
        with self.assertRaises(bos.HandoffError):
            bos.validate_result(result, TASK, JOB, ATTEMPT)

    def test_no_result_post_for_closed_stale_or_foreign_assignment(self):
        for field, value in [("status", "COMPLETED"), ("attempt_id", "stale-attempt"),
                             ("claimed_by", "another-worker"), ("contract_job_id", "another-job")]:
            record = handoff_fixture()
            record[field] = value
            opener = ScriptedOpener([{"handoffs": [record]}])
            with self.subTest(field=field), self.assertRaises(bos.HandoffError):
                bos.BosClient(KEY, opener=opener).submit(TASK, JOB, ATTEMPT, result_fixture())
            self.assertEqual([req.method for req in opener.calls], ["GET"])

    def test_cost_policy_rejection_happens_before_result_post(self):
        result = result_fixture()
        result["spend_consumed"] = 0.01
        opener = ScriptedOpener([{"handoffs": [handoff_fixture()]}])
        with self.assertRaises(bos.HandoffError):
            bos.BosClient(KEY, opener=opener).submit(TASK, JOB, ATTEMPT, result)
        self.assertEqual([req.method for req in opener.calls], ["GET"])

    def test_acknowledgement_requires_matching_persistent_readback(self):
        opener = ScriptedOpener([{"handoffs": [handoff_fixture()]}, {"ok": True},
                                  {"handoffs": [handoff_fixture(status="REVIEW_READY")]}])
        with self.assertRaisesRegex(bos.HandoffError, "readback does not match"):
            bos.BosClient(KEY, opener=opener).submit(TASK, JOB, ATTEMPT, result_fixture())

    def test_uncertain_post_never_automatically_retries(self):
        opener = ScriptedOpener([{"handoffs": [handoff_fixture()]}, URLError("synthetic timeout " + KEY)])
        with self.assertRaisesRegex(bos.HandoffError, "Delivery is unverified") as caught:
            bos.BosClient(KEY, opener=opener).submit(TASK, JOB, ATTEMPT, result_fixture())
        self.assertNotIn(KEY, str(caught.exception))
        self.assertEqual([req.method for req in opener.calls], ["GET", "POST"])

    def test_matching_return_is_reconciled_without_duplicate_post(self):
        result = result_fixture()
        opener = ScriptedOpener([{"handoffs": [handoff_fixture(result, "REVIEW_READY")]}])
        receipt = bos.BosClient(KEY, opener=opener).submit(TASK, JOB, ATTEMPT, result)
        self.assertTrue(receipt["alreadyPresent"])
        self.assertTrue(receipt["verifiedByReadback"])
        self.assertEqual([req.method for req in opener.calls], ["GET"])

    def test_redirect_is_not_followed_and_error_does_not_echo_response(self):
        error = HTTPError(bos.API_ORIGIN + "/api/contracts/status", 302, KEY,
                          {"Location": "https://example.com"}, io.BytesIO(KEY.encode()))
        opener = ScriptedOpener([error])
        with self.assertRaises(bos.HandoffError) as caught:
            bos.BosClient(KEY, opener=opener).handoff(TASK, JOB, ATTEMPT)
        self.assertNotIn(KEY, str(caught.exception))
        request = opener.calls[0]
        self.assertEqual(request.get_header("X-bos-key"), KEY)
        self.assertEqual(len(opener.calls), 1)
        self.assertIsNone(bos.NoRedirects().redirect_request(request, None, 302, "", {}, "https://example.com"))


NODE_SERVER = r"""
const path = require('path');
const root = process.argv[1], dataDir = process.argv[2];
const {createEngine} = require(path.join(root,'src/dispatch-engine'));
const {createServer} = require(path.join(root,'src/dashboard-server'));
const {forceApproveForExecution} = require(path.join(root,'test/support/dispatch-helpers'));
(async()=>{
const jobId='EP-BOS-SYNTHETIC-RETURN-TEST', revision=new Date().toISOString();
const engine=createEngine({dataDir});
const envelope={schema_version:'1.0',job_id:jobId,idempotency_key:'synthetic-local-return-test:1',
objective:'Synthetic local return-client integration only.',owning_project:'synthetic-test',requested_by:'local-test',
created_at:revision,due_at:null,priority:'P2',current_verified_state:'No live assignment.',
source_manifest:[{source_id:'drive:synthetic-local-doc',revision,kind:'google_doc'}],
scope:['Local synthetic test only.'],explicit_exclusions:['No production or remote writes.'],requirements:['Return local evidence.'],
constraints:['No spending.'],data_class:'INTERNAL',authorized_source_ids:['drive:synthetic-local-doc'],execution_lane:'deterministic',
repository:null,acceptance_criteria:['Local round-trip verified.'],required_tests:['Synthetic return round-trip.'],required_evidence:['Local test output.'],
rollback:'Remove temporary test state.',stop_conditions:['Any real connection.'],protected_actions:['merge','deploy'],
cost_policy:{metered_calls_allowed:false,max_job_usd:0,max_call_usd:null},
authorization_binding:{command_center_job_id:jobId,drive_file_id:'synthetic-local-doc',drive_revision:revision,
drive_doc_url:'https://docs.google.com/document/d/synthetic-local-doc/edit'},dependencies:[]};
const ingested=await engine.ingestJobEnvelope(envelope);
const taskId=ingested.handoff.task_id;
forceApproveForExecution(dataDir,taskId);
const claimed=await engine.claimTask(taskId,{machine:'synthetic-local-test',worker:'bos-worker'});
await engine.markContractWorking(taskId,{worker:'bos-worker',attemptId:claimed.attempt_id});
const server=createServer({dataDir,credentials:{worker:'synthetic-local-worker-key',operator:'synthetic-local-operator-key'}});
server.listen(0,'127.0.0.1',()=>process.stdout.write(JSON.stringify({port:server.address().port,taskId:claimed.task_id,attemptId:claimed.attempt_id})+'\n'));
process.on('SIGTERM',()=>server.close(()=>process.exit(0)));
})().catch(error=>{process.stderr.write(error.stack);process.exit(1)});
"""


class LocalMappingOpener:
    """Test-only map of the fixed production origin onto the existing local BOS server."""
    def __init__(self, port):
        self.port = port
        self.calls = []
        self.opener = build_opener(bos.NoRedirects())

    def open(self, request, timeout):
        self.calls.append(request.method)
        url = request.full_url.replace(bos.API_ORIGIN, f"http://127.0.0.1:{self.port}", 1)
        local = Request(url, data=request.data, method=request.method, headers=dict(request.header_items()))
        return self.opener.open(local, timeout=timeout)


class ExistingBosIntegrationTests(unittest.TestCase):
    def test_return_is_persisted_by_existing_bos_and_never_self_completes(self):
        reference = Path(os.environ.get("BOS_REFERENCE_DIR", "/tmp/ep-reference-bos"))
        if not (reference / "src" / "dashboard-server.js").exists():
            self.skipTest("Set BOS_REFERENCE_DIR to the existing BOS read-only checkout")
        with tempfile.TemporaryDirectory(prefix="ep-bos-synthetic-test-") as directory:
            proc = subprocess.Popen(["node", "-e", NODE_SERVER, str(reference), directory],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                startup = proc.stdout.readline()
                if not startup:
                    self.fail("Existing BOS server fixture did not start: " + proc.stderr.read())
                config = json.loads(startup)
                opener = LocalMappingOpener(config["port"])
                result = result_fixture(config["attemptId"])
                client = bos.BosClient(KEY, opener=opener)
                returned = client.submit(config["taskId"], JOB, config["attemptId"], result)
                self.assertEqual(returned["runtimeStatus"], "REVIEW_READY")
                self.assertFalse(returned["releaseAuthorized"])
                self.assertTrue(returned["verifiedByReadback"])
                self.assertEqual(opener.calls, ["GET", "POST", "GET"])
                records = list((Path(directory) / "dispatcher" / "handoffs").glob("*.json"))
                self.assertEqual(len(records), 1)
                saved = json.loads(records[0].read_text())
                self.assertEqual(saved["worker_result"], result)
                self.assertEqual(saved["status"], "REVIEW_READY")
                repeated = client.submit(config["taskId"], JOB, config["attemptId"], result)
                self.assertTrue(repeated["alreadyPresent"])
                self.assertEqual(opener.calls, ["GET", "POST", "GET", "GET"])
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
                proc.stdout.close()
                proc.stderr.close()


if __name__ == "__main__":
    unittest.main()
