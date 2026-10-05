"""Offline checks for the local, read-only GHL account integration.

Only loopback HTTP and explicit fake credentials are used. No provider request
may leave these tests: every account store receives an injected loader.
"""
import contextlib
import http.client
import io
import json
from pathlib import Path
import ssl
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, ProxyHandler, Request, build_opener
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_ghl_accounts as ghl
import serve_ep


MARKER = "EP-TEST-SECRET-NEVER-LOG"
LOCATION = "mock-location"
ACCOUNT = {
    "id": "mock-account",
    "profileId": "mock-platform-profile",
    "name": "Mock professor",
    "platform": "youtube",
    "type": "channel",
    "expire": "2000-01-01T00:00:00Z",
    "isExpired": False,
}


def inventory(accounts=None):
    records = [dict(ACCOUNT)] if accounts is None else accounts
    return {
        "locationId": LOCATION,
        "accountCount": len(records),
        "accounts": records,
        "httpStatus": 200,
    }


class FakeResponse:
    status = 200

    def __init__(self, payload=None, data=None):
        self.data = data if data is not None else json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size):
        return self.data[:size]


class FakeOpener:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error is not None:
            raise self.error
        return self.response


class ProviderTests(unittest.TestCase):
    def test_metadata_allowlist_preserves_conflicting_expiration_evidence(self):
        raw = dict(ACCOUNT, accessToken=MARKER, refreshToken=MARKER,
                   meta={"credential": MARKER})
        opener = FakeOpener(FakeResponse({
            "success": True, "results": {"accounts": [raw]},
            "accessToken": MARKER,
        }))
        result = ghl.fetch_accounts(LOCATION, MARKER, opener)
        self.assertEqual(result["httpStatus"], 200)
        account = result["accounts"][0]
        self.assertEqual(account["expire"], ACCOUNT["expire"])
        self.assertIs(account["isExpired"], False)
        self.assertNotIn(MARKER, json.dumps(result))
        self.assertEqual(set(account), set(ACCOUNT) | {
            "expirationTimestampPast", "expirationDiscrepancy",
        })
        self.assertIs(account["expirationTimestampPast"], True)
        self.assertIs(account["expirationDiscrepancy"], True)
        request, _ = opener.calls[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url,
                         f"{ghl.API_ORIGIN}/social-media-posting/{LOCATION}/accounts")

    def test_missing_accounts_is_not_confirmed_empty(self):
        for results in (None, {}, {"accounts": None}):
            with self.subTest(results=results):
                with self.assertRaises(ghl.AccountCheckError):
                    ghl.fetch_accounts(LOCATION, MARKER, FakeOpener(FakeResponse({
                        "success": True, "results": results,
                    })))
        result = ghl.fetch_accounts(LOCATION, MARKER, FakeOpener(FakeResponse({
            "success": True, "results": {"accounts": []},
        })))
        self.assertEqual(result["accounts"], [])
        self.assertEqual(result["accountCount"], 0)

    def test_missing_expiration_fields_remain_unknown(self):
        result = ghl.fetch_accounts(LOCATION, MARKER, FakeOpener(FakeResponse({
            "success": True,
            "results": {"accounts": [{"id": "mock", "platform": "linkedin"}]},
        })))
        self.assertIsNone(result["accounts"][0]["expire"])
        self.assertIsNone(result["accounts"][0]["isExpired"])
        self.assertIsNone(result["accounts"][0]["expirationTimestampPast"])
        self.assertIs(result["accounts"][0]["expirationDiscrepancy"], False)

    def test_expiration_evidence_is_not_guessed_from_invalid_or_naive_dates(self):
        for expiry in ("not-a-date", "2000-01-01T00:00:00"):
            with self.subTest(expiry=expiry):
                account = dict(ACCOUNT, expire=expiry)
                result = ghl.fetch_accounts(LOCATION, MARKER, FakeOpener(FakeResponse({
                    "success": True, "results": {"accounts": [account]},
                })))["accounts"][0]
                self.assertEqual(result["expire"], expiry)
                self.assertIs(result["isExpired"], False)
                self.assertIsNone(result["expirationTimestampPast"])
                self.assertIs(result["expirationDiscrepancy"], False)

    def test_malformed_expiration_is_a_safe_error(self):
        for field, value in (("expire", 42), ("isExpired", "false")):
            with self.subTest(field=field):
                account = dict(ACCOUNT)
                account[field] = value
                with self.assertRaises(ghl.AccountCheckError) as caught:
                    ghl.fetch_accounts(LOCATION, MARKER, FakeOpener(FakeResponse({
                        "success": True, "results": {"accounts": [account]},
                    })))
                self.assertNotIn(MARKER, str(caught.exception))

    def test_provider_errors_never_expose_raw_details(self):
        errors = [
            HTTPError("https://mock.invalid", 401, MARKER, {}, io.BytesIO(MARKER.encode())),
            HTTPError("https://mock.invalid", 302, MARKER, {}, io.BytesIO(MARKER.encode())),
            URLError(MARKER), TimeoutError(MARKER), OSError(MARKER),
            ValueError(MARKER),
        ]
        for error in errors:
            with self.subTest(error_type=type(error).__name__):
                with self.assertRaises(ghl.AccountCheckError) as caught:
                    ghl.fetch_accounts(LOCATION, MARKER, FakeOpener(error=error))
                self.assertNotIn(MARKER, str(caught.exception))
                self.assertNotIn(MARKER, caught.exception.message)

    def test_malformed_response_body_is_not_echoed(self):
        for body in (MARKER.encode(), b"\xff" + MARKER.encode(), b"x" * (2 * 1024 * 1024 + 1)):
            with self.subTest(size=len(body)):
                with self.assertRaises(ghl.AccountCheckError) as caught:
                    ghl.fetch_accounts(LOCATION, MARKER,
                                       FakeOpener(FakeResponse(data=body)))
                self.assertNotIn(MARKER, str(caught.exception))

    def test_timeout_while_reading_body_is_a_safe_gateway_timeout(self):
        class SlowResponse(FakeResponse):
            def read(self, _size):
                raise TimeoutError(MARKER)

        with self.assertRaises(ghl.AccountCheckError) as caught:
            ghl.fetch_accounts(LOCATION, MARKER,
                               FakeOpener(SlowResponse(data=b"")))
        self.assertEqual(caught.exception.http_status, 504)
        self.assertNotIn(MARKER, str(caught.exception))

    def test_timeout_and_proxy_status_diagnostics_are_safe(self):
        cases = [
            (URLError(TimeoutError(MARKER)), "UPSTREAM_TIMEOUT", 504, None),
            (URLError("Tunnel connection failed: 403 Forbidden " + MARKER),
             "UPSTREAM_NETWORK", 502, 403),
        ]
        for error, code, status, proxy_status in cases:
            with self.subTest(code=code):
                with self.assertRaises(ghl.AccountCheckError) as caught:
                    ghl.fetch_accounts(LOCATION, MARKER, FakeOpener(error=error))
                self.assertEqual(caught.exception.code, code)
                self.assertEqual(caught.exception.http_status, status)
                self.assertEqual(caught.exception.proxy_status, proxy_status)
                self.assertNotIn(MARKER, str(caught.exception))

    def test_bad_credential_format_never_reaches_opener(self):
        for token in (MARKER + "\nvalue", MARKER + "\rvalue", MARKER + " value", MARKER + "é"):
            with self.subTest(token_kind=token[-1]):
                opener = FakeOpener()
                with self.assertRaises(ghl.AccountCheckError) as caught:
                    ghl.fetch_accounts(LOCATION, token, opener)
                self.assertNotIn(MARKER, str(caught.exception))
                self.assertEqual(opener.calls, [])

    def test_redirects_are_rejected_and_proxy_tls_settings_are_retained(self):
        request = Request(ghl.API_ORIGIN + "/mock",
                          headers={"Authorization": "Bearer " + MARKER})
        for code in (301, 302, 303, 307, 308):
            self.assertIsNone(ghl.NoRedirects().redirect_request(
                request, None, code, "", {}, "https://untrusted.invalid"))
        with patch("urllib.request.getproxies", return_value={
            "https": "http://mock-proxy.invalid:8080",
        }):
            opener = build_opener(ghl.NoRedirects())
        proxy = next(h for h in opener.handlers if isinstance(h, ProxyHandler))
        self.assertEqual(proxy.proxies, {"https": "http://mock-proxy.invalid:8080"})
        https = next(h for h in opener.handlers if isinstance(h, HTTPSHandler))
        if https._context is not None:
            self.assertEqual(https._context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(https._context.check_hostname)


class LocalServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ep-server-test-")
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.dist = root / "dist"
        self.dist.mkdir()
        (self.dist / "index.html").write_text("<title>EP test page</title>")
        self.secret_file = root / "private.txt"
        self.secret_file.write_text(MARKER)
        self.calls = 0
        self.calls_lock = threading.Lock()
        self.loader_result = inventory()
        self.loader_error = None
        self.statistics_calls = 0
        self.statistics_error = None
        self.statistics_result = {
            "locationId": LOCATION, "status": "unavailable", "httpStatus": 401,
            "requiredScope": "socialplanner/statistics.readonly", "totals": {},
            "platforms": [], "excludedAccounts": [],
            "error": {"code": "STATISTICS_CREDENTIAL_REJECTED",
                      "message": "GoHighLevel rejected the analytics credential.",
                      "upstreamStatus": 401},
        }
        self.now = 100.0

        def loader():
            with self.calls_lock:
                self.calls += 1
            if self.loader_error is not None:
                raise self.loader_error
            return self.loader_result

        self.store = serve_ep.AccountsStore(loader=loader, ttl_seconds=60,
                                           clock=lambda: self.now)
        def statistics_loader():
            with self.calls_lock:
                self.statistics_calls += 1
            if self.statistics_error is not None:
                raise self.statistics_error
            return self.statistics_result

        self.statistics_store = serve_ep.StatisticsStore(
            loader=statistics_loader, ttl_seconds=60, clock=lambda: self.now)
        self.server = serve_ep.create_server(port=0, store=self.store,
                                              dist_dir=self.dist,
                                              statistics_store=self.statistics_store)
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)
        self.port = self.server.server_address[1]

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)

    def request(self, path="/api/social/accounts", method="GET", headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read().decode()
        finally:
            connection.close()

    def test_same_origin_accounts_json_is_not_browser_cached(self):
        status, headers, body = self.request(headers={
            "Origin": f"http://127.0.0.1:{self.port}",
            "Sec-Fetch-Site": "same-origin",
        })
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("Content-Type", ""))
        self.assertIn("no-store", headers.get("Cache-Control", ""))
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertNotIn(MARKER, body)
        self.assertEqual(self.calls, 1)
        result = json.loads(body)
        self.assertEqual(result["source"], "gohighlevel")
        self.assertEqual(result["capabilities"], {"accountRead": "verified"})
        self.assertFalse(result["cache"]["fromCache"])
        self.assertIn("linkedin", result["missingPlatforms"])
        self.assertNotIn("youtube", result["missingPlatforms"])

    def test_host_origin_and_cross_site_requests_are_rejected_before_fetch(self):
        invalid_headers = [
            {"Host": "attacker.invalid"},
            {"Origin": "https://attacker.invalid"},
            {"Origin": "null"},
            {"Sec-Fetch-Site": "cross-site"},
            {"Origin": f"http://127.0.0.1:{self.port + 1}"},
        ]
        for headers in invalid_headers:
            with self.subTest(headers=headers):
                status, _, body = self.request(headers=headers)
                self.assertEqual(status, 403)
                self.assertNotIn(MARKER, body)
        self.assertEqual(self.calls, 0)

    def test_static_files_health_and_traversal_do_not_query_provider(self):
        self.assertEqual(self.request("/")[0], 200)
        self.assertEqual(self.request("/api/health")[0], 200)
        (self.dist / "escape.txt").symlink_to(self.secret_file)
        for path in ("/../private.txt", "/%2e%2e/private.txt", "/escape.txt",
                     "/tools/check_ghl_accounts.py", "/.git/config"):
            with self.subTest(path=path):
                status, _, body = self.request(path)
                self.assertIn(status, (403, 404))
                self.assertNotIn(MARKER, body)
        self.assertEqual(self.calls, 0)

    def test_absolute_request_target_is_rejected_before_provider_lookup(self):
        status, _, _ = self.request("http://attacker.invalid/api/social/accounts",
                                    headers={"Host": f"127.0.0.1:{self.port}"})
        self.assertEqual(status, 400)
        self.assertEqual(self.calls, 0)

    def test_head_api_does_not_fetch_or_include_a_body(self):
        status, _, body = self.request(method="HEAD")
        self.assertEqual(status, 405)
        self.assertEqual(body, "")
        self.assertEqual(self.calls, 0)

    def test_unsupported_methods_never_query_provider(self):
        for method in ("POST", "PUT", "DELETE", "OPTIONS", "PATCH"):
            with self.subTest(method=method):
                status, _, body = self.request(method=method)
                self.assertIn(status, (403, 405, 501))
                self.assertNotIn(MARKER, body)
        self.assertEqual(self.calls, 0)

    def test_cache_refreshes_after_expiry_and_is_shared_by_requests(self):
        first = self.request()
        second = self.request()
        self.assertEqual(first[0], 200)
        self.assertEqual(second[0], 200)
        self.assertEqual(json.loads(first[2])["checkedAt"],
                         json.loads(second[2])["checkedAt"])
        self.assertTrue(json.loads(second[2])["cache"]["fromCache"])
        self.assertEqual(self.calls, 1)
        self.now += 61
        self.assertEqual(self.request()[0], 200)
        self.assertEqual(self.calls, 2)

    def test_cached_snapshot_cannot_be_mutated_through_returned_objects(self):
        first = self.store.get_snapshot()
        first["accounts"][0]["name"] = MARKER
        first["capabilities"]["accountRead"] = "not_verified"
        first["missingPlatforms"].clear()
        second = self.store.get_snapshot()
        self.assertNotIn(MARKER, json.dumps(second))
        self.assertEqual(second["capabilities"], {"accountRead": "verified"})
        self.assertIn("linkedin", second["missingPlatforms"])
        self.assertEqual(self.calls, 1)

    def test_concurrent_cold_requests_make_one_provider_call(self):
        barrier = threading.Barrier(8)

        def query():
            barrier.wait(timeout=5)
            return self.request()[0]

        with ThreadPoolExecutor(max_workers=8) as pool:
            statuses = list(pool.map(lambda _: query(), range(8)))
        self.assertEqual(statuses, [200] * 8)
        self.assertEqual(self.calls, 1)

    def test_provider_failure_is_a_safe_non_success_response(self):
        self.loader_error = ghl.AccountCheckError("mock_failure", "Safe mock failure",
                                                  http_status=503)
        status, headers, body = self.request()
        self.assertEqual(status, 503)
        self.assertNotIn(MARKER, body)
        self.assertIn("no-store", headers.get("Cache-Control", ""))
        self.assertIsInstance(json.loads(body), dict)

    def test_expired_cache_failure_does_not_claim_a_fresh_success(self):
        self.assertEqual(self.request()[0], 200)
        self.now += 61
        self.loader_error = ghl.AccountCheckError("mock_failure", "Safe mock failure",
                                                  http_status=503)
        status, _, body = self.request()
        self.assertEqual(status, 503)
        self.assertNotIn(MARKER, body)

    def test_unexpected_loader_exception_is_redacted_at_http_boundary(self):
        self.loader_error = RuntimeError(MARKER)
        logs = io.StringIO()
        with contextlib.redirect_stdout(logs), contextlib.redirect_stderr(logs):
            status, _, body = self.request()
        self.assertEqual(status, 502)
        self.assertNotIn(MARKER, body + logs.getvalue())

    def test_complete_http_response_filters_credentials_from_provider_payload(self):
        raw = dict(ACCOUNT, accessToken=MARKER, refreshToken=MARKER)
        opener = FakeOpener(FakeResponse({
            "success": True, "results": {"accounts": [raw]},
        }))
        self.store.loader = lambda: ghl.fetch_accounts(LOCATION, MARKER, opener)
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            status, _, body = self.request()
        self.assertEqual(status, 200)
        self.assertNotIn(MARKER, body + output.getvalue())
        self.assertTrue(json.loads(body)["accounts"][0]["expirationDiscrepancy"])

    def test_empty_success_is_distinct_from_upstream_failure(self):
        self.loader_result = inventory([])
        status, _, body = self.request()
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["accounts"], [])
        self.assertEqual(data["accountCount"], 0)
        self.assertEqual(data["capabilities"]["accountRead"], "verified")

    def test_statistics_denial_stays_unavailable_without_zero_filled_counts(self):
        status, headers, body = self.request("/api/social/statistics")
        self.assertEqual(status, 200)
        self.assertIn("no-store", headers.get("Cache-Control", ""))
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        data = json.loads(body)
        self.assertEqual(data["source"], "gohighlevel")
        self.assertEqual(data["status"], "unavailable")
        self.assertEqual(data["httpStatus"], 401)
        self.assertEqual(data["error"]["upstreamStatus"], 401)
        self.assertEqual(data["totals"], {})
        self.assertNotIn(MARKER, body)
        self.assertEqual(self.calls, 0)
        self.assertEqual(self.statistics_calls, 1)

    def test_statistics_route_preserves_security_guards_and_read_only_methods(self):
        path = "/api/social/statistics"
        status, _, _ = self.request(path, headers={"Origin": "https://attacker.invalid"})
        self.assertEqual(status, 403)
        status, _, _ = self.request(path, headers={"Host": "attacker.invalid"})
        self.assertEqual(status, 403)
        for method in ("HEAD", "POST", "PUT", "DELETE"):
            with self.subTest(method=method):
                status, _, _ = self.request(path, method=method)
                self.assertEqual(status, 405)
        self.assertEqual(self.statistics_calls, 0)
        self.assertEqual(self.calls, 0)

    def test_statistics_cache_preserves_snapshot_until_ttl(self):
        self.statistics_result.update(status="available", httpStatus=200,
                                      totals={"posts": 0, "followers": 12})
        self.statistics_result.pop("error")
        first = json.loads(self.request("/api/social/statistics")[2])
        second = json.loads(self.request("/api/social/statistics")[2])
        self.assertEqual(first["totals"], {"posts": 0, "followers": 12})
        self.assertTrue(second["cache"]["fromCache"])
        self.assertEqual(first["checkedAt"], second["checkedAt"])
        self.assertEqual(self.statistics_calls, 1)
        self.now += 61
        self.assertEqual(self.request("/api/social/statistics")[0], 200)
        self.assertEqual(self.statistics_calls, 2)

    def test_statistics_timeout_and_unexpected_failure_are_safely_reported(self):
        errors = [
            (ghl.AccountCheckError("UPSTREAM_TIMEOUT", "Safe timeout", 504), 504),
            (RuntimeError(MARKER), 502),
        ]
        for error, expected in errors:
            with self.subTest(error_type=type(error).__name__):
                self.statistics_error = error
                logs = io.StringIO()
                with contextlib.redirect_stdout(logs), contextlib.redirect_stderr(logs):
                    status, _, body = self.request("/api/social/statistics")
                self.assertEqual(status, expected)
                self.assertNotIn(MARKER, body + logs.getvalue())
                self.assertIn("error", json.loads(body))

    def test_request_path_does_not_echo_fake_secret_to_logs(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            self.request("/missing?credential=" + MARKER)
        self.assertNotIn(MARKER, output.getvalue())


if __name__ == "__main__":
    unittest.main()
