'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { HighContrastMode } from './HighContrastMode';
import { FontSizeControl } from './FontSizeControl';
import { X, Accessibility } from 'lucide-react';

export function AccessibilityToolbar() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [reducedMotion, setReducedMotion] = React.useState(false);

  React.useEffect(() => {
    // Check user preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setReducedMotion(prefersReducedMotion);
  }, []);

  const toggleReducedMotion = () => {
    const newValue = !reducedMotion;
    setReducedMotion(newValue);
    
    if (newValue) {
      document.documentElement.classList.add('reduce-motion');
    } else {
      document.documentElement.classList.remove('reduce-motion');
    }
    
    localStorage.setItem('reduced-motion', String(newValue));
  };

  if (!isOpen) {
    return (
      <Button
        variant="outline"
        size="icon"
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 z-50 h-12 w-12 rounded-full shadow-lg"
        title="Open accessibility toolbar"
      >
        <Accessibility className="h-6 w-6" />
      </Button>
    );
  }

  return (
    <Card className="fixed bottom-4 right-4 z-50 shadow-lg">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Accessibility className="h-5 w-5" />
            <h3 className="font-semibold">Accessibility</h3>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsOpen(false)}
            title="Close accessibility toolbar"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-sm">Contrast</span>
            <HighContrastMode />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm">Font Size</span>
            <FontSizeControl />
          </div>

          <div className="flex items-center justify-between">
            <span className="text-sm">Reduce Motion</span>
            <Button
              variant={reducedMotion ? 'default' : 'outline'}
              size="sm"
              onClick={toggleReducedMotion}
            >
              {reducedMotion ? 'On' : 'Off'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
