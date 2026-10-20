# SATARK / FIRSTLIGHT security and production implementation plan

Last reviewed: 2026-10-19
Branch: `feat/agentic-investigation-workflow`

This is an execution ledger, not a declaration of production readiness. A checkbox is complete only when the implementation exists, automated tests cover it, and environment-dependent behavior is verified in the target deployment. Do not use real or confidential incident data until the relevant gates pass.

## Current verified baseline

- [x] Shared Python FIRSTLIGHT investigation engine and versioned result schema exist.
- [x] Next.js can proxy to the shared Python API when configured.
- [x] API validates bounded structured evidence, timezone-aware timestamps, unique IDs, and submitted hashes.
- [x] Web auth helpers use Supabase Auth, refresh a near-expiry session, sign out, and clear local session state after refresh/401 failure.
- [x] Case API verifies the bearer token with Supabase Auth and sends user-scoped requests to Supabase; database RLS remains the actual tenant boundary.
- [x] A two-user tenant RLS integration test exists and fails fast in required integration mode when fixtures are absent.
- [x] Python API/engine tests, Node tests, type checks and workflow definitions exist.
- [x] Documentation explicitly limits current use to synthetic/non-sensitive data and simulated response actions.

## Release-blocking gaps

- [ ] Verify every private page and every API route is server-side authenticated; browser-only route hiding is not authorization.
- [ ] Verify the exact deployed Supabase schema, migrations, RLS policies, grants, and membership-role constraints. Never infer these from frontend code.
- [ ] Provision two distinct non-admin test users in distinct tenants and a viewer account; run the required integration suite without skipped tests.
- [x] Add password recovery request UI, generic anti-enumeration confirmation, and password reset completion page; email redirect configuration and live provider verification remain pending.
- [ ] Move auth persistence to a reviewed secure session design if server-rendered private pages need cookie-backed sessions; current localStorage tokens are exposed to same-origin JavaScript.
- [ ] Complete durable case CRUD, assignment, status transition validation, optimistic concurrency, and pagination.
- [ ] Persist evidence, findings, notes, reports, and audit events with tenant-scoped RLS and verified retention/deletion behavior.
- [ ] Add append-only database audit controls, actor/correlation metadata, and denied-action audit tests.
- [ ] Validate real file signatures/content, archive expansion limits, parser time budgets, and upload provenance; add SSRF/path traversal abuse tests.
- [ ] Make investigations reproducible with rule/schema versions, input hashes, deterministic fixture sets, and explicit uncertainty.
- [ ] Add monitoring, request IDs, distributed rate limits, concurrency and provider cost ceilings, tested backup/restore, and rollback drills.
- [ ] Test complete authenticated end-to-end workflows, mobile/accessibility behavior, deployed smoke tests, and high/critical dependency/code-scanning findings.
- [ ] Keep real provider response actions disabled until provider scopes, target binding, dry-run, server-side approval recheck, idempotency, audit persistence, and recovery tests pass.
- [ ] Verify deployed commit SHA, canonical URL, environment variables, migrations, health checks, and synthetic acceptance scenario.

## Execution order

### Phase 0 — Branch and CI hygiene
1. Reconcile the feature branch with the current base branch without force-pushing over teammates' work.
2. Resolve all conflict markers, run formatting/type/unit/build checks, and confirm the pull request's mergeability status.
3. Ensure required security checks fail clearly instead of silently skipping missing fixtures.

### Phase 1 — Authentication and tenant authorization
1. [In progress] Password recovery request and completion screens/helpers have been added; configure and verify the allowed redirect URL in Supabase and test real email delivery.
2. Inspect and version the actual database schema/migrations.
3. Audit every private page/API route and every database table for RLS and grants.
4. Enforce admin/analyst/viewer capabilities in database policies and server-side handlers.
5. Add password recovery, expiry/revocation tests, forged-token tests, and two-tenant integration coverage.

### Phase 2 — Durable data and accountability
1. Define canonical case/evidence/finding/report/audit schemas and migration strategy.
2. Implement transactional case lifecycle, state transitions, assignments, pagination and concurrency checks.
3. Persist provenance, evidence hashes, findings, investigation versions and append-only audit events.
4. Test refresh/restart survival, retention/deletion, backup/restore and cross-tenant denial.

### Phase 3 — Safe ingestion and reproducible analysis
1. Define versioned JSON/CSV/log schemas and explicit format support.
2. Bound bytes, rows, field sizes, nesting, parser time and archive expansion.
3. Preserve original bytes, source metadata, uploader, timestamps and hashes; never silently overwrite evidence.
4. Maintain labeled synthetic fixtures and measure false positives/negatives; version rules and record uncertainty.

### Phase 4 — Operational controls and UI
1. Add structured redacted logs, request/correlation IDs, metrics, alerts, rate/concurrency/cost controls.
2. Connect every screen to authorized persisted APIs; remove or clearly label mock data.
3. Complete keyboard/mobile/accessibility and end-to-end acceptance tests.
4. Exercise deployment rollback and disaster recovery.

### Phase 5 — Optional response integrations
1. Select one provider and document exact permissions, data handling and rollback.
2. Keep synthetic data and simulation-only execution until provider privacy/security approval.
3. Require target-bound dry-run and authorized approval revalidation immediately before execution.
4. Record idempotency key, approver, target, request/result, failure state and recovery guidance.

## Acceptance commands

Run from a clean checkout after installing dependencies:

```bash
python -m pip install -r requirements.txt -r firstlight-api-requirements.txt
python -m unittest discover -s tests -v
python -m pytest -q tests/test_firstlight_api.py tests/test_firstlight_engine.py
cd web
npm ci
npm run typecheck
npm test
npm run build
SATARK_REQUIRE_INTEGRATION=1 npm run test:integration
npm run test:browser
```

The integration suite must run against dedicated, disposable, non-admin accounts and separate tenant IDs. Do not put credentials in source control. A failure caused by missing test secrets is a release blocker, not a passing test.

## Data and action safety policy

- Use synthetic or public, non-sensitive input until identity, tenant isolation, persistence, retention, provider terms, and operational controls are verified.
- A matching SHA-256 proves equality with a supplied baseline, not that the original evidence was authentic or truthful.
- A deterministic rule match is a lead, not proof of compromise or malware.
- FIRSTLIGHT response actions remain simulation-only until the entire approval and provider execution path is independently tested.
- Never claim production readiness from CI alone; record the tested deployed commit and environment.
