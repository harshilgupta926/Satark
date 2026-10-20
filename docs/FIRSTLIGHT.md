# FIRSTLIGHT inside SATARK

FIRSTLIGHT is SATARK's primary incident-response workspace. Existing SATARK text, URL, image, QR, PDF and video analysis remain available as secondary threat-analysis tools.

## Current prototype scope

- Repeatable synthetic account-compromise incident.
- Evidence records sealed with SHA-256 over canonical JSON.
- Deterministic evidence verification and an interactive tamper challenge.
- Evidence-linked detection/correlation/verification workflow.
- Transparent deterministic evidence triage ranking based on volatility, relevance, timestamp recency and integrity status.
- Timeline reconstruction with explicit evidence gaps and uncertainty.
- Human approval/rejection for simulated response proposals.
- Shared FastAPI investigation service backed by the canonical Python engine, with web API proxy, request bounds, optional bearer-token enforcement and tamper verification.
- Hash-chained in-session audit events and JSON report export.

## Safety boundaries

This prototype does not collect live endpoint telemetry, execute shell commands, isolate hosts, revoke real sessions, block network traffic, or claim forensic certification. All response actions are simulated. The sample incident and indicators are fictional.

A hash mismatch indicates that a record differs from the stored baseline; it does not identify who changed it or prove that the original record was truthful. The in-session hash chain is tamper-evident only while its trusted baseline remains protected. Production use requires authenticated access, tenant isolation, durable append-only storage, independently protected/anchored manifests, reliable timestamps, retention policy, secrets management, network egress controls and operational review.

## Shared investigation API

The Next.js findings panel can call the same Python engine used by Streamlit through `POST /api/v1/cases/investigate`. The API checks the submitted digest against the canonical event record before investigation; mismatched records remain visible in the timeline but cannot support findings.

Run the API locally from the repository root:

```bash
python -m pip install -r firstlight-api-requirements.txt
uvicorn firstlight_api:app --host 127.0.0.1 --port 8788
```

For a separately running Next.js dev server, set `FIRSTLIGHT_API_URL=http://127.0.0.1:8788`. The local Docker Compose stack wires the web container to `http://firstlight-api:8788` automatically. For a remotely reachable API, use HTTPS and set the same random bearer token of at least 32 characters in `FIRSTLIGHT_API_TOKEN` for both the API and web server. The API reports `production_ready=false`; authentication alone is not a production security review.

## Local validation

Run:

```bash
python -m unittest tests.test_firstlight_engine -v
```

The main Streamlit app exposes the workspace through its sidebar. JSON/CSV import and the deterministic rule checks do not require an AI API key. Imported data remains in Streamlit session state and is not durable case storage. The artifact hash identifies the exact uploaded bytes but does not authenticate the source, prove truthfulness, or establish forensic chain of custody. Detection rules are intentionally small and can miss activity or produce false positives. Evidence priority scores are explainable triage heuristics, not calibrated risk probabilities; mismatched evidence is escalated for review and must not be treated as trustworthy.

See [FIRSTLIGHT implementation status](FIRSTLIGHT_IMPLEMENTATION_STATUS.md) for the current partial and unimplemented capabilities.
