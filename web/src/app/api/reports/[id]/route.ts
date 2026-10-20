import { isAllowedSupabaseEndpoint } from '@/lib/supabase-endpoint';
import { createHash } from 'node:crypto';
import { NextResponse } from 'next/server';
import { readBoundedResponseText } from '@/lib/read-bounded-response.mjs';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const MAX_REPORT_RESPONSE_BYTES = 2 * 1024 * 1024;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SHA256 = /^[0-9a-f]{64}$/;

function reply(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: { 'Cache-Control': 'no-store' } });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value);
}

function canonical(value: unknown): string {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') {
    const obj = value as Record<string, unknown>;
    return '{' + Object.keys(obj).sort().map(key => JSON.stringify(key) + ':' + canonical(obj[key])).join(',') + '}';
  }
  const encoded = JSON.stringify(value);
  if (encoded === undefined) throw new TypeError('Unsupported canonical value');
  return encoded;
}

export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  const raw = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!raw || !key) return reply({ error: 'Report storage is not configured.' }, 503);

  const match = /^Bearer ([A-Za-z0-9._~-]+)$/.exec(request.headers.get('authorization') || '');
  if (!match) return reply({ error: 'Sign in is required.' }, 401);

  const { id } = await context.params;
  if (!UUID.test(id)) return reply({ error: 'A valid report id is required.' }, 400);

  try {
    const url = new URL(raw);
    if (!isAllowedSupabaseEndpoint(url)) {
      return reply({ error: 'Report storage is not configured.' }, 503);
    }

    const query = new URLSearchParams({
      select: 'id,tenant_id,case_id,title,report_version,snapshot,snapshot_sha256,created_by,created_at',
      id: 'eq.' + id,
      limit: '1',
    });
    const response = await fetch(url.origin + '/rest/v1/satark_reports?' + query, {
      headers: {
        apikey: key,
        Authorization: 'Bearer ' + match[1],
        Accept: 'application/json',
      },
      cache: 'no-store',
      redirect: 'error',
      signal: AbortSignal.timeout(8_000),
    });

    if (response.status === 401 || response.status === 403) {
      return reply({ error: 'Workspace access denied.' }, 403);
    }
    if (!response.ok) return reply({ error: 'Report storage is temporarily unavailable.' }, 503);

    const bounded = await readBoundedResponseText(response, MAX_REPORT_RESPONSE_BYTES);
    if (!bounded.ok) {
      return reply({
        error: bounded.reason === 'too_large'
          ? 'Stored report exceeds the response size limit.'
          : 'Report storage returned an unreadable response.',
      }, 502);
    }

    let rows: unknown;
    try {
      rows = JSON.parse(bounded.text);
    } catch {
      return reply({ error: 'Report storage returned an invalid response.' }, 502);
    }
    if (!Array.isArray(rows) || !rows[0]) return reply({ error: 'Report was not found.' }, 404);

    const report = rows[0];
    if (!isRecord(report) || !Object.hasOwn(report, 'snapshot') ||
        typeof report.snapshot_sha256 !== 'string' || !SHA256.test(report.snapshot_sha256)) {
      return reply({ error: 'Stored report has an invalid integrity record.' }, 502);
    }

    let actual: string;
    try {
      actual = createHash('sha256').update(canonical(report.snapshot), 'utf8').digest('hex');
    } catch {
      return reply({ error: 'Stored report has an invalid snapshot.' }, 502);
    }

    const integrityMatches = actual === report.snapshot_sha256;
    return reply({
      report,
      integrity: {
        algorithm: 'SHA-256',
        expected_sha256: report.snapshot_sha256,
        actual_sha256: actual,
        matched: integrityMatches,
      },
    }, integrityMatches ? 200 : 409);
  } catch {
    return reply({ error: 'Report retrieval is temporarily unavailable.' }, 503);
  }
}
