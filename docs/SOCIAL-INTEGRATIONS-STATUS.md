# Social connection discovery

## Working implementation — October 5, 2026

The local Audience page now loads the four authenticated GHL accounts through
`tools/serve_ep.py` and `GET /api/social/accounts`. Account refresh, six-page
navigation, the meeting drawer, mobile layout, and honest failure/empty states
passed browser validation. Account names and dates are rendered as text;
credentials are excluded from API responses and page markup. Existing metrics
and recommendations remain explicitly labeled preview data.

`tools/check_ghl_statistics.py` implements the documented read-only V3 statistics
request using actual account `profileId` values. After the approved scope update,
the existing EP token now returns **HTTP 200** for both accounts and statistics.
Claude reports exactly two native scopes: `socialplanner/account.readonly` and
`socialplanner/statistics.readonly`, with no token rotation. Codex independently
verified the successful requests and live Audience display.

Instagram returned 41 impressions, reach 6, and 3 followers; TikTok returned
actual zeros. YouTube returned no metrics and remains unavailable. LinkedIn's
personal profile is excluded because GHL aggregate analytics requires a Page.
No missing metric was filled with zero. The development server exposes the
projection at `GET /api/social/statistics` with a 60-second cache. The original
401 and account-only scope are historical findings. The 401 diagnostic now
names the required analytics scope as well as credential validity.

Sanitized current evidence is saved in
[the authenticated readback](evidence/2026-10-05-ghl-live-readback.json).

Following independent review R5, the account response now declares only its own
verified account-read capability. It makes no analytics/publishing declaration;
statistics availability is checked separately. Both endpoints and the Audience
page remained working after the fix. The
[corrected live readback](evidence/2026-10-05-r5-live-readback.json) supersedes
that capability field in the earlier historical snapshot.

The existing access job stays closed. Current implementation and activation
evidence is in [LIVE-INTEGRATION-IMPLEMENTATION.md](LIVE-INTEGRATION-IMPLEMENTATION.md).
The [CC completion packet](CC-INTEGRATION-COMPLETION.md) specifies the secure
activation steps without creating another dispatcher or granting publishing.

## Historical discovery and access setup

Read-only audit performed October 3, 2026. Three agents inspected the prototype, existing BOS repositories, and available cloud connection metadata. This records observed access, not whether accounts are connected elsewhere.

| Service | Prototype | This cloud session | Existing BOS source |
| --- | --- | --- | --- |
| LinkedIn | Sample metrics and content previews | No callable connector or identifiable service binding | Personal-brand project labels; no account adapter found |
| YouTube | Sample metrics and Shorts previews | No callable connector or identifiable service binding | Personal-brand project labels; no account adapter found |
| TikTok | Sample metrics and content previews | No callable connector or identifiable service binding | Personal-brand project labels; no account adapter found |
| GoHighLevel | No integration references | No callable connector or identifiable service binding | No GoHighLevel/LeadConnector adapter found |

## Evidence and scope

- Prototype revision: `3af2b35425c684ddd3400461aeff568952711c44`. `dist/app.js` defines sample analytics; `dist/enhancements.js` implements simulated sends with UI updates. No backend, account configuration, OAuth, or API clients were found.
- BOS reference revision: `8ae0d4bf0475006a7892280a1fcf87d4d5911f2c`. Its `/entrepreneurship-professor` workspace reads authenticated `GET /api/source-snapshot`, backed by the existing Google Sheets Master Command Center. This provides routed work items, not social account connections or platform analytics.
- Classroom reference revision: `d1ff3e6062126eb40f8e1a0ec9723dde0aefee57`. No relevant social integration found.
- Runtime connection metadata contains no social connectors, secret bindings, outbound identities, or capabilities. The identity manifest's connections list is empty. The project-specific runtime variable is present, but its purpose and readiness are unverified; it was not read or repurposed.
- Saved network policy has the package-manager preset and no custom social API destinations. No authenticated social requests were made.
- Additional known repositories `bos-command-proxy` and `bos-registry` were unavailable through current Git access (`Repository not found`); private access and absence cannot be distinguished.

## Historical access job and close-out

**Latest result:** `EP-GHL-ACCESS-20261004-01` is **CLOSED — authenticated account-read access VERIFIED**, according to Claude's close-out supplied by the user (Oct 5, 11:12 AM EDT / 15:12 UTC). Codex's account check returned HTTP 200 and four accounts (Instagram, LinkedIn, TikTok, YouTube); the published token binding and running token are present. Claude reports that the canonical handoff and AI JOB LOG row 56 are updated, the integration grants exactly `socialplanner/account.readonly`, and this job holds no lease. The complete local result, IDs, expiration timestamps and remaining exceptions are in [the job handoff](EP-GHL-ACCESS-20261004-01-HANDOFF.md). Facebook was not returned. YouTube's expiration-field meaning, channel verification, analytics/publishing access, and direct worker-to-worker delivery remain unresolved or untested. Codex has not independently read the external close-out. Earlier missing-credential and lease notes below are historical observations.

### Current coordinated job

The user supplied Claude's status for `EP-GHL-ACCESS-20261004-01` (AI JOB LOG row 56), dated October 4, 2026 at 1:52 PM ET. Claude reports that the EP coordinator holds shared GHL write lease `CONT-C5-NATIVE-LEASE-02`; creation of "Entrepreneurship Professor — BOS Access" is waiting for lease release or grant. This lease state and external job-log row were reported by Claude, not independently queried by Codex.

