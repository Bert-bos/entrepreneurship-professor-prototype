'use strict';

// Offline regression/security checks through the real signed approval gate.
// BOS_SOURCE_DIR/BOS_REFERENCE_DIR may select a read-only source checkout.
// No approval-state edits, force helper, real key, or network transport is used.
const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');
const source = process.env.BOS_SOURCE_DIR || process.env.BOS_REFERENCE_DIR || path.resolve(__dirname, '..');
const { createEngine } = require(path.join(source, 'src/dispatch-engine'));
const { canonicalPayload, computePayloadHash, computeRecordVersion } = require(path.join(source, 'src/dispatch-binding'));
const { signPayload } = require(path.join(source, 'src/dispatch-producer-auth'));
const { TOKEN_URL } = require(path.join(source, 'src/dispatch-drive-auth'));
const { runScenario } = require('./bos-approval-timestamp-probe.cjs');
const epoch = Date.parse('2026-10-05T17:00:00.000Z');
const maxAgeMs = 30 * 60 * 1000;
const rsa = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
const credential = { clientEmail: 'synthetic@invalid.iam.gserviceaccount.com', privateKey: rsa.privateKey.export({ type: 'pkcs1', format: 'pem' }) };

async function fixture(t, { advancePerFetch = 10, jobId = 'EP-TIMESTAMP-SYNTHETIC', approvalMaxAgeMs = maxAgeMs } = {}) {
  const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'ep-timestamp-security-'));
  t.after(() => fs.rmSync(temporary, { recursive: true, force: true }));
  const pair = crypto.generateKeyPairSync('ed25519');
  const privateKeyPem = pair.privateKey.export({ type: 'pkcs8', format: 'pem' });
  const trustedKeysPath = path.join(temporary, 'synthetic-public-trust.json');
  fs.writeFileSync(trustedKeysPath, JSON.stringify([{ keyId: 'synthetic-test', publicKeyPem: pair.publicKey.export({ type: 'spki', format: 'pem' }), effectiveFrom: '2020-01-01T00:00:00Z', revokedAt: null }]));
  let currentMs = epoch;
  const clock = () => new Date(currentMs);
  const engine = createEngine({ dataDir: path.join(temporary, 'data'), clock, approvalMaxAgeMs });
  const revision = new Date(epoch - 60000).toISOString();
  const envelope = {
    schema_version: '1.0', job_id: jobId, idempotency_key: `${jobId}:1`,
    objective: 'Offline signed timestamp test.', owning_project: 'synthetic-test', requested_by: 'local-test',
    created_at: revision, due_at: null, priority: 'P2', current_verified_state: 'No live assignment.',
    source_manifest: [{ source_id: 'drive:synthetic-doc', revision, kind: 'google_doc' }],
    scope: ['Local temporary state.'], explicit_exclusions: ['No live access.'], requirements: ['Use real approval gate.'],
    constraints: ['No spending.'], data_class: 'INTERNAL', authorized_source_ids: ['drive:synthetic-doc'],
    execution_lane: 'deterministic', repository: null, acceptance_criteria: ['Signature and freshness checked.'],
    required_tests: ['Offline timestamp tests.'], required_evidence: ['Assertions.'], rollback: 'Delete temporary directory.',
    stop_conditions: ['Any real network request.'], protected_actions: ['deploy'],
    cost_policy: { metered_calls_allowed: false, max_job_usd: 0, max_call_usd: null }, dependencies: [],
    authorization_binding: { command_center_job_id: jobId, drive_file_id: 'synthetic-doc', drive_revision: revision, drive_doc_url: 'https://docs.google.com/document/d/synthetic-doc/edit' },
  };
  const { handoff } = await engine.ingestJobEnvelope(envelope);
  assert.equal(handoff.status, 'ROUTED');
  const body = `JOB_ID: ${jobId}\nAUTHORIZED_BY: synthetic-test\nNo live authorization.`;
  const row = [jobId, 'Synthetic', 'ChatGPT', 'Offline only', 'APPROVED_FOR_EXECUTION'];
  const headers = ['Job ID', 'Project / Domain', 'Worker', 'Job / Outcome', 'Execution State'];
  const observed = [];
  const live = { revision, row: [...row] };
  const fetchImpl = async (url) => {
    currentMs += advancePerFetch;
    observed.push(url);
    if (url === TOKEN_URL) return { ok: true, status: 200, json: async () => ({ access_token: 'synthetic-offline-token', expires_in: 3600 }) };
    if (url.startsWith('https://sheets.googleapis.com/')) return { ok: true, status: 200, json: async () => ({ values: [headers, live.row] }) };
    if (url.includes('/export')) return { ok: true, status: 200, text: async () => body };
    if (url.startsWith('https://www.googleapis.com/drive/v3/files/')) return { ok: true, status: 200, json: async () => ({ id: 'synthetic-doc', modifiedTime: live.revision, mimeType: 'application/vnd.google-apps.document' }) };
    throw new Error('Unexpected request rejected by offline test');
  };
  function signature(timestamp) {
    return signPayload({ privateKeyPem, canonicalPayload: canonicalPayload({ jobId, payloadHash: computePayloadHash(body), driveFileId: 'synthetic-doc', driveRevision: revision, ccRecordId: `AI JOB LOG:${jobId}`, ccRecordVersion: computeRecordVersion(row), approvalState: 'APPROVED_FOR_EXECUTION', approvalTimestamp: timestamp }) });
  }
  function approve(timestamp, signatureBase64 = signature(timestamp)) {
    return engine.approveForExecution(handoff.task_id, { producerKeyId: 'synthetic-test', signatureBase64, signedApprovalTimestamp: timestamp, driveCredential: credential, ccCredential: credential, fetchImpl, trustedKeysPath });
  }
  return { engine, taskId: handoff.task_id, approve, signature, clock, setTime: (ms) => { currentMs = ms; }, live, observed, fetchImpl, trustedKeysPath };
}

