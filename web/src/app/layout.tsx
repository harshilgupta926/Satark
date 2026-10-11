import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'SATARK — Digital Security Workspace',
  description: 'Investigate suspicious digital content with evidence-backed security checks.',
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
