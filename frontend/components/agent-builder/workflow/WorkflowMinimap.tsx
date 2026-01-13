'use client';

import React from 'react';
import { MiniMap, useReactFlow } from 'reactflow';
import { useTheme } from '@/contexts/ThemeContext';
import { useSafeTheme } from '../ThemeWrapper';

export function WorkflowMinimap() {
  const { theme } = useSafeTheme();
  const isDark = theme === 'dark';

  return (
    <MiniMap
      nodeColor={(node) => {
        switch (node.type) {
          case 'agent':
            return isDark ? '#3b82f6' : '#2563eb';
          case 'block':
            return isDark ? '#8b5cf6' : '#7c3aed';
          case 'condition':
            return isDark ? '#f59e0b' : '#d97706';
          case 'loop':
            return isDark ? '#10b981' : '#059669';
          default:
            return isDark ? '#6b7280' : '#9ca3af';
        }
      }}
      maskColor={isDark ? 'rgba(0, 0, 0, 0.6)' : 'rgba(255, 255, 255, 0.6)'}
      style={{
        backgroundColor: isDark ? '#1f2937' : '#f9fafb',
        border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
        borderRadius: '8px',
      }}
      position="bottom-right"
    />
  );
}

