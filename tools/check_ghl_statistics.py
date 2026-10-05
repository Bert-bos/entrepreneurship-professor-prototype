"""Retrieve a small, allowlisted projection of GHL Social Planner analytics.

The provider uses POST for this read-only operation. No publishing or account
mutation endpoint is called. Account selectors come only from the configured
location's account lookup; this CLI accepts no manually supplied profile IDs.

Contract: GoHighLevel/highlevel-api-docs, apps/v3/social-planner-v3.json,
revision 0af86a4cbd48c66a4071c7e509d1079f9f10ed17, get-statistics.
"""
import json
import math
import os
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener

from check_ghl_accounts import (
    API_ORIGIN, DEFAULT_LOCATION, AccountCheckError, NoRedirects, fetch_accounts,
)


REQUIRED_SCOPE = "socialplanner/statistics.readonly"
TARGET_PLATFORMS = ("instagram", "youtube", "linkedin", "tiktok")
TOTAL_COUNTS = ("posts", "likes", "followers", "impressions", "comments")
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
PERIOD = {
    "kind": "lastSevenCompleteDays",
    "excludeToday": True,
    "comparison": "precedingSevenDays",
}
REASONS = {
    "NOT_CONNECTED": "No account for this platform was returned by GoHighLevel.",
    "LINKEDIN_PAGE_REQUIRED": "GoHighLevel aggregated analytics supports LinkedIn Pages, not personal profiles.",
    "TIKTOK_BUSINESS_REQUIRED": "GoHighLevel aggregated analytics requires a verified TikTok Business account type.",
    "PROFILE_ID_UNAVAILABLE": "The account lookup did not supply a usable profileId; account id is not a substitute.",
    "ACCOUNT_EXPIRED": "GoHighLevel reports that the account token has expired.",
    "NO_METRICS_RETURNED": "GoHighLevel did not return supported count metrics for this selection.",
    "STATISTICS_ACCESS_DENIED": "GoHighLevel denied analytics access; this operation requires socialplanner/statistics.readonly.",
    "STATISTICS_CREDENTIAL_REJECTED": "GoHighLevel could not authorize analytics; verify the credential and socialplanner/statistics.readonly scope.",
}


class StatisticsResponseError(ValueError):
    """A locally authored validation error, never provider response contents."""


def _count(value):
    # bool is an int subclass; provider count strings/objects must not enter the
    # public projection, even if a nested object contains credential material.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StatisticsResponseError("GoHighLevel returned an invalid statistics count.")
    if value < 0 or (isinstance(value, float) and not math.isfinite(value)):
        raise StatisticsResponseError("GoHighLevel returned an invalid statistics count.")
    return value


def _optional_object(container, key):
    if key not in container:
        return {}
    value = container[key]
    if not isinstance(value, dict):
        raise StatisticsResponseError("GoHighLevel returned an invalid statistics structure.")
    return value


def _selection(inventory, location):
    if (not isinstance(inventory, dict)
            or inventory.get("locationId") != location
            or not isinstance(inventory.get("accounts"), list)):
        raise AccountCheckError("ACCOUNT_INVENTORY_INVALID", "The configured location's account inventory is invalid.")
    selected = {platform: [] for platform in TARGET_PLATFORMS}
    connected = {platform: 0 for platform in TARGET_PLATFORMS}
    excluded = []
    for account in inventory["accounts"]:
        if not isinstance(account, dict):
            raise AccountCheckError("ACCOUNT_INVENTORY_INVALID", "The configured location's account inventory is invalid.")
        raw_platform = account.get("platform")
        if not isinstance(raw_platform, str):
            continue
        raw_platform = raw_platform.lower()
        platform = "tiktok" if raw_platform == "tiktok-business" else raw_platform
        if platform not in selected:
            continue
        connected[platform] += 1
        account_type = account.get("type")
        account_type = account_type.lower() if isinstance(account_type, str) else None
        reason = None
        if platform == "linkedin" and account_type != "page":
            reason = "LINKEDIN_PAGE_REQUIRED"
        elif platform == "tiktok" and not (
            raw_platform == "tiktok-business"
            or account_type in ("business", "business_account", "business-account")
        ):
            reason = "TIKTOK_BUSINESS_REQUIRED"
        elif account.get("isExpired") is True:
            reason = "ACCOUNT_EXPIRED"
        else:
            profile_id = account.get("profileId")
            if (not isinstance(profile_id, str)
                    or not re.fullmatch(r"[A-Za-z0-9:_-]{1,256}", profile_id)):
                reason = "PROFILE_ID_UNAVAILABLE"
        if reason:
            # Never project an account name, identifier, or arbitrary metadata.
            excluded.append({"platform": platform, "reason": reason, "message": REASONS[reason]})
        elif profile_id not in selected[platform]:
            selected[platform].append(profile_id)
    profile_ids = list(dict.fromkeys(
        profile_id for platform in TARGET_PLATFORMS for profile_id in selected[platform]
    ))
    if len(profile_ids) > 100:
        raise AccountCheckError("ACCOUNT_SELECTION_LIMIT", "The statistics API accepts at most 100 profile IDs per read.", 503)
    return selected, connected, excluded, profile_ids


