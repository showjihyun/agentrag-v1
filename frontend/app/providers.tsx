'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState, useEffect } from 'react';
import { registerServiceWorker } from '@/lib/pwa/register-sw';
import { analytics } from '@/lib/monitoring/analytics';
import { initSentry } from '@/lib/monitoring/sentry';
import { performanceMonitor } from '@/lib/monitoring/performance';
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ToastProvider } from '@/components/Toast';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  useEffect(() => {
    // Initialize monitoring
    analytics.init();
    initSentry();
    performanceMonitor.init();

    // Register service worker
    registerServiceWorker();

    return () => {
      performanceMonitor.cleanup();
    };
  }, []);

  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <QueryClientProvider client={queryClient}>
            {children}
            {process.env.NODE_ENV === 'development' && <ReactQueryDevtools />}
          </QueryClientProvider>
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
