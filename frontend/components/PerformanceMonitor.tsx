'use client';

import { useEffect } from 'react';
import { measureWebVitals } from '@/lib/utils/performance';

export function PerformanceMonitor() {
  useEffect(() => {
    // Only run on client side
    measureWebVitals();
  }, []);

  return null; // This component doesn't render anything
}