def _empty_summary(location, selected, connected, excluded):
    platforms = []
    for platform in TARGET_PLATFORMS:
        item = {
            "platform": platform,
            "status": "unavailable",
            "connectedAccountCount": connected[platform],
            "eligibleAccountCount": len(selected[platform]),
            "metrics": {},
        }
        reasons = list(dict.fromkeys(
            record["reason"] for record in excluded if record["platform"] == platform
        ))
        reason = (
            "NO_METRICS_RETURNED" if selected[platform]
            else reasons[0] if len(reasons) == 1
            else "NOT_CONNECTED" if not connected[platform]
            else "NO_METRICS_RETURNED"
        )
        item.update(unavailableReason=reason, message=REASONS[reason])
        platforms.append(item)
    return {
        "locationId": location,
        "status": "unavailable",
        "requiredScope": REQUIRED_SCOPE,
        "httpStatus": None,
        "period": dict(PERIOD),
        "totals": {},
        "platforms": platforms,
        "excludedAccounts": excluded,
    }


def project_statistics(payload, summary, selected):
    if (not isinstance(payload, dict)
            or ("success" in payload and payload["success"] is not True)
            or not isinstance(payload.get("results"), dict)):
        raise StatisticsResponseError("GoHighLevel returned an invalid statistics response.")
    results = payload["results"]
    totals = _optional_object(results, "totals")
    summary["totals"] = {field: _count(totals[field]) for field in TOTAL_COUNTS if field in totals}
    breakdowns = _optional_object(results, "breakdowns")
    platform_totals = _optional_object(results, "platformTotals")
    for item in summary["platforms"]:
        platform = item["platform"]
        if not selected[platform]:
            continue
        metrics = {}
        # All source paths below are explicit count fields in the official V3
        # schema. Missing fields stay missing: no sample, estimate, or zero fill.
        for metric in ("posts", "impressions", "reach"):
            section = _optional_object(breakdowns, metric)
            values = _optional_object(section, "platforms")
            value = _optional_object(values, platform)
            if "value" in value:
                metrics[metric] = _count(value["value"])
        engagement = _optional_object(breakdowns, "engagement")
        engagement_values = _optional_object(engagement, platform)
        for metric in ("likes", "comments", "shares"):
            if metric in engagement_values:
                metrics[metric] = _count(engagement_values[metric])
        for metric in ("impressions", "followers", "likes"):
            values = _optional_object(platform_totals, metric)
            value = _optional_object(values, platform)
            if "total" in value:
                total = _count(value["total"])
                if metric in metrics and metrics[metric] != total:
                    raise StatisticsResponseError("GoHighLevel returned conflicting statistics counts.")
                metrics[metric] = total
        item["metrics"] = metrics
        if metrics:
            item["status"] = "available"
            item.pop("unavailableReason", None)
            item.pop("message", None)
    summary["status"] = "available" if summary["totals"] or any(
        item["status"] == "available" for item in summary["platforms"]
    ) else "unavailable"
    return summary


