'use client';

import React, { useState, useMemo } from 'react';
import { Search, Box, Wrench, Zap } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

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

const categoryIcons: Record<string, any> = {
  blocks: Box,
  tools: Wrench,
  triggers: Zap,
  agents: Box,
  control: Box,
};

const categoryEmojis: Record<string, string> = {
  agents: '🤖',
  control: '⚙️',
};

const categoryColors = {
  blocks: 'text-blue-500',
  tools: 'text-green-500',
  triggers: 'text-yellow-500',
  agents: 'text-purple-600',
  control: 'text-amber-600',
};

export function BlockPalette({ blocks = [], onAddBlock, className }: BlockPaletteProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'blocks' | 'tools' | 'triggers' | 'agents' | 'control'>('all');
  const searchInputRef = React.useRef<HTMLInputElement>(null);

  // Debug: Log blocks data
  React.useEffect(() => {
    console.log('BlockPalette - Total blocks:', blocks.length);
    console.log('BlockPalette - Blocks by category:', {
      control: blocks.filter(b => b.category === 'control').length,
      triggers: blocks.filter(b => b.category === 'triggers').length,
      agents: blocks.filter(b => b.category === 'agents').length,
      blocks: blocks.filter(b => b.category === 'blocks').length,
      tools: blocks.filter(b => b.category === 'tools').length,
    });
  }, [blocks]);

  // Keyboard shortcut: Ctrl+K to focus search
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Filter blocks
  const filteredBlocks = useMemo(() => {
    return blocks.filter((block) => {
      const matchesSearch =
        searchQuery === '' ||
        block.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        block.description.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesCategory = selectedCategory === 'all' || block.category === selectedCategory;

      return matchesSearch && matchesCategory;
    });
  }, [blocks, searchQuery, selectedCategory]);

  // Group blocks by category
  const groupedBlocks = useMemo(() => {
    const groups: Record<string, BlockConfig[]> = {
      control: [],
      triggers: [],
      agents: [],
      blocks: [],
      tools: [],
    };

    filteredBlocks.forEach((block) => {
      groups[block.category].push(block);
    });

    return groups;
  }, [filteredBlocks]);

  // Handle drag start
  const onDragStart = (event: React.DragEvent, block: BlockConfig) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify(block));
    event.dataTransfer.effectAllowed = 'move';
  };

  // Handle click to add block
  const handleBlockClick = (block: BlockConfig) => {
    if (onAddBlock) {
      onAddBlock(block);
    }
  };

  return (
    <div className={cn('flex flex-col h-full bg-card border-r', className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <h3 className="font-semibold text-lg mb-3">Block Palette</h3>
        
        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            ref={searchInputRef}
            placeholder="🔍 Search blocks... (Ctrl+K)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Category Tabs */}
        <div className="flex gap-1">
          <button
            onClick={() => setSelectedCategory('all')}
            className={cn(
              'flex-1 px-3 py-2 text-xs font-medium rounded-md transition-colors',
              selectedCategory === 'all'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80'
            )}
          >
            All
          </button>
          {(['control', 'triggers', 'agents', 'blocks', 'tools'] as const).map((category) => {
            const Icon = categoryIcons[category];
            const emoji = categoryEmojis[category];
            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={cn(
                  'flex-1 px-2 py-2 text-xs font-medium rounded-md transition-colors flex items-center justify-center gap-1',
                  selectedCategory === category
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted hover:bg-muted/80'
                )}
              >
                {emoji ? (
                  <span className="text-sm">{emoji}</span>
                ) : (
                  <Icon className="h-3 w-3" />
                )}
                <span className="capitalize text-[10px]">{category}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Block List */}
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-3">
          {selectedCategory === 'all' ? (
            // Show all categories
            Object.entries(groupedBlocks).map(([category, categoryBlocks]) => {
              if (categoryBlocks.length === 0) return null;
              const Icon = categoryIcons[category as keyof typeof categoryIcons];
              const emoji = categoryEmojis[category];
              return (
                <div key={category}>
                  <div className="flex items-center gap-1.5 mb-1.5">
                    {emoji ? (
                      <span className="text-sm">{emoji}</span>
                    ) : (
                      <Icon className={cn('h-3.5 w-3.5', categoryColors[category as keyof typeof categoryColors])} />
                    )}
                    <h4 className="font-semibold text-xs capitalize">{category}</h4>
                    <span className="text-[10px] text-muted-foreground">({categoryBlocks.length})</span>
                  </div>
                  <div className="space-y-1.5">
                    {categoryBlocks.map((block) => (
                      <BlockItem
                        key={block.type}
                        block={block}
                        onDragStart={onDragStart}
                        onClick={handleBlockClick}
                      />
                    ))}
                  </div>
                </div>
              );
            })
          ) : (
            // Show selected category
            <div className="space-y-1.5">
              {filteredBlocks.map((block) => (
                <BlockItem
                  key={block.type}
                  block={block}
                  onDragStart={onDragStart}
                  onClick={handleBlockClick}
                />
              ))}
            </div>
          )}

          {filteredBlocks.length === 0 && (
            <div className="text-center py-6 text-muted-foreground">
              <Box className="h-10 w-10 mx-auto mb-2 opacity-50" />
              <p className="text-xs">No blocks found</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

interface BlockItemProps {
  block: BlockConfig;
  onDragStart: (event: React.DragEvent, block: BlockConfig) => void;
  onClick: (block: BlockConfig) => void;
}

function BlockItem({ block, onDragStart, onClick }: BlockItemProps) {
  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, block)}
      onClick={() => onClick(block)}
      className="p-2 rounded-md border bg-card hover:bg-accent cursor-move transition-colors group"
      style={{
        borderLeftWidth: 3,
        borderLeftColor: block.bg_color,
      }}
    >
      <div className="flex items-center gap-2">
        <div
          className="w-6 h-6 rounded flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0"
          style={{ backgroundColor: block.bg_color }}
        >
          {block.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-xs truncate" title={block.name}>
            {block.name}
          </div>
        </div>
      </div>
    </div>
  );
}
