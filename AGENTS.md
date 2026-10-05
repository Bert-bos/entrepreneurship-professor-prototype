# Entrepreneurship Professor: Codex collaboration instructions

## Authority and handoffs

BOS (`Bert-bos/bos-workforce-orchestrator`) is the sole dispatcher and canonical status owner. Codex and Claude are workers or independent review lanes. Use the existing BOS job envelope and return results to its originating issue or job record. Do not create a second queue or assign work directly to another agent. Bert supplies goals, not routine handoff messages.

Read `docs/CLOSED-LOOP-STANDARD.md` and `docs/COLLABORATION-SETUP.md` before work. Proceed within the active job's scope and existing authorization. If no job is supplied, inspect and prepare the project but do not invent an assignment or claim a live dispatch occurred.

Claude's dashboard worker runs in the private BOS control plane, with this checkout at `.external/ep-professor`. The project-local Claude workflow was intentionally removed in commit `3af2b35425c684ddd3400461aeff568952711c44`. Do not restore it or duplicate authentication here as routine setup.

Codex may apply changes when authorized by the user or BOS job. The implementer cannot independently approve its own work. Return the exact revision, changed files, validation evidence, unresolved findings, and next action to BOS. Routine revisions return through that record; do not ask Bert to copy messages between agents. If transport is unavailable, preserve a reviewable result and report the specific blocker without claiming delivery.

Merge, deploy, spending, sensitive-data access, and material requirement changes follow the job's approval boundaries. Never expose credentials or broaden worker permissions to work around a blocked handoff.

## Development

Use the existing `/workspace/entrepreneurship-professor-prototype` checkout in Codex cloud. Tasks are already isolated; do not create a Git worktree unless explicitly requested. Check status before editing and preserve existing changes.

The application is HTML/CSS/JavaScript in `dist`, with a Python standard-library development server and server-side read-only GHL adapters in `tools`. There is no dependency installation, package manifest, or build command. Python unit tests are in `tests`.

Start from the repository root:

```sh
python3 tools/serve_ep.py --port 8000
```

Validate JavaScript from the repository root:

```sh
for file in dist/*.js; do node --check "$file" || exit; done
```

Run `python3 -B -m unittest discover -s tests -v` and `git diff --check`. The optional BOS existing-server integration requires a read-only BOS checkout configured with `BOS_REFERENCE_DIR`; record skipped tests rather than claiming live delivery.

Check the served page title and local assets with HTTP requests. For UI changes, use available Playwright and system Chromium to verify affected behavior, all six navigation pages, and the meeting drawer. Validate ready, empty, denied, and unavailable social-data states without substituting sample metrics. Distinguish syntax, offline tests, browser checks, and authenticated provider checks in evidence. Avoid recording hardware, external workspace navigation, publishing, or production operations unless assigned. Do not present loopback preview links in cloud onboarding.

Credentials stay in secure environment bindings and server memory, never `dist`, tracked files, logs, or browser responses. The server binds only loopback, serves only `dist`, and exposes read-only `/api/social/accounts` and `/api/social/statistics`. Preserve proxy routing, TLS verification, redirect denial, Host/Origin checks, and cache freshness. A past expiration timestamp with `isExpired=false` is an unresolved discrepancy, not proof of expiry or automatic refresh.

Use `tools/bos_handoff.py` only with an existing canonical assignment and its current task/job/attempt identifiers. Do not reuse closed access job `EP-GHL-ACCESS-20261004-01`. Successful result readback is delivery to review, not approval or release. Never retry an uncertain result POST automatically; reconcile the existing job first.
