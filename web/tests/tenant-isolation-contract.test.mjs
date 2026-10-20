import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('./tenant-isolation.integration.test.mjs', import.meta.url), 'utf8');

test('tenant integration probes have bounded network timeouts', () => {
  assert.ok(source.includes('AbortSignal.timeout(REQUEST_TIMEOUT_MS)'));
  assert.ok(source.includes('const REQUEST_TIMEOUT_MS = 8_000'));
});

test('cross-tenant create is accepted as denied only for authorization responses', () => {
  assert.ok(source.includes('[401, 403]'));
  assert.ok(source.includes('write.status'));
  assert.doesNotMatch(source, /401,\\s*403,\\s*409,\\s*422/);
});

test('viewer create requires an authorization denial and viewer update cannot silently skip', () => {
  assert.ok(source.includes('[401, 403]'));
  assert.ok(source.includes('create.status'));
  assert.ok(source.includes('rows.length > 0'));
  assert.match(source, /assert\.deepEqual\(await update\.json\(\), \[\],/);
});
