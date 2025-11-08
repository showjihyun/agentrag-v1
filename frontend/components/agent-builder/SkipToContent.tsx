'use client';

import React from 'react';
import { Button } from '@/components/ui/button';

export function SkipToContent() {
  const skipToMain = () => {
    const main = document.getElementById('main-content');
    if (main) {
      main.focus();
      main.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <Button
      onClick={skipToMain}
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50"
      variant="outline"
    >
      Skip to main content
    </Button>
  );
}
