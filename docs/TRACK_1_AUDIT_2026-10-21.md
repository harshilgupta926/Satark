# SATARK / FIRSTLIGHT Track 1 audit — 2026-10-21

**Repository:** `kaustubhdua/Satark`  
**Reviewed candidate:** `c34f361af92c79d4faf3b762f7d962f94f0002c6`  
**Review PR:** https://github.com/kaustubhdua/Satark/pull/217  
**Decision:** **NO-GO for a claim of full completion or live autonomous response.** The implementation and code-level checks are substantial, but real tenant isolation, real telemetry acceptance, live response, and deployment proof remain external release gates.

## Executive finding

The shortest credible path is to finish one traceable incident lifecycle—not to add more integrations. The candidate passes API, web, CodeQL, clean-database migration, Phase 0, and browser/accessibility validation. The required authenticated tenant-isolation job still fails closed because its credentials are not configured. Production smoke's contract job passes, but its live smoke job is skipped. Neither is proof of production operation.

## Verified in this audit

### GitHub candidate checks

| Check | Exact candidate result | Interpretation |
|---|---|---|
| FIRSTLIGHT API CI | PASS — 137 tests and 20 subtests reported by CI | API/worker regression suite and image-build steps passed |
| Web CI | PASS | Web build and tests passed |
| CodeQL | PASS | Static analysis passed for this candidate |
| Isolated Supabase migration validation | PASS | Clean-database migrations/tests passed; does not reconcile remote history |
| Phase 0 inventory | PASS | Inventory gate passed |
| Browser/accessibility smoke | PASS | CI browser smoke passed |
| Tenant-isolation integration | FAIL / BLOCKED | Required environment credentials are empty; authenticated requests did not run |
| Production smoke | Contract PASS; live smoke SKIPPED | No production deployment or provider-backed workflow proven |

The CI tenant-isolation preflight logs explicitly show empty values for the test project URL/key and dedicated test identities. Do not change this gate to warn-only and do not treat SQL pgTAP as a substitute for authenticated cross-tenant testing.

### Saathi test project — project ref `ibvgxgvcqcfnoyrlwywa`

Used only as the SATARK test project, as requested. A read-only live catalog/ACL inspection confirmed:

- SATARK tables for cases, evidence, findings, reports, memberships, tenants, notes, approvals, audit events, investigation jobs, and Wazuh ingestion checkpoints all have RLS enabled.
- RLS is forced on `satark_approvals`, `satark_case_notes`, `satark_investigation_jobs`, and `satark_ingestion_checkpoints`.
- Both public and private approval-consumption functions are not executable by `anon`, `authenticated`, or `service_role`; the public wrapper is SECURITY INVOKER and the private implementation has a fixed empty search path.
- Test fixture counts were zero for cases, evidence, approvals, investigation jobs, and ingestion checkpoints at inspection time.
- The Supabase security advisor's only finding on this project was informational: ingestion checkpoints have RLS enabled and no policies. This is intentional fail-closed behavior for a service-only worker table; service-role access is separately constrained.

These are database-catalog/ACL checks. They are not authenticated tenant-isolation proof.

### Nirdhoom production project — project ref `igqgtlmnwssjaoxkkzbm`

Production was inspected read-only; no production migration or data mutation was made during this audit.

- SATARK tables have RLS enabled; the same four sensitive tables above have FORCE RLS.
- Approval-consumption RPC execution remains revoked for API roles and `service_role`.
- SATARK case count was zero at inspection time.
- The security advisor reports the same informational service-only checkpoint finding. It also reports unrelated SECURITY DEFINER RPC warnings in Nirdhoom's own application and disabled leaked-password protection. Those Nirdhoom findings were not changed because they are outside SATARK scope and could alter the farmer-facing product.

### Migration-history reconciliation

The clean-database migration workflow passes, but the repository and live Nirdhoom migration ledger are not a one-to-one match. Nirdhoom's ledger records the original SATARK changes under versions such as `20261013184054` through `20261013195438`, while the current repository contains corresponding files with versions `202610130001` through `202610160001`. The ledger also contains later SATARK hardening versions and the repository has older versions `20261020042000`, `20261020050000`, `20261020051000`, and `20261020052000` that do not appear under those exact versions in the remote ledger.

