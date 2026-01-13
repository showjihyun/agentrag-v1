'use client';

/**
 * Theme Wrapper Component
 * Handles theme-related hydration issues and provides safe theme access
 */

import { useTheme } from '@/contexts/ThemeContext';
import { useEffect, useState } from 'react';

interface ThemeWrapperProps {
  children: React.ReactNode;
}

export function ThemeWrapper({ children }: ThemeWrapperProps) {
  return <>{children}</>;
}

/**
 * Hook for safe theme usage with hydration protection
 * This hook prevents hydration mismatches by ensuring theme values are consistent
 * between server and client rendering
 */
export function useSafeTheme() {
  const [mounted, setMounted] = useState(false);
  
  // Use a try-catch to handle cases where useTheme is called outside ThemeProvider
  let themeData;
  try {
    themeData = useTheme();
  } catch (error) {
    // Fallback if useTheme is called outside ThemeProvider
    console.warn('useTheme called outside ThemeProvider, using fallback values');
    themeData = {
      theme: 'light',
      setTheme: () => {},
      resolvedTheme: 'light',
      themes: ['light', 'dark', 'system'],
      systemTheme: 'light',
    };
  }

  useEffect(() => {
    setMounted(true);
  }, []);

  // Return theme data but with safe defaults during SSR
  return {
    ...themeData,
    theme: mounted ? themeData.theme : 'light',
    resolvedTheme: mounted ? themeData.resolvedTheme : 'light',
    systemTheme: mounted ? themeData.systemTheme : 'light',
  };
}
