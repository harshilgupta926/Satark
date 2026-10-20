import Link from 'next/link';

const workspace = [
  { href: '/investigate', label: 'Investigate' },
  { href: '/tools', label: 'Tools & status' },
  { href: '/firstlight', label: 'FIRSTLIGHT' },
  { href: '/learn', label: 'Academy' },
];
const records = [
  { href: '/cases', label: 'Cases' },
  { href: '/reports', label: 'Reports' },
  { href: '/login', label: 'Sign in' },
];

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="site-footer-inner">
        <div>
          <Link href="/" className="footer-brand"><span className="footer-brand-mark" aria-hidden="true">S</span> SATARK</Link>
          <p className="footer-blurb">Evidence-led digital security triage. Local-first checks, transparent signals, human review.</p>
        </div>
        <nav className="footer-col" aria-label="Workspace links">
          <h2>Workspace</h2>
          <ul>{workspace.map(l => <li key={l.href}><Link href={l.href}>{l.label}</Link></li>)}</ul>
        </nav>
        <nav className="footer-col" aria-label="Records links">
          <h2>Records</h2>
          <ul>{records.map(l => <li key={l.href}><Link href={l.href}>{l.label}</Link></li>)}</ul>
        </nav>
        <p className="footer-legal">SATARK provides triage guidance, not verdicts, forensic certification or incident-response services. A missing signal never proves content is safe — verify through a trusted channel before acting.</p>
      </div>
    </footer>
  );
}