def fetch_statistics(location=None, token=None, opener=None, account_loader=None):
    """Read provider statistics using only profile IDs from the account lookup.

    account_loader accepts (location, token) and returns fetch_accounts' safe
    inventory. Injection supports cached server inventories and offline tests;
    callers cannot supply profile IDs via this CLI or an HTTP request parameter.
    """
    location = location if location is not None else os.environ.get("GHL_LOCATION_ID", DEFAULT_LOCATION)
    if not isinstance(location, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", location):
        raise AccountCheckError("LOCATION_INVALID", "The configured GoHighLevel location is invalid.", 503)
    token = token if token is not None else os.environ.get("GHL_ACCESS_TOKEN")
    if not token:
        raise AccountCheckError("CREDENTIAL_MISSING", "GoHighLevel access is not configured for this environment.", 503)
    if (not isinstance(token, str) or not token.isascii()
            or any(ord(char) < 33 or ord(char) == 127 for char in token)):
        raise AccountCheckError("CREDENTIAL_INVALID", "The secure GoHighLevel credential binding has an invalid format.", 503)
    loader = account_loader if account_loader is not None else fetch_accounts
    inventory = loader(location, token)
    selected, connected, excluded, profile_ids = _selection(inventory, location)
    summary = _empty_summary(location, selected, connected, excluded)
    if not profile_ids:
        return summary
    platforms = [platform for platform in TARGET_PLATFORMS if selected[platform]]
    request = Request(
        f"{API_ORIGIN}/social-media-posting/statistics?{urlencode({'locationId': location})}",
        data=json.dumps({"profileIds": profile_ids, "platforms": platforms}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}", "Version": "v3",
            "Accept": "application/json", "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        # Keep inherited proxy routing and TLS trust. Deny every redirect rather
        # than forwarding the secret or replaying a POST to another endpoint.
        client = opener if opener is not None else build_opener(NoRedirects())
        with client.open(request, timeout=30) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise StatisticsResponseError("GoHighLevel response exceeded the statistics size limit.")
            if response.status != 200:
                raise AccountCheckError("UPSTREAM_HTTP", "GoHighLevel could not return statistics.", upstream_status=response.status)
            summary["httpStatus"] = response.status
            return project_statistics(json.loads(data), summary, selected)
    except HTTPError as error:
        if error.code in (401, 403):
            reason = "STATISTICS_CREDENTIAL_REJECTED" if error.code == 401 else "STATISTICS_ACCESS_DENIED"
            summary["httpStatus"] = error.code
            summary["error"] = {"code": reason, "message": REASONS[reason], "upstreamStatus": error.code}
            for item in summary["platforms"]:
                if selected[item["platform"]]:
                    item.update(unavailableReason=reason, message=REASONS[reason])
            return summary
        raise AccountCheckError("UPSTREAM_HTTP", "GoHighLevel could not return statistics.", upstream_status=error.code) from None
    except URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise AccountCheckError("UPSTREAM_TIMEOUT", "GoHighLevel did not respond in time. Try again shortly.", 504) from None
        match = re.search(r"Tunnel connection failed:\s*(\d{3})", str(error.reason))
        raise AccountCheckError("UPSTREAM_NETWORK", "GoHighLevel statistics could not be reached from this environment.", proxy_status=int(match.group(1)) if match else None) from None
    except TimeoutError:
        raise AccountCheckError("UPSTREAM_TIMEOUT", "GoHighLevel did not respond in time. Try again shortly.", 504) from None
    except OSError:
        raise AccountCheckError("UPSTREAM_NETWORK", "GoHighLevel statistics could not be reached from this environment.") from None
    except StatisticsResponseError as error:
        raise AccountCheckError("UPSTREAM_RESPONSE_INVALID", str(error)) from None
    except (ValueError, UnicodeError):
        raise AccountCheckError("UPSTREAM_RESPONSE_INVALID", "GoHighLevel returned an invalid statistics response.") from None


def main():
    try:
        summary = fetch_statistics()
    except AccountCheckError as error:
        detail = {"code": error.code, "message": error.message}
        if error.upstream_status is not None:
            detail["upstreamStatus"] = error.upstream_status
        if error.proxy_status is not None:
            detail["proxyStatus"] = error.proxy_status
        print(json.dumps({"status": "error", "requiredScope": REQUIRED_SCOPE, "error": detail}), file=sys.stderr)
        return 2 if error.http_status == 503 else 1
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "available" else 1


if __name__ == "__main__":
    sys.exit(main())
