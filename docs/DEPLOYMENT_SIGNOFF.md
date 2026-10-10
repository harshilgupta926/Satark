# Deployment verification and release sign-off

This is an execution record. A missing result is unknown, not a pass. Repository CI does not prove that the hosted application is running the merged commit.

## Candidate identity

- Canonical repository: `kaustubhdua/Satark`
- Candidate branch: `main`
- Approved merge commit: `edfb72c7f5b8654ef4ed76de4a632c59438e220e`
- UI change PR: [#25](https://github.com/kaustubhdua/Satark/pull/25) (merged; merge commit `edfb72c7f5b8654ef4ed76de4a632c59438e220e`)
- Deployment repository inspected read-only: [harshilgupta926/Satark](https://github.com/harshilgupta926/Satark) — older home/FIRSTLIGHT labels remain on its `main` branch
- CI run on exact PR head `ed44973b458916cd7a9d61cd8b719d65c90f722e`: [run #842](https://github.com/kaustubhdua/Satark/actions/runs/38095332214) — PASS
- CodeQL run on exact PR head `ed44973b458916cd7a9d61cd8b719d65c90f722e`: [run #311](https://github.com/kaustubhdua/Satark/actions/runs/38095332252) — PASS
- Public demo URL: https://satark-32uppvjxwmderrchbhj7gj.streamlit.app/
- Hosting dashboard repository / branch / deployed SHA: NOT VERIFIED (dashboard access/revision evidence unavailable)
- Tester / timestamp: automated repository checks inspected 2026-10-11; live sign-off incomplete

## Automated release-candidate result

The exact PR head passed CI and CodeQL before merge. CI included dependency consistency, Python compilation, unit tests, desktop/mobile browser smoke/layout tests, and project/style/asset checks. These results apply to the PR head above; verify the merged commit's own workflow state separately when available.

## P0 — live demonstration smoke test

Status: **FAIL — deployed UI is stale; NOT SIGNED OFF**. An interactive browser session successfully rendered the public app and opened FIRSTLIGHT, but its visible home still contains `SAMPLE`, `ILLUSTRATIVE`, `FLAGSHIP WORKSPACE 01 / 03`, and `Open guided sample report`. FIRSTLIGHT still exposes `Load / reset synthetic incident`. These labels predate PR #25, so the public deployment is not serving the approved UI content. The app is created by `harshilgupta926`; the canonical repo `kaustubhdua/Satark` is a different repository. GitHub integration access to the deployment repository is read-only (branch creation returned 403), and the hosting dashboard revision is not accessible. The live app's home and FIRSTLIGHT entry render, but that does not satisfy the revision identity gate.

| Check | Result | Evidence / notes |
|---|---|---|
| Hosting repository and branch | PARTIAL | Live shell identifies app creator as `harshilgupta926`; read-only inspection of `harshilgupta926/Satark` shows the older UI copy. Exact host branch still requires dashboard confirmation |
| Deployed revision equals approved SHA | BLOCKED | No dashboard build SHA or in-app build identifier |
| Home renders without runtime error | PASS (basic render only) | Interactive browser shows the home UI and navigation; no visible runtime error. This does not verify the deployed revision |
| FIRSTLIGHT entry / training case | PARTIAL | FIRSTLIGHT opens and the existing synthetic incident is visible; deployed button label is the old `Load / reset synthetic incident`, confirming stale UI |
| Evidence integrity and tampering | NOT RUN | Needs live interaction |
| Findings, timeline, gaps | NOT RUN | Needs live interaction |
| Simulated approval and rejection | NOT RUN | Needs live interaction |
| Audit-chain validation | NOT RUN | Needs live interaction |
| FIRSTLIGHT JSON export | NOT RUN | Needs live interaction |
| Scanner workflows and graceful provider failure | NOT RUN | Authorized provider credentials and controlled test inputs needed |
| URL SSRF / redirect protections | NOT RUN | Must use controlled test endpoints |
| PDF export opens and contains expected sections | NOT RUN | Needs live browser download |
| Video / image / QR scanner edge cases | NOT RUN | Needs controlled sample corpus |
| Desktop/mobile live layout | NOT RUN | Live browser blocked |
| Secret hygiene | PARTIAL / NOT VERIFIED | Repository config reviewed; live logs and browser errors not inspectable |
| Hosting-level body/time/concurrency/egress limits | NOT VERIFIED | Requires hosting configuration access |

## P1 — provider and security validation

Status: **BLOCKED pending authorized target-environment testing**.

- Model IDs are configured in `ai_provider.py`; availability to the target API account has not been verified.
- No live provider success/failure test was run in this pass. Do not infer provider health from unit tests.
- No production-host adversarial file/URL or concurrency tests were run.
- Provider data-processing/retention terms and the intended data's privacy/legal basis still require owner review.
- Continue to use synthetic or non-sensitive data until these gates are closed.

## P1 — investigation quality

Repository unit tests cover evidence hash mismatches, ID substitution, malformed evidence, evidence references, timeline ordering across timezones, malformed audit chains, simulated approval/rejection, and bounded imports. These are automated code-level checks, not a complete live or operational evaluation. A repeatable evaluation dataset and measured precision/recall, false-positive rate, grounding rate and latency remain open.

## P2 — broader-use architecture

Not a production approval. Before confidential or multi-tenant use, complete authenticated access and authorization, tenant isolation, durable case/evidence storage, protected/independently verifiable audit records, retention/deletion and backup/recovery, distributed quotas and cost controls, monitoring, incident ownership, and a measured evaluation program.

## Go / no-go

- **Supervised hackathon demo:** NO-GO for a verified release sign-off until the hosting revision is matched to the approved commit and applicable live P0 checks are run.
- **Public anonymous service with a shared provider key:** NO-GO until host-level abuse controls, global quotas and monitoring are verified.
- **Confidential / regulated data:** NO-GO until P1 identity, tenant isolation, persistence, retention, provider and recovery controls are implemented and reviewed.

## Sign-off

- Final status: **FAIL / BLOCKED — automated PR checks passed, but the live deployment demonstrably serves older UI content and the approved SHA cannot be deployed from this connection**
- Candidate SHA: `edfb72c7f5b8654ef4ed76de4a632c59438e220e`
- Outstanding blockers: update deployment repo/host to the approved commit, verify exact deployed SHA, complete remaining live interactive workflows, authorized provider and adversarial tests, host controls/privacy review. GitHub write access to `harshilgupta926/Satark` is unavailable to this integration.
- Accepted residual risks / owner: not yet assigned
- Rollback tested: NO / NOT VERIFIED
- Reviewer: automated repository review; human deployment owner sign-off pending
- Date: 2026-10-11
