# BOS execution approval: verified activation requirements

Checked October 5, 2026 against reported deployed BOS revision
`769cc8477d44be7abfab2f44157ddbb997c9e091` and reference
`8ae0d4bf0475006a7892280a1fcf87d4d5911f2c`.

**The existing approval gate is real, but its CLI has a reproduced timestamp
defect and its credentialed canonical-runtime path has not been established.
Binding the worker key alone cannot activate this assignment.** The bounded
repair below is an offline proposal, not a change to BOS or a deployment.

Claude reports that `EP-LIVE-SOCIAL-BOS-20261005-01` is registered in AI JOB LOG
row 58. Its envelope is prepared offline; no hosted contract or execution
approval is established by that registration. The earlier
`EP-GHL-ACCESS-20261004-01` remains closed. No live assignment, source row,
credential, or production state was changed during this investigation.

## What the existing implementation requires

| Step | Existing authority and evidence |
| --- | --- |
| Ingest | `POST /api/contracts/ingest`, authenticated producer role using the deployment's matching `BOS_PRODUCER_KEY`. The resulting contract starts in `ROUTED`. Use the returned task ID; never fabricate one. |
| Approve | `approveForExecution` requires an active trusted Ed25519 producer key and signature, a fresh Drive metadata/body read matching the routed revision, and a fresh uniquely matched Command Center row whose trimmed, case-sensitive Execution State is exactly `APPROVED_FOR_EXECUTION`. |
| Execute | Only an approved contract is claimable. The matching `BOS_WORKER_KEY` gives worker identity `bos-worker`; claim creates the attempt ID, then the claimant enters `WORKING` before returning that attempt's result. |
| Review | Worker completion enters `REVIEW_READY`. Reviewer authority uses `BOS_REVIEWER_KEY`; worker return does not approve release. |

The HTTP producer role key authorizes ingestion; it does **not** substitute for
the Ed25519 signing identity. No approval HTTP route exists in either checked
revision. The dashboard entrypoint leaves `commandCenterCredential=null` and
starts no source-reconciliation daemon. That parameter supports source
snapshots; populating it alone would not create a signed approval route.

The exact implemented CLI syntax is:

```sh
node src/dispatch-cli.js approve-for-execution EXISTING_TASK_ID --key-id=EXISTING_TRUSTED_KEY_ID
```

This command operates on local `ORCHESTRATOR_DATA_DIR`, defaulting to that
checkout's `data` directory. It does not call the hosted service. Render's
blueprint specifies `/opt/render/project/src/data`. Approval must run against
the same canonical persistent store as the hosted server. Running this command
in Codex or a reference clone would act on a different store and is not an
activation method for the Render assignment.

## Credentials and source checks

The CLI correctly resolves `driveIntakeCredential` and passes it to both Drive
and Command Center. There is no undefined-credential bug in this path.

- Intake resolves from macOS Keychain service
  `bos-handoff-dispatcher-drive-intake-ro`, or supported **actual GCP metadata
  impersonation** selected by `GCP_INTAKE_SERVICE_ACCOUNT_EMAIL`. Setting that
  email on Render does not provide GCP identity. No environment access-token or
  credential-file alternative is implemented by this resolver.
- The intake identity needs read access to the exact routed Drive document and
  the pinned Command Center spreadsheet. OAuth scopes are `drive.readonly` and
  `spreadsheets.readonly`. Google browser login is not this service credential.
- Producer private-key loading is exclusively macOS `/usr/bin/security`, using
  Keychain service `bos-handoff-dispatcher-producer-key-<keyId>`. This signer is
  unsupported on the current Linux/Render path. GCP Google impersonation does
  not supply an Ed25519 producer private key.
- Public trust is checkout-relative `config/trusted-producer-keys.json`, with
  `keyId`, `publicKeyPem`, `effectiveFrom`, and `revokedAt`. The source contains
  public key ID `producer-2026-09-06`; its corresponding private-key availability
  was not inspected. Reuse established trusted signing authority; no real key
  was generated for this work.

Command Center uses spreadsheet
`1Qe_XXOsqOuiaH6L_u18d7qgjv1zeP4i6sapGQzDzHm4`, tab `AI JOB LOG`, range
`'AI JOB LOG'!A1:Z2000`. Matching uses the exact Job ID, not row number. Missing
or duplicate matches fail closed. `ccRecordId` is `AI JOB LOG:<jobId>`;
`ccRecordVersion` hashes every exact row value. The fresh record window defaults
to five minutes. Drive revision must match exactly, and the signature binds the
hash of the complete fetched body, Drive ID/revision, Command Center ID/version,
job ID, approval state, and approval timestamp. Claim approval lifetime defaults
to 30 minutes from the signed timestamp.

Required network destinations depend on the approved credentialed runtime:
`oauth2.googleapis.com`, `www.googleapis.com`, `sheets.googleapis.com`; supported
GCP impersonation additionally uses `iamcredentials.googleapis.com` and its
runtime's metadata service. Codex worker delivery separately requires
`bos-workforce-orchestrator.onrender.com`. These are requirements, not evidence
that any missing allowance or identity has been configured.

## Reproduced defect and isolated repair proposal

The unchanged CLI signs a newly created timestamp. The engine performs its own
asynchronous source reads and then creates another timestamp for verification.
Those signed bytes differ when the clock advances. Both checked BOS revisions
reject actual CLI approval with `producer_signature_signature_invalid`, remain
`ROUTED`, and incorrectly exit with status 0. A fixed **test** clock passes.
Freezing the production clock is not a repair.

The actual CLI was exercised through its real ingest and signed approval gate
using only temporary synthetic state, memory-generated synthetic keys, and
intercepted Google responses. No `forceApprove` helper or direct approval-state
edit was used. Source checkouts are read-only inputs; the probe copies code to
temporary storage before injecting its public test trust entry and loaders.

