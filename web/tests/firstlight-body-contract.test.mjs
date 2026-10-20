import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('FIRSTLIGHT API bounds streamed request bytes before JSON parsing', async () => {
  const source = await readFile(new URL('../src/app/api/firstlight/investigate/route.ts', import.meta.url), 'utf8');
  assert.ok(source.includes("const MAX_BODY_BYTES = 2 * 1024 * 1024"));
  assert.ok(source.includes("request.body?.getReader()"), 'request must be read incrementally');
  assert.ok(source.includes('totalBytes += value.byteLength'), 'actual streamed bytes must be counted');
  assert.ok(source.includes('if (totalBytes > MAX_BODY_BYTES)'), 'chunked requests must be rejected at the byte limit');
  assert.ok(source.includes("return reply({ error: 'Investigation request is too large.' }, 413)"), 'oversized request must return 413');
  assert.ok(source.includes("void reader.cancel().catch(() => undefined)"), 'cancellation failure must not change the oversized response');
  assert.ok(!source.includes('await request.text()'), 'the endpoint must not buffer an unbounded body before checking its size');
});


test('saved FIRSTLIGHT evidence reload preserves its original browser digest', async () => {
  const source = await readFile(new URL('../src/app/firstlight/persistent-case-panel.tsx', import.meta.url), 'utf8');
  assert.ok(source.includes("digest: typeof row.metadata?.browser_record_sha256 === 'string' ? row.metadata.browser_record_sha256 : ''"),
    'the server envelope hash must not be substituted for the browser canonical evidence hash');
  assert.ok(source.includes('never substitute a different hash'),
    'the integrity boundary must remain documented beside the mapping');
});


test('saved FIRSTLIGHT reports include the visible session audit and simulated decisions', async () => {
  const source = await readFile(new URL('../src/app/firstlight/persistent-case-panel.tsx', import.meta.url), 'utf8');
  assert.ok(source.includes('audit_events_visible_in_session: audit.map(event => ({ ...event }))'),
    'the saved report must preserve the session audit instead of exporting an empty array');
  assert.ok(source.includes('simulated_response_decisions: [...actions]'),
    'the saved report must preserve the explicit simulated response decisions');
  assert.ok(source.includes('Database-triggered audit events are separate from this session log'),
    'session events must not be misrepresented as server audit events');
});

test('evidence, findings, and report APIs enforce actual streamed request size', async () => {
  const helper = await readFile(new URL('../src/lib/read-bounded-json.ts', import.meta.url), 'utf8');
  assert.ok(helper.includes('request.body.getReader()'), 'shared parser must consume the stream');
  assert.ok(helper.includes('totalBytes += value.byteLength'), 'shared parser must count actual bytes');
  assert.ok(helper.includes('if (totalBytes > maxBytes)'), 'shared parser must reject chunked oversized requests');
  assert.ok(helper.includes("void reader.cancel().catch(() => undefined)"), 'cancel failures must not hide the 413 result');
  assert.ok(helper.includes("new TextDecoder('utf-8', { fatal: true })"), 'invalid UTF-8 must fail closed');
  for (const [path, limit] of [
    ['../src/app/api/evidence/records/route.ts', 'MAX_BODY'],
    ['../src/app/api/findings/route.ts', '24 * 1024'],
    ['../src/app/api/reports/route.ts', '1100 * 1024'],
  ]) {
    const source = await readFile(new URL(path, import.meta.url), 'utf8');
    assert.ok(source.includes('readBoundedJson(request,' ) || source.includes('readBoundedJson(request, '), path + ' must use the shared bounded parser');
    assert.ok(source.includes(limit), path + ' must retain an explicit route-specific limit');
    assert.ok(!source.includes('await request.json()'), path + ' must not parse an unbounded body first');
  }
});

test('persistent FIRSTLIGHT retries verify duplicate content instead of silently skipping conflicts', async () => {
  const source = await readFile(new URL('../src/app/firstlight/persistent-case-panel.tsx', import.meta.url), 'utf8');
  assert.ok(source.includes('Evidence conflict detected: the stored record differs from this version.'), 'mismatched duplicate evidence must fail closed');
  assert.ok(source.includes('Finding conflict detected: the stored finding differs from this version.'), 'mismatched duplicate findings must fail closed');
  assert.ok(source.includes('browser_record_sha256 !== item.digest'), 'duplicate evidence must compare the original browser digest');
  assert.ok(source.includes('verified identical evidence retries'), 'the save result must distinguish newly saved records from verified retries');
  assert.ok(source.includes('evidence.length > 500'), 'oversized evidence sets must not be silently truncated');
  assert.ok(source.includes('duplicate records are skipped only after exact stored-content verification.'), 'partial-save messaging must explain the safe retry behavior');
});

test('independent FIRSTLIGHT model agent implementation is opt-in, bounded, and read-only', async () => {
  const source = await readFile(new URL('../../firstlight_agents.py', import.meta.url), 'utf8');
  assert.ok(source.includes('FIRSTLIGHT_MODEL_AGENTS_ENABLED'), 'model agents must require explicit enablement');
  assert.ok(source.includes('MAX_EVIDENCE = 80'), 'each agent prompt must receive a bounded evidence projection');
  assert.ok(source.includes('ALLOWED_TOOL_NAMES: frozenset[str] = frozenset()'), 'agents must have no executable tool permissions');
  assert.ok(source.includes('AgentResult.model_validate(payload)'), 'agent output must be schema validated');
  assert.ok(source.includes('all(ref in known_ids for ref in finding.evidence_ids)'), 'invented evidence references must be discarded');
  assert.ok(source.includes('AGENT_TIMEOUT_SECONDS = 22'), 'provider calls must have a bounded timeout');
  assert.ok(source.includes('deterministic analysis remains authoritative'), 'model failures must not suppress deterministic findings');
});
