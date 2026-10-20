# Self-hosted and offline-capable runtime

SATARK's deterministic analysis, evidence handling, and local Ollama inference do not require a hosted AI API. The Next.js web application can now be configured to talk to a self-hosted Supabase endpoint as well. This is an endpoint-configuration capability, **not proof that a complete air-gapped installation has passed acceptance**.

## Local Supabase development

1. Install Docker and the Supabase CLI, then run `supabase start` from the repository.
2. Read the local API URL and publishable/anon key from `supabase status -o env`. Keep service-role and database secrets out of browser-visible variables.
3. For the browser bundle, set `NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321` and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` to the local publishable/anon key before building the web image.
4. For server-side route handlers running inside Docker, set `SUPABASE_URL=http://host.docker.internal:54321` and `SUPABASE_PUBLISHABLE_KEY` to the same local publishable/anon key. The browser and server URLs differ because `127.0.0.1` inside a container refers to that container.
5. Set `SATARK_ALLOW_INSECURE_LOCAL_SUPABASE=true` only for this local HTTP development setup. The server-side guard only permits this flag for the explicit local host allowlist. Do not set it on a public deployment.
6. Apply the reviewed repository migrations to the local instance, then run the web, API, RLS, and browser tests.

## Self-hosted HTTPS

For a self-hosted Supabase stack behind a trusted HTTPS domain, set `SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_URL` to that domain and set `SATARK_SUPABASE_ALLOW_SELF_HOSTED=true` in the server environment. Use a valid TLS certificate. Do not put service-role keys in `NEXT_PUBLIC_*` variables.

## Offline acceptance checklist

- Download/pin all container images, model weights, and package artifacts before disconnecting from the internet.
- Confirm login, tenant-scoped case/evidence/approval reads, writes, and storage work against local Supabase.
- Stop Ollama and confirm deterministic detection/investigation still returns a truthful result without model output.
- Disable external network access and exercise a genuine local test event through detection, evidence storage, investigation, and an approved local-only response.
- Restart the web app, API, database, and worker; confirm cases, checkpoints, and audit events persist.
- Capture the exact commit, test output, image/model versions, and failures.

A hosted Microsoft Defender/Entra response cannot run in a fully disconnected environment. The product must report that connector as unavailable rather than claim a remote action succeeded. A successful local setup or green unit suite alone is not an air-gap acceptance result.
