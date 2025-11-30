'use client';

/**
 * Workflow Skeleton Loader
 * 
 * Polished skeleton UI for workflow loading states:
 * - Animated placeholders
 * - Realistic layout preview
 * - Smooth transitions
 */

import React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  animate?: boolean;
}

// Base skeleton component with shimmer animation
function Skeleton({ className, animate = true }: SkeletonProps) {
  return (
    <div
      className={cn(
        'bg-muted rounded',
        animate && 'animate-pulse',
        className
      )}
    />
  );
}

// Skeleton node for workflow canvas
function SkeletonNode({ className, variant = 'default' }: { className?: string; variant?: 'default' | 'start' | 'end' | 'condition' }) {
  const variants = {
    default: 'w-44 h-20',
    start: 'w-24 h-12 rounded-full',
    end: 'w-24 h-12 rounded-full',
    condition: 'w-32 h-32 rotate-45',
  };

  return (
    <div className={cn('relative', className)}>
      <Skeleton className={cn(variants[variant], 'shadow-sm')} />
      {variant === 'default' && (
        <>
          <Skeleton className="absolute top-3 left-3 w-8 h-8 rounded-lg" />
          <Skeleton className="absolute top-3 left-14 w-24 h-3 rounded" />
          <Skeleton className="absolute top-8 left-14 w-16 h-2 rounded" />
        </>
      )}
    </div>
  );
}

// Skeleton edge/connection
function SkeletonEdge({ className }: { className?: string }) {
  return (
    <div className={cn('relative', className)}>
      <Skeleton className="w-px h-16 mx-auto" />
      <Skeleton className="absolute bottom-0 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full" />
    </div>
  );
}

// Full workflow canvas skeleton
export function WorkflowCanvasSkeleton() {
  return (
    <div className="relative w-full h-full bg-background overflow-hidden">
      {/* Grid background */}
      <div 
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: 'radial-gradient(circle, hsl(var(--muted-foreground)) 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />

      {/* Skeleton workflow */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          {/* Start node */}
          <SkeletonNode variant="start" />
          <SkeletonEdge />
          
          {/* Main nodes */}
          <SkeletonNode />
          <SkeletonEdge />
          
          {/* Branching */}
          <div className="flex gap-16">
            <div className="flex flex-col items-center gap-4">
              <SkeletonNode />
              <SkeletonEdge />
              <SkeletonNode />
            </div>
            <div className="flex flex-col items-center gap-4">
              <SkeletonNode />
              <SkeletonEdge />
              <SkeletonNode />
            </div>
          </div>
          
          <SkeletonEdge />
          
          {/* End node */}
          <SkeletonNode variant="end" />
        </div>
      </div>

      {/* Loading indicator */}
      <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-2 rounded-full bg-background/80 backdrop-blur-sm border shadow-lg">
        <div className="flex gap-1">
          <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 rounded-full bg-primary animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
        <span className="text-sm text-muted-foreground">Loading workflow...</span>
      </div>
    </div>
  );
}

// Sidebar/palette skeleton
export function PaletteSkeleton() {
  return (
    <div className="w-full h-full p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Skeleton className="w-8 h-8 rounded-lg" />
        <Skeleton className="w-32 h-5 rounded" />
      </div>

      {/* Search */}
      <Skeleton className="w-full h-10 rounded-lg" />

      {/* Tabs */}
      <div className="flex gap-2">
        <Skeleton className="w-16 h-8 rounded-md" />
        <Skeleton className="w-16 h-8 rounded-md" />
        <Skeleton className="w-16 h-8 rounded-md" />
        <Skeleton className="w-16 h-8 rounded-md" />
      </div>

      {/* Items */}
      <div className="space-y-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
            <Skeleton className="w-10 h-10 rounded-lg" />
            <div className="flex-1 space-y-2">
              <Skeleton className="w-24 h-4 rounded" />
              <Skeleton className="w-32 h-3 rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Properties panel skeleton
export function PropertiesPanelSkeleton() {
  return (
    <div className="w-full h-full p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Skeleton className="w-16 h-5 rounded-full" />
          <Skeleton className="w-24 h-5 rounded" />
        </div>
        <Skeleton className="w-8 h-8 rounded" />
      </div>

      <Skeleton className="w-full h-px" />

      {/* Tabs */}
      <div className="flex gap-1">
        <Skeleton className="flex-1 h-9 rounded-md" />
        <Skeleton className="flex-1 h-9 rounded-md" />
      </div>

      {/* Form fields */}
      <div className="space-y-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="w-20 h-4 rounded" />
            <Skeleton className="w-full h-10 rounded-lg" />
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="absolute bottom-4 left-4 right-4 space-y-2">
        <Skeleton className="w-full h-10 rounded-lg" />
        <Skeleton className="w-full h-10 rounded-lg" />
      </div>
    </div>
  );
}

// Full editor skeleton
export function WorkflowEditorSkeleton() {
  return (
    <div className="flex h-screen w-full">
      {/* Left sidebar */}
      <div className="w-80 border-r bg-background">
        <PaletteSkeleton />
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <WorkflowCanvasSkeleton />
      </div>

      {/* Right sidebar */}
      <div className="w-80 border-l bg-background relative">
        <PropertiesPanelSkeleton />
      </div>
    </div>
  );
}

// Card skeleton for lists
export function WorkflowCardSkeleton() {
  return (
    <div className="p-4 rounded-lg border bg-card space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="w-32 h-5 rounded" />
          <Skeleton className="w-48 h-4 rounded" />
        </div>
        <Skeleton className="w-16 h-6 rounded-full" />
      </div>
      <div className="flex gap-2">
        <Skeleton className="w-20 h-6 rounded-full" />
        <Skeleton className="w-24 h-6 rounded-full" />
      </div>
      <div className="flex items-center justify-between pt-2 border-t">
        <Skeleton className="w-24 h-4 rounded" />
        <div className="flex gap-2">
          <Skeleton className="w-8 h-8 rounded" />
          <Skeleton className="w-8 h-8 rounded" />
        </div>
      </div>
    </div>
  );
}

// Export individual components
export { Skeleton, SkeletonNode, SkeletonEdge };
