"""Offline validation of read-only statistics, strict selectors and redaction."""
import contextlib
import io
import json
from pathlib import Path
import ssl
import sys
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, ProxyHandler
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_ghl_statistics as statistics
from check_ghl_accounts import AccountCheckError


SECRET = "FAKE-STATISTICS-SECRET-NEVER-LOG"
LOCATION = "mock-location"


def account(platform="instagram", account_type="profile", profile_id="mock-profile"):
    return {"id": "mock-account-NOT-profile", "profileId": profile_id,
            "platform": platform, "type": account_type, "isExpired": False}


def loader(records):
    return lambda location, token: {"locationId": location, "accounts": records}


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
    def __init__(self, payload=None, data=None, error=None):
        self.response = FakeResponse(payload, data)
        self.error = error
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error is not None:
            raise self.error
        return self.response


class StatisticsTests(unittest.TestCase):
    def fetch(self, opener, records=None):
        return statistics.fetch_statistics(
            LOCATION, SECRET, opener,
            loader([account()] if records is None else records),
        )

    def test_uses_documented_profile_id_v3_and_fixed_read_endpoint(self):
        opener = FakeOpener({"results": {"totals": {"posts": 0}}})
        result = self.fetch(opener)
        request, timeout = opener.calls[0]
        self.assertEqual(request.full_url,
                         statistics.API_ORIGIN + "/social-media-posting/statistics?locationId=" + LOCATION)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Version"), "v3")
        self.assertEqual(json.loads(request.data), {
            "profileIds": ["mock-profile"], "platforms": ["instagram"],
        })
        self.assertEqual(timeout, 30)
        self.assertEqual(result["totals"], {"posts": 0})
        self.assertEqual(result["period"], statistics.PERIOD)
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertNotIn("mock-account-NOT-profile", json.dumps(result))

    def test_no_fallback_to_account_id_when_profile_id_missing(self):
        records = [dict(account(), profileId=None)]
        opener = FakeOpener({"results": {"totals": {"posts": 9}}})
        result = self.fetch(opener, records)
        self.assertEqual(opener.calls, [])
        self.assertEqual(result["totals"], {})
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["excludedAccounts"][0]["reason"], "PROFILE_ID_UNAVAILABLE")

    def test_excludes_linkedin_personal_and_unverified_tiktok_type(self):
        records = [account("linkedin", "profile", "li-profile"),
                   account("tiktok", "profile", "tt-creator")]
        opener = FakeOpener({"results": {}})
        result = self.fetch(opener, records)
        self.assertEqual(opener.calls, [])
        self.assertEqual({r["reason"] for r in result["excludedAccounts"]},
                         {"LINKEDIN_PAGE_REQUIRED", "TIKTOK_BUSINESS_REQUIRED"})
        self.assertNotIn("li-profile", json.dumps(result))

    def test_page_and_business_account_types_are_eligible(self):
        records = [account("linkedin", "PAGE", "li-page"),
                   account("tiktok", "BUSINESS", "tt-business"),
                   account("tiktok-business", "profile", "tt-platform-business")]
        opener = FakeOpener({"results": {"totals": {"posts": 2}}})
        result = self.fetch(opener, records)
        body = json.loads(opener.calls[0][0].data)
        self.assertEqual(body["profileIds"], ["li-page", "tt-business", "tt-platform-business"])
        self.assertEqual(body["platforms"], ["linkedin", "tiktok"])
        self.assertEqual(result["excludedAccounts"], [])

    def test_explicit_expired_account_excluded_but_stale_timestamp_is_not_assumed_expired(self):
        records = [dict(account("youtube", "channel", "yt-expired"), isExpired=True),
                   dict(account("youtube", "channel", "yt-current"),
                        expire="2000-01-01T00:00:00Z", isExpired=False)]
        opener = FakeOpener({"results": {"totals": {"posts": 1}}})
        result = self.fetch(opener, records)
        self.assertEqual(json.loads(opener.calls[0][0].data)["profileIds"], ["yt-current"])
        self.assertEqual(result["excludedAccounts"][0]["reason"], "ACCOUNT_EXPIRED")

    def test_only_allowlisted_numeric_counts_are_projected(self):
        payload = {"results": {
            "totals": {"posts": 0, "followers": 123, "accessToken": SECRET},
            "breakdowns": {
                "posts": {"platforms": {"instagram": {"value": 0, "token": SECRET}}},
                "reach": {"platforms": {"instagram": {"value": 24}}},
                "engagement": {"instagram": {"likes": 8, "comments": 2, "shares": 0,
                                               "change": SECRET}},
            },
            "platformTotals": {"followers": {"instagram": {"total": 123, "series": [SECRET]}}},
            "demographics": {"credential": SECRET},
        }, "message": SECRET, "accessToken": SECRET}
        result = self.fetch(FakeOpener(payload))
        instagram = next(p for p in result["platforms"] if p["platform"] == "instagram")
        self.assertEqual(instagram["status"], "available")
        self.assertEqual(instagram["metrics"], {
            "posts": 0, "reach": 24, "likes": 8, "comments": 2, "shares": 0, "followers": 123,
        })
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertNotIn("change", instagram["metrics"])

    def test_missing_metrics_are_unavailable_and_never_zero_filled(self):
        result = self.fetch(FakeOpener({"results": {}}))
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["totals"], {})
        instagram = next(p for p in result["platforms"] if p["platform"] == "instagram")
        self.assertEqual(instagram["metrics"], {})
        self.assertEqual(instagram["unavailableReason"], "NO_METRICS_RETURNED")

    def test_response_cannot_claim_metrics_for_excluded_personal_profile(self):
        payload = {"results": {"breakdowns": {
            "posts": {"platforms": {"linkedin": {"value": 999}, "instagram": {"value": 2}}},
        }}}
        result = self.fetch(FakeOpener(payload), [account(), account("linkedin", "profile", "li-profile")])
        linkedin = next(p for p in result["platforms"] if p["platform"] == "linkedin")
        self.assertEqual(linkedin["metrics"], {})
        self.assertEqual(linkedin["status"], "unavailable")

    def test_unsafe_count_values_and_structures_fail_without_echoing(self):
        payloads = [
            {"results": {"totals": {"posts": value}}}
            for value in (SECRET, True, -1, float("nan"), float("inf"), {"token": SECRET}, None)
        ] + [
            {"results": {"totals": [SECRET]}},
            {"results": {"breakdowns": {"posts": {"platforms": {"instagram": SECRET}}}}},
            {"results": None, "message": SECRET},
            {"results": {}, "success": False, "message": SECRET},
        ]
        for payload in payloads:
            with self.subTest(payload_kind=type(payload.get("results")).__name__):
                with self.assertRaises(AccountCheckError) as caught:
                    self.fetch(FakeOpener(payload))
                self.assertEqual(caught.exception.code, "UPSTREAM_RESPONSE_INVALID")
                self.assertNotIn(SECRET, str(caught.exception))

    def test_conflicting_provider_metric_sources_are_not_arbitrarily_resolved(self):
        payload = {"results": {
            "breakdowns": {"impressions": {"platforms": {"instagram": {"value": 3}}}},
            "platformTotals": {"impressions": {"instagram": {"total": 5}}},
        }}
        with self.assertRaises(AccountCheckError):
            self.fetch(FakeOpener(payload))

    def test_auth_errors_return_only_local_diagnostics_and_http_status(self):
        for status in (401, 403):
            with self.subTest(status=status):
                error = HTTPError("https://mock.invalid", status, SECRET, {}, io.BytesIO(SECRET.encode()))
                result = self.fetch(FakeOpener(error=error))
                self.assertEqual(result["status"], "unavailable")
                self.assertEqual(result["httpStatus"], status)
                self.assertEqual(result["requiredScope"], statistics.REQUIRED_SCOPE)
                self.assertNotIn(SECRET, json.dumps(result))
                self.assertEqual(result["totals"], {})

    def test_other_network_provider_and_body_errors_are_redacted(self):
        errors = [HTTPError("https://mock.invalid", 302, SECRET, {}, io.BytesIO(SECRET.encode())),
                  HTTPError("https://mock.invalid", 500, SECRET, {}, io.BytesIO(SECRET.encode())),
                  URLError(SECRET), URLError(TimeoutError(SECRET)), TimeoutError(SECRET),
                  OSError(SECRET), ValueError(SECRET)]
        for error in errors:
            with self.subTest(error_type=type(error).__name__):
                with self.assertRaises(AccountCheckError) as caught:
                    self.fetch(FakeOpener(error=error))
                self.assertNotIn(SECRET, str(caught.exception))
        for body in (SECRET.encode(), b"\xff" + SECRET.encode(),
                     b"x" * (statistics.MAX_RESPONSE_BYTES + 1)):
            with self.assertRaises(AccountCheckError) as caught:
                self.fetch(FakeOpener(data=body))
            self.assertNotIn(SECRET, str(caught.exception))

    def test_bad_inputs_stop_before_credential_is_sent(self):
        for token in (None, SECRET + "\n", SECRET + "é", True):
            opener = FakeOpener({"results": {}})
            with patch.dict(statistics.os.environ, {}, clear=True):
                with self.assertRaises(AccountCheckError) as caught:
                    statistics.fetch_statistics(LOCATION, token, opener, loader([account()]))
            self.assertEqual(opener.calls, [])
            self.assertNotIn(SECRET, str(caught.exception))
        with self.assertRaises(AccountCheckError):
            statistics.fetch_statistics("invalid/location", SECRET, FakeOpener(), loader([account()]))

    def test_mismatched_location_inventory_and_profile_limit_fail_locally(self):
        with self.assertRaises(AccountCheckError):
            statistics.fetch_statistics(LOCATION, SECRET, FakeOpener(),
                                        lambda *args: {"locationId": "other", "accounts": [account()]})
        records = [account(profile_id="p" + str(n)) for n in range(101)]
        opener = FakeOpener()
        with self.assertRaises(AccountCheckError):
            self.fetch(opener, records)
        self.assertEqual(opener.calls, [])

    def test_default_opener_preserves_proxy_tls_and_denies_redirects(self):
        with patch("urllib.request.getproxies", return_value={"https": "http://mock-proxy.invalid:8080"}):
            opener = statistics.build_opener(statistics.NoRedirects())
        proxy = next(h for h in opener.handlers if isinstance(h, ProxyHandler))
        self.assertEqual(proxy.proxies, {"https": "http://mock-proxy.invalid:8080"})
        https = next(h for h in opener.handlers if isinstance(h, HTTPSHandler))
        if https._context is not None:
            self.assertEqual(https._context.verify_mode, ssl.CERT_REQUIRED)
            self.assertTrue(https._context.check_hostname)
        request = statistics.Request(statistics.API_ORIGIN + "/mock")
        for status in (301, 302, 303, 307, 308):
            self.assertIsNone(statistics.NoRedirects().redirect_request(
                request, None, status, "", {}, "https://untrusted.invalid"))

    def test_cli_does_not_print_raw_auth_error_body(self):
        opener = FakeOpener(error=HTTPError("https://mock.invalid", 403, SECRET, {}, io.BytesIO(SECRET.encode())))
        summary = self.fetch(opener)
        with patch.object(statistics, "fetch_statistics", return_value=summary):
            output, errors = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                code = statistics.main()
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["httpStatus"], 403)
        self.assertNotIn(SECRET, output.getvalue() + errors.getvalue())


if __name__ == "__main__":
    unittest.main()