test('advancing clock: signed timestamp survives fresh independent reads and stays in receipt', async (t) => {
  const f = await fixture(t, { advancePerFetch: 1000 });
  const timestamp = f.clock().toISOString();
  const result = await f.approve(timestamp);
  assert.equal(result.ok, true);
  assert.ok(f.clock().getTime() > Date.parse(timestamp));
  assert.equal(result.handoff.approval.approvalTimestamp, timestamp);
  assert.ok(f.observed.some((url) => url.includes('sheets.googleapis.com')));
  assert.ok(f.observed.some((url) => url.includes('/export')));
});

test('approval lease starts at signed time, not verification time; stale signature cannot reapprove', async (t) => {
  const f = await fixture(t, { advancePerFetch: 1000 });
  const timestamp = f.clock().toISOString();
  assert.equal((await f.approve(timestamp)).ok, true);
  f.setTime(epoch + maxAgeMs);
  await assert.rejects(f.engine.claimTask(f.taskId, { machine: 'synthetic', worker: 'synthetic-worker' }), /approval had expired/);
  assert.equal(f.engine.getHandoff(f.taskId).status, 'ROUTED');
  const replay = await f.approve(timestamp);
  assert.equal(replay.ok, false);
  assert.equal(replay.reason, 'approval_timestamp_stale');
  assert.equal(f.engine.getHandoff(f.taskId).status, 'ROUTED');
});

test('fresh signed request that ages out during source reads is rejected', async (t) => {
  const f = await fixture(t, { advancePerFetch: 1000 });
  const timestamp = new Date(epoch - maxAgeMs + 1).toISOString();
  assert.equal((await f.approve(timestamp)).reason, 'approval_timestamp_stale');
  assert.equal(f.engine.getHandoff(f.taskId).status, 'ROUTED');
});

