import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('server-side Supabase endpoint guard supports explicit self-hosted deployment without weakening hosted defaults', () => {
  const source = readFileSync(new URL('../src/lib/supabase-endpoint.ts', import.meta.url), 'utf8');
  assert.match(source, /SATARK_SUPABASE_ALLOW_SELF_HOSTED/);
  assert.match(source, /SATARK_ALLOW_INSECURE_LOCAL_SUPABASE/);
  assert.match(source, /LOCAL_HTTP_HOSTS/);
  assert.match(source, /hostname\.endsWith\("\.supabase\.co"\)/);
  assert.match(source, /url\.username \|\| url\.password \|\| url\.search \|\| url\.hash/);
});

test('all Supabase-backed server route handlers use the shared endpoint guard', () => {
  const paths = [
    '../src/app/api/audit/verify/route.ts',
    '../src/app/api/auth/session/route.ts',
    '../src/app/api/cases/notes/route.ts',
    '../src/app/api/cases/route.ts',
    '../src/app/api/evidence/[id]/verify/route.ts',
    '../src/app/api/evidence/records/route.ts',
    '../src/app/api/evidence/route.ts',
    '../src/app/api/findings/route.ts',
    '../src/app/api/firstlight/approvals/route.ts',
    '../src/app/api/firstlight/evidence/source/route.ts',
    '../src/app/api/firstlight/investigate/route.ts',
    '../src/app/api/firstlight/jobs/route.ts',
    '../src/app/api/firstlight/wazuh/alerts/route.ts',
    '../src/app/api/reports/[id]/route.ts',
    '../src/app/api/reports/route.ts',
  ];
  for (const path of paths) {
    const source = readFileSync(new URL(path, import.meta.url), 'utf8');
    assert.match(source, /isAllowedSupabaseEndpoint/, path);
    assert.doesNotMatch(source, /hostname\.endsWith\(['"]\.supabase\.co['"]\)/, path);
  }
});
