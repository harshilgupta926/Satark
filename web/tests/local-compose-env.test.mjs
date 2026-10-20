import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const compose = await readFile(new URL('../../docker-compose.local.yml', import.meta.url), 'utf8');
const dockerfile = await readFile(new URL('../Dockerfile', import.meta.url), 'utf8');

test('local Compose passes server-side Supabase auth config to the web container', () => {
  assert.ok(compose.includes('SUPABASE_URL: ${SUPABASE_URL:-}'));
  assert.ok(compose.includes('SUPABASE_PUBLISHABLE_KEY: ${SUPABASE_PUBLISHABLE_KEY:-}'));
});

test('local Next.js image receives public Supabase config at build time', () => {
  assert.ok(compose.includes('NEXT_PUBLIC_SUPABASE_URL: ${NEXT_PUBLIC_SUPABASE_URL:-}'));
  assert.ok(compose.includes('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: ${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:-}'));
  assert.ok(dockerfile.includes('ARG NEXT_PUBLIC_SUPABASE_URL'));
  assert.ok(dockerfile.includes('ARG NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY'));
});

test('local containers can reach the host Supabase API on Linux Docker', () => {
  assert.ok(compose.includes('host.docker.internal:host-gateway'));
});

test('offline acceptance probe uses loopback-only service URLs by default', async () => {
  const probe = await readFile(new URL('../../scripts/check-local-offline-services.sh', import.meta.url), 'utf8');
  assert.ok(probe.includes('http://127.0.0.1:3000'));
  assert.ok(probe.includes('http://127.0.0.1:54321'));
  assert.ok(probe.includes('http://127.0.0.1:11434'));
  assert.ok(probe.includes('check_local_url'));
  assert.ok(probe.includes('does not itself prove that the host is offline'));
});
