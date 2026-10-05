# EP-GHL-ACCESS-20261004-01 — authenticated account check

Observed October 5, 2026 at approximately 1:08 AM EDT (05:08 UTC).

**Result: VERIFIED — GoHighLevel account-read access works for location `2cCtht46QwERbvs3uITM`.** Claude's close-out, supplied by the user, reports that the canonical handoff document and AI JOB LOG row 56 were updated and the job is **CLOSED — authenticated account-read access VERIFIED**. This file is the local handoff copy; Codex did not independently query those external records.

## Execution and credential presence

- Command executed from the project root: `GHL_LOCATION_ID=2cCtht46QwERbvs3uITM python3 tools/check_ghl_accounts.py`.
- Initial account check succeeded. The helper was then extended to include the documented `expire` field and observed HTTP status; the enriched read-only check also succeeded.
- Request: `GET https://services.leadconnectorhq.com/social-media-posting/2cCtht46QwERbvs3uITM/accounts`, API version `2021-07-28`.
- HTTP status: **200**. Command exit status: **0**. Accounts returned: **4**.
- `GHL_ACCESS_TOKEN` has a saved binding in the published configuration and is present in the running environment. The token was used through the supported proxy route and was never printed, recorded, or copied into source.
- `GHL_LOCATION_ID` is present. The request explicitly targeted the specified location.
- Published configuration version: `a172fd3b-f5f8-4692-bca3-bd33dc37defc~cecfgver_6ac315140914819c961e3de9a178fed7`. The configuration read reports no pending draft and no pending runtime requirements.
- Runtime metadata still reports generic readiness states as `unknown`; the successful authenticated request independently verifies this operation's actual access.

## Returned accounts

The dates below are the exact API `expire` values and their America/New_York equivalents. They are recorded separately from the API's explicit `isExpired` flags.

| Platform | Account name | API account type | API expiration timestamp (UTC) | Expiration timestamp (ET) | `isExpired` | Missing flag | Finding |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Instagram | entrepreneurshipprofessor | profile | 2026-12-04T04:57:09.136Z | Dec 3, 2026, 11:57:09 PM EST | false | false | Listed; API reports not expired |
| LinkedIn | Bert Seither, DBA | profile | 2026-12-01T10:50:46.737Z | Dec 1, 2026, 5:50:46 AM EST | false | false | Listed; API reports not expired |
| TikTok | entrepreneurshipprof | business | 2027-10-02T10:54:18.235Z | Oct 2, 2027, 6:54:18 AM EDT | false | false | Listed; API reports not expired |
| YouTube | Dr. Bert Seither | profile | 2026-10-05T04:36:06.992Z | Oct 5, 2026, 12:36:06 AM EDT | false | false | Listed; expiration timestamp is past observation time despite API reporting not expired |
| Facebook | No account returned | — | — | — | unknown | true | Missing from this inventory; consistent with Claude Chrome's reported UI findings |

### Exact returned account IDs

- Instagram: `6ac32f51b9b1fffc8877c2e7_2cCtht46QwERbvs3uITM_17841430070835087`
- LinkedIn: `6abf8db31561f5f050679baa_2cCtht46QwERbvs3uITM_M2EZQl_SqN_profile`
- TikTok: `6abf8e869b50a04808d828b6_2cCtht46QwERbvs3uITM_0005byRAlEHOHPXg4Ji7NdTPG8wBAxdO73_business`
- YouTube: `6abf8e45b9b1fffc8846efba_2cCtht46QwERbvs3uITM_UCfpxznhUUBSHxjT-ekSXQrQ_profile`

## Interpretation and remaining exceptions

- Instagram, LinkedIn, TikTok, and YouTube are all returned by the authenticated account-list API. No returned account has `isExpired: true`; none is missing.
- YouTube has a **timestamp/flag discrepancy**. Its `expire` field predates the observed run, while `isExpired` is explicitly false. Claude Chrome separately reported no reconnect prompt, no account under the Expired filter, and a UI validity value of `-`. Do not infer that the channel is expired or that this timestamp represents long-term platform authorization without further evidence.
- Claude Chrome's statement that the YouTube channel is unverified and has thumbnail/long-video restrictions is a browser-observed report, not something this API request tested.
- The successful request proves sufficient authorization for the account-read endpoint. Claude subsequently inspected the integration's native Scopes step and reports that `socialplanner/account.readonly` is its sole scope. This resolves the scope exception based on Claude's readback, rather than API scope introspection by Codex.
- Publishing, analytics, and content creation were not tested or performed. Facebook is not connected according to this inventory; adding it was not part of this check.
- No lease write, lease release, integration modification, or application deployment was performed by Codex during validation.

