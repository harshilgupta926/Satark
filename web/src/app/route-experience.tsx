'use client';

import { useEffect, useRef, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';

export default function RouteExperience() {
  const pathname = usePathname();
  const router = useRouter();
  const [navigating, setNavigating] = useState(false);
  const lastPath = useRef(pathname);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (lastPath.current !== pathname) {
      lastPath.current = pathname;
      if (timer.current) clearTimeout(timer.current);
      // Keep the veil only briefly after the new route is ready; never trap navigation.
      timer.current = setTimeout(() => setNavigating(false), 180);
    }
  }, [pathname]);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const target = event.target;
      if (!(target instanceof Element)) return;
      const anchor = target.closest('a[href]');
      if (!(anchor instanceof HTMLAnchorElement)) return;
      if (anchor.target && anchor.target !== '_self' || anchor.hasAttribute('download')) return;
      const url = new URL(anchor.href, window.location.href);
      if (url.origin !== window.location.origin || url.pathname === pathname && url.search === window.location.search && url.hash) return;
      if (!url.pathname.startsWith('/') || url.pathname.startsWith('/api/')) return;
      if (url.pathname === pathname && url.search === window.location.search) return;
      event.preventDefault();
      setNavigating(true);
      if (timer.current) clearTimeout(timer.current);
      // Fail open if a route transition errors or is interrupted.
      timer.current = setTimeout(() => setNavigating(false), 4500);
      router.push(url.pathname + url.search + url.hash);
    };
    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  }, [pathname, router]);

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  return (
    <div className={`route-veil${navigating ? ' route-veil-visible' : ''}`} aria-hidden="true">
      <div className="route-veil-card">
        <span className="route-veil-mark">S<span>.</span></span>
        <span className="route-veil-label">SATARK SENTINEL</span>
        <span className="route-veil-track"><i /></span>
      </div>
    </div>
  );
}
