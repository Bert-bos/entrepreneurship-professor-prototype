# Codex and Claude collaboration setup

## Existing routing verified from repository contents

- Project: `Bert-bos/entrepreneurship-professor-prototype`.
- Dispatcher and Claude worker: `Bert-bos/bos-workforce-orchestrator`.
- BOS reference revision inspected: `8ae0d4bf0475006a7892280a1fcf87d4d5911f2c`.
- Project revision inspected: `3af2b35425c684ddd3400461aeff568952711c44`.
- Project-local Claude workflow was deliberately removed in that revision to route through private BOS.
- BOS's Claude workflow prepares `.external/ep-professor` when an issue-comment job's issue body includes `entrepreneurship-professor-prototype`.
- Its trigger requires an `@claude` mention from a non-Bot author. A trusted coordinator using a user identity may fit this guard; arbitrary bot-to-bot handoffs do not. Do not assume a workflow-authored comment wakes the lane.
- BOS holds the Claude subscription OAuth secret and the narrow command allowlist. This project does not need another Claude credential or duplicate worker.

These are configuration observations, not proof of a successful live job. Git reads succeeded during setup; GitHub API calls returned `Forbidden`, so Actions status, secret availability, and end-to-end delivery remain unverified.

## Job and return contract

Use BOS's existing Master Command Center job envelope and originating record. This checklist supplements that envelope; it does not define another queue or machine schema.

A project job should include:

- Job identity and originating BOS record.
- Target repository, branch and exact commit.
- Objective, acceptance criteria, permitted files and operations.
- Execution owner, independent reviewer, dependencies and approval boundaries.
- Required checks, evidence and return location.

For Claude issue-comment dispatch, the BOS issue body must name `entrepreneurship-professor-prototype`. Claude reads `.external/ep-professor`, verifies the revision, and returns findings or a bounded patch. BOS dispatches authorized application and independent review to the suitable lane. Revisions remain in that job; Bert is not asked to relay them.

Every returned package should state the exact revision, result, changes or patch, executed checks and outcomes, evidence, blockers, and next action. A patch awaiting application is not a completed implementation. A saved local report is not a delivered BOS result.

## Current environment

Python 3, Node.js, system Chromium and Python Playwright are available. There are no project dependencies to install. See `AGENTS.md` for startup and validation. Live processes restart in later tasks; the environment's saved startup instructions describe this workflow.

## Activation status

Local worker instructions can be used immediately in this checkout. For GitHub-hosted workers to read these new files, they must be included in the authorized branch/default-branch update. This setup does not merge, deploy, start a new dispatcher, post a Claude trigger, or prove continuous unattended coordination. Activation and live verification must use the existing BOS lane and its credentials, rather than rebuilding it in this project.

## Implemented direct result return (October 5, 2026)

`tools/bos_handoff.py` uses the existing BOS contract API, pinned to the reference
revision above. The bundled `tools/schemas/worker-result-v1.schema.json` is an
unchanged copy of BOS's Worker Result v1 contract. It accepts a complete result
file and the existing task/job/current-attempt IDs, validates them, verifies the
live assignment, submits once, and verifies the stored result by readback:

```sh
python3 -B tools/bos_handoff.py validate --task-id EXISTING_TASK_ID --job-id EXISTING_JOB_ID --attempt-id CURRENT_ATTEMPT_ID --result worker-result.json
python3 -B tools/bos_handoff.py status --task-id EXISTING_TASK_ID --job-id EXISTING_JOB_ID --attempt-id CURRENT_ATTEMPT_ID
python3 -B tools/bos_handoff.py submit --task-id EXISTING_TASK_ID --job-id EXISTING_JOB_ID --attempt-id CURRENT_ATTEMPT_ID --result worker-result.json
```

Validation is offline and does not establish live assignment authority. Live
commands use `BOS_WORKER_KEY` through `x-bos-key` and only the approved HTTPS
origin `https://bos-workforce-orchestrator.onrender.com`. `BOS_BASE_URL` may name
that origin; arbitrary destinations are rejected. A result can be submitted only
for the current `WORKING` assignment claimed by the authenticated `bos-worker`,
within its existing cost policy. The client creates no queue, claim, job,
review, approval, or release. An uncertain POST is not automatically retried;
read the existing job to reconcile delivery first.