## External handoff delivery

Canonical document supplied by the user: [Google handoff document](https://docs.google.com/document/d/1_HAf-w_SLFMnPqvByIfqMzHR9-X7hZgdwY_Tvyb7fDk/edit).

**Codex direct external write status: UNAVAILABLE.** This session exposes no Google Docs/Drive write tool or declared Google outbound identity/credential binding, and its network policy contains no Google Docs/Drive API destinations. No unsupported credential reuse or proxy bypass was attempted. Claude reports that it appended the sanitized result to the canonical Google document and updated AI JOB LOG row 56. Delivery was relayed through Bert; this was not a direct Codex-to-Claude handoff or an independently verified external write by Codex.

## Claude close-out supplied by the user

Report dated October 5, 2026 at 11:12 AM EDT (15:12 UTC); follow-up API read was around 11:09 AM EDT (15:09 UTC).

- **Canonical records:** Claude reports an appended close-out titled "CODEX AUTHENTICATED ACCOUNT-READ RESULT, SCOPE + YOUTUBE READBACK, CLOSE-OUT" in the existing handoff document and an updated AI JOB LOG row 56. The stated job status is **CLOSED — authenticated account-read access VERIFIED**. It reports a preflight receipt referencing Gate `GOV-2026-09-23.1`.
- **Integration:** `Entrepreneurship Professor — BOS Access`, ID `6ac3148cde99fd539e34a394`. Claude opened Edit and the Scopes step, observed exactly one scope (View Social Media Accounts — `socialplanner/account.readonly`), then canceled without Update or Rotate. It reports Updated At remained Oct 4, 11:07 PM and Last Used remained Oct 5, 1:07 AM ET. There is no remaining scope exception on this evidence.
- **YouTube UI:** Connected; Profile; Validity `-`; no reconnect prompt; Expired filter count 0. The channel-verification restriction is separate from GHL account-read access.
- **YouTube later API observation:** `isExpired: false`, `expire: 2026-10-05T09:19:03Z` (Oct 5, 5:19:03 AM EDT), still earlier than the reported read time. This is a later reported observation; it does not replace Codex's original snapshot above. The field's meaning remains unresolved. No automatic-refresh explanation is established.
- **Lease:** Claude reports that `EP-ACCESS-LEASE-01` had already been released in the implementation record at 03:10 UTC. This job holds no lease. Claude released no lease and touched no other job's lease during close-out.
- **Changes:** Claude reports no GHL modification during the scope/YouTube readbacks or close-out. No credential values were included.
- **Review:** Codex independently executed the authenticated account check. Claude's scope and YouTube readbacks were not checked by a separate reviewer. The closure report is user-supplied evidence, not a direct external-record read by Codex.

### Remaining recorded exceptions

| Exception | Status |
| --- | --- |
| E1 — YouTube expiration field meaning | Unresolved; API says not expired despite a past timestamp |
| E2 — YouTube channel verification | Channel unverified according to Claude's UI readback; thumbnail/long-video restrictions remain |
| E3 — Facebook | Not connected/not returned |
| E4 — Analytics and publishing | Not tested; current grant is account-read only |
| E5 — Direct worker evidence delivery | Codex's result reached the canonical record through Bert; direct automated handoff remains unproven |

These exceptions do not invalidate the successful account-read request or reopen the completed access job. They do not establish broader integration capabilities or automatic cross-lane coordination.

## Subsequent implementation observation — account job remains closed

On October 5, following Bert's approval, Claude reports updating the same
integration to exactly the account-read and statistics-read scopes, with no
rotation, and releasing `EP-STATS-SCOPE-LEASE-01`. Codex independently reran both
helpers using the existing EP token: accounts and statistics returned HTTP 200.
Instagram returned 41 impressions, reach 6, and 3 followers; TikTok returned
actual zeros. YouTube supplied no metrics; LinkedIn personal-profile aggregate
analytics is unsupported. This is subsequent product implementation evidence,
not a reopened access job. E4's historical analytics limitation is superseded by
the verified read; publishing remains untested and unauthorized by this packet.
The [implementation report](LIVE-INTEGRATION-IMPLEMENTATION.md) and
[sanitized snapshot](evidence/2026-10-05-ghl-live-readback.json) retain the current
observations. Direct hosted BOS delivery has not occurred.
