# SATARK Supabase migration-history repair

Last verified: 2026-10-21 UTC (live SATARK-scoped migrations applied; migration-ledger reconciliation still requires a trusted CLI dry-run)

## Scope and evidence

Official CLI reference: [Supabase migration repair](https://supabase.com/docs/reference/cli/supabase-migration-repair).

The shared Supabase project `nihdhoom` (`igqgtlmnwssjaoxkkzbm`) hosts SATARK alongside Nirdhoom and Saathi. Do not reset it or run a broad `supabase db push` to resolve this mismatch.

A read-only migration-list check on 2026-10-20 found these relevant entries:

- `20261018114039` — `isolate_satark_membership_helper`: recorded.
- `20261018114205` — `harden_satark_audit_verification_rpc`: recorded in the live ledger and now included in the repository migration history by the RPC-hardening PR. The migration keeps the public audit-verification function as a `SECURITY INVOKER` wrapper.
- `20261018114247` — `harden_satark_tenant_creation_rpc`: recorded in the live ledger and now included in the repository migration history by the RPC-hardening PR. The migration keeps the public tenant-creation function as a `SECURITY INVOKER` wrapper.
- `202610200004` — `satark_storage_policy_membership_hardening`: not recorded.
- `20261020042000` — `satark_storage_policy_private_helper_rebind`: not recorded (repository file is a no-op; canonical policy was applied under `20261020044018`).
- `20261020042449` — `satark_evidence_storage_dual_path_policy`: recorded.
- `20261020044018` — `satark_storage_policy_private_helper_rebind`: recorded.
- `20261020050000` — `satark_foreign_key_support_indexes`: source version not recorded in the live ledger. The five SATARK support indexes were applied and verified under live version `20261020184535`; a no-op reconciliation file now represents that recorded version.
- `20261020051000` — `satark_rebind_membership_policies`: source version not recorded in the live ledger. The live policy rebind was applied and verified under version `20261020184538`; approval, case-note, and investigation-job policies now call `satark_private.has_membership`. A no-op reconciliation file represents the recorded live version.
- `20261020052000` — `satark_private_approval_rpc_implementations`: source version not recorded in the live ledger. Its effects were applied under live version `20261020184208`, and a no-op reconciliation file represents that recorded version. The source migration was also updated so a clean migration run does not re-grant approval consumption. The public approval/assignment wrappers are now `SECURITY INVOKER`; approval consumption is revoked from API roles and service_role under live version `20261020184213`.

The live private helper, ACLs, final storage policies, approval policy rebind, and five support indexes have been verified by live catalog queries. The live ledger records the index/policy/RPC changes under versions `20261020184535`, `20261020184538`, and `20261020184208`/`20261020184213`; the repository contains reconciliation files for those recorded versions. The repository migration `202610200004` remains available for clean database resets; do not change it to a no-op. The repository migration `20261020042000` is already a no-op because the canonical policy was applied under `20261020044018`. The duplicate version `20261020043000` was removed from the repository in PR #164 and is not part of the repair command.

The live SATARK tenant, membership, case, evidence, finding, report, audit-event, ingestion-checkpoint, investigation-job, case-note and approval tables currently contain zero rows. Do not add fake production rows to test the application.

## Security-advisor status (read-only check, 2026-10-20)

The public audit-verification, tenant-creation, and approval/assignment wrappers are `SECURITY INVOKER` in the live shared database. Approval consumption is intentionally disabled until a trusted response executor exists. Their private implementations are kept in `satark_private` with fixed empty `search_path` values:

- `20261018114205_harden_satark_audit_verification_rpc`: the public `satark_verify_audit_chain(uuid)` function is a `SECURITY INVOKER` wrapper; the private implementation uses an empty fixed `search_path` and checks membership in the requested tenant.
- `20261018114247_harden_satark_tenant_creation_rpc`: the public `satark_create_tenant(text)` function is a `SECURITY INVOKER` wrapper; the private implementation derives the owner from `auth.uid()`, validates the name, creates the owner membership, and appends the audit event atomically.

Read-only privilege checks confirmed that authenticated callers can execute the public wrappers, anonymous callers cannot, and both private implementations use an empty fixed `search_path`. The latest shared-project security-advisor response did not include these two wrappers. The clean-database suite now includes `supabase/tests/satark_rpc_hardening.test.sql`, which verifies invoker-only public wrappers, anonymous denial, authenticated tenant creation, owner-membership creation, valid audit-chain verification, blank-name rejection, and cross-tenant audit-verification denial in a rollback transaction.

This does **not** mean the shared multi-application project's entire security-advisor output is clean. The latest read-only shared-project check still reports security-definer findings for unrelated Nirdhoom application functions and the intentional no-policy notice for the worker-private checkpoint table. No SATARK approval/assignable-member functions appeared in the current security-definer advisor findings. The remaining warnings belong to other applications sharing the database and require separate behavior-preserving review; do not blanket-revoke them or modify Nirdhoom/Saathi functions as part of this SATARK repair. The live PostgREST suite contains guard checks for owner-only assignable-member listing, cross-tenant denial, pending approvals not authorizing responses, and self/cross-tenant decisions being rejected. Approval consumption is now deliberately denied to API roles and service_role until a trusted executor exists. The isolated database regression suite in `supabase/tests/satark_approvals.test.sql` exercises requester/responder/viewer/foreign-tenant cases, successful approval decisions, exact-payload authorization, denied consumption, expiry, and audit-chain integrity inside a rollback transaction. The `satark_ingestion_checkpoints` RLS informational finding was also reviewed: the table has RLS enabled/forced and no grants to `anon` or `authenticated`, so it remains server-only.

## Required operator procedure

The SATARK-scoped DDL has already been applied to Nirdhoom through the approved database connection, but the repository migration ledger has not been repaired through the Supabase CLI. The source migration versions `20261020050000`, `20261020051000`, and `20261020052000` are not the versions recorded for their equivalent live changes; the live versions are `20261020184535`, `20261020184538`, `20261020184208`, and `20261020184213`. Other older reconciliation files also exist. Therefore the earlier expected-three-pending-migrations instruction is stale and must not be followed blindly.

From a trusted checkout, first confirm that the linked project is `igqgtlmnwssjaoxkkzbm`:

```sh
supabase migration list --linked
supabase db push --dry-run --linked
```

Review the complete output against the live migration ledger and the source/reconciliation files. Do not execute a repair or push if any listed version or SQL is unexpected. The intended schema effects for the support indexes, membership-policy rebind, and private approval RPC implementation have already been applied and verified; the remaining operator task is to reconcile version history safely, not to blindly reapply broad DDL.

Use `supabase migration repair --help` from the installed CLI version before preparing a repair command. Mark a source version as applied only after confirming its effect is already present in the live database and that the later recorded version is its equivalent. Do not directly edit `supabase_migrations.schema_migrations` with SQL. After any history repair, rerun both commands above and run the isolated migration/security workflow. Keep the project linked to Nirdhoom; use Saathi only for test-specific work.

## Read-only policy and ACL verification

```sql
select version, name
from supabase_migrations.schema_migrations
where version in ('20261018114039', '202610200004', '20261020042000', '20261020042449', '20261020044018', '20261020050000', '20261020051000', '20261020052000')
order by version;

select policyname, cmd, roles, qual, with_check
from pg_policies
where schemaname = 'storage'
  and tablename = 'objects'
  and policyname in ('satark_evidence_object_insert', 'satark_evidence_object_read')
order by policyname;

select
  has_function_privilege('authenticated', 'satark_private.has_membership(uuid,text[])', 'EXECUTE') as authenticated_private_helper,
  has_function_privilege('authenticated', 'public.satark_has_membership(uuid,text[])', 'EXECUTE') as authenticated_public_wrapper,
  has_function_privilege('anon', 'public.satark_has_membership(uuid,text[])', 'EXECUTE') as anon_public_wrapper,
  has_function_privilege('authenticated', 'public.satark_reject_audit_mutation()', 'EXECUTE') as authenticated_audit_trigger_rpc;
```

Expected privilege values are `true, false, false, false`. The read policy must allow `viewer` only for generic evidence objects; raw `wazuh/<sha256>.json` source snapshots require owner/responder/analyst membership. Both policies must use `satark_private.has_membership` and verify the owning case/tenant.

## Boundary

The connected Supabase tools were used to apply and verify only SATARK-scoped schema changes in Nirdhoom and test-schema changes in Saathi. They do not expose the Supabase CLI migration-repair command. The live migration ledger still differs from repository source versions, so this document intentionally does not prescribe a blind repair command or `db push`. Finish the ledger reconciliation from a trusted CLI after checking the exact linked project and dry-run. Do not change unrelated Nirdhoom application functions or insert persistent SATARK fixtures into Nirdhoom.
