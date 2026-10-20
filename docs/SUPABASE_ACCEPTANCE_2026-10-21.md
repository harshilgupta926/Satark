# SATARK Supabase hardening and acceptance record

**Date:** 2026-10-21  
**Scope:** SATARK/FIRSTLIGHT schema and approval RPCs only  
**Production-like project:** Nirdhoom Supabase  
**Test project:** Saathi Supabase

## Changes applied

### Nirdhoom Supabase

Applied the private approval-RPC implementation migration and the approval-consumption ACL hardening migration. Live migration history records:

- `20261020184208 satark_private_approval_rpc_implementations`
- `20261020184213 satark_approval_consumption_acl`
- `20261020184535 satark_foreign_key_support_indexes`
- `20261020184538 satark_rebind_membership_policies`

The live catalog was re-queried after applying the changes. The support indexes on approval actors, case-note creators, assigned cases, and investigation-job requesters are present. Approval, case-note, and investigation-job membership policies now call the non-exposed `satark_private.has_membership` helper rather than the public wrapper. The four public approval/assignment wrappers (`satark_authorize_response_action`, `satark_decide_approval`, `satark_consume_response_approval`, `satark_list_assignable_members`) are `SECURITY INVOKER`. Anonymous execution is denied. The consumption RPC and its private implementation are not executable by `anon`, `authenticated`, or `service_role`.

The source migration `20261020052000_satark_private_approval_rpc_implementations.sql` was updated so a fresh migration run does not re-grant approval consumption. A no-op reconciliation file records the live version `20261020184208`; the ACL migration is recorded in source at `20261020184213_satark_approval_consumption_acl.sql`.

### Saathi Supabase test project

Applied test-only schema and RPC migrations:

- `20261020184030 satark_test_wazuh_ingestion_checkpoints`
- `20261020184103 satark_test_private_approval_rpc_implementations`
- `20261020184120 satark_test_approval_consumption_acl`
- `20261020184150 satark_test_enable_pgtap`

The checkpoint schema has forced RLS, no policies, no table privileges for `anon` or `authenticated`, and the expected `service_role` privileges. This is intentional: the checkpoint is a worker-private cursor, not a client-facing resource. The unique `satark_evidence_wazuh_document_once` index was verified in the database catalog.

## Test execution and results

Ran `supabase/tests/satark_rpc_hardening.test.sql` against the Saathi Supabase test project after updating its ACL assertions. Result: **30/30 pgTAP assertions passed**.

The transaction creates temporary test users and two tenant fixtures to exercise tenant creation and cross-tenant audit-verification denial. The test ends with rollback. A post-test query confirmed that persistent counts remained zero for SATARK tenants, cases, evidence, audit events, approvals, investigation jobs, and ingestion checkpoints.

Additional live catalog checks verified:

- Public RPC wrappers are invoker-security functions.
- Approval, case-note and investigation-job policies reference `satark_private.has_membership`.
- Five SATARK foreign-key support indexes are present in Nirdhoom.
- The approval-consumption RPC is not executable by API roles or service_role.
- Wazuh checkpoints force RLS and intentionally have no client-facing policies.
- The Wazuh evidence source-document uniqueness index exists.

### Additional live Saathi isolation test

Executed `supabase/tests/satark_security.test.sql` against the Saathi test project through the connected SQL runner. The run reached the final assertion, which returned `ok 50 - viewers cannot read raw Wazuh source snapshots`; no SQL error was returned. Immediately afterwards, read-only checks found zero fixture tenants, cases, evidence, findings, or storage objects, and confirmed the temporary `satark-evidence` bucket was absent again. This verifies that the test transaction rolled back its fixture data and bucket.

The SQL connector surfaces only the final result row for a multi-statement script, not the complete per-assertion TAP transcript. Therefore the complete assertion-by-assertion record remains the isolated GitHub CI run below; it reports all database test files successful (113 total tests).

### Security-advisor snapshot

- Nirdhoom: SATARK's worker-private checkpoint table is reported as RLS-enabled with no policy; this is intentional alongside FORCE RLS and no API-role table privileges. The advisor also reports nine authenticated SECURITY DEFINER functions belonging to Nirdhoom's other application workflows and a leaked-password-protection warning. Those unrelated functions and auth settings were not changed during this SATARK-only repair.
- Saathi: the same intentional worker-private checkpoint notice is present; no additional security findings were returned in the latest advisor query.

## Important limitations

These are database/schema tests, not a live provider acceptance run.

- No Wazuh Indexer endpoint was contacted in this database test.
- No real Wazuh alert was ingested.
- No Microsoft Defender device isolation or Entra session revocation was executed.
- The GitHub CI tenant-isolation job still requires dedicated test-account secrets. The clean-database workflow passed all four SQL test files (113 tests total), including `satark_rpc_hardening.test.sql` and `satark_security.test.sql`; see [workflow run 39479567883](https://github.com/kaustubhdua/Satark/actions/runs/39479567883).
- The Supabase security advisor reports an `rls_enabled_no_policy` informational finding for `satark_ingestion_checkpoints`; the no-policy state is deliberate and combined with forced RLS and zero API-role grants. Do not add a permissive policy just to silence this advisory.
- Nirdhoom has unrelated security-definer advisor findings for non-SATARK functions. They were not modified because they belong to the Nirdhoom application and are outside this change's scope.

## Reproduction

In an isolated Supabase environment with the SATARK migrations applied and pgTAP available:

```sh
supabase test db
```

The specific RPC hardening test is `supabase/tests/satark_rpc_hardening.test.sql`. Use Saathi for test-only work; keep Nirdhoom's application data and non-SATARK schema out of fixture setup.

## Decision

**Database approval-RPC hardening and the Saathi schema/ACL test pass.** This is a meaningful completed sub-gate, not a release approval. Real Wazuh ingestion, provider-side response acceptance, the dedicated CI tenant-isolation job, and production deployment verification remain separate release gates.
