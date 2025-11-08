'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Contrast, Check } from 'lucide-react';

type ContrastMode = 'normal' | 'high' | 'extra-high';

export function HighContrastMode() {
  const [mode, setMode] = React.useState<ContrastMode>('normal');

  React.useEffect(() => {
    // Load saved preference
    const saved = localStorage.getItem('contrast-mode') as ContrastMode;
    if (saved) {
      setMode(saved);
      applyContrastMode(saved);
    }
  }, []);

  const applyContrastMode = (newMode: ContrastMode) => {
    const root = document.documentElement;
    
    // Remove existing classes
    root.classList.remove('contrast-normal', 'contrast-high', 'contrast-extra-high');
    
    // Apply new class
    root.classList.add(`contrast-${newMode}`);
    
    // Save preference
    localStorage.setItem('contrast-mode', newMode);
    setMode(newMode);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" title="Contrast settings">
          <Contrast className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Contrast Mode</DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={() => applyContrastMode('normal')}>
          {mode === 'normal' && <Check className="h-4 w-4 mr-2" />}
          {mode !== 'normal' && <span className="w-4 mr-2" />}
          Normal
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => applyContrastMode('high')}>
          {mode === 'high' && <Check className="h-4 w-4 mr-2" />}
          {mode !== 'high' && <span className="w-4 mr-2" />}
          High Contrast (7:1)
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => applyContrastMode('extra-high')}>
          {mode === 'extra-high' && <Check className="h-4 w-4 mr-2" />}
          {mode !== 'extra-high' && <span className="w-4 mr-2" />}
          Extra High (10:1+)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
