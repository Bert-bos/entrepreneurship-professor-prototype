# Entrepreneurship Professor: Claude collaboration instructions

Read `AGENTS.md` and `docs/COLLABORATION-SETUP.md` first. BOS is the sole dispatcher; work only within the supplied BOS job envelope and return evidence to that originating job. Codex is another worker or independent reviewer, not a competing dispatcher.

The established unattended worker is `.github/workflows/claude.yml` in `Bert-bos/bos-workforce-orchestrator`, not this repository. On issue-comment jobs, including `entrepreneurship-professor-prototype` in the BOS issue body causes that workflow to prepare `.external/ep-professor` before Claude starts.

That lane permits repository reads and `node --check` but explicitly disallows Write, Edit, commits, pushes, and worker-initiated clones. Do not bypass those permissions. Return bounded patch text and evidence for an authorized technical lane to apply and independently verify. Run syntax checks with explicit target paths, for example `node --check .external/ep-professor/dist/app.js`; repeat for the relevant JavaScript files. HTTP serving and browser checks are performed by a lane with those capabilities, such as the Codex cloud environment; do not claim you ran them when they are unavailable.

A BOS job must identify the target revision, bounded objective, authorized files and operations, acceptance criteria, reviewer, evidence, and return location. Verify the target revision using permitted Git reads. If the clone is at a different revision, return that discrepancy to BOS instead of silently reviewing the wrong code. Avoid implementing or approving your own release. No metered API fallback or extra project-local worker should be introduced during routine setup.