test('future signed timestamp is rejected', async (t) => {
  const f = await fixture(t);
  assert.equal((await f.approve(new Date(epoch + 60000).toISOString())).reason, 'approval_timestamp_in_future');
});

test('configured freshness window accepts boundary minus 1 millisecond and rejects the boundary', async (t) => {
  const valid = await fixture(t, { advancePerFetch: 0, approvalMaxAgeMs: 5000 });
  assert.equal((await valid.approve(new Date(epoch - 4999).toISOString())).ok, true);
  const stale = await fixture(t, { advancePerFetch: 0, approvalMaxAgeMs: 5000 });
  assert.equal((await stale.approve(new Date(epoch - 5000).toISOString())).reason, 'approval_timestamp_stale');
});

for (const timestamp of [null, 0, NaN, Infinity, '', 'not-a-date', '2026-10-05T17:00:00Z', '2026-02-30T17:00:00.000Z', '2026-10-05T17:00:00.000+00:00']) {
  test(`malformed/noncanonical timestamp ${JSON.stringify(timestamp)} fails closed`, async (t) => {
    const f = await fixture(t);
    assert.equal((await f.approve(timestamp, f.signature(new Date(epoch).toISOString()))).reason, 'approval_timestamp_invalid');
    assert.equal(f.engine.getHandoff(f.taskId).status, 'ROUTED');
  });
}

test('changing a valid timestamp without resigning fails signature verification', async (t) => {
  const f = await fixture(t);
  const original = new Date(epoch).toISOString();
  assert.equal((await f.approve(new Date(epoch - 1).toISOString(), f.signature(original))).reason, 'producer_signature_signature_invalid');
});

test('same valid approval cannot be replayed while already approved', async (t) => {
  const f = await fixture(t);
  const timestamp = f.clock().toISOString();
  assert.equal((await f.approve(timestamp)).ok, true);
  await assert.rejects(f.approve(timestamp), /not "ROUTED"/);
  assert.equal(f.engine.getHandoff(f.taskId).approval.approvalTimestamp, timestamp);
});

test('fresh timestamp does not bypass changed Drive revision or Command Center binding', async (t) => {
  const f = await fixture(t);
  const timestamp = f.clock().toISOString();
  f.live.revision = '2026-10-05T17:00:01.000Z';
  assert.equal((await f.approve(timestamp)).reason, 'drive_revision_mismatch_doc_changed_since_routing');
  f.live.revision = '2026-10-05T16:59:00.000Z';
  f.live.row[2] = 'Changed worker';
  assert.equal((await f.approve(timestamp)).reason, 'producer_signature_signature_invalid');
  f.live.row[4] = 'ROUTED';
  assert.equal((await f.approve(timestamp)).reason, 'command_center_execution_state_not_approved_for_execution');
});

test('legacy same-clock caller can still omit signedApprovalTimestamp', async (t) => {
  const f = await fixture(t, { advancePerFetch: 0 });
  const result = await f.engine.approveForExecution(f.taskId, { producerKeyId: 'synthetic-test', signatureBase64: f.signature(f.clock().toISOString()), driveCredential: credential, ccCredential: credential, fetchImpl: f.fetchImpl, trustedKeysPath: f.trustedKeysPath });
  assert.equal(result.ok, true);
});

test('actual CLI succeeds with advancing wall clock through real signed gate', async () => {
  const result = await runScenario({ source, frozen: false });
  assert.equal(result.cliExitCode, 0);
  assert.equal(result.approvalOk, true);
  assert.equal(result.persistedStatus, 'APPROVED_FOR_EXECUTION');
});

test('actual CLI sets nonzero exit code when fresh Command Center recheck rejects', async () => {
  const result = await runScenario({ source, frozen: false, rejectSecondRow: true });
  assert.equal(result.cliExitCode, 1);
  assert.equal(result.approvalOk, false);
  assert.equal(result.approvalReason, 'command_center_execution_state_not_approved_for_execution');
  assert.equal(result.persistedStatus, 'ROUTED');
});
