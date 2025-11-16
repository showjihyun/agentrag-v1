'use client';

import React from 'react';
import { LayoutGrid, ArrowRight, ArrowDown, Minimize2, Maximize2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { layoutPresets, LayoutPreset } from '@/lib/workflow-layout';

interface LayoutSelectorProps {
  onLayoutChange: (preset: LayoutPreset) => void;
  disabled?: boolean;
}

const layoutIcons: Record<LayoutPreset, React.ReactNode> = {
  horizontal: <ArrowRight className="h-4 w-4" />,
  vertical: <ArrowDown className="h-4 w-4" />,
  compact: <Minimize2 className="h-4 w-4" />,
  spacious: <Maximize2 className="h-4 w-4" />,
};

export function LayoutSelector({ onLayoutChange, disabled }: LayoutSelectorProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          disabled={disabled}
          title="Auto Layout"
        >
          <LayoutGrid className="h-4 w-4 mr-2" />
          Layout
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Auto Layout</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {(Object.keys(layoutPresets) as LayoutPreset[]).map((preset) => {
          const layout = layoutPresets[preset];
          return (
            <DropdownMenuItem
              key={preset}
              onClick={() => onLayoutChange(preset)}
              className="cursor-pointer"
            >
              <div className="flex items-center gap-3 w-full">
                <div className="flex-shrink-0">
                  {layoutIcons[preset]}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{layout.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {layout.description}
                  </div>
                </div>
              </div>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