Claude also reports that its browser tools cannot operate `chatgpt.com`. The remaining owner action is therefore to enter the issued token securely in the existing Codex environment secret field, confirm the location variable, and save/publish the prepared environment configuration. Do not deploy the app.

Codex independently rechecked the cloud configuration after receiving that report: draft revision 7 still has `GHL_ACCESS_TOKEN` with `has_saved_binding: false`, the location variable is pending, and the running instance has neither GHL variable nor an applied GHL network destination. No authenticated account check was attempted with these unchanged prerequisites. After secure binding and publication take effect, Codex should verify runtime access, run `python3 tools/check_ghl_accounts.py`, and report the result under this same job identity. No credential values belong in that result.

The user supplied the GoHighLevel workspace on October 4, 2026: [location launchpad](https://app.gohighlevel.com/v2/location/2cCtht46QwERbvs3uITM/launchpad). The location ID is `2cCtht46QwERbvs3uITM`. This resolves the workspace identity, but does not authenticate this cloud session or establish which social accounts it contains.

Official [HighLevel API documentation](https://github.com/GoHighLevel/highlevel-api-docs/blob/0af86a4cbd48c66a4071c7e509d1079f9f10ed17/apps/social-media-posting.json#L841) specifies:

```text
GET https://services.leadconnectorhq.com/social-media-posting/2cCtht46QwERbvs3uITM/accounts
Version: 2021-07-28
Required scope: socialplanner/account.readonly
Credential: Sub-Account OAuth access token or Sub-Account Private Integration Token
```

The environment draft now saves the location as `GHL_LOCATION_ID`, a `GHL_ACCESS_TOKEN` requirement bound only to `services.leadconnectorhq.com`, and additive app/API/documentation network destinations (`app.gohighlevel.com`, `services.leadconnectorhq.com`, `marketplace.gohighlevel.com`). Existing settings and bindings were preserved. Draft saving does not provide a token, apply runtime changes, or publish.

The portable helper `tools/check_ghl_accounts.py` can run the read-only inventory after configuration takes effect. It preserves proxy and TLS verification, rejects redirects, and selects only account identity/platform/expiration metadata. A missing account list is a failure rather than an empty success. The helper is separate from the public static frontend. It has passed independent review and 20 offline checks; its repository copy is byte-identical to the reviewed helper. Run `python3 tools/check_ghl_accounts.py` from the repository root. It must be included in an authorized repository update before other Git-based lanes can use it; publishing the cloud environment can retain it in that environment's filesystem snapshot.

Initial prepublication validation was blocked: requests to the supplied app and API returned proxy tunnel `403 Forbidden`, and no identifiable GHL credential existed in that instance. The helper correctly exited with a missing-credential prerequisite. Those blockers were subsequently resolved for the authenticated account-read operation, as documented in the latest job handoff. Never paste tokens into chat.

Then use that owner's supported read-only API or connector to verify account identity, granted capabilities, and one representative data response. Reuse existing bindings and add only the required network destinations through supported settings. Implement a bounded adapter in the authorized existing backend after its transport and response contract are verified. Keep credentials out of the static frontend. Do not replace sample metrics with invented live data or mark a connection ready based only on its display label.

BOS remains the sole dispatcher. Account discovery does not authorize posting, uploading, messaging, publishing, deployment, or a new dispatcher. Those actions follow the originating job's authorization and review boundaries.

## Durable access across workers

An environment-level GHL secret binding and published network configuration provide reusable access for future tasks in this Codex environment; a saved requirement without a secret value does not. Authentication is revocable and may require rotation. The retrieved official docs do not establish a lifetime for Private Integration Tokens, so do not promise an indefinitely valid token.

Other Claude, desktop, Chrome, or GitHub Actions sessions do not inherit this environment's credentials. Cross-lane access should use the authorized existing BOS backend connector or separately approved credential bindings. No shared live GHL backend has been established by this setup. This session has no authenticated browser tool and cannot use the account owner's signed-in desktop browser.

For initial account discovery, a location-authorized Private Integration Token with `socialplanner/account.readonly` is the smallest supported route. Existing OAuth authorization can also be reused, but its access token is short-lived: official HighLevel documentation specifies a one-day access-token lifetime and replacement access/refresh token pairs on refresh. Durable OAuth requires persistent token storage and refresh handling in an approved backend, not a desktop chat session. Neither token issuance nor permissions can be manufactured by additional agents.

The account owner or an already authorized delegated session must grant and securely provide the credential. Codex can implement and validate the connector; Claude can implement or independently review within its job permissions. A browser lane such as Claude in Chrome can help with the signed-in settings only if it actually has authorized access. Credential values stay out of chat, source files, and browser frontend code.

Account inventory does not prove other capabilities. Reading posts requires `socialplanner/post.readonly`, analytics require `socialplanner/statistics.readonly`, and publishing requires `socialplanner/post.write`; add them only for a corresponding authorized job. Official Social Planner analytics support LinkedIn Pages and TikTok Business accounts, so account type also matters. Verify platform capabilities before replacing sample metrics or enabling publication.
