'use client';

/**
 * Draggable Block Component
 * 
 * Enhanced drag and drop with:
 * - Ghost preview during drag
 * - Drop zone indicators
 * - Smooth animations
 * - Touch support
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { GripVertical, Plus } from 'lucide-react';

interface DraggableBlockProps {
  id: string;
  name: string;
  description?: string;
  icon: React.ReactNode;
  category?: string;
  color?: string;
  onDragStart?: (id: string) => void;
  onDragEnd?: (id: string, dropped: boolean) => void;
  onClick?: () => void;
  children?: React.ReactNode;
}

interface DragState {
  isDragging: boolean;
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
}

export function DraggableBlock({
  id,
  name,
  description,
  icon,
  category,
  color = '#6366f1',
  onDragStart,
  onDragEnd,
  onClick,
  children,
}: DraggableBlockProps) {
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0,
  });
  const [isMounted, setIsMounted] = useState(false);
  const blockRef = useRef<HTMLDivElement>(null);
  const dragThreshold = 5; // Pixels before drag starts

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return; // Only left click
    
    setDragState({
      isDragging: false,
      startX: e.clientX,
      startY: e.clientY,
      currentX: e.clientX,
      currentY: e.clientY,
    });

    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = Math.abs(moveEvent.clientX - e.clientX);
      const deltaY = Math.abs(moveEvent.clientY - e.clientY);

      if (deltaX > dragThreshold || deltaY > dragThreshold) {
        setDragState((prev) => ({
          ...prev,
          isDragging: true,
          currentX: moveEvent.clientX,
          currentY: moveEvent.clientY,
        }));
        onDragStart?.(id);
      } else {
        setDragState((prev) => ({
          ...prev,
          currentX: moveEvent.clientX,
          currentY: moveEvent.clientY,
        }));
      }
    };

    const handleMouseUp = (upEvent: MouseEvent) => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);

      const wasDragging = dragState.isDragging;
      setDragState({
        isDragging: false,
        startX: 0,
        startY: 0,
        currentX: 0,
        currentY: 0,
      });

      // Check if dropped on canvas
      const dropTarget = document.elementFromPoint(upEvent.clientX, upEvent.clientY);
      const isOnCanvas = dropTarget?.closest('[data-tour="workflow-canvas"]') !== null;
      
      onDragEnd?.(id, isOnCanvas);

      // If it was just a click (not drag), trigger onClick
      if (!wasDragging) {
        onClick?.();
      }
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  }, [id, onDragStart, onDragEnd, onClick, dragState.isDragging]);

  // Touch support
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0];
    setDragState({
      isDragging: false,
      startX: touch.clientX,
      startY: touch.clientY,
      currentX: touch.clientX,
      currentY: touch.clientY,
    });
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    const touch = e.touches[0];
    const deltaX = Math.abs(touch.clientX - dragState.startX);
    const deltaY = Math.abs(touch.clientY - dragState.startY);

    if (deltaX > dragThreshold || deltaY > dragThreshold) {
      setDragState((prev) => ({
        ...prev,
        isDragging: true,
        currentX: touch.clientX,
        currentY: touch.clientY,
      }));
      if (!dragState.isDragging) {
        onDragStart?.(id);
      }
    }
  }, [dragState.startX, dragState.startY, dragState.isDragging, id, onDragStart]);

  const handleTouchEnd = useCallback(() => {
    const wasDragging = dragState.isDragging;
    setDragState({
      isDragging: false,
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
    });
    onDragEnd?.(id, false);

    if (!wasDragging) {
      onClick?.();
    }
  }, [dragState.isDragging, id, onDragEnd, onClick]);

  return (
    <>
      {/* Original block */}
      <div
        ref={blockRef}
        className={cn(
          'group relative p-3 border rounded-lg transition-all cursor-grab',
          'bg-background hover:border-primary hover:shadow-md',
          'active:cursor-grabbing',
          dragState.isDragging && 'opacity-50 border-dashed'
        )}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        role="button"
        tabIndex={0}
        aria-label={`Drag ${name} to canvas`}
      >
        <div className="flex items-start gap-3">
          {/* Drag handle */}
          <div className="opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground">
            <GripVertical className="h-4 w-4" />
          </div>

          {/* Icon */}
          <div
            className="p-2 rounded-lg transition-colors"
            style={{ backgroundColor: `${color}20` }}
          >
            <div style={{ color }}>{icon}</div>
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="font-medium text-sm truncate">{name}</h4>
            </div>
            {description && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {description}
              </p>
            )}
            {category && (
              <Badge variant="outline" className="text-xs mt-2">
                {category}
              </Badge>
            )}
          </div>

          {/* Add indicator */}
          <div className="opacity-0 group-hover:opacity-100 transition-opacity">
            <Plus className="h-4 w-4 text-primary" />
          </div>
        </div>

        {children}
      </div>

      {/* Ghost preview during drag */}
      {isMounted && dragState.isDragging && createPortal(
        <div
          className={cn(
            'fixed pointer-events-none z-[10000]',
            'p-3 rounded-lg border-2 border-primary shadow-2xl',
            'bg-background/95 backdrop-blur-sm',
            'animate-in zoom-in-95 duration-150'
          )}
          style={{
            left: dragState.currentX - 100,
            top: dragState.currentY - 30,
            width: 200,
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-lg"
              style={{ backgroundColor: `${color}20` }}
            >
              <div style={{ color }}>{icon}</div>
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-sm truncate">{name}</h4>
              {category && (
                <span className="text-xs text-muted-foreground">{category}</span>
              )}
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}

// Drop zone indicator component
interface DropZoneIndicatorProps {
  isActive: boolean;
  position?: { x: number; y: number };
}

export function DropZoneIndicator({ isActive, position }: DropZoneIndicatorProps) {
  if (!isActive) return null;

  return (
    <div
      className={cn(
        'absolute pointer-events-none z-50',
        'w-48 h-24 rounded-lg border-2 border-dashed border-primary',
        'bg-primary/10 flex items-center justify-center',
        'animate-pulse'
      )}
      style={position ? { left: position.x - 96, top: position.y - 48 } : undefined}
    >
      <div className="text-center">
        <Plus className="h-6 w-6 text-primary mx-auto mb-1" />
        <span className="text-xs text-primary font-medium">Drop here</span>
      </div>
    </div>
  );
}

// Hook for managing drag state across components
export function useDragAndDrop() {
  const [isDragging, setIsDragging] = useState(false);
  const [draggedItem, setDraggedItem] = useState<string | null>(null);
  const [dropPosition, setDropPosition] = useState<{ x: number; y: number } | null>(null);

  const handleDragStart = useCallback((id: string) => {
    setIsDragging(true);
    setDraggedItem(id);
  }, []);

  const handleDragEnd = useCallback((id: string, dropped: boolean) => {
    setIsDragging(false);
    setDraggedItem(null);
    setDropPosition(null);
    return dropped;
  }, []);

  const updateDropPosition = useCallback((x: number, y: number) => {
    setDropPosition({ x, y });
  }, []);

  return {
    isDragging,
    draggedItem,
    dropPosition,
    handleDragStart,
    handleDragEnd,
    updateDropPosition,
  };
}
