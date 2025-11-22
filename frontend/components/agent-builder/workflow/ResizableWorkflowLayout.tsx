'use client';

import { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { GripVertical } from 'lucide-react';

interface ResizableWorkflowLayoutProps {
  canvas: React.ReactNode;
  logs: React.ReactNode;
  defaultLogsHeight?: number; // percentage
  minLogsHeight?: number; // percentage
  maxLogsHeight?: number; // percentage
}

export const ResizableWorkflowLayout = ({
  canvas,
  logs,
  defaultLogsHeight = 30,
  minLogsHeight = 20,
  maxLogsHeight = 60,
}: ResizableWorkflowLayoutProps) => {
  const [logsHeight, setLogsHeight] = useState(defaultLogsHeight);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const containerHeight = containerRect.height;
      const mouseY = e.clientY - containerRect.top;
      
      // Calculate new logs height as percentage
      const newLogsHeight = ((containerHeight - mouseY) / containerHeight) * 100;
      
      // Clamp between min and max
      const clampedHeight = Math.max(
        minLogsHeight,
        Math.min(maxLogsHeight, newLogsHeight)
      );
      
      setLogsHeight(clampedHeight);
    };

    const handleMouseUp = () => {
      setIsDragging(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, minLogsHeight, maxLogsHeight]);

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const canvasHeight = 100 - logsHeight;

  return (
    <div
      ref={containerRef}
      className="h-full flex flex-col overflow-hidden"
      style={{ cursor: isDragging ? 'row-resize' : 'default' }}
    >
      {/* Canvas Area */}
      <div
        className="overflow-hidden"
        style={{ height: `${canvasHeight}%` }}
      >
        {canvas}
      </div>

      {/* Resize Handle */}
      <div
        className={cn(
          'h-1 bg-border hover:bg-primary/50 transition-colors cursor-row-resize relative group',
          isDragging && 'bg-primary'
        )}
        onMouseDown={handleMouseDown}
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <div className={cn(
            'bg-background border rounded px-2 py-0.5 opacity-0 group-hover:opacity-100 transition-opacity',
            isDragging && 'opacity-100'
          )}>
            <GripVertical className="h-3 w-3 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Logs Panel */}
      <div
        className="overflow-hidden border-t bg-white dark:bg-gray-950"
        style={{ height: `${logsHeight}%` }}
      >
        {logs}
      </div>
    </div>
  );
};