This is drift, not permission to reset or rewrite the remote ledger. The later reconciliation files are intentionally no-op files for already-recorded versions. Before any push, run the trusted CLI's linked migration list and dry-run, compare every pending SQL file to the actual schema/function ACLs, and apply only a reviewed, explicitly safe set. Do not run a blanket push from this branch into the shared production project.

## Implementation present

- Bounded FIRSTLIGHT investigation API and Wazuh Indexer adapter.
- Persistent Wazuh worker and investigation-job worker code paths.
- Evidence snapshot digests, source identifiers, tenant-bound storage and checkpoint/deduplication logic.
- Deterministic investigation engine; local Ollama is optional and advisory.
- Lazy loading for below-the-fold UI sections, selected FIRSTLIGHT tabs, QR fallback decoder, and image/video previews.
- Response executor foundation with tenant/case-bound approval records, immutable target/action/payload binding, expiry, separate requester/approver, idempotency key, one-time execution claim, unknown-outcome handling, restart recovery, append-only hash-chained audit, and local unit tests.
- Local Docker Compose and local model runtime support.

## Critical gaps still open

1. **Authenticated tenant isolation:** configure the 11 dedicated test-only Actions secrets from `docs/TRACK_1_RELEASE_RUNBOOK.md`, then prove tenant A/B isolation, viewer restrictions, and revoked membership behavior against Saathi.
2. **Real Wazuh acceptance:** run the adapter and persistent worker against genuine alerts in an authorized lab. Verify source IDs, raw snapshots, hashes, checkpoints, duplicate replay, late events, empty windows, invalid credentials, and worker restart.
3. **Trusted executor integration:** the local ledger is not wired into the authenticated web approval route/Supabase lifecycle. Do not enable provider response or restore approval-consumption permissions until identity, role, case/tenant binding, transaction semantics, and audit integration are reviewed.
4. **Provider-side response:** no authorized Defender/Entra lab action and independent final-state verification has been demonstrated. No provider credentials or disposable target were available in this audit.
5. **Fully offline product:** local Ollama is supported, but `docker-compose.local.yml` still configures the web and investigation worker to use Supabase. The current full web application is not offline-independent. A local database/auth/storage adapter or self-hosted Supabase stack and a no-internet acceptance test remain required.
6. **Durability/recovery proof:** live case creation → evidence ingestion → investigation → reload after API/worker restart → export/restore has not been proven end-to-end.
7. **Deployment:** no linked SATARK production deployment was verified. Production smoke's live job is skipped. Deploy only an approved exact SHA and then verify the deployed SHA, auth, readiness, worker, migrations, logs, backup/restore and rollback.
8. **Performance evidence:** lazy loading is implemented and browser smoke passes, but there is no measured before/after Lighthouse or bundle-size result. Do not claim a numeric performance improvement.

## Release decision

**NO-GO for "fully complete", "fully autonomous", or "production-ready".**  
**GO for continued controlled integration/testing on PR #217.**

Keep provider response disabled. Keep production Supabase unchanged until migration dry-run/history reconciliation is complete. The next release gate is: configure test identities, pass authenticated tenant isolation, run live Wazuh acceptance, wire and test the trusted executor in a disposable response lab, then deploy and verify the exact reviewed commit.

## Reproducible evidence pointers

- PR: https://github.com/kaustubhdua/Satark/pull/217
- Runbook: https://github.com/kaustubhdua/Satark/blob/ops/track1-readiness-audit/docs/TRACK_1_RELEASE_RUNBOOK.md
- Response executor: https://github.com/kaustubhdua/Satark/blob/ops/track1-readiness-audit/docs/FIRSTLIGHT_RESPONSE_EXECUTOR.md
- Wazuh adapter: https://github.com/kaustubhdua/Satark/blob/ops/track1-readiness-audit/docs/FIRSTLIGHT_WAZUH_API.md
- Completion plan: https://github.com/kaustubhdua/Satark/blob/ops/track1-readiness-audit/docs/TRACK_1_COMPLETION_PLAN.md
