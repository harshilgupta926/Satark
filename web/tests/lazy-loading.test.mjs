import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const source = path => readFile(new URL(path, import.meta.url), 'utf8');

test('home service-readiness bundle waits until its section approaches the viewport', async () => {
  const page = await source('../src/app/page.tsx');
  assert.match(page, /dynamic\(\(\) => import\('\.\.\/components\/service-readiness'\)/);
  assert.match(page, /new IntersectionObserver/);
  assert.match(page, /readinessVisible\s*\?\s*<ServiceReadiness\s*\/>/);
  assert.match(page, /readiness-lazy-placeholder/);
  assert.doesNotMatch(page, /^import ServiceReadiness from/m);
});

test('FIRSTLIGHT defers workspace and insight modules until they are needed', async () => {
  const page = await source('../src/app/firstlight/page.tsx');
  assert.match(page, /dynamic\(\(\) => import\('\.\/persistent-case-panel'\)/);
  assert.match(page, /dynamic\(\(\) => import\('\.\/insights'\)\.then\(module => module\.FindingsInsights\)/);
  assert.match(page, /dynamic\(\(\) => import\('\.\/insights'\)\.then\(module => module\.EventTracker\)/);
  assert.match(page, /persistentPanelVisible\s*\?\s*<PersistentCasePanel/);
  assert.match(page, /new IntersectionObserver/);
  assert.doesNotMatch(page, /^import PersistentCasePanel from/m);
  assert.doesNotMatch(page, /^import \{ EventTracker, FindingsInsights \} from/m);
});

test('QR fallback decoder is downloaded only when fallback decoding is needed', async () => {
  const page = await source('../src/app/qr/page.tsx');
  assert.doesNotMatch(page, /^import jsQR from ['"]jsqr['"]/m);
  assert.match(page, /const \{ default: jsQR \} = await import\('jsqr'\)/);
});
