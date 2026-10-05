# Live integration implementation

The Audience page now loads actual GoHighLevel account identities through a local Python service. Analytics and direct BOS result delivery have separate helpers and explicit readiness checks. This implementation is prepared in the project checkout; it does not establish a production deployment or a completed unattended worker loop.

## Account inventory and development service

Start from the repository root:

```sh
python3 tools/serve_ep.py --port 8000
```

The server binds only `127.0.0.1`. It serves `dist` and three same-origin, read-only endpoints:

| Endpoint | Behavior |
| --- | --- |
| `GET /api/health` | Checks the local service without contacting GoHighLevel. |
| `GET /api/social/accounts` | Returns selected account metadata, the observation time, expiration evidence, missing platforms, and cache information. |
| `GET /api/social/statistics` | Returns a selected analytics projection or explicit unavailability. Its local HTTP success does not imply successful upstream analytics authorization. |

`tools/check_ghl_accounts.py` uses the existing `GHL_LOCATION_ID` and securely bound `GHL_ACCESS_TOKEN`. Its upstream operation is `GET /social-media-posting/{locationId}/accounts` with `Version: 2021-07-28`. The required scope is `socialplanner/account.readonly`. The projection includes account and platform identifiers, name, type, `expire`, and `isExpired`; it excludes credential and arbitrary metadata fields.

The adapter preserves the explicit expiration flag separately from the timestamp. Missing evidence remains unknown. A past timestamp with `isExpired: false` produces a discrepancy for review; it does not establish automatic refresh behavior or an expired connection.

`dist/ep-social-accounts.js` adds the inventory above the Audience preview sections, renders provider fields with `textContent`, and labels the existing analytics, recommendations, and audience insights as preview data. It provides refresh, loading, failure, and confirmed-empty states. It does not populate a failed lookup with sample accounts. Observation dates use `America/New_York`.

Account and statistics stores share results for up to 60 seconds, serialize concurrent refreshes, and return copies. A failed refresh cannot relabel stale successful data as newly verified. Browser responses use `Cache-Control: no-store`; the UI states that refresh may use the short server cache.

The service validates Host, Origin, and cross-site request metadata before processing requests. It rejects mutating local methods, absolute request targets, and static paths or symlinks escaping `dist`. Upstream clients preserve proxy routing and TLS verification, reject redirects, limit response sizes, and return authored diagnostics instead of raw credential-bearing exceptions. Credentials remain server-side.

## Observed account access and analytics boundary

The authenticated account lookup succeeded with HTTP 200 and returned Instagram, LinkedIn, TikTok, and YouTube. Facebook was not returned. The original account-read job, `EP-GHL-ACCESS-20261004-01`, is closed according to the user-supplied Claude close-out. Its observations and exceptions remain in `docs/EP-GHL-ACCESS-20261004-01-HANDOFF.md`.

The live statistics probe returned **upstream HTTP 401** and `STATISTICS_CREDENTIAL_REJECTED`; account lookup still succeeded. This observation does not establish why that particular statistics request was rejected. No live analytics success is claimed. The documented statistics operation requires `socialplanner/statistics.readonly` in addition to the existing account-read capability.

`tools/check_ghl_statistics.py` selects exact `profileId` values from the configured location's inventory. It never substitutes the account `id`, accepts no manually supplied profile IDs, and performs the documented V3 analytics read using `POST /social-media-posting/statistics?locationId=...` with `Version: v3`. This POST retrieves statistics; it does not publish content or modify accounts.

The helper excludes LinkedIn personal profiles because the documented aggregate analytics support LinkedIn Pages. TikTok selection requires explicit Business account metadata. An account is excluded as expired only when the API explicitly reports `isExpired: true`. Missing selectors or unsupported account types remain unavailable with an explanation.

The output includes only supported numeric count fields and identifies the provider's last-seven-complete-days period and preceding-seven-days comparison. Missing metrics are not estimated or filled with zero. A genuine returned zero remains zero. No publishing permission or `socialplanner/post.write` is required for this work.

Useful commands:

```sh
python3 tools/check_ghl_accounts.py
python3 tools/check_ghl_statistics.py
python3 -m unittest discover -s tests -v
for file in dist/*.js; do node --check "$file" || exit; done
```

## Existing BOS return contract

`tools/bos_handoff.py` returns a complete Worker Result v1 to the existing BOS API at `https://bos-workforce-orchestrator.onrender.com`. `tools/schemas/worker-result-v1.schema.json` is the pinned existing contract, rather than a project-specific replacement queue or dispatcher.

The client has three commands: `validate` checks a supplied result offline; `status` reads the existing canonical handoff; `submit` checks the current assignment, posts the result once, and requires matching persistent readback. Each command requires the actual task, job, and attempt identifiers. Submission requires a current `WORKING` assignment claimed by `bos-worker`, its existing cost policy, a matching result, and the supported `BOS_WORKER_KEY` binding. The fixed HTTPS origin and redirect guard prevent retargeting the worker credential.

The client cannot create assignments, claim work, approve its own result, release changes, or deploy. A delivered result can become `REVIEW_READY`; independent QA and release authority remain with BOS. An uncertain POST is not automatically retried. A later status read reconciles a matching existing result without duplicate submission.

Live BOS delivery remains unverified: `BOS_WORKER_KEY` is not supplied to this session, and applying the prepared BOS destination/secret requirements has not been verified. The latest environment draft is saved and reports `requires_publish: true`. It adds the BOS origin, a `BOS_BASE_URL` suggestion, and the scoped worker-key requirement while preserving the three GHL destinations. No key value was supplied and the running instance was not changed by the save. A current canonical product implementation task/job/attempt must also be supplied. Do not reuse or reopen the closed GHL account-read job.

## Validation and completion

The 30 independent account/server tests passed, covering credential redaction, malformed versus empty inventory, expiration evidence, redirect/proxy/TLS behavior, network and body-read timeouts, loopback request guards, static isolation, caching, concurrency, and account/statistics failure states. The statistics lane reports 16 passing offline tests for account selection, supported projections, explicit unavailability, and credential-safe failures. BOS tests cover contract validation, stale or foreign assignments, cost policy, single submission, matching readback, and independent review boundaries. The optional existing-server BOS test requires a read-only reference checkout and records a skip when that checkout is absent; it is not a live production handoff.

The combined Python suite passed **58 tests**, with no skips in this environment,
including the roundtrip against the actual BOS server in a temporary local
fixture. JavaScript syntax and whitespace checks also passed.

The root lane verified the served application in a browser: four returned account cards, refresh of both live sections, the actual analytics upstream-401 unavailable state, all six navigation pages, the ENT 330 preparation drawer, a 390-pixel mobile viewport without horizontal overflow, honest failure/empty states, and no JavaScript page errors. It checked that credentials did not appear in either API response or rendered page. Independent frontend checks used mocked responses to verify partial/zero/missing metrics, hostile labels rendered as text, denied and failed analytics clearing live values, malformed reporting periods, preview drawer labels, navigation remounts, and keyboard refresh. These checks establish local application behavior, not analytics authorization, production deployment, or cross-agent delivery.

`docs/CC-INTEGRATION-COMPLETION.md` contains one bounded completion packet for the existing coordinator. Publication of the prepared cloud configuration, secure BOS credential access, a current assignment, successful authorized statistics read, and direct result readback remain to be verified.
