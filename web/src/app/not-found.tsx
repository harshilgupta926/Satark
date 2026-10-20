import SiteHeader from './site-header';

export default function NotFound() {
  return (
    <main className="shell">
      <SiteHeader />
      <div className="system-screen" id="main-content" tabIndex={-1}>
        <div>
          <div className="eyebrow">404 · Page not found</div>
          <h1>This page doesn’t exist.</h1>
          <p>The address may be incorrect, or the page may have moved.</p>
          <a className="btn btn-primary" href="/">Return home</a>
        </div>
      </div>
    </main>
  );
}
