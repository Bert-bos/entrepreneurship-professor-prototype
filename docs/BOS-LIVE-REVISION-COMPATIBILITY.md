# BOS worker-return compatibility with the reported deployed revision

Verified October 5, 2026 at approximately 1:06 PM EDT (17:06 UTC).

**Result: the Entrepreneurship Professor return client is compatible with both the reported deployed BOS revision and the pinned reference. No BOS runtime deployment or client change is required to reconcile these two revisions. Live return delivery remains unverified.**

## Evidence boundary

Claude reported that the live BOS service runs `769cc84`, that `/api/contracts/status` contains zero handoffs, and that `/api/status` contains zero tasks. It also reported that the BOS worker key exists in Render but is absent from the Codex environment, and that the published Codex configuration lacks the BOS host allowance. These are Claude-supplied production observations; this compatibility check did not independently query the live service or read any real key.

Codex independently resolved the reported short revision using the existing authenticated native Git read route, inspected both complete source revisions, compared the contract and runtime files, and executed the existing-server integration tests against both. The test jobs are explicitly synthetic and exist only in temporary local directories; they are not live BOS assignments or evidence of remote dispatch.

## Exact revisions and source comparison

| Component | Exact revision |
| --- | --- |
| BOS reported deployed revision, independently resolved through Git | `769cc8477d44be7abfab2f44157ddbb997c9e091` |
| BOS pinned reference | `8ae0d4bf0475006a7892280a1fcf87d4d5911f2c` |
| EP base containing the tested return client | `20b63f958e1e5b9fa314a94d181e66f7bb4eba17` |

The deployed revision is dated September 18, 2026, 5:52 PM EDT, and the pinned reference is nine commits ahead. The complete source diff between them changes only:

- `README.md`
- `docs/CLOSED-LOOP-STANDARD.md`
- `docs/FORECASTING-STANDARD.md`
- `docs/VISUAL-RELEASE-CONTRACT.md`

No runtime source, authentication logic, endpoint implementation, store, or JSON schema differs. In particular, `src/dashboard-server.js`, `src/auth-boundary.js`, `src/dispatch-engine.js`, `src/runtime-contract.js`, `src/dispatch-store.js`, and `schemas/worker-result-v1.schema.json` are identical across the two revisions.

The bundled EP schema and both BOS schemas have the same SHA-256:

```text
a2da3ebf9399d07779e93405e35fd73e3f1763e115fed6a0e95012e38dc552a8
```

## Existing API contract confirmed at both revisions

| Boundary | Confirmed behavior |
| --- | --- |
| Status | Authenticated `GET /api/contracts/status` returns a `handoffs` array. Each relevant record includes `task_id`, `contract_job_id`, `attempt_id`, runtime `status`, `claimed_by`, `contract_cost_policy`, and the persisted `worker_result`. |
| Result return | Authenticated `POST /api/contracts/{task_id}/result` accepts Worker Result v1 JSON. Successful response is `{ "ok": true, "handoff": ... }`. |
| Identity | `x-bos-key` with the deployment's matching `BOS_WORKER_KEY` maps to immutable identity `bos-worker`; the result handler overwrites a caller-supplied `worker_id` with the authenticated identity. |
| Existing authority | Result intake requires an existing v1 contract in `WORKING`, the matching logical job ID, the current attempt ID, and the matching claimant. A closed or unassigned job cannot receive a new return through this route. |
| Cost and evidence | Intake enforces the existing job's cost cap and zero-spend policy; `COMPLETED` and `PARTIAL` results require evidence references. |
| Independent review | A worker's `COMPLETED` or `PARTIAL` return enters `REVIEW_READY`. It does not approve itself or authorize release. |
| Readback | Persisted `worker_result` is available in the status record, so the EP client can verify the exact returned JSON and reconcile a previously accepted result without a duplicate POST. |

Source references at the reported deployed revision:

- [Status and result routes](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dashboard-server.js#L482)
- [Role authentication](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/auth-boundary.js#L11)
- [Result authority, spend, and evidence enforcement](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dispatch-engine.js#L721)
- [Worker Result schema](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/schemas/worker-result-v1.schema.json)

## Executed validation

Both complete runs used the same EP client and tests. Each passed **12 tests, zero skipped**, including the actual existing BOS server and dispatch engine. The server bound only `127.0.0.1` on an ephemeral port, using fake local role credentials and temporary synthetic job state. The production hostname was mapped to loopback by the test's injected opener; the production client still accepts only its fixed approved HTTPS origin.

Pinned reference:

```sh
BOS_REFERENCE_DIR=/tmp/ep-reference-bos PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -m unittest discover -s tests -p test_bos_handoff.py -v
```

Reported deployed source exported with `git archive`:

```sh
BOS_REFERENCE_DIR=/tmp/ep-reference-bos-deployed-769cc84 PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -m unittest discover -s tests -p test_bos_handoff.py -v
```

At both revisions the integration exercised a local `WORKING` assignment, one HTTP Worker Result POST, subsequent status readback, exact on-disk result persistence, and the transition to `REVIEW_READY`. A repeated client return performed only a GET and reported the matching result already present. No independent review or release action was issued.

The remaining cases verified schema equality, offline validation, absent or stale authority, foreign worker ownership, cost-policy violations, missing evidence, invalid/ambiguous JSON, credential-retargeting rejection, redirect rejection, sanitized errors, and the absence of automatic retries after an uncertain POST.

## Remaining production prerequisites

1. Bind the existing matching `BOS_WORKER_KEY` securely into Codex, restricted to `bos-workforce-orchestrator.onrender.com`; do not generate a replacement or expose it to the browser, source, evidence files, or chat.
2. Publish the additive BOS hostname allowance and apply it to the running environment. A saved draft alone is not active access.
3. Obtain a real current BOS assignment through the sole dispatcher, including its task ID, logical job ID, current attempt ID, and `WORKING` ownership as `bos-worker`. The reported empty runtime currently supplies none.
4. Verify the live status route using that worker identity, return the supplied Worker Result once, and verify the exact persisted record. Preserve the live response and attribution before declaring the direct handoff proven.

The completed access job `EP-GHL-ACCESS-20261004-01` remains closed. This check creates no production assignment, reopens no job, starts no competing dispatcher, and performs no live result POST. BOS owns creation and approval of the next real assignment; routine worker evidence should return directly through the existing transport once the prerequisites are available.
