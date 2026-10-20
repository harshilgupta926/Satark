# Web lazy-loading strategy

SATARK's web UI defers work that is not needed for the first viewport or current workflow. The intent is to reduce initial JavaScript parsing and avoid decoding media previews before they are needed; this change does not claim a measured Lighthouse improvement until a before/after run is recorded.

## Implemented

- **Home service configuration snapshot:** the module is dynamically imported only when its section approaches the viewport. An IntersectionObserver with a 240 px root margin triggers loading; browsers without the API fall back to immediate loading. The placeholder reserves space and explains the deferred state.
- **FIRSTLIGHT persistent workspace:** the case-management panel is dynamically imported when its section approaches the viewport. Findings summaries and event-timeline components are dynamically imported when their tabs are selected.
- **QR decoder fallback:** the jsqr package is dynamically imported only when the native browser barcode detector is missing or fails to return a result. Native decoding remains the first path.
- **Media previews:** local image previews and sampled video-frame previews use native loading="lazy" and decoding="async". Video metadata remains preload="metadata" because duration and dimensions are required for bounded local processing.

## Regression coverage

- web/tests/lazy-loading.test.mjs protects the dynamic-import boundaries.
- web/tests/browser-smoke.mjs checks that home readiness starts with a deferred placeholder and appears when scrolled into view.
- Run cd web && npm run typecheck && npm test && npm run build before release.
- Run the browser smoke in the same environment used by CI and record a separate before/after Lighthouse report before making quantitative performance claims.

## Safety and correctness

Lazy loading must not defer authorization checks, change server-side access control, hide provider failures, or imply that configuration proves operational health. The QR fallback stays local; it does not upload the image or visit decoded destinations. The user-selected media stays in the browser.
