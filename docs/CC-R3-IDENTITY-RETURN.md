# Direct CC review: R3 and hosting identity

Existing job `EP-LIVE-SOCIAL-BOS-20261005-01`, AI JOB LOG row58, remains open.
Account-access job `EP-GHL-ACCESS-20261004-01` remains closed. No lease or live
assignment was created, claimed or released.

## Direct receipt and independent review

Browser Claude/Cowork sent a message directly in this Codex conversation and
[posted comment6023965178](https://github.com/Bert-bos/bos-workforce-orchestrator/issues/68#issuecomment-6023965178).
Codex GET-read the stored comment and verified its body and exact production
revision. GitHub records author `Bert-bos`; the body identifies browser CC.
It acknowledges Codex's prior receipt6023720230. Native browser communication
is now evidenced, separately from the earlier GitHub-worker receipt-only run.
No routine packet relay or another conversation URL from Bert is needed for
this exchange. A later reply still requires actual acknowledgement/readback.

CC's static verdict is PASS WITH OPERATIONAL PREREQUISITES for the disabled
candidate at `72da093e9b9e045190d18ffa8876d44b1d8185f3`. CC read production
changes but ran no tests and did not review tests line by line. R1 global
readiness, R2 concurrent reconciliation returning503, and R4 local CLI duplicate
JSON keys remain nonblocking follow-ups. No production change was made in this
continuation.

## R3: actual client/server readback

Published BOS revision:
`7d50d9a19babb81d87d93aa16594a548b2ecd2be`, test/evidence only, parent `72da093`.
Exact local commit/tree was published and read back; independent native Git fetch
returned the same revision. Production code, workflow, blueprint and client
origin are unchanged.

[The new test](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/7d50d9a19babb81d87d93aa16594a548b2ecd2be/test/dispatch-approval-transport.test.js#L124)
invokes unchanged Python `approve` and `BosTransport` against actual Node
`createServer`/dispatch-engine HTTP routes. The temporary store is approved
through the genuine Ed25519 gate, with synthetic Google/Keychain dependencies;
no forced approval is used.

- Producer status GET returns200; unauthenticated status GET returns401.
- Python executes GET context, one approval POST, then independent status GET.
- The persisted receipt contains all ten fields, including `producerKeyId`,
  and Python returns `verifiedByReadback: true`.
- Removing or changing each field in delivery copies of the actual returned
  receipt is rejected: twenty negative assertions. The audit chain remains valid.
- Full `npm test`: 673 passed, zero failed/skipped. Remote Python suite: 26 passed.
  Whitespace checks passed. An independent reviewer checked the test hashes and
  executed the new focused test successfully.

Source basis, unchanged from the reviewed production candidate:
[producer read permission](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/72da093e9b9e045190d18ffa8876d44b1d8185f3/src/auth-boundary.js#L13),
[actual status route](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/72da093e9b9e045190d18ffa8876d44b1d8185f3/src/dashboard-server.js#L513),
[complete stored handoffs](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/72da093e9b9e045190d18ffa8876d44b1d8185f3/src/dispatch-engine.js#L1014).
[Exact test evidence](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/7d50d9a19babb81d87d93aa16594a548b2ecd2be/docs/evidence/2026-10-06-ep-r3-real-server-validation.json)
records scope and hashes. This closes the implementation-compatibility question;
it does not establish live Render authorization or activation. The test-only
loopback opener does not change the production fixed origin.

The new exact-head PR CI
[run37520911428](https://github.com/Bert-bos/bos-workforce-orchestrator/actions/runs/37520911428)
completed SUCCESS. Codex independently fetched both jobs: Test suite
`112465761934` and Authentication and queue boundary `112465761765`, all steps
successful. The previous runner-acquisition failure is historical; this required
check is now resolved on `7d50d9a`, with no waiver or manual rerun. The normal push
CI `37520906366` also completed SUCCESS. See the saved CI readback evidence.

## Hosting reading and next receipt

CC reports a running VM, attached runner identity, keyless service accounts,
runner Token Creator grant on intake, and Render769cc84 without federation.
Codex has not independently inspected today's console, IAM or VM processes.
The September7 checkpoint corroborates the historical VM identity configuration.

The source confirms the mismatch: producer `BOS_ORIGIN` and EP worker
`API_ORIGIN` target Render. Render's disk and the VM's disk are separate.
Current impersonation calls obtain ambient access from GCP metadata; there is
no external-federation adapter or enabled executable bootstrap in this PR.

Render WIF is a separate design requiring a real supported workload issuer,
token acquisition/exchange implementation, scoped trust and reviewed startup.
Setting federation variables or an intake email cannot enable this candidate.
Making the VM canonical requires a reviewed cutover plus authenticated client
connectivity and matching origins/bindings. Historically it has no external IP
and IAP SSH ingress; RUNNING alone does not supply a reachable BOS API. No
reviewed bridge resolving this split was found.

The existing native hosting lane should produce a narrow read-only receipt of
VM service revision/active services, actual store ownership/current assignments,
Render store/current assignments, and whether a legitimate Render workload
issuer exists. Use selected `snapshotStatus()` projections; CLI `status`
performs stale-claim recovery. Do not dump credentials, systemd Environment,
Google source bodies or entire canonical stores. That receipt permits one
concrete architecture recommendation and reviewable release proposal before
requesting the release authority's decision. No architecture release, migration,
federation grant, deployment or state edit is approved by this return.

The existing worker binding still requires secure entry/publication. Domain
verification remains separately blocked on the four DNS writes prohibited by
CC's session classifier. Preserve Gather Slate ownership and the existing mail
records; no DNS-control bypass or domain completion is implied here.
