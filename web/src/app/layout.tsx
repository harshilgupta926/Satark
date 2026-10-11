import type { Metadata } from 'next';
import './globals.css';
import RouteExperience from './route-experience';

export const metadata: Metadata = {
  title: 'SATARK — Digital Security Workspace',
  description: 'Investigate suspicious digital content with evidence-backed security checks.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><div className="ambient-backdrop" aria-hidden="true"><i /><i /><i /></div><RouteExperience />{children}</body></html>;
}
