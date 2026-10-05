# Coordinator completion packet

Complete the Entrepreneurship Professor integration through the existing BOS dispatcher and its canonical records. Independently review the prepared implementation, apply it through the authorized technical lane, finish the account/analytics read access, and prove a direct Worker Result return. Bert supplies the goal and is not the routine transport between workers.

This packet is a local instruction document. It has not been sent directly to Claude Chrome or another coordinator by this session. Follow the supplied assignment's approval and lease boundaries; it authorizes no production deployment, publishing, or additional spending.

Review branch: `codex/ep-live-social-bos-20261005` in
`Bert-bos/entrepreneurship-professor-prototype`, based on project revision
`3af2b35425c684ddd3400461aeff568952711c44`. Verify the branch's exact current
commit and carry that revision through review and the originating BOS record.
The cloud configuration draft is saved as
`a172fd3b-f5f8-4692-bca3-bd33dc37defc~cecfgdraft_6ac3caf77124819c91627a3d1097ca1c`;
readback confirmed the preserved GHL binding and the new unfilled worker-key
requirement. Saving has not published it.

## Verified follow-up to Claude's October 5 coordinator return

The existing EP token now returns **HTTP 200** for both account inventory and
statistics after the approved scope addition. Instagram returned 41 impressions,
reach 6, and 3 followers; TikTok returned actual zeros. YouTube metrics remain
unavailable and LinkedIn personal-profile aggregate analytics is unsupported.
The live Audience display, refresh, six pages, drawer, keyboard operation, and
mobile layout passed. All 58 unit tests and JavaScript syntax checks passed.
Finding R1 is fixed: the 401 message now names the required statistics-read scope.

The reported deployed BOS revision `769cc84` has identical runtime code and schema
to the pinned reference. All twelve client tests, including the actual-server
roundtrip, passed at each revision; no deployment update is required. Evidence:
[current authenticated readback](evidence/2026-10-05-ghl-live-readback.json) and
[BOS compatibility report](BOS-LIVE-REVISION-COMPATIBILITY.md).

Claude subsequently registered canonical job `EP-LIVE-SOCIAL-BOS-20261005-01`
in AI JOB LOG row 58 and prepared a schema-valid envelope pinned to `e145b95`.
The hosted contract is not ingested, approved, or assigned. Do not create a
duplicate registration. The recorded `drive_revision` is only a snapshot and
must be refreshed after any canonical-document edit.

Claude's independent static review of `e145b95` is PASS WITH FINDINGS. Codex
fixed R5 by dropping the account endpoint's unrelated analytics/publishing
capability fields and verified the live response with all 58 tests passing.
R6 is corrected in the compatibility report: producer ingestion only reaches
`ROUTED`; a fresh trusted signed execution approval is mandatory before claim.
The existing CLI additionally has a reproduced timestamp-signature defect.
The [approval activation investigation](BOS-APPROVAL-ACTIVATION.md) contains the
reviewable repair and the operational constraints. The prepared worker secret
field remains unfilled. Binding that key alone cannot supply execution approval.

## One end-to-end execution

1. **Complete BOS approval activation for the existing registered job.** Preserve job `EP-LIVE-SOCIAL-BOS-20261005-01`, row 58, and the closed account-read job. Have the existing BOS technical/owner lane review the approval investigation and its bounded repair proposal. Establish an authorized approval path that reaches the same canonical runtime store, verifies the trusted producer signature, freshly reads the matching Drive revision/body and approved Command Center row, and maintains reconciliation. The current Google session is operator-only; it cannot perform producer-role ingestion or signed approval. The existing Mac CLI does not remotely approve Render state, and a worker credential cannot replace the producer signing/approval gate. Do not hand-edit approval state, use test-only approval helpers, copy a producer private key onto a verifier, or invent an approval HTTP route. Any BOS runtime implementation/deployment requires its own authorized technical review and release boundary. Once that path is actually usable, refresh the envelope's repository revision and Drive binding, ingest using the existing producer role, verify `ROUTED` then genuine `APPROVED_FOR_EXECUTION`, and claim/mark working through the actual worker lane. Preserve actual generated task/current-attempt IDs for the return.

2. **Independently review and apply the prepared branch.** Review `tools/check_ghl_accounts.py`, `tools/check_ghl_statistics.py`, `tools/serve_ep.py`, the Audience integration assets, `tools/bos_handoff.py`, the pinned Worker Result schema, and their tests. An authorized technical lane applies repository changes; the implementer does not approve its own release. Preserve existing files and credentials, and record the exact revision and any approved change in scope. The loopback development service does not provide a production deployment plan.

3. **Preserve the now-verified GHL access.** The existing integration is `Entrepreneurship Professor — BOS Access`, ID `6ac3148cde99fd539e34a394`, for location `2cCtht46QwERbvs3uITM`. Claude reports exactly `socialplanner/account.readonly` and `socialplanner/statistics.readonly` after the approved update; the existing EP token now succeeds for both reads. Preserve those two scopes and the secure `GHL_ACCESS_TOKEN` binding restricted to `services.leadconnectorhq.com`. The old account-only integration description is stale metadata, not the actual scope grant. No token replacement is needed on the successful current evidence. Credential values never belong in chat, documents, commits, logs, or browser code. This packet requires no `socialplanner/post.write`, post creation, or publishing operation.

