"""Read the configured GHL location's Social Planner account metadata only."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

DEFAULT_LOCATION = "2cCtht46QwERbvs3uITM"
API_ORIGIN = "https://services.leadconnectorhq.com"


class AccountCheckError(Exception):
    """An operational failure with a safe, locally authored diagnostic."""

    def __init__(self, code, message, http_status=502, upstream_status=None, proxy_status=None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.http_status = http_status
        self.upstream_status = upstream_status
        self.proxy_status = proxy_status


class AccountResponseError(ValueError):
    """Validation error whose message never includes server or credential data."""


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def summarize(payload, location):
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise AccountResponseError("GoHighLevel did not report a successful account lookup.")
    results = payload.get("results")
    if not isinstance(results, dict) or not isinstance(results.get("accounts"), list):
        raise AccountResponseError("GoHighLevel response lacks the documented account list.")
    accounts = []
    for account in results["accounts"]:
        if not isinstance(account, dict):
            raise AccountResponseError("GoHighLevel returned an invalid account record.")
        safe = {}
        for field in ("id", "profileId", "name", "platform", "type", "expire"):
            value = account.get(field)
            if value is not None and not isinstance(value, str):
                raise AccountResponseError("GoHighLevel returned an unexpected account field type.")
            safe[field] = value
        expired = account.get("isExpired")
        if expired is not None and not isinstance(expired, bool):
            raise AccountResponseError("GoHighLevel returned an invalid expiration flag.")
        safe["isExpired"] = expired
        timestamp_past = None
        if safe.get("expire"):
            try:
                timestamp = datetime.fromisoformat(safe["expire"].replace("Z", "+00:00"))
                if timestamp.tzinfo is not None:
                    timestamp_past = timestamp < datetime.now(timezone.utc)
            except ValueError:
                pass
        safe["expirationTimestampPast"] = timestamp_past
        safe["expirationDiscrepancy"] = timestamp_past is not None and expired is not None and timestamp_past != expired
        accounts.append(safe)
    return {"locationId": location, "accountCount": len(accounts), "accounts": accounts}


def fetch_accounts(location=None, token=None, opener=None):
    location = location if location is not None else os.environ.get("GHL_LOCATION_ID", DEFAULT_LOCATION)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", location):
        raise AccountCheckError("LOCATION_INVALID", "The configured GoHighLevel location is invalid.", 503)
    token = token if token is not None else os.environ.get("GHL_ACCESS_TOKEN")
    if not token:
        raise AccountCheckError("CREDENTIAL_MISSING", "GoHighLevel access is not configured for this environment.", 503)
    if not token.isascii() or any(ord(char) < 33 or ord(char) == 127 for char in token):
        raise AccountCheckError("CREDENTIAL_INVALID", "The secure GoHighLevel credential binding has an invalid format.", 503)
    request = Request(
        f"{API_ORIGIN}/social-media-posting/{location}/accounts",
        headers={"Authorization": f"Bearer {token}", "Version": "2021-07-28", "Accept": "application/json"},
        method="GET",
    )
    try:
        # Retain inherited proxy and TLS trust; never forward credentials through redirects.
        client = opener if opener is not None else build_opener(NoRedirects())
        with client.open(request, timeout=30) as response:
            data = response.read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                raise AccountResponseError("GoHighLevel response exceeded the account-check size limit.")
            summary = summarize(json.loads(data), location)
            summary["httpStatus"] = response.status
            return summary
    except HTTPError as error:
        raise AccountCheckError("UPSTREAM_HTTP", "GoHighLevel could not return the connected accounts.", upstream_status=error.code) from None
    except URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise AccountCheckError("UPSTREAM_TIMEOUT", "GoHighLevel did not respond in time. Try again shortly.", 504) from None
        match = re.search(r"Tunnel connection failed:\s*(\d{3})", str(error.reason))
        raise AccountCheckError("UPSTREAM_NETWORK", "GoHighLevel could not be reached from this environment.", proxy_status=int(match.group(1)) if match else None) from None
    except TimeoutError:
        raise AccountCheckError("UPSTREAM_TIMEOUT", "GoHighLevel did not respond in time. Try again shortly.", 504) from None
    except OSError:
        raise AccountCheckError("UPSTREAM_NETWORK", "GoHighLevel could not be reached from this environment.") from None
    except AccountResponseError as error:
        raise AccountCheckError("UPSTREAM_RESPONSE_INVALID", str(error)) from None
    except (ValueError, UnicodeError):
        raise AccountCheckError("UPSTREAM_RESPONSE_INVALID", "GoHighLevel returned an invalid account response.") from None


def main():
    try:
        summary = fetch_accounts()
    except AccountCheckError as error:
        detail = f" HTTP {error.upstream_status}." if error.upstream_status is not None else ""
        if error.proxy_status is not None:
            detail += f" Proxy HTTP {error.proxy_status}."
        print(error.message + detail, file=sys.stderr)
        return 2 if error.http_status == 503 else 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