Twelve client tests passed, including an HTTP roundtrip against the actual BOS
server and dispatch engine in a temporary local fixture: `WORKING` became
`REVIEW_READY`, the result persisted, and a repeat performed only a confirming
GET. This proves compatibility with that implementation, not the hosted
service or an unattended Claude wake-up. Live delivery has not occurred: this
running environment has no `BOS_WORKER_KEY` or supplied current assignment.
The BOS network destination and secure-key requirement are being saved in the
cloud configuration draft; saving is separate from publication.

The reported deployed revision `769cc8477d44be7abfab2f44157ddbb997c9e091` was
subsequently compared and tested independently. It has identical runtime code,
auth, routes, engine, and Worker Result schema to the pinned reference; all twelve
client tests also passed against its actual server in a temporary local fixture.
See [the compatibility report](BOS-LIVE-REVISION-COMPATIBILITY.md). The nine-commit
revision gap is documentation-only and requires no deployment to use this client.

The account-access job `EP-GHL-ACCESS-20261004-01` remains closed. New implementation
work returns through its own existing BOS assignment. See
[CC completion instructions](CC-INTEGRATION-COMPLETION.md) for the secure
activation and end-to-end verification packet.

## Canonical registration and execution approval

Claude reports registering `EP-LIVE-SOCIAL-BOS-20261005-01` in AI JOB LOG row 58
and preparing, but not ingesting, its Job Envelope v1. Registration is not
runtime execution approval. Producer-role HTTP ingestion reaches `ROUTED`;
`approveForExecution` must verify a trusted Ed25519 signature, fresh Drive
revision/body, and a fresh Command Center row exactly `APPROVED_FOR_EXECUTION`
before worker claim and working can occur. The existing dashboard has no
approval HTTP route. A Google operator session or `BOS_WORKER_KEY` cannot supply
that authority.

The actual CLI approval path has a reproduced real-clock signature mismatch
and unverified canonical Render credential/storage integration. The bounded
[approval investigation and proposal](BOS-APPROVAL-ACTIVATION.md) preserves the
existing gate and distinguishes code repair from operational activation.
The earlier return tests deliberately started from a synthetic test-approved
assignment; they proved return compatibility, not hosted approval. Future
workers must not repeat that test helper against real state or assume an
identically named directory on another machine is Render's shared store.

## Pre-assignment coordination and current return thread

Subsequent live check: GitHub API access became HTTP 200. The sole registered
EP job now has [BOS issue 68](https://github.com/Bert-bos/bos-workforce-orchestrator/issues/68)
as its coordination thread, with a directly posted/read-back Codex return and
an actual existing-workflow Claude run. No runtime assignment was created.
Use that thread for routine coordination; the earlier no-issue/API-denial
observations below are historical. Browser Claude's acknowledgement of the
branch was relayed by Bert; direct canonical-Docs readback remains unavailable.
The GitHub worker's independent communication receipt was read back directly:
[ACK](https://github.com/Bert-bos/bos-workforce-orchestrator/issues/68#issuecomment-6001790546)
and [Codex confirmation](https://github.com/Bert-bos/bos-workforce-orchestrator/issues/68#issuecomment-6001832169).
The receipt-only workflow completed successfully. This verifies the GitHub
communication roundtrip, while source verification/tests in that turn were
explicitly unrun and hosted execution remains blocked. The browser session is
distinct; its Google-document ACK remains reported rather than directly fetched.

The existing Worker Result endpoint does not accept a pre-ingest BLOCKED report.
At the initial check, the canonical EP row/document were known, but no GitHub
issue ID or writable Docs connector was available. The API read was blocked by
proxy/transport HTTP 403 before reaching the destination. The API host was saved
separately from Git transport; the later successful API call, verified issue and
comment writes, and actual workflow run supplied functional transport evidence.
See [the shared Codex return](CC-CODEX-RETURN.md) for the exact receipt state.
A pushed file alone never establishes receipt, and working GitHub communication
does not establish hosted execution or close the integration job.
