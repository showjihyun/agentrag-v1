/**
 * @deprecated Use ImprovedBlockPalette instead
 * 
 * This component is deprecated and will be removed in a future version.
 * Please use ImprovedBlockPalette for a better user experience.
 */

'use client';

import { ImprovedBlockPalette } from './ImprovedBlockPalette';

export interface BlockConfig {
  type: string;
  name: string;
  description: string;
  category: 'blocks' | 'tools' | 'triggers' | 'agents' | 'control';
  bg_color: string;
  icon: string;
  sub_blocks?: any[];
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  agentId?: string;
  nodeType?: string;
  triggerType?: 'manual' | 'schedule' | 'webhook' | 'email' | 'event' | 'database';
}

interface BlockPaletteProps {
  blocks?: BlockConfig[];
  onAddBlock?: (block: BlockConfig) => void;
  className?: string;
}

/**
 * @deprecated Use ImprovedBlockPalette instead
 */
export function BlockPalette({ blocks = [], onAddBlock, className }: BlockPaletteProps) {
  console.warn('BlockPalette is deprecated. Please use ImprovedBlockPalette instead.');
  
  // Forward to ImprovedBlockPalette
  return (
    <ImprovedBlockPalette 
      onAddNode={(type, toolId) => {
        // Convert to old format for compatibility
        const block: BlockConfig = {
          type,
          name: type,
          description: '',
          category: 'tools',
          bg_color: '#10b981',
          icon: '🔧',
          ...(toolId && { nodeType: toolId }),
        };
        onAddBlock?.(block);
      }}
    />
  );
}
