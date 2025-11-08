'use client';

import { useEffect } from 'react';
import { initMonitoring, trackAppLifecycle } from '@/lib/monitoring/init';
import { usePathname } from 'next/navigation';
import { analytics } from '@/lib/monitoring/analytics';

export function MonitoringInit() {
  const pathname = usePathname();

  // Initialize monitoring on mount
  useEffect(() => {
    initMonitoring();
    trackAppLifecycle();
  }, []);

  // Track page views
  useEffect(() => {
    if (pathname) {
      analytics.page(pathname);
    }
  }, [pathname]);

  return null;
}
