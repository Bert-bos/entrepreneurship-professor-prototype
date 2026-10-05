# Concrete BOS activation proposal for owner review

Job: `EP-LIVE-SOCIAL-BOS-20261005-01`, existing AI JOB LOG row 58.
Access job `EP-GHL-ACCESS-20261004-01` remains closed.

This is a reviewable proposal, not an owner authorization, implemented route,
production change, or delivered coordinator message.

## October 5 continuation received from Claude

Claude's static independent review approved the timestamp patch for adoption
by the BOS technical lane. Claude did not apply it or run its tests. Codex's
previous offline validation remains the executed evidence. R5 was independently
confirmed fixed. No hosted approval or contract exists in the supplied report.

The prepared v2 envelope pins EP revision
`1e6a4f49318b71cff428390b8065cdc0a52c5a9f` and reported Drive revision
`2026-10-05T18:14:50.322Z`. Neither the envelope file nor live source records
were supplied to this session. Refresh the actual repository/source bindings
before ingestion; this document's new commit does not update those records.

O1 is accepted as a nonblocking finding for the bounded timestamp repair:
restoring the exact signed source values within the original approval window
can permit reuse of the same signature after reconciliation demotes a job.
The original timestamp prevents extending the lease; it does not make the
signature single-use. One-time challenges require a separately reviewed binding
and persistence change, not a claim that the existing patch already has a nonce.

## Recommended approval architecture

Keep the producer signing authority separate from the hosted verifier. Reuse
the existing trusted Ed25519 key on its established signing host; verify its
availability without revealing or replacing it. Hosted BOS retains the public
trust store and owns all approval-state mutations on its existing Render disk.
This avoids requiring a producer private key on the Linux verifier.

Implement a narrowly authenticated approval transport in BOS:

1. A producer-authenticated context operation reads the actual routed task,
   freshly fetches the bound Drive metadata/body and uniquely matched Command
   Center row, and returns only the exact binding fields needed for signing.
   Do not expose the document body or credential values. These are proposed
   operations; they do not exist in the checked deployment.
2. The signing host verifies the intended job and source binding, signs the
   existing canonical payload with its exact timestamp, and submits only the
   trusted key ID, signature, and signed timestamp for that existing task.
3. The hosted approval operation uses the existing producer permission boundary
   and `approveForExecution` on its canonical store. It independently re-fetches
   Google sources rather than trusting context or row values from the caller.
   Apply the reviewed timestamp patch so verification uses the signed timestamp.
   Preserve strict body validation, audit transactions, role separation, size
   limits, and sanitized diagnostics. Caller-selected URLs, credentials, trust
   files, fetch implementations, and approval-state overrides are disallowed.
4. Establish hosted source reconciliation and its existing demotion behavior.
   Missing credentials, expired identity, or unavailable sources must prevent
   execution; a scheduler silently checking zero records is not verification.
   Verify reconciliation before enabling approval/claim on the new path.

An HTTP producer key does not substitute for the Ed25519 signature. Operator,
worker, and reviewer credentials must not gain producer approval authority.
Use the established audit/rollback mechanisms so a failed audit cannot leave
an approval committed. No new dispatcher or copy of canonical state is needed.

### Keyless Google identity is a required part of this design

The checked BOS dashboard explicitly prohibits downloadable Google
service-account keys. Its existing hosted-runtime design records the
organization's key-creation restriction. Do not copy a Google JSON key into
Render, generate another key, or weaken the organization policy.

The technical lane must verify a supported keyless intake identity that the
canonical runtime can actually use, with only `drive.readonly` and
`spreadsheets.readonly` and access to the exact source document and Command
Center. Actual GCP metadata impersonation works only on an established GCP
runtime. Render is not that runtime. External federation requires an actually
available trusted workload identity and a reviewed token path; setting an
email or naming federation does not supply one. No usable Render external
identity was established by this source inspection.

