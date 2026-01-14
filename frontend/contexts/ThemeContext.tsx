'use client';

/**
 * Theme Context
 * Safe wrapper around next-themes useTheme hook
 * Provides fallback values when used outside ThemeProvider
 */

import { useTheme as useNextTheme, ThemeProvider } from 'next-themes';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface ThemeContextType {
  theme: string | undefined;
  setTheme: (theme: string) => void;
  resolvedTheme: string | undefined;
  themes: string[];
  systemTheme: string | undefined;
  mounted: boolean;
}

const defaultThemeContext: ThemeContextType = {
  theme: 'light',
  setTheme: () => {},
  resolvedTheme: 'light',
  themes: ['light', 'dark', 'system'],
  systemTheme: 'light',
  mounted: false,
};

const ThemeContext = createContext<ThemeContextType>(defaultThemeContext);

interface ThemeProviderWrapperProps {
  children: ReactNode;
}

/**
 * Inner component that safely uses next-themes hook
 * This is rendered inside ThemeProvider so useNextTheme is safe
 */
function ThemeProviderInner({ children }: { children: ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const themeData = useNextTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  const value: ThemeContextType = {
    ...themeData,
    theme: mounted ? themeData.theme : 'light',
    resolvedTheme: mounted ? themeData.resolvedTheme : 'light',
    systemTheme: mounted ? themeData.systemTheme : 'light',
    mounted,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Combined ThemeProvider that includes both next-themes and our custom context
 * This ensures useNextTheme is always called within ThemeProvider
 */
export function ThemeProviderWrapper({ children }: ThemeProviderWrapperProps) {
  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      storageKey="agenticrag-theme"
    >
      <ThemeProviderInner>
        {children}
      </ThemeProviderInner>
    </ThemeProvider>
  );
}

/**
 * Safe useTheme hook that provides fallback values
 * Use this instead of next-themes useTheme directly
 */
export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  
  if (context === undefined) {
    // Fallback when used outside ThemeProviderWrapper
    console.warn('useTheme called outside ThemeProviderWrapper, using fallback values');
    return {
      theme: 'light',
      setTheme: () => {},
      resolvedTheme: 'light',
      themes: ['light', 'dark', 'system'],
      systemTheme: 'light',
      mounted: false,
    };
  }
  
  return context;
}

/**
 * Hook for components that need to wait for theme to be mounted
 * Prevents hydration mismatches
 */
export function useThemeWithMounted() {
  const theme = useTheme();
  
  if (!theme.mounted) {
    return {
      ...theme,
      theme: undefined,
      resolvedTheme: undefined,
      systemTheme: undefined,
    };
  }
  
  return theme;
}
