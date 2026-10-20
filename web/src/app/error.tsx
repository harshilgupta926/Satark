'use client';

export default function Error({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="system-screen" id="main-content">
      <div>
        <div className="eyebrow">Something went wrong</div>
        <h1>This view needs another try.</h1>
        <p>Unsaved work in this view may be lost. Retry, or return home.</p>
        <div className="actions" style={{ justifyContent: 'center' }}>
          <button className="btn btn-primary" onClick={() => reset()}>Retry view</button>
          <a className="btn btn-secondary" href="/">Back to SATARK</a>
        </div>
      </div>
    </main>
  );
}
