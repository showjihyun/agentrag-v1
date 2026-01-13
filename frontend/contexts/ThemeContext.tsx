'use client';

/**
 * Theme Context
 * Safe wrapper around next-themes useTheme hook
 * Provides fallback values when used outside ThemeProvider
 */

import { useTheme as useNextTheme } from 'next-themes';
import { createContext, useContext, useEffect, useState, ReactNode } from 'react';

interface ThemeContextType {
  theme: string | undefined;
  setTheme: (theme: string) => void;
  resolvedTheme: string | undefined;
  themes: string[];
  systemTheme: string | undefined;
  mounted: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderWrapperProps {
  children: ReactNode;
}

export function ThemeProviderWrapper({ children }: ThemeProviderWrapperProps) {
  const [mounted, setMounted] = useState(false);
  
  // Use a try-catch to handle cases where useTheme is called outside ThemeProvider
  let themeData;
  try {
    themeData = useNextTheme();
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
