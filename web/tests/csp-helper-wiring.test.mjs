import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const config = readFileSync(new URL('../next.config.ts', import.meta.url), 'utf8');

test('Next.js wires CSP to the validated Supabase origin helper', () => {
  assert.ok(config.includes("import { buildSecurityHeaders } from './src/lib/security-headers.mjs';"));
  assert.ok(config.includes('const securityHeaders = buildSecurityHeaders(process.env);'));
  assert.ok(!config.includes('https://*.supabase.co'));
  assert.ok(!config.includes('wss://*.supabase.co'));
});
