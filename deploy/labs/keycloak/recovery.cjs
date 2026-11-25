const assert = require('node:assert/strict');
const { readFileSync, writeFileSync } = require('node:fs');
const { join, resolve } = require('node:path');
const { request } = require('playwright');

const [mode, state, output] = process.argv.slice(2);
const configuration = JSON.parse(readFileSync(join(state, 'projects.json'))).TEST;
const repository = configuration.repositories.backend;
const scanner = 'Semgrep JSON Report';
const source = readFileSync(resolve(__dirname, '../../../unittests/scans/semgrep/one_finding.json'));

async function post(api, key) {
  return api.post('/api/aspm/v1/scans/', {
    headers: { 'Idempotency-Key': key },
    multipart: {
      project_id: String(configuration.id), repository_url: repository.url, commit_sha: 'c'.repeat(40),
      scanner_type: scanner, pipeline_id: 'qualification-recovery',
      file: { name: 'one_finding.json', mimeType: 'application/json', buffer: source },
    },
  });
}

async function main() {
  const api = await request.newContext({
    baseURL: 'https://localhost:48141', ignoreHTTPSErrors: true, extraHTTPHeaders: { Authorization: `ASPM ${configuration.token}` },
  });
  try {
    if (mode === 'submit') {
      const key = `worker-recovery-${Date.now()}`;
      const accepted = await post(api, key);
      assert.equal(accepted.status(), 202);
      const scan = await accepted.json();
      assert.equal(scan.status, 'ACCEPTED');
      const stored = await api.get(`/api/aspm/v1/scans/${scan.id}/`);
      assert.equal(stored.status(), 200);
      assert.equal((await stored.json()).status, 'ACCEPTED');
      writeFileSync(output, JSON.stringify({ key, id: scan.id, accepted_without_worker: true }) + '\n');
    } else if (mode === 'recover') {
      const prior = JSON.parse(readFileSync(output));
      const deadline = Date.now() + 45000;
      let scan;
      while (Date.now() < deadline) {
        const response = await api.get(`/api/aspm/v1/scans/${prior.id}/`);
        assert.equal(response.status(), 200);
        scan = await response.json();
        if (scan.status === 'COMPLETED' || scan.status === 'FAILED') break;
        await new Promise(resolve => setTimeout(resolve, 400));
      }
      assert.equal(scan.status, 'COMPLETED');
      assert.equal(scan.attempt, 1);
      assert.ok(scan.test);
      const replay = await post(api, prior.key);
      assert.equal(replay.status(), 200);
      const seen = await replay.json();
      assert.equal(seen.id, scan.id);
      assert.equal(seen.test, scan.test);
      writeFileSync(output, JSON.stringify({
        accepted_without_worker: prior.accepted_without_worker, status_after_restart: scan.status,
        attempts: scan.attempt, idempotent_replay_status: replay.status(), same_scan_and_test: true,
      }, null, 2) + '\n');
    } else {
      throw new Error('Expected submit or recover');
    }
  } finally {
    await api.dispose();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
