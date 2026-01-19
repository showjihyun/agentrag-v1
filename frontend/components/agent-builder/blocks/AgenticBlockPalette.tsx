'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { blockTypesAPI, BlockTypeConfig } from '@/lib/api/block-types';
import { 
  Sparkles, 
  Brain, 
  ListTree, 
  Wrench,
  AlertCircle 
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Icon mapping
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  sparkles: Sparkles,
  brain: Brain,
  'list-tree': ListTree,
  wrench: Wrench,
};

interface AgenticBlockCardProps {
  block: BlockTypeConfig;
  onSelect?: (block: BlockTypeConfig) => void;
  onDragStart?: (block: BlockTypeConfig) => void;
}

function AgenticBlockCard({ block, onSelect, onDragStart }: AgenticBlockCardProps) {
  const Icon = ICON_MAP[block.icon] || Sparkles;
  
  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:shadow-lg hover:scale-105",
        "border-2 hover:border-purple-500"
      )}
      style={{
        background: `linear-gradient(135deg, ${block.bg_color}15 0%, ${block.bg_color}05 100%)`,
      }}
      draggable
      onClick={() => onSelect?.(block)}
      onDragStart={() => onDragStart?.(block)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div
            className="p-2 rounded-lg"
            style={{ backgroundColor: `${block.bg_color}20` }}
          >
            <Icon 
              className="h-5 w-5" 
              style={{ color: block.bg_color }}
            />
          </div>
          <Badge variant="outline" className="text-xs">
            Agentic
          </Badge>
        </div>
        <CardTitle className="text-base mt-2">{block.name}</CardTitle>
        <CardDescription className="text-xs line-clamp-2">
          {block.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{Object.keys(block.inputs).length} inputs</span>
          <span>•</span>
          <span>{Object.keys(block.outputs).length} outputs</span>
        </div>
      </CardContent>
    </Card>
  );
}

interface AgenticBlockPaletteProps {
  onBlockSelect?: (block: BlockTypeConfig) => void;
  onBlockDragStart?: (block: BlockTypeConfig) => void;
}

export function AgenticBlockPalette({ 
  onBlockSelect, 
  onBlockDragStart 
}: AgenticBlockPaletteProps) {
  const { data: agenticBlocks, isLoading, error } = useQuery({
    queryKey: ['block-types', 'agentic'],
    queryFn: () => blockTypesAPI.getAgenticBlocks(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Skeleton className="h-6 w-6 rounded" />
          <Skeleton className="h-6 w-32" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-40 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <CardTitle className="text-destructive">Error Loading Blocks</CardTitle>
          </div>
          <CardDescription>
            Failed to load agentic blocks. Please try again.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!agenticBlocks || agenticBlocks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Agentic Blocks Available</CardTitle>
          <CardDescription>
            Agentic workflow blocks are not currently available.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2">
        <div className="p-2 rounded-lg bg-purple-500/10">
          <Sparkles className="h-5 w-5 text-purple-500" />
        </div>
        <div>
          <h3 className="text-lg font-semibold">Agentic Workflows</h3>
          <p className="text-sm text-muted-foreground">
            Advanced blocks with intelligent capabilities
          </p>
        </div>
      </div>

      {/* Block Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {agenticBlocks.map((block) => (
          <AgenticBlockCard
            key={block.type}
            block={block}
            onSelect={onBlockSelect}
            onDragStart={onBlockDragStart}
          />
        ))}
      </div>

      {/* Info */}
      <Card className="bg-muted/50">
        <CardContent className="pt-4">
          <p className="text-xs text-muted-foreground">
            💡 <strong>Tip:</strong> Drag blocks onto the canvas or click to configure.
            Agentic blocks provide self-evaluation, planning, tool selection, and intelligent retrieval.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default AgenticBlockPalette;
