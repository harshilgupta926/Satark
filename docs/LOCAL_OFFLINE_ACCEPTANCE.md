# SATARK local/offline deployment and acceptance

**Goal:** run the core UI, authentication/database/storage, investigation API and local model on infrastructure controlled by the operator. This removes hosted AI dependencies and can remove hosted Supabase from the core path. It does not make remote Wazuh or Defender services reachable without a network path.

## Scope and limits

The local stack uses the repository's Supabase CLI configuration and `docker-compose.local.yml`. Supabase local provides a local Postgres/Auth/REST/Storage stack; Ollama provides local inference. The model is advisory: deterministic detection, evidence hashing, and rule-based checks must still work if Ollama is unavailable.

This document is a runbook, not proof that offline acceptance has already passed. No offline test has been claimed until it is run on the target machine with external networking disabled.

## One-time preparation (internet available)

Prerequisites: Docker Engine/Desktop with Compose v2, Supabase CLI, Git, Python 3, and enough disk/RAM for local database containers and the chosen model.

1. From the repository root, start the **local** Supabase stack:

   ```bash
   supabase start
   supabase status -o env
   ```

2. Apply the repository migrations to the local database only:

   ```bash
   supabase db reset
   ```

   This command resets the local development database. Never run it against a linked/production project.

3. Copy the local CLI's API URL, anon/publishable key, and service-role key into an untracked local environment file. Keep service-role keys out of `NEXT_PUBLIC_*` variables and out of Git. The Docker containers need to reach the host's local Supabase API through `host.docker.internal`; the browser should use loopback. Example mapping (replace key values with those printed by the local CLI):

   ```dotenv
   NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
   SUPABASE_URL=http://host.docker.internal:54321
   NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=<local-anon-or-publishable-key>
   SUPABASE_PUBLISHABLE_KEY=<local-anon-or-publishable-key>
   SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>
   FIRSTLIGHT_API_TOKEN=<random-local-secret>
   FIRSTLIGHT_WAZUH_SYNC_TOKEN=<different-random-local-secret>
   SATARK_OLLAMA_MODEL=qwen2.5:3b
   ```

   Generate local-only tokens with `python3 -c 'import secrets; print(secrets.token_urlsafe(32))'`. Use a different value for each token. Do not reuse any production credential.

4. Build and start the local Ollama service, then download the model while internet is available:

   ```bash
   docker compose --env-file .env.local -f docker-compose.local.yml up -d ollama
   docker compose --env-file .env.local -f docker-compose.local.yml exec ollama ollama pull qwen2.5:3b
   ```

5. Start the local application services:

   ```bash
   docker compose --env-file .env.local -f docker-compose.local.yml up --build -d web firstlight-api streamlit
   ```

   Start the persistent worker profiles only after their local database credentials and test tenant/case fixtures have been configured. Do not enable the Wazuh worker with empty/default tenant identifiers.

## Offline acceptance

After all images, dependencies, migrations, and model weights are cached:

1. Disable external network connectivity at the host/network level. Keep Docker's local bridge and loopback access available.
2. Run the local service probe:

   ```bash
   SATARK_OLLAMA_MODEL=qwen2.5:3b bash scripts/check-local-offline-services.sh
   ```

3. In the browser at `http://127.0.0.1:3000`, sign in with a dedicated local test account; create a case; attach a permitted test evidence artifact; run deterministic investigation; view the evidence digest and audit record.
4. Restart the web/API services and local Supabase containers. Verify that the case, evidence, and audit record persist and that the same account can read them after restart.
5. Stop the Ollama container and rerun deterministic analysis. The application must show AI enrichment as unavailable, not fail the core detection/investigation path.
6. Restore external networking only after recording the outputs and commit SHA.

The service probe checks local HTTP endpoints and confirms the configured Ollama model is present. It does not itself prove that the host is offline, that authentication is correctly isolated, or that database data survives restart. Those are separate acceptance steps.

## Security guardrails

- Do not use the Nirdhoom production project for local/offline tests. Use the local Supabase stack or Saathi test project.
- Never use production service-role keys in browser-visible environment variables.
- Do not connect response actions to local tests by default. Live actions require a separately reviewed trusted executor, an authorized test target, approval, and independent provider-side verification.
- Do not claim remote Wazuh ingestion or Defender isolation in a fully offline run. Those integrations require an explicitly permitted network path.
- Keep test identities, passwords, local secrets, model weights, logs, and evidence artifacts out of Git.

## Acceptance record template

Record these fields after an actual run:

- Commit SHA:
- OS / Docker / Supabase CLI versions:
- Network disabled at host level: yes/no (evidence):
- Local Supabase Auth health:
- Web home and health route:
- Ollama model tag present:
- Sign-in and role used:
- Case/evidence IDs (non-sensitive):
- Deterministic analysis result and source digest:
- Persistence after restart:
- Deterministic mode with Ollama stopped:
- Failures / limitations:
- Operator and UTC timestamp:

Do not mark offline acceptance passed if any required field is missing or the run used a hosted Supabase URL.
