# SATARK live test-project security catalog audit

**Date:** 2026-10-21 UTC  
**Environment:** Saathi Supabase test project (project ref `ibvgxgvcqcfnoyrlwywa`)  
**Purpose:** Read-only validation of the deployed SATARK database security posture. This is not a substitute for authenticated end-to-end testing.

## Results observed

| Check | Observed result | Status |
|---|---:|---|
| SATARK tables in `public` | 11 | Pass |
| SATARK tables with RLS enabled | 11/11 | Pass |
| SATARK tables missing RLS | 0 | Pass |
| Policies on SATARK tables | 19 | Pass |
| Policies referencing `satark_private.has_membership` in `USING` or `WITH CHECK` | 19/19 | Pass |
| Critical tables with FORCE ROW LEVEL SECURITY (`satark_approvals`, `satark_case_notes`, `satark_ingestion_checkpoints`, `satark_investigation_jobs`) | 4/4 | Pass |
| `satark_consume_response_approval` callable by `anon` | No | Pass |
| `satark_consume_response_approval` callable by `authenticated` | No | Pass |
| `satark_consume_response_approval` callable by `service_role` | No | Pass |
| Public membership helper callable by `authenticated` | No | Pass |
| Public membership helper callable by `service_role` | Yes | Expected service-only helper access |
| Approval consumption function is `SECURITY DEFINER` | No | Pass |

## Reproducible read-only SQL

Run in the Saathi test project SQL editor or via the Supabase SQL connector:

```sql
WITH table_checks AS (
  SELECT
    count(*) FILTER (WHERE c.relrowsecurity) AS rls_enabled,
    count(*) AS total_tables,
    count(*) FILTER (WHERE c.relforcerowsecurity) AS force_rls
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public'
    AND c.relname LIKE 'satark_%'
    AND c.relkind = 'r'
),
approval_acl AS (
  SELECT
    has_function_privilege('anon',
      'public.satark_consume_response_approval(uuid,uuid,uuid,text,text)', 'EXECUTE') AS anon_can_consume,
    has_function_privilege('authenticated',
      'public.satark_consume_response_approval(uuid,uuid,uuid,text,text)', 'EXECUTE') AS authenticated_can_consume,
    has_function_privilege('service_role',
      'public.satark_consume_response_approval(uuid,uuid,uuid,text,text)', 'EXECUTE') AS service_role_can_consume
),
membership_acl AS (
  SELECT
    has_function_privilege('authenticated',
      'public.satark_has_membership(uuid,text[])', 'EXECUTE') AS authenticated_can_call_public_membership_helper,
    has_function_privilege('service_role',
      'public.satark_has_membership(uuid,text[])', 'EXECUTE') AS service_role_can_call_public_membership_helper
),
policies AS (
  SELECT
    count(*) AS policy_count,
    count(*) FILTER (
      WHERE coalesce(qual, '') LIKE '%satark_private.has_membership%'
         OR coalesce(with_check, '') LIKE '%satark_private.has_membership%'
    ) AS membership_bound_policy_count
  FROM pg_policies
  WHERE schemaname = 'public' AND tablename LIKE 'satark_%'
)
SELECT table_checks.*, approval_acl.*, membership_acl.*, policies.*,
  (SELECT count(*) FROM pg_class c
   JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'public' AND c.relname LIKE 'satark_%'
     AND c.relkind = 'r' AND NOT c.relrowsecurity) AS tables_without_rls,
  (SELECT count(*) FROM pg_class c
   JOIN pg_namespace n ON n.oid = c.relnamespace
   WHERE n.nspname = 'public'
     AND c.relname IN ('satark_approvals', 'satark_case_notes',
                       'satark_ingestion_checkpoints', 'satark_investigation_jobs')
     AND NOT c.relforcerowsecurity) AS critical_tables_without_force_rls,
  (SELECT prosecdef FROM pg_proc
   WHERE oid = 'public.satark_consume_response_approval(uuid,uuid,uuid,text,text)'::regprocedure)
    AS consume_is_security_definer
FROM table_checks, approval_acl, membership_acl, policies;
```

## Interpretation and remaining gate

The deployed schema's RLS, membership-bound policy expressions, and approval-consumption ACLs match the expected baseline. These are catalog assertions executed with administrative SQL privileges; they do **not** prove that independent authenticated users can sign in and are blocked from reading/writing each other's records through the actual PostgREST API.

The dedicated tenant integration still needs three distinct non-admin identities (tenant A owner, tenant B owner, viewer), valid passwords, fixture tenant IDs, and the required GitHub Actions secrets. Do not enable live response actions on the basis of this catalog audit. Approval consumption remains disabled.

## Data handling

This audit performed read-only catalog queries. It did not create users, cases, alerts, evidence, storage objects, approvals, or other persistent fixtures in the test project.
