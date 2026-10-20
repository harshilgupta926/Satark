# FIRSTLIGHT live response integrations

## Scope

SATARK includes an opt-in Microsoft integration adapter for:
- Microsoft Defender for Endpoint device isolation.
- Microsoft Entra ID session revocation for a named user.

These are real tenant-side operations when configured with valid Microsoft app credentials and permissions. They are **not enabled by default**, are not wired to automatic AI decisions, and have not been live-tested against a tenant by this repository change. No credentials are included.

## Required server-side configuration

Set these only in the trusted server/host secret manager:
- `SATARK_ENABLE_LIVE_RESPONSE=true` (otherwise every action fails closed)
- `MICROSOFT_TENANT_ID`
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`

The app registration must be granted the least-privilege Microsoft API permissions and admin consent required by the target action. Defender device isolation requires the Microsoft Defender for Endpoint `Machine.Isolate` permission and an eligible device. Entra session revocation requires `User.RevokeSessions.All`. Review the current vendor documentation and your tenant's role/device-group policies before enabling.

Official references:
- https://learn.microsoft.com/en-us/defender-endpoint/api/isolate-machine
- https://learn.microsoft.com/en-us/graph/api/user-revokesigninsessions

## Human approval and safety controls

- Live response is disabled unless the explicit server-side feature flag is enabled.
- Every call requires an exact, action- and target-bound confirmation string.
- The operator must provide a target ID/UPN and a reason; no target is inferred from AI output.
- Requests have a finite timeout, redirects are rejected, provider response bodies are not surfaced to the UI, and target values are URL-encoded.
- The API response means the provider accepted/submitted the action, not that containment has completed. Verify the machine action or user session state in the vendor console.
- Never expose client secrets to browser code or commit them to the repository.
- Start with a dedicated test tenant and a disposable test endpoint/account. Keep a documented recovery/unisolation procedure and independent administrator access.

## What remains unimplemented

- No firewall/network appliance block action is implemented. Defender device isolation is endpoint containment, not a universal network firewall rule.
- No live action is triggered from FIRSTLIGHT's current simulated approval UI yet.
- No immutable external audit anchor, durable case store, or independently timestamped evidence manifest is implemented.
- No tenant has been connected or live action verified in this change.

Before presenting this as a live-response product, integrate these adapters into an authenticated operator workflow, store approvals and results in durable append-only storage, independently anchor audit manifests, add integration tests in a disposable tenant, and exercise rollback/unisolation.


## Operator CLI for explicit live actions

The repository also includes `scripts/firstlight_live_response.py`, a direct operator path to the guarded adapters above. It is intentionally not called automatically by the investigation agent.

Example (only in an authorized test tenant with a disposable device/account and approved app permissions):

```bash
python scripts/firstlight_live_response.py --action isolate-device --target '<exact-defender-machine-id>' --reason 'Case FL-123: approved containment' --execute-live-action
python scripts/firstlight_live_response.py --action revoke-user-sessions --target '<exact-user-id-or-upn>' --reason 'Case FL-123: approved session revocation' --execute-live-action
```

The command requires an interactive terminal, the explicit `--execute-live-action` flag, `SATARK_ENABLE_LIVE_RESPONSE=true` in the trusted runtime environment, server-side Microsoft credentials, a non-empty reason, and an exact confirmation typed at the prompt. A mismatch or non-interactive invocation makes no provider call. Never use a real user or device as a test target without the tenant owner's authorization and a recovery plan.

The command reports provider submission, not completion. Verify the resulting machine action or session state in the Microsoft console. The CLI does not currently persist the approval/action result into the durable FIRSTLIGHT case audit store, and the web approval UI is still not wired to these adapters. This is an explicit remaining production gate, not a completed integration.
