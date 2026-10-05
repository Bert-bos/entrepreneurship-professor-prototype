# Codex return to the existing EP coordinator

Job: `EP-LIVE-SOCIAL-BOS-20261005-01`, AI JOB LOG row 58, preserved.
State: **BLOCKED — direct coordinator transport not active**.
Access job `EP-GHL-ACCESS-20261004-01` stays closed. No lease held.

Bert's latest instruction explicitly authorizes this return to CC and asks that
he be removed from routine message transport. It does not supply missing
credentials, a live task/attempt, or a separate production-release approval.
This file is the shared return artifact, not a Worker Result v1 or another queue.
Repository availability is not a coordinator receipt.

## Return and exact implementation evidence

Claude's review at `1e6a4f4` independently approved the timestamp repair for
BOS adoption and confirmed R5 fixed. No repair was deployed by that review.
The newer implementation/operations proposal is published at EP revision
`6d97d9fee096a13e06a0497c555c293ff570a4e5`; see
[the concrete activation packet](CC-BOS-ACTIVATION-DECISION.md) and
[the complete existing-job packet](CC-INTEGRATION-COMPLETION.md).

Previously executed Codex evidence: 58 EP tests passed after R5, HTTP-200 account
and statistics reads, live UI checks, and 94 distinct offline BOS proposal checks.
One existing real GCP metadata-probe test was deliberately not run. Claude's
review was static; it did not run those tests. These are historical executed
checks, not a new provider/test run for this documentation-only return.

The activation proposal keeps producer signing separate from the hosted
verifier, requires an actually usable keyless Google intake identity, preserves
source reconciliation, and records low-priority O1 accurately: signature reuse
within its original window is possible when exact signed values are restored.
It includes the assigned `mail.bertseither.com` verification warning and reported
October 26 deadline. No mail-domain repair or provider verification is claimed.

## Direct transport checks in this session

[Sanitized check evidence](evidence/2026-10-05-direct-return-status.json)
records the observed transport denial and the unverified delivery state.

- Native Git read/push works for this EP review branch. The current GitHub
  issue API read fails before reaching GitHub with proxy/transport HTTP 403
  Forbidden; it is not evidence that GitHub rejected a role credential.
- `api.github.com` is absent from the applied destination list. Its requirement
  is saved in the prepared draft while preserving GHL and BOS destinations.
  Publication, API authentication, issue-write scope, and caller identity remain
  separate checks. Existing Git access does not prove issue-comment access.
- `BOS_WORKER_KEY` is absent in the runtime and its prepared secure field has
  no saved binding. No task/current-attempt ID exists in the supplied report.
- BOS's existing result endpoint only accepts its genuine `WORKING` assignment.
  A pre-ingest blocked progress return cannot be posted there as a fake result.
- No exposed browser, Google Docs/Drive, or messaging connector can write the
  known canonical document from this session. The outbound-identity manifest
  contains zero connections. No unidentified credential was repurposed.
- No canonical GitHub issue number or URL for this EP job was found in supplied
  records or tracked artifacts. No issue ID, comment, approval, or delivery
  receipt was fabricated. No external message was sent by this check.

## CC's next action: activate return transport before asking Bert to relay again

Read this return directly from the existing EP review branch. A GitHub-hosted
Claude worker must explicitly fetch that branch: its initial EP clone uses the
default branch. In the EP checkout, use allowed read operations:

```sh
git fetch origin codex/ep-live-social-bos-20261005
git show --no-patch --format=%H FETCH_HEAD
git show FETCH_HEAD:docs/CC-CODEX-RETURN.md
```

Record the exact fetched commit in an independent receipt. Preserve the existing
job and canonical owner. Have BOS establish the writable return route associated
with that job rather than treating this repository file as a second dispatcher.
For the normal GitHub route, identify or bind this same existing job to BOS's
originating issue under coordinator authority, supply its actual URL, and enable
scoped API read/comment access. Do not request broad repository-write or deploy
rights for Claude. For the known Drive-origin route, use its existing authorized
record connection; do not invent a Google credential or a parallel status store.

Verify the loop in both directions: Codex posts this return to that real record,
reads it back, CC acknowledges the exact revision there, and Codex reads that
acknowledgement. The existing GitHub workflow requires a non-Bot `@claude`
comment; verify the authenticated actor and a real worker receipt rather than
loosening that guard or claiming a bot comment woke Claude. A browser CC session
and the GitHub Claude lane are distinct workers; record which received the return.

After genuine approval and worker claim, use the existing BOS result client for
the full attempt result and require `verifiedByReadback: true` and independent QA.
That result route complements pre-assignment coordination; it does not solve the
bootstrap communication gap by itself. Keep the signed Drive body and row stable
during execution and return routine heartbeat/results through BOS's task records.

If secure Codex settings cannot be operated by the authorized lane, Bert's
one-time secure field entry/publication is an access prerequisite. Ask for only
that necessary action; never ask him to carry routine evidence or credentials in
chat. No owner decisions are marked approved just because this return was
prepared. Do not report the loop closed until the actual acknowledgement is read
back.
