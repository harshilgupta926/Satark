# SATARK Sentinel — local review and release acceptance

## New local review workflows

### PDF and text documents

Route: `/pdf-review`.

- PDF parsing uses Mozilla PDF.js 6.4.299 and a same-origin worker copied to `public/pdf.worker.mjs` by `predev` / `prebuild`.
- PDF limit: 15 MiB and 50 pages. Selectable text is capped at 300,000 characters.
- TXT, Markdown, CSV and LOG limit: 2 MiB and 300,000 characters.
- The page calculates SHA-256 for the original bytes and checks a small, deterministic set of textual cues.
- The file and extracted text are processed in the browser and are not submitted to an API by this page.
- Password-protected PDFs, office files, embedded attachments, OCR of scanned PDFs, layout reconstruction, and document-signature verification are not included.
- A missing indicator is not a safety verdict. The exported TXT summary includes file metadata and signals, not the original extracted content.

### Video metadata and frame sampling

Route: `/media-review`.

- Supports MP4/WebM only, up to 50 MiB and 120 seconds, subject to the browser's available codec support.
- The browser reads duration and dimensions and calculates SHA-256 for the original file.
- The workflow samples up to six representative timestamps and generates a JPEG preview + SHA-256 for each encoded preview.
- Mean frame luminance is descriptive metadata only. Preview hashes are not hashes of source-frame bytes.
- Audio analysis/transcription, deepfake detection, all-frame inspection, codec/container forensics, and authenticity/provenance certification are not included.
- Video bytes are read from a local object URL; this page does not upload video or call a third-party analysis service.

## Validation

Run from `web/`:

```bash
npm ci
npm run test:ci
npm run test:browser
```

The CI browser-acceptance job covers desktop/mobile routes, response security headers, keyboard/focus structure, axe checks, PDF text extraction from a synthetic PDF, and local video frame sampling from a browser-generated synthetic WebM fixture.

The JavaScript unit/contract suite checks the local-processing boundaries, size/page/sample caps, and capability directory. The legacy Python workflow remains a separate compatibility check; it does not substitute for testing the Next.js routes.

## UI and open-source reference notes

The design direction uses a consistent Sentinel token set (ink/navy surfaces, muted slate, mint/cyan signal colors, restrained amber warnings), composable cards and clear status badges, responsive dashboard-style summaries, and reduced-motion-safe interactions. Keep the interface truthful about partial support: every capability entry must link to the working route or disclose that it is not available.

Reference projects:

- [shadcn/ui](https://github.com/shadcn-ui/ui) — accessible, composable, editable component patterns (MIT).
- [Tremor](https://github.com/tremorlabs/tremor) — compact dashboard cards, metrics and structured information hierarchy (Apache-2.0).
- [Magic UI](https://github.com/magicuidesign/magicui) — restrained motion/visual treatment patterns (MIT); preserve reduced-motion behavior.
- [Corsair](https://github.com/corsairdev/corsair) — tenant-scoped integration permissions and user approval concepts (Apache-2.0). It is not a UI kit and has not been added as a runtime dependency; evaluate it only before introducing third-party agent actions.
- [NirDiamant/GenAI_Agents](https://github.com/NirDiamant/GenAI_Agents) — research/tutorial reference only. Its repository declares a custom non-commercial license; do not copy or ship its code in a commercial product without explicit permission.

PDF.js is distributed under Apache-2.0; jsQR is distributed under Apache-2.0. Keep dependency licensing checks enabled and preserve required notices for any copied implementation.

## Production gates that code changes cannot safely fake

1. Configure the dedicated non-production Supabase test project and all documented `SATARK_TEST_*` GitHub Actions secrets. Include two distinct least-privilege tenant users and a viewer with a seeded disposable case. Never use the shared Nirdhoom/Saathi database for these tests.
2. Verify the SATARK Vercel project/team, confirm both production `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`, and run live Redis/rate-limit checks. The health snapshot is configuration-only, not a connectivity probe.
3. Resolve deployment quota/access and verify the deployed `/api/version` SHA, primary analysis flow, safe health response, authenticated case persistence/RLS, and production browser smoke.
4. Only then consider the release gate satisfied. Do not remove the fail-closed tenant integration check when its credentials are absent.

## Explicit remaining product boundaries

- Scanned PDFs need OCR before they can be text-inspected; no OCR engine is shipped here.
- URL input inspection remains distinct from fetching a public destination; submitted URLs are not automatically visited.
- QR payload decoding is cross-browser via the bundled fallback, but destination fetching/opening remains intentionally disabled.
- Persistent cases and reports require a correctly configured dedicated workspace and live tenant/RLS acceptance.
- Threat-intelligence match results still need an approved, versioned feed with freshness/provenance metadata before they can be represented as a live reputation lookup.
- FIRSTLIGHT response controls remain simulation-only; no real containment action should be enabled without explicit permissions, approval gates, audit trails and tenant isolation.
