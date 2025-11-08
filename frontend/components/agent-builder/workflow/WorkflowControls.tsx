'use client';

import React from 'react';
import { useReactFlow } from 'reactflow';
import { Button } from '@/components/ui/button';
import {
  ZoomIn,
  ZoomOut,
  Maximize,
  Grid3x3,
  AlignHorizontalJustifyCenter,
  AlignVerticalJustifyCenter,
} from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface WorkflowControlsProps {
  onAutoLayout?: () => void;
  snapToGrid?: boolean;
  onToggleGrid?: () => void;
}

export function WorkflowControls({ onAutoLayout, snapToGrid, onToggleGrid }: WorkflowControlsProps) {
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  return (
    <TooltipProvider>
      <div className="absolute top-4 right-4 flex flex-col gap-2 bg-background border rounded-lg p-2 shadow-lg z-10">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => zoomIn()}
              aria-label="Zoom in"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Zoom In</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => zoomOut()}
              aria-label="Zoom out"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Zoom Out</TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fitView({ padding: 0.2 })}
              aria-label="Fit view"
            >
              <Maximize className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent side="left">Fit View</TooltipContent>
        </Tooltip>

        <div className="h-px bg-border my-1" />

        {onToggleGrid && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant={snapToGrid ? 'default' : 'ghost'}
                size="icon"
                onClick={onToggleGrid}
                aria-label="Toggle grid snap"
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">
              {snapToGrid ? 'Disable' : 'Enable'} Grid Snap
            </TooltipContent>
          </Tooltip>
        )}

        {onAutoLayout && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                onClick={onAutoLayout}
                aria-label="Auto layout"
              >
                <AlignHorizontalJustifyCenter className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="left">Auto Layout</TooltipContent>
          </Tooltip>
        )}
      </div>
    </TooltipProvider>
  );
}
