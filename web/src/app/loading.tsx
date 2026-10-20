export default function Loading() {
  return (
    <main className="loading-screen" role="status" aria-live="polite" aria-label="Loading SATARK workspace">
      <div className="loading-console">
        <div className="loader-mark" aria-hidden="true"><span>S</span></div>
        <div className="loader-eyebrow">SATARK</div>
        <h1>Preparing your workspace</h1>
        <p>Loading the investigation tools and review controls.</p>
        <div className="loader-track" aria-hidden="true"><span /></div>
      </div>
    </main>
  );
}
