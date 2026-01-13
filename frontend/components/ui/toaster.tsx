'use client';

import { Toaster as Sonner } from 'sonner';
import { useSafeTheme } from './ThemeWrapper';

export function Toaster() {
  const { theme } = useSafeTheme();

  return (
    <Sonner
      theme={theme as 'light' | 'dark' | 'system'}
      position="top-right"
      toastOptions={{
        classNames: {
          toast: 'group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg',
          description: 'group-[.toast]:text-muted-foreground',
          actionButton: 'group-[.toast]:bg-primary group-[.toast]:text-primary-foreground',
          cancelButton: 'group-[.toast]:bg-muted group-[.toast]:text-muted-foreground',
          error: 'group-[.toast]:bg-destructive group-[.toast]:text-destructive-foreground',
          success: 'group-[.toast]:bg-green-600 group-[.toast]:text-white',
          warning: 'group-[.toast]:bg-yellow-600 group-[.toast]:text-white',
          info: 'group-[.toast]:bg-blue-600 group-[.toast]:text-white',
        },
      }}
      richColors
      closeButton
      duration={4000}
    />
  );
}
