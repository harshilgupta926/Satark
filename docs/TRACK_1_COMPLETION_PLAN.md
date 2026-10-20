# SATARK Track 1 — completion plan and evidence matrix

**Audit date:** 2026-10-21  
**Repository:** `kaustubhdua/Satark`  
**Active implementation review:** [PR #217](https://github.com/kaustubhdua/Satark/pull/217)  
**Decision:** Release remains **NO-GO** until the externally gated tests in this document are completed. This document distinguishes code present from behavior actually verified.

## 1. Acceptance target

Track 1 asks for an agentic cybersecurity system that detects, analyzes, investigates, and responds to threats. SATARK should be accepted only when the same traceable incident can be followed through:

1. Real telemetry collection from a configured source.
2. Bounded normalization with original source identity, timestamps, and preserved source evidence.
3. Deterministic detections and an explainable investigation, with optional model output clearly marked advisory.
4. Tenant-scoped, durable case/evidence/finding/job storage and recoverable checkpoints.
5. A response recommendation bound to the case, evidence, actor, target, and reason.
6. A durable approval/denial/expiry/consumption lifecycle, including replay prevention and authorization re-checks at execution time.
7. A provider-side response request, followed by a provider-side status/result check and a durable audit record.
8. Recovery, retry, idempotency, rollback/undo where the provider supports it, and a truthful final report.

A hash calculated after collection proves that the stored snapshot has not changed relative to that calculated digest; it does not independently prove upstream authenticity or immutability. Likewise, a provider API accepting a response request is not proof that the action completed successfully.

## 2. Implementation and evidence matrix

| Capability | Current evidence | Required acceptance proof | Status |
|---|---|---|---|
| Wazuh alert collection | Configured Indexer adapter; bounded agent allowlist; source index/document ID and SHA-256 snapshot | Run against an authorized Wazuh lab with genuine alerts; verify TLS/auth, source IDs, time bounds, paging, and empty-window behavior | **Implemented; live test blocked** |
| Read-only investigation API | `POST /api/v1/integrations/wazuh/investigate`; token and tenant binding; deterministic investigation; no persistence/action | Live call using a dedicated read-only account; verify returned source IDs against the Indexer | **Implemented; live test blocked** |
| Persistent Wazuh worker | Service-role-only worker; tenant/case/actor validation; source snapshot storage; duplicate-safe evidence writes; checkpoint and retry logic. Saathi test schema now has forced-RLS checkpoints and no API-role grants; the unique Wazuh source-document index is verified. | Real authorized test case; verify raw source objects, evidence rows, duplicate replay, late events, empty poll, and failure recovery | **Schema verified; live ingestion blocked** |
| Deterministic investigation | Shared engine and regression tests; optional bounded model specialists | Documented end-to-end case; inspect each finding's evidence references, severity rationale, false-positive behavior, model timeout/malformed output | **Partial** |
| Durable case/evidence/job persistence | Supabase tables, storage policies, job/audit migrations exist in repository | Real tenant fixture; create/import/investigate/reload/export; restart service and verify persistence | **Not end-to-end verified** |
| Tenant isolation and RLS | Policies and pgTAP coverage exist; current CI preflight lacks dedicated test-account secrets | Run the real integration job with separate least-privilege identities for two tenants and a read-only viewer; demonstrate cross-tenant read/write denial | **Blocked; release gate** |
| Approval lifecycle | Live public wrappers are SECURITY INVOKER; approval consumption is revoked from API/service roles until a trusted executor exists. Saathi pgTAP RPC hardening suite passed 30/30 assertions. New `firstlight_response_executor.py` provides a SQLite-backed, four-eyes, expiring, one-time approval ledger with hash-chained append-only audit, restart recovery and explicit verification state; 10 local unit tests pass. | Wire ledger into authenticated UI/server path or equivalent transactional store; connect provider adapters; independently verify provider-side outcome; run authenticated tenant and live lab tests | **Local executor foundation implemented; production integration not complete** |
| Microsoft Defender/Entra response | Guarded provider adapters exist separately | Use disposable authorized lab device/account; verify exact target, provider action ID/status, completion, audit record, retry/idempotency, and recovery | **Not live verified** |
| Audit integrity | Session-local hash chain and persisted audit structures exist in code | Verify append-only semantics and tamper detection; document trusted clock, key/anchor, retention, and export validation | **Partial** |
| Deployment and operations | Docker images and runtime imports pass dedicated CI | Deploy approved commit; verify health/readiness, auth, logs, secrets, worker restart, migrations, backups, restore, and rollback | **Blocked / unverified** |

## Supabase verification completed in this audit (2026-10-21)

- Nirdhoom Supabase received the missing private approval-RPC implementation and a follow-up ACL migration. Live catalog checks confirm the public wrappers are SECURITY INVOKER and the consumption RPC is not executable by API roles or service_role.
- Saathi Supabase was used as the test environment. The checkpoint schema was added there with FORCE RLS and no API-role privileges; the Wazuh source-document uniqueness index was verified.
- `supabase/tests/satark_rpc_hardening.test.sql` passed **30/30 pgTAP assertions** against Saathi. The test transaction rolled back; a post-test count confirmed zero persistent SATARK tenants, cases, evidence, audit events, approvals, investigation jobs, and checkpoints.
- Full evidence and migration version details: [SUPABASE_ACCEPTANCE_2026-10-21.md](SUPABASE_ACCEPTANCE_2026-10-21.md).
- This does not clear the GitHub tenant-isolation job, because its separate least-privilege test-account preflight still needs protected CI secrets. It also does not prove live Wazuh ingestion or provider-side response.

## Response executor foundation added (2026-10-21)

- `firstlight_response_executor.py` implements a durable local approval ledger with an allowlist for two response actions, tenant/case binding, requester/approver separation, expiry, idempotency keys, a single-use execution claim, explicit `submitted` versus `verified` states, fail-closed handling of uncertain outcomes, restart recovery, and an append-only SHA-256 audit chain.
- `tests/test_firstlight_response_executor.py` covers nine unit scenarios. These are mocked/local guardrail tests, not live-provider evidence.
- `docs/FIRSTLIGHT_RESPONSE_EXECUTOR.md` documents the integration boundary and acceptance requirements.
- **Important:** this foundation is not yet wired into the current simulation-only web approval route or Supabase approval RPCs. Existing consumption restrictions must remain in place. Do not enable live response based on this foundation alone.

## 3. Prioritized work list

### P0 — must pass before claiming a functional real-world agent

- [ ] Complete CI and CodeQL checks on the exact proposed merge commit, including the new response-executor tests.
- [ ] Provide dedicated, least-privilege Supabase test-account secrets in the repository's protected CI environment; do not weaken or skip the tenant-isolation job to make CI green.
- [ ] Run the real two-tenant RLS tests and inspect results for cases, evidence, notes, investigation jobs, approvals, and storage objects.
- [ ] Reconcile Supabase migration history using the repository's guarded repair procedure. Inspect the linked project and the exact dry-run first; never use an unreviewed broad `supabase db push`.
- [ ] Apply only the specifically reviewed pending migrations, then verify policy/function permissions, foreign keys, indexes, and migration history.
- [ ] Run the persistent worker once against a dedicated Wazuh test tenant and a real case. Confirm original source snapshot bytes, evidence row, source and normalized digests, and checkpoint advancement.
- [ ] Repeat the same window and verify idempotency; test an empty window, a late-arriving event, a connector failure, a storage failure, and a revoked membership.
- [ ] Complete an authorized Defender/Entra lab run only after durable approval and execution audit are connected. Verify provider-side outcome; do not act on production devices/accounts as a test.
- [ ] Deploy only after all checks pass; verify the exact deployed SHA and execute post-deploy smoke and recovery tests.

### P1 — needed for a credible submission and maintainable operation

- [ ] Produce one reproducible end-to-end acceptance report with commit SHA, environment class, test command, test result, real source IDs redacted as necessary, and provider action IDs where authorized.
- [ ] Ensure every finding has evidence references, rule/model provenance, timestamps, confidence/limitations, and a deterministic explanation.
- [ ] Expand the current FIRSTLIGHT rule metadata into a reviewed detection catalogue: map each supported rule to the relevant current MITRE ATT&CK technique/detection strategy and cite its source; treat mappings as triage context, never proof.
- [ ] Define a versioned normalized event contract and assess OCSF compatibility before adding more providers; preserve source-native fields and provenance so normalization does not discard forensic detail.
- [ ] If adding portable third-party detections, validate imported Sigma rules against the official Sigma specification and a test corpus; do not claim Sigma compatibility until parsing, field mapping, and expected-match tests exist.
- [ ] Add explicit state-machine tests for investigation job retries, cancellation, deadline exhaustion, duplicate jobs, and worker crashes.
- [ ] Verify response execution is impossible without an unexpired approval bound to the exact tenant, case, target, action, and reason.
- [ ] Ensure API readiness is degraded when required authentication, persistence, or provider configuration is absent; never advertise production readiness from a process-only health check.
- [ ] Test secret rotation, rate limits, request-size limits, timeouts, log redaction, backup/restore, and retention/deletion policy.
- [ ] Verify UI and API behavior against real authenticated roles, including denied actions and expired sessions.

### P2 — quality improvements after safety gates

- [ ] Add reproducible local developer setup and a no-network unit-test path.
- [ ] Add operational metrics for ingestion lag, failures, queue age, investigation duration, and response verification.
- [ ] Add a threat-model document covering service-role credential compromise, prompt injection in evidence, tenant boundary failures, alert flooding, and malicious/oversized source records.
- [ ] Keep synthetic fixtures only for explicitly labeled unit tests and demos; never count them as live integration evidence.

## 4. Safe execution sequence

1. **Local/CI:** unit tests, static checks, dependency checks, CodeQL, image builds, browser/accessibility smoke.
2. **Isolated database:** migration dry-run, tenant fixture creation using dedicated test identities, RLS and storage policy tests.
3. **Wazuh lab:** read-only connectivity, genuine event retrieval, persistent worker ingestion, idempotency and failure recovery.
4. **Response lab:** durable approval and one explicitly authorized disposable target; confirm provider outcome and recovery.
5. **Staging deployment:** least-privilege secrets, deployed SHA verification, authenticated smoke tests, restart/recovery.
6. **Release review:** close every P0 item with attached evidence. Any skipped or externally blocked item remains an explicit blocker.

## 5. Environment and safety boundaries

- Never commit Wazuh, Supabase, Microsoft, or deployment credentials.
- Never create fake production tenant/case/user records to satisfy acceptance checks.
- Never execute isolation or session revocation against real user devices/accounts as a test.
- Keep model output advisory. Deterministic findings and original evidence must remain available if the model is disabled or unavailable.
- Do not claim that a hash alone proves source authenticity, that an HTTP success proves response completion, or that a skipped test passed.
- The connected/shared Supabase project is not a disposable test database. Use the specifically approved isolated test environment for fixtures and destructive tests.
- Any live action requires separate authorization from the environment owner.

## 6. Research references

- NIST SP 800-61 Rev. 3, incident-response recommendations: https://csrc.nist.gov/pubs/sp/800/61/r3/final
- Wazuh Indexer API reference and authentication: https://documentation.wazuh.com/current/user-manual/indexer-api/reference.html
- Microsoft Defender for Endpoint isolate-machine API, prerequisites and permissions: https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/isolate-machine
- Supabase database/RLS testing overview and pgTAP: https://supabase.com/docs/guides/local-development/testing/overview
- MITRE ATT&CK detection strategies: https://attack.mitre.org/detectionstrategies/
- Official Sigma rule specification: https://github.com/SigmaHQ/sigma-specification
- Open Cybersecurity Schema Framework (OCSF) schema: https://github.com/ocsf/ocsf-schema

## 7. Audit truth statement

This plan is not a declaration that all capabilities are complete. The latest observed FIRSTLIGHT API CI run passed the shared API/engine tests, all three Docker image builds, and runtime imports. CodeQL also passed on the observed candidate SHA. The general CI run still had a Supabase tenant-isolation preflight failure because dedicated test credentials were missing; the real RLS tests were skipped. No live Wazuh acceptance run, authorized Microsoft response run, or production deployment verification is established by those CI results.
