export default function Loading() {
  return (
    <main className="loading-screen" role="status" aria-live="polite" aria-label="Loading SATARK workspace">
      <div className="loading-grid" aria-hidden="true" />
      <div className="loader-mark" aria-hidden="true">S<span>.</span></div>
      <div className="loader-eyebrow">SATARK SENTINEL <span aria-hidden="true">/</span> SECURE WORKSPACE</div>
      <h1>Preparing your workspace<span aria-hidden="true">…</span></h1>
      <p>Bringing your investigation tools and evidence workspace into focus.</p>
      <div className="loader-track" aria-hidden="true"><span /></div>
      <div className="loader-foot">EVIDENCE FIRST <span aria-hidden="true">·</span> HUMAN REVIEW ALWAYS</div>
    </main>
  );
}
