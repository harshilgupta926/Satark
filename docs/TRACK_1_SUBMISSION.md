# FIRSTLIGHT — Track 1: Agentic AI for Cybersecurity

## Submission statement

FIRSTLIGHT is an evidence-first, agent-assisted security operations system designed to turn suspicious telemetry into explainable investigations and policy-controlled response proposals. It combines deterministic detection and event correlation with bounded, optional local-LLM analysis; preserves source-linked evidence and integrity hashes; and routes response proposals through server-side authorization and human approval. The default response posture is simulation-only. The system is designed to keep deterministic detection and case workflows available when the local model is unavailable.

## Problem

Security teams receive noisy alerts spread across event sources. Analysts must determine whether events are related, reconstruct a timeline, preserve supporting evidence, communicate uncertainty, and choose a proportionate response. An AI summary alone is insufficient: conclusions must be traceable to events, permissions must be enforced outside the model, and actions must not run merely because an LLM recommends them.

## Proposed solution

FIRSTLIGHT connects these stages:

1. **Ingest** bounded JSON/CSV events or Wazuh alert exports, normalize fields and timestamps, retain source provenance, and handle malformed or repeated events.
2. **Detect** with deterministic, explainable rules and rule identifiers; keep the triggering event references.
3. **Correlate** related activity and assemble a timeline that distinguishes observed events from inferred hypotheses.
4. **Investigate** using bounded specialist analysis where configured. Structured results are validated; deterministic analysis remains the fallback.
5. **Preserve evidence** with source references, collection metadata, SHA-256 integrity checks, and investigation/audit records.
6. **Recommend and authorize** a response through explicit policy and persisted human approval. The model is not an authorization authority.
7. **Verify and report** action outcome where an adapter is configured, and export an investigation summary with timeline, evidence references, detection rationale, uncertainty, ATT&CK mapping where justified, and action history.

## What is implemented in the repository

The repository already contains substantial implementation: Streamlit and Next.js analyst interfaces; a FastAPI investigation service; event ingestion and normalization; deterministic rules and analysis; Wazuh integration and a durable worker; optional Ollama-based analysis; evidence integrity/reporting paths; Supabase-backed cases, notes, investigation jobs and approval APIs; and CI tests for Python, web validation, browser behavior, and accessibility.

This description is a source-based capability summary, not a claim that every integration has been proven end to end in a production environment. See [FIRSTLIGHT implementation status](FIRSTLIGHT_IMPLEMENTATION_STATUS.md) and [local review and release acceptance](engineering/SATARK_LOCAL_REVIEW_AND_RELEASE_ACCEPTANCE.md) for detailed evidence and blockers.

## Differentiators

- **Evidence before explanation:** important conclusions should link to concrete source events or deterministic rule matches.
- **Bounded agentic analysis:** specialist model analysis is optional, structured, resource-bounded and not allowed to execute arbitrary shell commands, SQL, URLs or code.
- **Deterministic fallback:** basic detection and case workflows should continue without an LLM.
- **Policy-separated response:** authorization is enforced by application code and database policies, not by trusting model output. High-impact actions require explicit approval.
- **Tamper-evident evidence:** SHA-256 checks can detect changes to retained bytes; hashes do not, by themselves, prove that an event source was authentic.
- **Reproducible, open-source-oriented demo:** synthetic fixtures can demonstrate the core flow without paid hosted AI APIs or live attack activity.

## Demonstration scenario

Use a synthetic brute-force-then-success authentication scenario on a disposable local dataset:

1. Load labelled benign events and repeated failed logins followed by a successful login for the same account/source within a bounded time window.
2. Show which deterministic rule matched and open the exact source events.
3. Review the correlated timeline, host/account/source context, evidence IDs, uncertainty and recommended next steps.
4. Generate a simulation-only response proposal. Show the target, rationale, risk, expiry and required approval.
5. Approve or reject the proposal in the test environment; confirm that an unapproved, expired, replayed or unauthorized request is denied.
6. Verify the evidence hashes, export the report, and deliberately alter a test copy to show that integrity verification detects tampering.

Do not run this scenario against real accounts or production systems. Do not describe the demo as live containment unless a separate, authorized lab adapter has been configured and the actual outcome verified.

## Current validation and limitations

As of the 2026-10-20 repository review:

- Python validation/regression, Next.js validation/build, browser smoke and accessibility checks passed in the reviewed CI runs.
- CodeQL passed on the reviewed base-main run.
- The tenant-isolation integration job did not complete its RLS assertions because dedicated least-privilege test-account secrets were missing. This is a blocker, not a pass.
- A production smoke run failed, and the exact current commit's production deployment has not been verified.
- The local execution environment could not resolve GitHub for a clean clone, so a fresh local installation and full local acceptance run are not claimed.
- Live migration history differs from the repository's migration history and requires a carefully scoped, reviewed reconciliation. The shared Saathi project must not be reset or broadly migrated.
- Live response execution is not authorized by this submission. The default remains simulation-only.

**Release decision: NO-GO until the tenant-isolation, migration, end-to-end scenario and exact-release deployment gates documented in the implementation status are closed with recorded evidence.** This does not mean the repository has no working implementation; it means the remaining operational proof is material and must not be misrepresented.

## Suggested judge-facing summary

FIRSTLIGHT demonstrates a practical path from security telemetry to a traceable investigation: deterministic rules detect suspicious behavior, bounded agents help explain it, evidence records preserve what the conclusion is based on, and a separate policy/approval gate controls proposed response. Its focus is not autonomous action at any cost; it is verifiable investigation with bounded autonomy and safe failure modes.

## References

- Wazuh, *Ruleset and security event analysis*: https://documentation.wazuh.com/current/user-manual/ruleset/
- Wazuh, *External API integration*: https://documentation.wazuh.com/current/user-manual/manager/integration-with-external-apis.html
- MITRE ATT&CK: https://attack.mitre.org/
- OWASP GenAI Security Project, *LLM and GenAI risks*: https://genai.owasp.org/initiatives/top-10-for-llm-and-genai/
- OWASP, *Prompt Injection*: https://owasp.org/www-project-top-10-for-large-language-model-applications/ (historical project page; consult the current GenAI LLM Top 10 for updated guidance)
