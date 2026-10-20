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

## Response contract and limitations

A non-empty response reports `mode: "live_read_only_investigation"`, `persisted: false`, source evidence IDs/digests, deterministic findings, and explicit limitations. The endpoint does not persist a case, maintain a durable ingestion cursor, schedule polling, or execute containment. It is an operator-triggered read-only path; the separate Wazuh worker and persistent case/job workflow remain distinct.

The source digest is calculated over the source JSON received from the Indexer. The investigation digest is computed after retrieval. Neither is a Wazuh signature and neither proves upstream authenticity, truthfulness, or independently immutable chain of custody. Findings are triage leads, not verdicts. Live acceptance requires a real authorized Wazuh test environment, source document IDs, and an end-to-end result trace.

## Official references

- Wazuh Indexer API: https://documentation.wazuh.com/current/user-manual/indexer-api/index.html
- Wazuh Indexer API reference: https://documentation.wazuh.com/current/user-manual/indexer-api/reference.html
- Wazuh role-based access control: https://documentation.wazuh.com/current/user-manual/api/rbac/index.html
