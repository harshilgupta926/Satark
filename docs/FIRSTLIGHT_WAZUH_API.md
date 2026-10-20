# FIRSTLIGHT Wazuh investigation API

## Endpoint

The FastAPI service exposes an authenticated, read-only live query-and-investigate endpoint:

`POST /api/v1/integrations/wazuh/investigate?tenant_id=<configured-tenant-uuid>&limit=100&since=<ISO-8601>`

Send `Authorization: Bearer <FIRSTLIGHT_WAZUH_SYNC_TOKEN>`. The page size is capped at 100 for this investigation endpoint, even though the underlying connector can fetch a larger page. The configured tenant UUID must exactly match `FIRSTLIGHT_WAZUH_TENANT_ID`; cross-tenant requests are rejected.

The endpoint calls the server-configured Wazuh Indexer connector, builds a stable case identifier from the fetched alert IDs, computes a SHA-256 digest for each normalized event, and runs the canonical deterministic FIRSTLIGHT investigation engine. Optional local Ollama agents are advisory only. An empty result returns zero events and no investigation; it is not a clean bill of health.

## Required environment

Configure these only in the API service's secret manager or trusted runtime environment:

- `FIRSTLIGHT_WAZUH_INDEXER_URL`: HTTPS URL of the Wazuh Indexer.
- `FIRSTLIGHT_WAZUH_INDEXER_USERNAME` and `FIRSTLIGHT_WAZUH_INDEXER_PASSWORD`: dedicated read-only Indexer account.
- `FIRSTLIGHT_WAZUH_ALLOWED_AGENT_IDS`: explicit comma-separated agent ID allowlist.
- `FIRSTLIGHT_WAZUH_SYNC_TOKEN`: random bearer token of at least 32 characters.
- `FIRSTLIGHT_WAZUH_TENANT_ID`: UUID of the one tenant bound to this connector.
- Optional: `FIRSTLIGHT_WAZUH_INDEX_PATTERN`, `FIRSTLIGHT_WAZUH_TIMEOUT_SECONDS`, `FIRSTLIGHT_WAZUH_ALLOW_HTTP` (local isolated lab only).

Use verified TLS, no redirects, short timeouts, least-privilege read-only credentials, and restricted network egress. Never expose these values to the browser, commit them, or paste them into issue logs.

## Live acceptance probe (real telemetry only)

A no-fallback acceptance script is available at `scripts/accept_firstlight_wazuh_live.py`. It calls the deployed API; it never creates alerts or switches to the fictional demo case. It exits non-zero when configuration is missing, the API is unreachable, no matching real alerts are returned, provenance is incomplete, or a normalized snapshot digest fails verification. A passing run proves only that the configured API returned Wazuh-indexed records whose normalized snapshot digests verify; it does not prove upstream source signatures, persistence, tenant RLS, or response actions.

Run it from a trusted environment with the API URL and short-lived test credentials provided through environment variables, never committed to the repository:

```sh
export FIRSTLIGHT_API_BASE_URL='https://<your-firstlight-api-host>'
export FIRSTLIGHT_WAZUH_SYNC_TOKEN='<server-issued-token-of-at-least-32-characters>'
export FIRSTLIGHT_WAZUH_TENANT_ID='<authorized-test-tenant-uuid>'
export FIRSTLIGHT_WAZUH_ACCEPTANCE_LIMIT=20
# Optional ISO-8601 lower time bound for the real alert query:
export FIRSTLIGHT_WAZUH_SINCE='2026-10-20T00:00:00Z'
python scripts/accept_firstlight_wazuh_live.py
```

Use an authorized test tenant and an existing, genuine Wazuh alert in the configured agent allowlist. If no alert matches, the script fails rather than fabricating a passing result. The API-side Wazuh Indexer credentials and agent allowlist remain configured only in the API runtime.

## Persistent worker acceptance (real writes; test case only)

The separate `scripts/accept_firstlight_worker_live.py` probe exercises the persistent worker against the configured Wazuh Indexer and Supabase project. Unlike the API probe above, **this command writes evidence and updates an ingestion checkpoint**. It requires the worker's normal trusted-runtime configuration plus three explicit opt-ins: `FIRSTLIGHT_WAZUH_ACCEPTANCE_ALLOW_WRITES=I_AUTHORIZE_WRITES_TO_THIS_TEST_CASE`, `FIRSTLIGHT_WAZUH_ACCEPTANCE_CONFIRM_TENANT_ID`, and `FIRSTLIGHT_WAZUH_ACCEPTANCE_CONFIRM_CASE_ID`. The confirmation IDs must exactly match `FIRSTLIGHT_WAZUH_TENANT_ID` and `FIRSTLIGHT_WAZUH_CASE_ID`.

Run only against a dedicated, isolated test tenant and case with an authorized actor membership. The worker verifies the case/tenant and membership before writes; after one poll the probe reads the checkpoint and evidence rows back, re-fetches up to ten preserved source objects, and checks their bytes against stored source digests. It exits non-zero if no real alert was fetched, the checkpoint is missing/mismatched, evidence is absent, or any checked source object fails digest verification. It does not create synthetic alerts and it does not execute response actions.

```sh
export FIRSTLIGHT_WAZUH_ACCEPTANCE_ALLOW_WRITES='I_AUTHORIZE_WRITES_TO_THIS_TEST_CASE'
export FIRSTLIGHT_WAZUH_ACCEPTANCE_CONFIRM_TENANT_ID="$FIRSTLIGHT_WAZUH_TENANT_ID"
export FIRSTLIGHT_WAZUH_ACCEPTANCE_CONFIRM_CASE_ID="$FIRSTLIGHT_WAZUH_CASE_ID"
PYTHONPATH=. python -m scripts.accept_firstlight_worker_live
```

The worker also needs its normal private-host configuration, including `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `FIRSTLIGHT_WAZUH_ACTOR_ID`, `FIRSTLIGHT_WAZUH_INITIAL_SINCE` for the first run when no checkpoint exists, and the Wazuh Indexer credentials/agent allowlist. Do not run this command against production or the shared Nirdhoom/Saathi project as a substitute for an isolated test environment. A passing report verifies the observed ingestion/checkpoint/object path only; it does not prove tenant RLS isolation, upstream authenticity, provider response, or production readiness.

## Response contract and limitations

A non-empty response reports `mode: "live_read_only_investigation"`, `persisted: false`, source evidence IDs/digests, deterministic findings, and explicit limitations. The endpoint does not persist a case, maintain a durable ingestion cursor, schedule polling, or execute containment. It is an operator-triggered read-only path; the separate Wazuh worker and persistent case/job workflow remain distinct.

The source digest is calculated over the source JSON received from the Indexer. The investigation digest is computed after retrieval. Neither is a Wazuh signature and neither proves upstream authenticity, truthfulness, or independently immutable chain of custody. Findings are triage leads, not verdicts. Live acceptance requires a real authorized Wazuh test environment, source document IDs, and an end-to-end result trace.

## Official references

- Wazuh Indexer API: https://documentation.wazuh.com/current/user-manual/indexer-api/index.html
- Wazuh Indexer API reference: https://documentation.wazuh.com/current/user-manual/indexer-api/reference.html
- Wazuh role-based access control: https://documentation.wazuh.com/current/user-manual/api/rbac/index.html
