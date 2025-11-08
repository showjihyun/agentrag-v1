'use client';

import React from 'react';
import { Button, ButtonProps } from '@/components/ui/button';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AccessibleButtonProps extends ButtonProps {
  isLoading?: boolean;
  loadingText?: string;
  ariaLabel?: string;
  children: React.ReactNode;
}

export function AccessibleButton({
  isLoading,
  loadingText,
  ariaLabel,
  children,
  disabled,
  className,
  ...props
}: AccessibleButtonProps) {
  return (
    <Button
      {...props}
      disabled={disabled || isLoading}
      aria-label={ariaLabel}
      aria-busy={isLoading}
      aria-disabled={disabled || isLoading}
      className={cn(
        'focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
        'transition-all duration-200',
        className
      )}
    >
      {isLoading && (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden="true" />
          <span className="sr-only">Loading</span>
        </>
      )}
      {isLoading && loadingText ? loadingText : children}
    </Button>
  );
}