Retain the separation from the Drive return identity. If Render cannot obtain
a supported keyless identity, return that precise verified constraint for a
separately approved hosting/identity change. Do not migrate canonical storage,
create compute resources, or incur spending under this proposal.

### Source records must remain stable during execution

The approving authority sets the exact row state `APPROVED_FOR_EXECUTION`
immediately before the fresh read and signature. The gate hashes every row
value and the complete Drive body, not just the execution-state cell. Routine
heartbeat, output, or status edits to row 58 or the signed document can therefore
invalidate the approval. Keep those signed sources stable during the bounded
attempt; record live heartbeat/results in BOS's existing task/attempt records.
Perform final canonical-document updates after the attempt reaches review, or
use genuine reapproval when a source change is necessary. Do not weaken the
hash binding to hide this behavior.

## Release acceptance and rollback

The BOS technical lane must prove, before its normal release approval:

- Producer-only access; worker/operator/reviewer and unauthenticated calls denied.
- Actual advancing-clock signed approval on the canonical store, plus invalid,
  future, stale, tampered, revoked-key, changed-source, and missing-identity denial.
- No credentials in responses, errors, request/audit logs, or stored task results.
- Reconciliation invalidates a changed/unavailable source and clears worker
  ownership as required; restart retains canonical state and receipts.
- A real approved EP task is claimed by `bos-worker`, enters `WORKING`, returns
  one result, and yields `verifiedByReadback: true`, followed by independent QA.

Rollback disables the new approval transport and restores the previous reviewed
runtime while preserving the canonical disk and audit evidence. Do not reverse
task state through raw file edits or make already-approved work automatically
execute after rollback. Deploy remains subject to the BOS release authority.

## Assigned mail-domain work

Claude reports `mail.bertseither.com` has an unverified-domain warning with an
October 26 auto-delete deadline. This session cannot access its authenticated
email settings or DNS provider. Local resolution returned temporary resolver
failure for both the parent and mail names; that is not evidence of absent DNS.

Through the existing authorized GHL browser/admin lane, inspect the exact
warning and the existing dedicated sending-domain verification records. Match
the actual sending domain to the intended location before changing anything.
Use the established DNS-owner lane to compare those exact records with the
authoritative zone, repair only the necessary conflicts/missing records, and
invoke the existing domain verification. Preserve current mail delivery records;
do not invent a DKIM selector, add a second SPF record at the same name, replace
mail routing, delete/recreate the domain, or broaden the EP social API token.
Record the authenticated verified-state readback and deadline resolution. No
campaign sending, test mail to others, or publishing is included in this work.

## Secure worker binding

The current runtime still has no `BOS_WORKER_KEY`. The prepared environment
draft preserves GHL and declares the BOS host and worker-secret requirement.
Use the existing Render credential through the supported secure environment
entry flow, then publish and verify propagation. If the browser cannot operate
the Codex settings, Bert's secure entry is the necessary one-time manual step;
never relay the value in chat or pretend a draft is published.

## Exact owner instruction to give the coordinator

> Authorize the BOS technical lane to adopt the independently reviewed timestamp
> repair and implement the authenticated approval transport described here,
> subject to its normal independent review and release boundary. Verify a
> supported keyless read-only Google intake identity before activation; keep
> producer signing separate from the hosted verifier. Continue the existing EP
> job through real approval, worker execution, verified direct return, and QA.
> Complete its assigned mail-domain verification through the existing GHL/DNS
> lanes. Set row 58 to the exact approved state only at signing and preserve
> the signed sources during execution. Arrange secure transfer of the existing
> worker key into Codex; ask me only for secure entry or an actual authority
> boundary you cannot cross. Keep the closed access job closed. Do not create
> another dispatcher, fabricate IDs, bypass approval, export Google keys, or
> create new hosting resources/spending under this instruction.

This text becomes an owner instruction only if Bert issues it. Claude's static
patch approval alone is not authorization to deploy a new BOS architecture.