[The reviewable patch](proposals/bos-approval-timestamp.patch) changes only the
CLI, approval engine, and focused offline tests. It has not been applied to
either reference checkout or to production. It:

- Passes optional `signedApprovalTimestamp` from the CLI to the engine and
  binds the exact value in both signature verification and persisted receipt.
- Requires a finite, canonical UTC ISO timestamp with milliseconds, no future
  timestamp, and age strictly less than the existing approval window after
  fresh source reads and again before persistence. Claim/recovery still expire
  from that original signing time, so replay cannot renew the lease.
- Preserves existing valid same-clock callers that omit the new parameter.
  External signers using advancing clocks should supply it. Explicit malformed
  values, including null or nonfinite numbers, fail closed.
- Sets CLI exit status 1 for a structured approval rejection.

The canonical binding format and schemas are unchanged. Existing Drive,
Command Center, active-key, signature, dependency, claim, and review checks stay
in place. Linux signing support, source-credential provisioning, canonical
runtime transport, and source reconciliation remain separate unresolved work.
This repair alone does not activate Render.

## Executed validation and repeatable offline checks

| Check | Result |
| --- | --- |
| Unchanged actual CLI, both revisions, advancing wall clock | Expected signature rejection reproduced; persisted `ROUTED`; incorrect exit 0 confirmed. |
| Isolated patched actual CLI, advancing wall clock | Approval accepted and persisted `APPROVED_FOR_EXECUTION`; structured fresh-source rejection exits 1. |
| New real-gate security/CLI tests | 20 passed, zero failures or skips. Also passed from the exported standalone test artifact. |
| Existing approval, binding, producer-auth, stale-claim, claim-lifecycle, runtime-contract suites | Independently run: 63 passed, zero failures or skips. |
| Existing CLI suite | Independently run: 11 passed; its remaining real GCP metadata-probe test deliberately not run. Node excludes that test before registration, so TAP's `skipped=0` does not mean all 12 ran. |
| Patch applicability | `git apply --check` succeeded against both unchanged BOS source revisions; no patch was applied. |

New tests cover advancing clocks, exact receipt timestamps, custom freshness
boundaries, ageing during source reads, malformed/future/nonfinite values,
unsigned timestamp tampering, original-lease expiry, rejected replay after real
claim-expiry demotion, changed Drive/Command Center bindings, legacy callers,
and actual subprocess exit status. Existing suites that use older approval
helpers are regression checks; they are not the signed-gate activation proof.

Run from the EP checkout with a supplied read-only BOS source directory:

```sh
BOS_REFERENCE_DIR=/path/to/unchanged/bos \
  node docs/proposals/bos-approval-timestamp-probe.cjs --expect=baseline

BOS_SOURCE_DIR=/path/to/isolated/patched/bos \
  node docs/proposals/bos-approval-timestamp-probe.cjs --expect=patched

BOS_SOURCE_DIR=/path/to/isolated/patched/bos \
  node --test docs/proposals/bos-approval-timestamp-regression.test.cjs
```

Saved probe evidence:

- [Deployed-revision baseline](evidence/2026-10-05-bos-approval-baseline-769cc84.json)
- [Reference-revision baseline](evidence/2026-10-05-bos-approval-baseline-8ae0d4b.json)
- [Isolated patched result](evidence/2026-10-05-bos-approval-patched.json)

## Operational activation sequence once the missing path is implemented

1. Keep the existing registered implementation job. Confirm its exact Drive
   source/revision and unique Command Center row; registration or a prose state
   is insufficient. Use the established approval authority to set the exact
   machine-approved execution state when the job is authorized.
2. Have the existing producer ingest the schema-valid envelope once through the
   authenticated hosted API and retain the server-returned task ID. A worker
   key or prepared envelope cannot perform this producer action.
3. Review the timestamp patch and implement a supported credentialed approval
   process against the hosted server's canonical disk, or a separately reviewed
   authenticated approval transport using the same gate. Establish the trusted
   signer and fresh Drive/Sheets identity there. Do not copy runtime state into
   another dispatcher, force the status, or treat an unsupported Linux Keychain
   command as a usable path.
4. Execute signed approval only on that established canonical process. Require
   both a successful command/result and status readback showing
   `APPROVED_FOR_EXECUTION` with its source-bound receipt. Failure exit 0 on
   unchanged BOS is not approval evidence.
5. Bind the matching worker key securely and publish/apply the BOS host
   allowance in Codex. Claim through the existing worker API, retain its real
   attempt ID, and enter `WORKING` as `bos-worker`. Then use EP's existing return
   client, verify persisted result readback, and leave independent review to
   BOS. No routine evidence relay through Bert is required once this path works.

These are conditional implementation/operations requirements. No credentialed
production approval, ingestion, worker claim, or live result return was
performed or proven here.

## Authoritative source references

- [CLI approval and local data directory](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dispatch-cli.js#L654)
- [Real signed execution gate and original timestamp reconstruction](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dispatch-engine.js#L435)
- [Drive credential resolution](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dispatch-drive-auth.js#L135)
- [Keychain-only producer private-key loading](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dispatch-producer-auth.js#L157)
- [Command Center identity, freshness, and exact state](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dispatch-command-center.js#L61)
- [Canonical signed payload fields](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dispatch-binding.js#L54)
- [HTTP contract routes and server entrypoint](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/src/dashboard-server.js#L466)
- [Canonical Render disk and environment](https://github.com/Bert-bos/bos-workforce-orchestrator/blob/769cc8477d44be7abfab2f44157ddbb997c9e091/render.yaml#L15)
