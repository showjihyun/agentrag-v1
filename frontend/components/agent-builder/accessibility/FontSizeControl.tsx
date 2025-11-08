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
import { Type, Check } from 'lucide-react';

type FontSize = 'small' | 'normal' | 'large' | 'extra-large';

const fontSizeMap: Record<FontSize, string> = {
  small: '14px',
  normal: '16px',
  large: '18px',
  'extra-large': '20px',
};

export function FontSizeControl() {
  const [fontSize, setFontSize] = React.useState<FontSize>('normal');

  React.useEffect(() => {
    // Load saved preference
    const saved = localStorage.getItem('font-size') as FontSize;
    if (saved) {
      setFontSize(saved);
      applyFontSize(saved);
    }
  }, []);

  const applyFontSize = (size: FontSize) => {
    document.documentElement.style.fontSize = fontSizeMap[size];
    localStorage.setItem('font-size', size);
    setFontSize(size);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon" title="Font size settings">
          <Type className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>Font Size</DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        <DropdownMenuItem onClick={() => applyFontSize('small')}>
          {fontSize === 'small' && <Check className="h-4 w-4 mr-2" />}
          {fontSize !== 'small' && <span className="w-4 mr-2" />}
          Small (14px)
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => applyFontSize('normal')}>
          {fontSize === 'normal' && <Check className="h-4 w-4 mr-2" />}
          {fontSize !== 'normal' && <span className="w-4 mr-2" />}
          Normal (16px)
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => applyFontSize('large')}>
          {fontSize === 'large' && <Check className="h-4 w-4 mr-2" />}
          {fontSize !== 'large' && <span className="w-4 mr-2" />}
          Large (18px)
        </DropdownMenuItem>
        
        <DropdownMenuItem onClick={() => applyFontSize('extra-large')}>
          {fontSize === 'extra-large' && <Check className="h-4 w-4 mr-2" />}
          {fontSize !== 'extra-large' && <span className="w-4 mr-2" />}
          Extra Large (20px)
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
