import test from 'node:test';
import assert from 'node:assert/strict';

const env = process.env;
const required = [
  'SUPABASE_URL', 'SUPABASE_PUBLISHABLE_KEY',
  'SATARK_TEST_USER_A_EMAIL', 'SATARK_TEST_USER_A_PASSWORD', 'SATARK_TEST_TENANT_A_ID',
  'SATARK_TEST_USER_B_EMAIL', 'SATARK_TEST_USER_B_PASSWORD', 'SATARK_TEST_TENANT_B_ID',
];
const missing = required.filter(key => !env[key]);
const configured = missing.length === 0;
const viewerRequired = [
  'SUPABASE_URL',
  'SUPABASE_PUBLISHABLE_KEY',
  'SATARK_TEST_VIEWER_EMAIL',
  'SATARK_TEST_VIEWER_PASSWORD',
  'SATARK_TEST_VIEWER_TENANT_ID',
];
const viewerMissing = viewerRequired.filter(key => !env[key]);
const base = (env.SUPABASE_URL || '').replace(/\/$/, '');
const apiKey = env.SUPABASE_PUBLISHABLE_KEY || '';
const REQUEST_TIMEOUT_MS = 8_000;

async function login(email, password) {
  const response = await fetch(base + '/auth/v1/token?grant_type=password', {
    method: 'POST',
    headers: { apikey: apiKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    cache: 'no-store',
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });
  assert.equal(response.status, 200, 'test account must be able to sign in');
  const session = await response.json();
  assert.ok(session.access_token, 'Supabase Auth must return an access token');
  assert.ok(session.user?.id, 'Supabase Auth must return a user ID');
  return { token: session.access_token, userId: session.user.id };
}

async function rest(session, path, init = {}) {
  return fetch(base + '/rest/v1/' + path, {
    ...init,
    headers: {
      apikey: apiKey,
      Authorization: 'Bearer ' + session.token,
      Accept: 'application/json',
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
    cache: 'no-store',
    signal: init.signal ?? AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });
}

test('tenant RLS blocks cross-tenant reads and writes for two distinct users', {
  skip: configured ? false : 'Set up two non-admin Supabase test users and separate tenant IDs; missing: ' + missing.join(', '),
}, async () => {
  assert.notEqual(env.SATARK_TEST_TENANT_A_ID, env.SATARK_TEST_TENANT_B_ID, 'test tenants must be distinct');
  const [a, b] = await Promise.all([
    login(env.SATARK_TEST_USER_A_EMAIL, env.SATARK_TEST_USER_A_PASSWORD),
    login(env.SATARK_TEST_USER_B_EMAIL, env.SATARK_TEST_USER_B_PASSWORD),
  ]);
  assert.notEqual(a.userId, b.userId, 'test users must be distinct');

  for (const [session, ownTenant, foreignTenant] of [
    [a, env.SATARK_TEST_TENANT_A_ID, env.SATARK_TEST_TENANT_B_ID],
    [b, env.SATARK_TEST_TENANT_B_ID, env.SATARK_TEST_TENANT_A_ID],
  ]) {
    const ownTenantRead = await rest(session, 'satark_tenants?' + new URLSearchParams({
      select: 'id,name',
      id: 'eq.' + ownTenant,
    }));
    assert.equal(ownTenantRead.status, 200, 'tenant member should be able to read their own tenant');
    const ownTenants = await ownTenantRead.json();
    assert.equal(ownTenants.length, 1, 'tenant member should see exactly their own tenant fixture');

    const ownMembershipRead = await rest(session, 'satark_memberships?' + new URLSearchParams({
      select: 'tenant_id,user_id,role',
      tenant_id: 'eq.' + ownTenant,
    }));
    assert.equal(ownMembershipRead.status, 200, 'tenant owner should be able to read own tenant memberships');
    const ownMemberships = await ownMembershipRead.json();
    assert.ok(ownMemberships.some(row => row.user_id === session.userId && row.role === 'owner'),
      'owner should see their own membership in the tenant');

    const foreignTenantRead = await rest(session, 'satark_tenants?' + new URLSearchParams({
      select: 'id',
      id: 'eq.' + foreignTenant,
    }));
    assert.equal(foreignTenantRead.status, 200, 'foreign tenant reads should be safely filtered by RLS');
    assert.deepEqual(await foreignTenantRead.json(), [], 'a user must not read another tenant row');

    const foreignMembershipRead = await rest(session, 'satark_memberships?' + new URLSearchParams({
      select: 'tenant_id,user_id,role',
      tenant_id: 'eq.' + foreignTenant,
    }));
    assert.equal(foreignMembershipRead.status, 200, 'foreign membership reads should be safely filtered by RLS');
    assert.deepEqual(await foreignMembershipRead.json(), [], 'a user must not enumerate another tenant memberships');

    const query = new URLSearchParams({ select: 'id,tenant_id,title', tenant_id: 'eq.' + foreignTenant, limit: '20' });
    const read = await rest(session, 'satark_cases?' + query);
    assert.equal(read.status, 200, 'RLS should return an empty list instead of leaking foreign rows');
    assert.deepEqual(await read.json(), [], 'a user must not read another tenant’s cases');

    // Tenant isolation applies to every persisted investigation resource, not
    // only the parent case table. Query each resource directly so this test
    // exercises database RLS rather than relying on frontend/API filtering.
    for (const table of ['satark_evidence', 'satark_findings', 'satark_reports', 'satark_audit_events', 'satark_case_notes', 'satark_approvals', 'satark_investigation_jobs']) {
      const resourceQuery = new URLSearchParams({
        select: 'id,tenant_id',
        tenant_id: 'eq.' + foreignTenant,
        limit: '20',
      });
      const resourceRead = await rest(session, table + '?' + resourceQuery);
      assert.equal(resourceRead.status, 200, table + ' cross-tenant read should be safely filtered by RLS');
      assert.deepEqual(await resourceRead.json(), [], table + ' must not expose another tenant’s records');
    }

    const write = await rest(session, 'satark_cases', {
      method: 'POST',
      headers: { Prefer: 'return=representation' },
      body: JSON.stringify({
        tenant_id: foreignTenant,
        title: 'SATARK isolated RLS integration probe',
        status: 'open',
        severity: 'unknown',
        created_by: session.userId,
        metadata: { test_probe: true },
      }),
    });
    assert.ok(
      [401, 403].includes(write.status),
      `foreign-tenant writes must be rejected by authorization/RLS, got HTTP ${write.status}`,
    );
  }
});

test('tenant owners can read and update cases in their own tenant', {
  skip: configured ? false : 'Set up two non-admin Supabase test users and separate tenant IDs; missing: ' + missing.join(', '),
}, async () => {
  assert.notEqual(env.SATARK_TEST_TENANT_A_ID, env.SATARK_TEST_TENANT_B_ID, 'test tenants must be distinct');
  const [a, b] = await Promise.all([
    login(env.SATARK_TEST_USER_A_EMAIL, env.SATARK_TEST_USER_A_PASSWORD),
    login(env.SATARK_TEST_USER_B_EMAIL, env.SATARK_TEST_USER_B_PASSWORD),
  ]);
  assert.notEqual(a.userId, b.userId, 'test users must be distinct');

  for (const [session, tenantId, label] of [
    [a, env.SATARK_TEST_TENANT_A_ID, 'A'],
    [b, env.SATARK_TEST_TENANT_B_ID, 'B'],
  ]) {
    const ownCasesResponse = await rest(session, 'satark_cases?' + new URLSearchParams({
      select: 'id,title',
      tenant_id: 'eq.' + tenantId,
      order: 'created_at.asc',
      limit: '1',
    }));
    assert.equal(ownCasesResponse.status, 200, 'tenant owner should be able to read cases in their own tenant');
    const ownCases = await ownCasesResponse.json();
    assert.ok(ownCases.length > 0, 'each tenant fixture must contain a disposable case');
    const fixture = ownCases[0];
    const originalTitle = fixture.title;
    const updatedTitle = originalTitle + ' [authorized update probe ' + label + ' ' + Date.now() + ']';

    try {
      const update = await rest(session, 'satark_cases?' + new URLSearchParams({
        id: 'eq.' + fixture.id,
        tenant_id: 'eq.' + tenantId,
      }), {
        method: 'PATCH',
        headers: { Prefer: 'return=representation' },
        body: JSON.stringify({ title: updatedTitle }),
      });
      assert.equal(update.status, 200, 'tenant owner should be able to update a case in their own tenant');
      const updatedRows = await update.json();
      assert.equal(updatedRows.length, 1, 'same-tenant update should return exactly the updated case');
      assert.equal(updatedRows[0].title, updatedTitle, 'same-tenant update should persist the change');
    } finally {
      // Restore even if an assertion fails so a failed CI attempt cannot leave
      // a mutated fixture that makes later runs nondeterministic.
      const restore = await rest(session, 'satark_cases?' + new URLSearchParams({
        id: 'eq.' + fixture.id,
        tenant_id: 'eq.' + tenantId,
      }), {
        method: 'PATCH',
        headers: { Prefer: 'return=representation' },
        body: JSON.stringify({ title: originalTitle }),
      });
      assert.equal(restore.status, 200, 'tenant owner should be able to restore the disposable fixture');
      const restoredRows = await restore.json();
      assert.equal(restoredRows.length, 1, 'fixture restoration should update exactly one case');
      assert.equal(restoredRows[0].title, originalTitle, 'fixture title should be restored after the probe');
    }
  }
});

test('audit verification RPC permits tenant members and denies cross-tenant access', {
  skip: configured ? false : 'Set up two non-admin Supabase test users and separate tenant IDs; missing: ' + missing.join(', '),
}, async () => {
  const [a, b] = await Promise.all([
    login(env.SATARK_TEST_USER_A_EMAIL, env.SATARK_TEST_USER_A_PASSWORD),
    login(env.SATARK_TEST_USER_B_EMAIL, env.SATARK_TEST_USER_B_PASSWORD),
  ]);
  assert.notEqual(a.userId, b.userId, 'test users must be distinct');

  const ownVerification = await rest(a, 'rpc/satark_verify_audit_chain', {
    method: 'POST',
    body: JSON.stringify({ target_tenant: env.SATARK_TEST_TENANT_A_ID }),
  });
  assert.equal(ownVerification.status, 200, 'tenant member should be allowed to verify their own audit chain');
  const ownResult = await ownVerification.json();
  assert.ok(Array.isArray(ownResult) && ownResult.length === 1, 'audit verifier should return one result row');
  assert.equal(typeof ownResult[0].chain_valid, 'boolean', 'audit verifier should return a chain validity result');
  assert.ok(Number(ownResult[0].event_count) > 0, 'Tenant A fixture should produce audit events so verification is not vacuous');
  assert.equal(ownResult[0].chain_valid, true, 'seeded tenant audit chain should verify successfully');

  const foreignVerification = await rest(a, 'rpc/satark_verify_audit_chain', {
    method: 'POST',
    body: JSON.stringify({ target_tenant: env.SATARK_TEST_TENANT_B_ID }),
  });
  assert.ok(
    [401, 403].includes(foreignVerification.status),
    'audit verifier must deny a caller from another tenant; got HTTP ' + foreignVerification.status,
  );

  const bVerification = await rest(b, 'rpc/satark_verify_audit_chain', {
    method: 'POST',
    body: JSON.stringify({ target_tenant: env.SATARK_TEST_TENANT_B_ID }),
  });
  assert.equal(bVerification.status, 200, 'Tenant B member should verify Tenant B audit chain');
  const bResult = await bVerification.json();
  assert.ok(Array.isArray(bResult) && bResult.length === 1, 'Tenant B audit verifier should return one result row');
  assert.ok(Number(bResult[0].event_count) > 0, 'Tenant B fixture should produce audit events so verification is not vacuous');
  assert.equal(bResult[0].chain_valid, true, 'Tenant B seeded audit chain should verify successfully');
});

test('approval and assignable-member RPCs enforce tenant roles and fail closed', {
  skip: configured && viewerMissing.length === 0 ? false : 'Set up two non-admin Supabase test users and a viewer; missing: ' + [...missing, ...viewerMissing].join(', '),
}, async () => {
  const [a, b, viewer] = await Promise.all([
    login(env.SATARK_TEST_USER_A_EMAIL, env.SATARK_TEST_USER_A_PASSWORD),
    login(env.SATARK_TEST_USER_B_EMAIL, env.SATARK_TEST_USER_B_PASSWORD),
    login(env.SATARK_TEST_VIEWER_EMAIL, env.SATARK_TEST_VIEWER_PASSWORD),
  ]);

  const assignable = await rest(a, 'rpc/satark_list_assignable_members', {
    method: 'POST',
    body: JSON.stringify({ p_tenant_id: env.SATARK_TEST_TENANT_A_ID }),
  });
  assert.equal(assignable.status, 200, 'tenant owner should be able to enumerate assignable members in their tenant');
  const assignableRows = await assignable.json();
  assert.ok(assignableRows.some(row => row.user_id === a.userId && row.role === 'owner'),
    'assignable-member RPC should include the authenticated tenant owner');

  const foreignAssignable = await rest(a, 'rpc/satark_list_assignable_members', {
    method: 'POST',
    body: JSON.stringify({ p_tenant_id: env.SATARK_TEST_TENANT_B_ID }),
  });
  assert.ok([401, 403].includes(foreignAssignable.status),
    'assignable-member RPC must deny cross-tenant enumeration');

  const viewerAssignable = await rest(viewer, 'rpc/satark_list_assignable_members', {
    method: 'POST',
    body: JSON.stringify({ p_tenant_id: env.SATARK_TEST_VIEWER_TENANT_ID }),
  });
  assert.ok([401, 403].includes(viewerAssignable.status),
    'viewer must not enumerate assignable tenant members');

  async function pendingApproval(session, tenantId) {
    const response = await rest(session, 'satark_approvals?' + new URLSearchParams({
      select: 'id,tenant_id,case_id,action_key,payload_sha256,status,requested_by',
      tenant_id: 'eq.' + tenantId,
      status: 'eq.pending',
      limit: '1',
    }));
    assert.equal(response.status, 200, 'tenant owner should be able to read their pending approval fixture');
    const rows = await response.json();
    assert.ok(rows.length > 0, 'each owner tenant must have a pending simulation approval fixture');
    return rows[0];
  }

  const [approvalA, approvalB] = await Promise.all([
    pendingApproval(a, env.SATARK_TEST_TENANT_A_ID),
    pendingApproval(b, env.SATARK_TEST_TENANT_B_ID),
  ]);

  const authorizationArgs = approval => ({
    p_approval_id: approval.id,
    p_tenant_id: approval.tenant_id,
    p_case_id: approval.case_id,
    p_action_key: approval.action_key,
    p_payload_sha256: approval.payload_sha256,
  });
  const pendingAuthorization = await rest(a, 'rpc/satark_authorize_response_action', {
    method: 'POST',
    body: JSON.stringify(authorizationArgs(approvalA)),
  });
  assert.equal(pendingAuthorization.status, 200, 'member authorization check should return a boolean for a pending approval');
  assert.equal(await pendingAuthorization.json(), false, 'pending approvals must never authorize a response action');

  const foreignAuthorization = await rest(a, 'rpc/satark_authorize_response_action', {
    method: 'POST',
    body: JSON.stringify(authorizationArgs(approvalB)),
  });
  assert.equal(foreignAuthorization.status, 200, 'authorization check should fail closed for a foreign approval');
  assert.equal(await foreignAuthorization.json(), false, 'a tenant member must not authorize another tenant approval');

  const consumePending = await rest(a, 'rpc/satark_consume_response_approval', {
    method: 'POST',
    body: JSON.stringify(authorizationArgs(approvalA)),
  });
  assert.ok(
    [401, 403, 404].includes(consumePending.status),
    'authenticated clients must not invoke approval consumption until a trusted executor exists; got HTTP ' + consumePending.status,
  );

  const selfDecision = await rest(a, 'rpc/satark_decide_approval', {
    method: 'POST',
    body: JSON.stringify({
      p_approval_id: approvalA.id,
      p_decision: 'approved',
      p_reason: 'self-approval must be rejected by the security gate',
    }),
  });
  assert.ok([400, 403].includes(selfDecision.status), 'requester must not approve their own request');

  const foreignDecision = await rest(a, 'rpc/satark_decide_approval', {
    method: 'POST',
    body: JSON.stringify({
      p_approval_id: approvalB.id,
      p_decision: 'approved',
      p_reason: 'cross-tenant approval must be rejected',
    }),
  });
  assert.ok([400, 403].includes(foreignDecision.status), 'tenant member must not decide another tenant approval');

  const verifyPending = await rest(a, 'satark_approvals?' + new URLSearchParams({
    select: 'id,status',
    id: 'eq.' + approvalA.id,
    tenant_id: 'eq.' + env.SATARK_TEST_TENANT_A_ID,
  }));
  assert.equal(verifyPending.status, 200, 'owner should be able to verify rejected approval transitions');
  const unchangedApproval = await verifyPending.json();
  assert.equal(unchangedApproval.length, 1, 'rejected approval transitions must not delete the request');
  assert.equal(unchangedApproval[0].status, 'pending', 'rejected approval transitions must leave the request pending');
});

test('tenant creation RPC rejects anonymous calls and invalid tenant names', {
  skip: configured ? false : 'Set up a dedicated non-admin Supabase test user; missing: ' + missing.join(', '),
}, async () => {
  const owner = await login(env.SATARK_TEST_USER_A_EMAIL, env.SATARK_TEST_USER_A_PASSWORD);

  const anonymous = await fetch(base + '/rest/v1/rpc/satark_create_tenant', {
    method: 'POST',
    headers: { apikey: apiKey, 'Content-Type': 'application/json' },
    body: JSON.stringify({ tenant_name: '   ' }),
    cache: 'no-store',
    signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
  });
  assert.ok(
    [401, 403, 404].includes(anonymous.status),
    'tenant creation RPC must not be callable without an authenticated user; got HTTP ' + anonymous.status,
  );

  const invalidName = await rest(owner, 'rpc/satark_create_tenant', {
    method: 'POST',
    body: JSON.stringify({ tenant_name: '   ' }),
  });
  assert.equal(invalidName.status, 400, 'authenticated tenant creation should reject a blank tenant name');
});

// The ordinary unit-test suite may skip live integration checks when no test
// project is configured. The dedicated integration command must never report a
// green run with these checks skipped: missing fixtures are a configuration error.
const requireIntegration = env.SATARK_REQUIRE_INTEGRATION === '1'
  || env.npm_lifecycle_event === 'test:integration';
if (requireIntegration && (missing.length || viewerMissing.length)) {
  throw new Error(
    'Tenant integration tests require dedicated, non-admin test fixtures. Missing: '
    + [...new Set([...missing, ...viewerMissing])].join(', '),
  );
}

test('viewer role cannot create or update cases', {
  skip: viewerMissing.length ? 'Set up a dedicated viewer test account; missing: ' + viewerMissing.join(', ') : false,
}, async () => {
  const viewer = await login(env.SATARK_TEST_VIEWER_EMAIL, env.SATARK_TEST_VIEWER_PASSWORD);
  const tenantId = env.SATARK_TEST_VIEWER_TENANT_ID;
  const create = await rest(viewer, 'satark_cases', {
    method: 'POST',
    headers: { Prefer: 'return=representation' },
    body: JSON.stringify({
      tenant_id: tenantId,
      title: 'Viewer permission integration probe',
      status: 'open',
      severity: 'unknown',
      created_by: viewer.userId,
      metadata: { test_probe: true },
    }),
  });
  assert.ok(
    [401, 403].includes(create.status),
    `viewer create must be rejected by authorization/RLS, got HTTP ${create.status}`,
  );

  const listQuery = new URLSearchParams({ select: 'id', tenant_id: 'eq.' + tenantId, limit: '1' });
  const listed = await rest(viewer, 'satark_cases?' + listQuery);
  assert.equal(listed.status, 200, 'viewer should be allowed to list cases in their own tenant');
  const rows = await listed.json();
  assert.ok(rows.length > 0, 'seed the dedicated viewer tenant with at least one disposable test case so update authorization is exercised');

  const viewerCaseId = rows[0].id;
  const hash = 'c'.repeat(64);
  const viewerWrites = [
    ['satark_case_notes', {
      tenant_id: tenantId, case_id: viewerCaseId,
      body: 'Viewer write probe must not persist', created_by: viewer.userId,
    }],
    ['satark_audit_events', {
      tenant_id: tenantId, case_id: viewerCaseId, actor_id: viewer.userId,
      action: 'viewer.audit_write_probe', details: { test_probe: true },
      previous_hash: null, event_hash: hash,
    }],
    ['satark_approvals', {
      tenant_id: tenantId, case_id: viewerCaseId,
      action_key: 'simulation.viewer_write_probe',
      action_payload: { mode: 'simulation', test_probe: true },
      payload_sha256: hash, status: 'pending', requested_by: viewer.userId,
    }],
    ['satark_investigation_jobs', {
      tenant_id: tenantId, case_id: viewerCaseId,
      requested_by: viewer.userId,
      idempotency_key: 'viewer-write-probe-' + viewer.userId,
      status: 'queued', attempts: 0, result: null, result_sha256: null,
      started_at: null, finished_at: null,
    }],
  ];
  for (const [table, payload] of viewerWrites) {
    const response = await rest(viewer, table, {
      method: 'POST',
      headers: { Prefer: 'return=representation' },
      body: JSON.stringify(payload),
    });
    assert.ok(
      [401, 403].includes(response.status),
      'viewer writes to ' + table + ' must be denied by authorization/RLS; got HTTP ' + response.status,
    );
  }

  const update = await rest(viewer, 'satark_cases?id=eq.' + rows[0].id + '&tenant_id=eq.' + tenantId, {
    method: 'PATCH',
    headers: { Prefer: 'return=representation' },
    body: JSON.stringify({ status: 'resolved' }),
  });
  if ([401, 403].includes(update.status)) {
    // Explicit database denial is acceptable.
  } else {
    assert.equal(update.status, 200, `viewer update must be denied by authorization/RLS, got HTTP ${update.status}`);
    assert.deepEqual(await update.json(), [], 'viewer update must not return a changed row');
  }

  const verifyViewerCase = await rest(viewer, 'satark_cases?' + new URLSearchParams({
    select: 'id,status',
    id: 'eq.' + viewerCaseId,
    tenant_id: 'eq.' + tenantId,
  }));
  assert.equal(verifyViewerCase.status, 200, 'viewer should be able to verify their own fixture');
  const unchangedViewerRows = await verifyViewerCase.json();
  assert.equal(unchangedViewerRows.length, 1, 'viewer write probe must not delete the case');
  assert.equal(unchangedViewerRows[0].status, 'open', 'viewer write probe must not change the case status');
});

test('cross-tenant mutations are denied across all tenant-scoped resources', {
  skip: configured ? false : 'Set up two non-admin Supabase test users and separate tenant IDs; missing: ' + missing.join(', '),
}, async () => {
  assert.notEqual(env.SATARK_TEST_TENANT_A_ID, env.SATARK_TEST_TENANT_B_ID, 'test tenants must be distinct');
  const [a, b] = await Promise.all([
    login(env.SATARK_TEST_USER_A_EMAIL, env.SATARK_TEST_USER_A_PASSWORD),
    login(env.SATARK_TEST_USER_B_EMAIL, env.SATARK_TEST_USER_B_PASSWORD),
  ]);
  assert.notEqual(a.userId, b.userId, 'test users must be distinct');

  for (const [session, foreignTenant, foreignSession] of [
    [a, env.SATARK_TEST_TENANT_B_ID, b],
    [b, env.SATARK_TEST_TENANT_A_ID, a],
  ]) {
    const ownCases = await rest(foreignSession, 'satark_cases?' + new URLSearchParams({
      select: 'id,tenant_id,title', tenant_id: 'eq.' + foreignTenant, order: 'created_at.asc', limit: '1',
    }));
    assert.equal(ownCases.status, 200, 'fixture owner must be able to query its tenant cases');
    const foreignCases = await ownCases.json();
    assert.ok(foreignCases.length > 0, 'each tenant fixture must contain one disposable case');
    const foreignCaseId = foreignCases[0].id;
    const originalTitle = foreignCases[0].title;

    const update = await rest(session, 'satark_cases?' + new URLSearchParams({
      id: 'eq.' + foreignCaseId, tenant_id: 'eq.' + foreignTenant,
    }), {
      method: 'PATCH',
      headers: { Prefer: 'return=representation' },
      body: JSON.stringify({ title: 'Cross-tenant mutation must not persist' }),
    });
    if ([401, 403].includes(update.status)) {
      // Explicit database denial is acceptable.
    } else {
      assert.equal(update.status, 200, 'RLS-filtered cross-tenant update should return an empty success');
      assert.deepEqual(await update.json(), [], 'cross-tenant update must not return a row');
    }

    const remove = await rest(session, 'satark_cases?' + new URLSearchParams({
      id: 'eq.' + foreignCaseId, tenant_id: 'eq.' + foreignTenant,
    }), { method: 'DELETE', headers: { Prefer: 'return=representation' } });
    if ([401, 403].includes(remove.status)) {
      // Explicit database denial is acceptable.
    } else {
      assert.ok([200, 204].includes(remove.status), 'RLS-filtered cross-tenant delete must not return a server error');
      if (remove.status === 200) {
        assert.deepEqual(await remove.json(), [], 'cross-tenant delete must not return a deleted row');
      }
    }

    // Do not treat a filtered/no-content response as proof by itself: verify
    // through the tenant owner that the original row still exists unchanged.
    const verifyOriginal = await rest(foreignSession, 'satark_cases?' + new URLSearchParams({
      select: 'id,title', id: 'eq.' + foreignCaseId, tenant_id: 'eq.' + foreignTenant,
    }));
    assert.equal(verifyOriginal.status, 200, 'tenant owner must be able to verify the fixture');
    const originalRows = await verifyOriginal.json();
    assert.equal(originalRows.length, 1, 'cross-tenant delete must not remove the other tenant case');
    assert.equal(originalRows[0].title, originalTitle, 'cross-tenant update must not change the other tenant case');

    // Verify all other persisted tenant resources remain unchanged as well.
    // These child tables intentionally do not grant authenticated UPDATE/DELETE.
    const immutableResourceProbes = [
      ['satark_evidence', 'summary'],
      ['satark_findings', 'title'],
      ['satark_reports', 'title'],
      ['satark_audit_events', 'action'],
      ['satark_case_notes', 'body'],
      ['satark_approvals', 'decision_reason'],
      ['satark_investigation_jobs', 'error_code'],
    ];
    for (const [table, column] of immutableResourceProbes) {
      const ownerRead = await rest(foreignSession, table + '?' + new URLSearchParams({
        select: 'id,' + column,
        tenant_id: 'eq.' + foreignTenant,
        limit: '1',
      }));
      assert.equal(ownerRead.status, 200, table + ' fixture owner should be able to read its resource');
      const ownerRows = await ownerRead.json();
      assert.ok(ownerRows.length > 0, table + ' fixture must contain a row so immutability is not vacuous');
      const rowId = ownerRows[0].id;
      const originalValue = ownerRows[0][column];

      const resourceUpdate = await rest(session, table + '?' + new URLSearchParams({
        id: 'eq.' + rowId,
        tenant_id: 'eq.' + foreignTenant,
      }), {
        method: 'PATCH',
        headers: { Prefer: 'return=representation' },
        body: JSON.stringify({ [column]: 'Cross-tenant mutation must not persist' }),
      });
      assert.ok(
        [401, 403].includes(resourceUpdate.status),
        table + ' cross-tenant update must be denied; got HTTP ' + resourceUpdate.status,
      );

      const resourceDelete = await rest(session, table + '?' + new URLSearchParams({
        id: 'eq.' + rowId,
        tenant_id: 'eq.' + foreignTenant,
      }), { method: 'DELETE', headers: { Prefer: 'return=representation' } });
      assert.ok(
        [401, 403].includes(resourceDelete.status),
        table + ' cross-tenant delete must be denied; got HTTP ' + resourceDelete.status,
      );

      const verifyResource = await rest(foreignSession, table + '?' + new URLSearchParams({
        select: 'id,' + column,
        id: 'eq.' + rowId,
        tenant_id: 'eq.' + foreignTenant,
      }));
      assert.equal(verifyResource.status, 200, table + ' fixture owner should verify its record is unchanged');
      const verifiedRows = await verifyResource.json();
      assert.equal(verifiedRows.length, 1, table + ' cross-tenant delete must not remove the other tenant record');
      assert.equal(verifiedRows[0][column], originalValue, table + ' cross-tenant update must not change the other tenant record');
    }

    const hash = 'a'.repeat(64);
    const attempts = [
      ['satark_evidence', {
        tenant_id: foreignTenant, case_id: foreignCaseId,
        source_label: 'integration probe', event_kind: 'file',
        observed_at: new Date().toISOString(), summary: 'Synthetic cross-tenant access probe',
        source_sha256: hash, record_sha256: 'b'.repeat(64),
        metadata: { test_probe: true }, created_by: session.userId,
      }],
      ['satark_findings', {
        tenant_id: foreignTenant, case_id: foreignCaseId,
        finding_key: 'cross-tenant-probe-' + session.userId,
        title: 'Synthetic cross-tenant probe', severity: 'unknown',
        detail: 'This record must not be persisted.', evidence_refs: [],
        source: 'integration test', confidence: null, created_by: session.userId,
      }],
      ['satark_reports', {
        tenant_id: foreignTenant, case_id: foreignCaseId,
        title: 'Synthetic cross-tenant probe', report_version: 1,
        snapshot: { test_probe: true }, snapshot_sha256: hash,
        created_by: session.userId,
      }],
      ['satark_case_notes', {
        tenant_id: foreignTenant, case_id: foreignCaseId,
        body: 'Synthetic cross-tenant note probe', created_by: session.userId,
      }],
      ['satark_audit_events', {
        tenant_id: foreignTenant, case_id: foreignCaseId, actor_id: session.userId,
        action: 'integration.cross_tenant_audit_write_probe',
        details: { test_probe: true }, previous_hash: null, event_hash: hash,
      }],
      ['satark_approvals', {
        tenant_id: foreignTenant, case_id: foreignCaseId,
        action_key: 'simulation.cross_tenant_probe',
        action_payload: { mode: 'simulation', test_probe: true },
        payload_sha256: hash, status: 'pending', requested_by: session.userId,
      }],
      ['satark_investigation_jobs', {
        tenant_id: foreignTenant, case_id: foreignCaseId,
        requested_by: session.userId,
        idempotency_key: 'cross-tenant-probe-' + session.userId,
        status: 'queued', attempts: 0, result: null, result_sha256: null,
        started_at: null, finished_at: null,
      }],
    ];

    for (const [table, payload] of attempts) {
      const response = await rest(session, table, {
        method: 'POST',
        headers: { Prefer: 'return=representation' },
        body: JSON.stringify(payload),
      });
      assert.ok(
        [401, 403].includes(response.status),
        table + ' cross-tenant insert must be denied by database authorization/RLS; got HTTP ' + response.status,
      );
    }
  }
});

