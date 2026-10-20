# SATARK Track 1 — release runbook

**Purpose:** turn the current implementation into a verified, real-provider cybersecurity investigation flow without weakening authorization or inventing evidence.

**Current release state:** NO-GO until all mandatory gates below have evidence on the exact release commit. A green unit-test run, a configured URL, a hash, or an HTTP 202 response is not proof of end-to-end provider behavior.

## Required end-to-end acceptance path

1. **Prepare an isolated lab.** Use a dedicated Saathi Supabase test project, two distinct least-privilege users in different tenants, and a viewer/read-only identity. Use a Wazuh test manager/indexer with genuine, non-sensitive lab alerts. Use a disposable Microsoft Defender for Endpoint test device/tenant only if response testing is authorized.
2. **Verify authentication and tenant boundaries first.** Run the authenticated integration suite. Demonstrate own-tenant access, cross-tenant read/write denial for cases, evidence, findings, reports, audit events, notes, approvals and jobs, plus viewer write denial. Verify the RPC approval-consumption endpoint remains denied to API users until the trusted executor is implemented.
3. **Exercise real Wazuh collection.** Run the documented read-only acceptance probe with a dedicated least-privilege Wazuh account. Capture the commit SHA, UTC test window, non-sensitive source index/document identifiers, event counts, source timestamps, connector response, and result. A zero-alert response is a failed acceptance run, not a successful investigation.
4. **Exercise persistent ingestion.** Run the worker against a dedicated tenant and case. Verify original source snapshot bytes in private storage, source and normalized digests, evidence rows, unique source-document identity, and checkpoint advancement. Repeat the same window to prove idempotency; test empty pages, late events, revoked membership, connector outage, storage failure, and restart/recovery.
5. **Verify analysis provenance.** Each finding must reference evidence IDs and show its rule/model provenance, severity rationale, timestamp, and limitations. Optional model output must be labeled advisory and must not replace deterministic evidence checks.
6. **Keep response disabled until safe execution exists.** Approval consumption is intentionally revoked from public/API roles. Implement a server-only executor that binds tenant, case, evidence, actor, exact action, target, reason, expiry and single-use approval. Re-check authorization at execution time, enforce replay protection/idempotency, persist an append-only audit record, and reconcile uncertain provider outcomes. Do not re-enable consumption before these tests pass.
7. **Run a real provider response only in an authorized lab.** For Defender/Entra, verify the exact target and action, provider action ID, final provider-side state, audit entry, timeout/retry behavior and recovery. A submitted request alone is not proof that isolation or another action completed.
8. **Reconcile Supabase migrations safely.** Use the documented migration-history procedure and trusted Supabase CLI. Inspect `supabase migration list --linked` and `supabase db push --dry-run --linked` first. Compare every pending version with the live schema and migration ledger. Apply only specifically reviewed migrations; do not reset, blanket-push, or edit history to silence drift.
9. **Release and verify.** Require exact-head CI, web CI, CodeQL, clean-database migration/security tests, authenticated tenant isolation, live Wazuh acceptance, persistent worker recovery, and authorized provider-side response acceptance. Deploy only the approved SHA. Verify the deployment's commit SHA, readiness, authentication, logs, worker restart, backup/restore and rollback.

## GitHub Actions test identities

In `Settings → Secrets and variables → Actions`, configure these repository secrets with **dedicated test-only identities**. Do not use production user credentials, a service-role key, or an administrator identity for these tests.

| Secret | Value required |
|---|---|
| `SATARK_TEST_SUPABASE_URL` | HTTPS URL of the Saathi test project |
| `SATARK_TEST_SUPABASE_PUBLISHABLE_KEY` | Publishable/anon client key for that test project |
| `SATARK_TEST_USER_A_EMAIL` | Test user A email; member/owner in tenant A only |
| `SATARK_TEST_USER_A_PASSWORD` | Password for test user A |
| `SATARK_TEST_TENANT_A_ID` | Tenant A UUID |
| `SATARK_TEST_USER_B_EMAIL` | Test user B email; member/owner in tenant B only |
| `SATARK_TEST_USER_B_PASSWORD` | Password for test user B |
| `SATARK_TEST_TENANT_B_ID` | Tenant B UUID, different from tenant A |
| `SATARK_TEST_VIEWER_EMAIL` | Read-only viewer identity |
| `SATARK_TEST_VIEWER_PASSWORD` | Password for the read-only viewer |
| `SATARK_TEST_VIEWER_TENANT_ID` | Tenant UUID for that viewer |

The workflow maps the first two secrets to the integration-test process variables `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`. The credentials must belong to the same Saathi test project where the tenant fixtures exist. If identities or tenant rows are missing, create them through the approved test setup and verify their role/membership before rerunning CI. Never paste values into pull-request comments, issue descriptions, source files, or logs.

After configuring the secrets, rerun PR checks and inspect the **Supabase tenant-isolation integration** job logs. The job must execute actual authenticated requests; a skipped test, a credential preflight, or SQL-only pgTAP assertions are not a substitute.

## UI and operational truthfulness

The FIRSTLIGHT readiness panel calls `/api/capabilities` and shows configuration-only status. It intentionally does not label configured integrations as healthy, connected, or production-ready. If the endpoint is unavailable, the UI must say that status could not be verified.

The training scenario and browser-test fixtures are synthetic by design and must remain visibly labeled as training/test data. They are not telemetry, incident evidence, model output, or provider response proof. For real investigations, use authorized Wazuh telemetry or a permitted evidence artifact with source provenance. The live-response capability remains disabled until the trusted executor and lab acceptance exist.

## Evidence to attach to the release record

- Exact Git commit SHA and workflow run URLs.
- Test identity role/membership verification without passwords or tokens.
- Authenticated tenant-isolation results for every persisted resource.
- Wazuh source IDs/index, UTC window, count, source digest and preserved snapshot verification.
- Worker checkpoint, duplicate replay, outage recovery and late-event results.
- Provider action ID and independently fetched final state from the authorized lab.
- Migration list and dry-run output, reviewed migration versions, and post-migration catalog checks.
- Deployment URL, deployed SHA, health/readiness results, rollback and restore evidence.
- Explicit limitations, unresolved failures and approver identity.

## Official references

- NIST SP 800-61 Rev. 3 — incident response: https://csrc.nist.gov/pubs/sp/800/61/r3/final
- Wazuh Indexer API reference: https://documentation.wazuh.com/current/user-manual/indexer-api/reference.html
- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- Supabase database testing: https://supabase.com/docs/guides/database/testing
- Microsoft Defender for Endpoint isolate machine API: https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/isolate-machine
