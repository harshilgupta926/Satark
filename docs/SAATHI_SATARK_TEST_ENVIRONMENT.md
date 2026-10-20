# Saathi Supabase project as the SATARK test environment

## Operator-approved scope

On 2026-10-20, the operator approved reusing the existing Supabase project named **Saathi** (project ref `ibvgxgvcqcfnoyrlwywa`) as SATARK's disposable integration-test environment, with no new paid Supabase project or branch.

This is a scoped authorization to use the existing project for SATARK tests. It is **not** authorization to drop/reset the whole project or modify Saathi-owned tables, Auth configuration, Edge Functions, secrets, or application data.

## Read-only baseline captured before test setup

- Project status: `ACTIVE_HEALTHY`.
- Region: `ap-northeast-2`.
- The project contains Saathi-owned public tables (`households`, `household_members`, `consents`, `conversations`, `tasks`, `scheme_catalog`, `scheme_applications`, `audit_logs`).
- SATARK tables are also present under `public`, including tenants, memberships, cases, evidence, audit events, findings, reports, approvals, investigation jobs, and case notes.
- The table-list API reported zero rows for the listed Saathi and SATARK application tables at the time of inspection. This does not establish that Auth users, storage objects, logs, or other project resources are empty.
- The migration ledger contains `saathi_initial_schema` and numerous `satark_test_*` migrations. These version names do not match the normal SATARK repository migration versions exactly; do not assume that applying the repository migration set is safe or necessary.
- A read-only security-advisor query reported four exposed authenticated `SECURITY DEFINER` SATARK RPCs: `satark_authorize_response_action`, `satark_consume_response_approval`, `satark_decide_approval`, and `satark_list_assignable_members`.

## Safety rules

1. Never run `supabase db reset`, `supabase db push` without a reviewed dry-run, or broad `DROP SCHEMA` / `TRUNCATE` operations against this project.
2. Never alter or delete Saathi-owned tables, functions, policies, storage buckets/objects, Auth users, Edge Functions, or secrets as part of SATARK work.
3. Scope any test fixtures and cleanup strictly to disposable SATARK records and dedicated SATARK test identities. Use the application's supported provisioning flow or a reviewed SATARK-only fixture script.
4. Use distinct ordinary Auth users for tenant A, tenant B, and the viewer. Do not use service-role credentials in the integration suite.
5. Before applying any DDL, compare the live migration ledger with the exact repository migration files and inspect a dry-run. Stop on any unexpected migration, duplicate version, non-SATARK change, or ambiguous schema drift.
6. Do not mark tenant isolation passed until the real PostgREST tests run and succeed—not skipped—against this exact project and exact commit.
7. Do not enable live containment/response actions. SATARK response integrations must remain simulation-only until their independent approval and provider tests pass.
8. Keep credentials in GitHub Actions secrets; never commit them or paste passwords/service-role keys into chat, issues, logs, or docs.

## Remaining operator actions

### A. Confirm project-specific configuration

In Supabase Dashboard, open project ref `ibvgxgvcqcfnoyrlwywa` and verify the project name/ref before doing anything else. Confirm that no Saathi development/demo workflow is actively using the project while SATARK fixtures are created and removed. Keep the Saathi-owned schema and resources intact.

### B. Create dedicated test identities

Create three confirmed, ordinary Auth users used only for SATARK tests:
- Tenant A owner
- Tenant B owner
- Viewer

Use the reviewed SATARK tenant/membership provisioning path to create distinct disposable tenants and at least one disposable case for each. Do not grant admin/service-role privileges to these accounts. Record the three tenant UUIDs locally for configuring GitHub secrets.

### C. Configure GitHub Actions secrets

Repository: `kaustubhdua/Satark` → **Settings → Secrets and variables → Actions**.

Set these exact repository secrets, using the test project's values only:

- `SATARK_TEST_SUPABASE_URL`
- `SATARK_TEST_SUPABASE_PUBLISHABLE_KEY`
- `SATARK_TEST_USER_A_EMAIL`
- `SATARK_TEST_USER_A_PASSWORD`
- `SATARK_TEST_TENANT_A_ID`
- `SATARK_TEST_USER_B_EMAIL`
- `SATARK_TEST_USER_B_PASSWORD`
- `SATARK_TEST_TENANT_B_ID`
- `SATARK_TEST_VIEWER_EMAIL`
- `SATARK_TEST_VIEWER_PASSWORD`
- `SATARK_TEST_VIEWER_TENANT_ID`

Use a publishable/anon key, never a service-role key. Do not send any secret values in chat.

### D. Reconcile migrations before DDL

The live ledger currently contains Saathi plus SATARK test-prefixed migrations, while the SATARK repository includes versions `20261020050000`, `20261020051000`, and `20261020052000` for support indexes, membership-policy rebinding, and private approval RPC implementations. First inspect the exact live definitions, policies, grants, and migration history for those capabilities. Do not replay these migrations merely because the version strings differ. Apply only a reviewed, idempotent SATARK-only repair after a dry-run proves the exact effects.

### E. Execute and record the integration gate

Run CI for the intended commit and verify the `Supabase tenant-isolation integration` job completes successfully with no skipped test. It must cover cross-tenant reads/writes, same-tenant access, viewer restrictions, approval RPC protections, and cleanup/restoration of disposable fixtures. Record the exact commit SHA and workflow run URL in the release evidence.

## Current status

- Existing project selected; no paid resources created.
- Read-only project/table/migration/advisor inspection performed.
- No schema changes, fixture writes, migration repairs, project resets, or secret changes performed.
- Tenant-isolation integration is still blocked until test users, tenant fixtures, and GitHub Actions secrets are configured and the migration state is reconciled.