4. **Supply the existing scoped BOS worker access and publish the prepared cloud configuration.** Bind the established return-lane credential as `BOS_WORKER_KEY`, restricted to `bos-workforce-orchestrator.onrender.com`, through the supported secure environment flow. Do not generate another dispatcher, broaden worker authority, reuse the unidentified project key, or copy a worker key into source. The BOS destination, `BOS_BASE_URL` suggestion, startup instructions, and worker-key requirement are saved in the draft, which reports `requires_publish: true`; publication/application is not yet verified and no worker-key value has been supplied. Publish through the supported environment settings, then verify propagation in the selected runtime. Existing GHL bindings and network destinations must remain intact. A saved draft is not publication, and publication does not establish authenticated API success.

5. **Run the helpers and verify the local product.** From the reviewed checkout, execute:

   ```sh
   python3 tools/check_ghl_accounts.py
   python3 tools/check_ghl_statistics.py
   python3 -m unittest discover -s tests -v
   for file in dist/*.js; do node --check "$file" || exit; done
   python3 tools/serve_ep.py --port 8000
   ```

   Run the server in a persistent session and check its local health and same-origin APIs. The statistics helper uses the provider's read-only V3 POST operation with exact inventory `profileId` selectors. Confirm actual numeric metrics or retain explicit unavailability; do not replace missing data with samples or zero. LinkedIn personal-profile analytics remain unsupported by the documented aggregate endpoint. Preserve the YouTube expiration timestamp/flag discrepancy unless an authoritative new observation resolves it. Check all six navigation pages, the preparation drawer, account refresh, failure and empty states, mobile layout, and browser errors. Account API success proves account read only.

6. **Return one evidence package directly to BOS and verify readback.** Produce a complete Worker Result v1 JSON file for the supplied job/attempt and authenticated `bos-worker` identity. Include exact changes/revision, changed files, executed checks, actual live observations, evidence references, unresolved issues, cost, rollback state, and next action. Record unrun checks accurately. Use the existing canonical values in these task-specific variables; they are not sample assignments:

   ```sh
   python3 tools/bos_handoff.py validate \
     --task-id "$EP_BOS_TASK_ID" --job-id "$EP_BOS_JOB_ID" \
     --attempt-id "$EP_BOS_ATTEMPT_ID" --result "$EP_BOS_RESULT_FILE"
   python3 tools/bos_handoff.py status \
     --task-id "$EP_BOS_TASK_ID" --job-id "$EP_BOS_JOB_ID" \
     --attempt-id "$EP_BOS_ATTEMPT_ID"
   python3 tools/bos_handoff.py submit \
     --task-id "$EP_BOS_TASK_ID" --job-id "$EP_BOS_JOB_ID" \
     --attempt-id "$EP_BOS_ATTEMPT_ID" --result "$EP_BOS_RESULT_FILE"
   ```

   `validate` is offline and does not verify live authority. Successful `submit` requires a matching persistent result readback and returns `verifiedByReadback: true`. That receipt establishes direct delivery, not release approval. If delivery is uncertain, read the existing job before retrying; do not blindly repeat a POST or ask Bert to relay the package. The client reconciles an identical stored result without another POST. If access remains blocked, retain the reviewable result and report the specific missing prerequisite in the authorized record.

7. **Complete independent QA and update the canonical record.** A reviewer verifies the implementation, observed account/statistics capabilities, direct result receipt, and remaining exceptions. BOS owns status and any authorized next transition. Update the current implementation record with that evidence; keep the closed account-read job closed. If revisions are necessary, dispatch them through the same canonical job and return path. Do not describe the workflow as unattended until a real bounded assignment, worker execution, return, independent review, and any necessary revision have been observed.

## Starting evidence and acceptance

The local account/analytics workflow is implemented and browser-verified.
Authenticated account read returned four accounts, and current statistics read
returned HTTP 200 with the exact metrics listed above. The initial HTTP 401 is
historical evidence preceding the scope fix. The BOS return client passed actual
local-server tests at both revisions but has not submitted a hosted Worker Result
from this session. The later review's R5 correction is also live-verified; R6's
missing execution-approval gate is documented. Local return compatibility
fixtures used test-only approval to establish their starting assignment and
must not be treated as proof of a real approval pipeline.

Completion requires the reviewed implementation to be available to its authorized workers, applied cloud settings and secure bindings, accurate capability results, a genuinely approved current BOS assignment, a directly verified Worker Result receipt, and independent QA recorded in that assignment. Current outside prerequisites are repair/activation of the producer execution-approval path on canonical storage, the existing `BOS_WORKER_KEY`, and publication/application of the BOS network/configuration requirements. The canonical implementation job is already registered; analytics access and return compatibility are verified. Coordinate BOS activation work through its existing authorized technical lane, not another EP registration or dispatcher. These requirements do not require rebuilding the established GHL integration or asking Bert to carry routine messages.
