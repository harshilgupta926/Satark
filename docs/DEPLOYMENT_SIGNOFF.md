# Deployment verification and release sign-off

This is an execution record, not a declaration that the checks have passed. A checkbox may be marked complete only by the person who ran the test against the stated candidate and captured its result. Repository CI does not prove the hosted app is running that commit.

## Candidate identity

Record these values for each release:

- Candidate repository:
- Candidate branch:
- Candidate commit SHA (full 40 characters):
- Hosting provider and app identifier:
- Public app URL:
- Hosting dashboard's deployed commit / build identifier:
- CI run URL and result:
- CodeQL run URL and result:
- Tester, date, and timezone:

**Identity gate:** the hosting dashboard's deployed revision must match the approved candidate SHA. If the host cannot expose a SHA, add a safe build identifier to the app and verify it in the live UI. Never expose environment variables, secret values, or provider credentials as build metadata.

## P0 — live demonstration smoke test

Run in a fresh browser session against the public deployment, not only localhost. Save screenshots or logs that do not contain submitted private data.

| Check | Pass condition | Result / evidence |
|---|---|---|
| App startup | Home renders without traceback or blank screen | |
| FIRSTLIGHT entry | Workspace opens and synthetic scenario loads without provider credentials | |
| Evidence verification | Original evidence verifies; tampering challenge is detected | |
| Investigation | Findings link back to evidence; unknowns/gaps remain visible | |
| Simulated response | Approval/rejection is explicit; every outcome remains clearly simulated; no real action occurs | |
| Audit integrity | Valid chain verifies; modified/malformed chain fails verification | |
| JSON export | Export downloads and parses; no secret or unrelated session content included | |
| Text scanner | Valid sample produces a bounded result; provider failure is not described as safe | |
| URL scanner | Public test URL works where permitted; private/reserved targets and blocked redirects are rejected | |
| Image / QR scanner | Valid sample and invalid image both produce bounded outcomes | |
| PDF scanner / report | Valid sample is processed within limits; report downloads and opens | |
| Video scanner | Supported sample works when dependencies are available; unsupported/oversized input fails gracefully | |
| History | Current-session behavior is clear; refresh/restart persistence is not implied | |
| Responsive layout | Navigation, actions, errors and downloads work on desktop and mobile viewport | |
| Offline behavior | With provider key absent, deterministic FIRSTLIGHT and sample/demo paths remain usable | |
| Secret hygiene | Browser-visible UI, URLs, logs and errors contain no API key, auth header or raw provider payload | |

A check is **blocked**, not passed, if the required sample, credentials, dashboard access, or evidence is unavailable.

## P0 — adversarial and failure tests

Run only in a controlled test environment with synthetic inputs and bounded resource limits.

| Area | Test cases | Required result |
|---|---|---|
| File parser safety | Empty, truncated, malformed, encrypted and oversized PDF; malformed/oversized image; extreme pixel dimensions; empty/oversized video | Clear rejection or bounded fallback; no traceback or runaway memory/CPU |
| URL / SSRF | localhost, private/reserved IP, IPv4-mapped IPv6, mixed public/private DNS answers, DNS changes, credentials in URL, redirect to private IP, redirect loop, HTTPS downgrade | Rejected before sensitive/internal access; redirect targets revalidated; request and redirect budgets enforced |
| Provider failures | Success, vision request, timeout, invalid/revoked key, model missing, malformed response, provider 429/5xx | Bounded user-facing error; no false-safe verdict; no secret/raw response leakage |
| Abuse controls | Rapid repeated scans, parallel requests, oversized request body, slow provider, simultaneous large files | Explicit request/concurrency/time limits and bounded resource use |
| Data leakage | Deliberate fake API key marker and synthetic sensitive string through input/error paths | Marker does not appear in logs, reports, browser output or exceptions except where intentionally echoed as submitted content |
| Recovery | Restart app, provider outage, invalid configuration | No misleading durability claim; deterministic demo remains available; rollback path documented |

Do not run load tests against the public shared demo or third-party providers without authorization. Record request counts, concurrency, durations and observed resource usage. Application-level limits must be complemented by host-level request size, timeout, concurrency, egress and provider spend limits.

## P1 — architecture required before sensitive or multi-tenant use

- [ ] Authentication and explicit authorization for every case/report operation.
- [ ] Tenant isolation enforced server-side and covered by negative tests.
- [ ] Durable case/evidence storage with access controls, integrity verification and independent evidence-manifest anchoring where chain-of-custody claims are made.
- [ ] Documented retention, deletion, export and backup/restore procedures; recovery exercise completed.
- [ ] Distributed rate limits, per-user and global quotas, concurrency limits and provider cost alerts.
- [ ] Provider data-processing, retention, region and training-use terms reviewed and approved for the intended data.
- [ ] Privacy notice, acceptable-use policy, security contact, incident owner and incident-response playbook.
- [ ] Structured monitoring for errors, latency, limits and resource saturation without logging raw submitted content or secrets.
- [ ] Rollback procedure exercised and dependency/security update owner assigned.
- [ ] FIRSTLIGHT simulated response boundaries reviewed in UI, report, docs and demo script.
- [ ] Evaluation dataset and measured precision/recall/false-positive rate, evidence-grounding rate and latency published with limitations.

## Go / no-go rule

- **GO — supervised hackathon demo:** only synthetic/non-sensitive inputs; exact deployed SHA verified; all applicable P0 live smoke checks pass; no known critical/high unresolved release-blocking finding; provider failures and simulated actions behave safely.
- **NO-GO — public service with a shared key:** until host-level abuse controls, global quotas and monitoring are verified.
- **NO-GO — confidential or regulated data:** until the P1 identity, tenant isolation, persistence, retention, provider and recovery controls are reviewed and tested.
- A missing result is **unknown**, not a pass. CI green, a successful local run, or a repository sync alone cannot change that status.

## Sign-off

- Final status: NOT RUN / BLOCKED / PASS / FAIL
- Candidate SHA:
- Failed or blocked checks:
- Accepted residual risks and owner:
- Rollback tested:
- Reviewer:
- Date/time:
