'use client';

/**
 * VectorSearchConfig - Vector Search Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Database, Search } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  TextareaField,
  useToolConfig,
} from './common';

// ============================================
// Types
// ============================================

interface VectorSearchConfigData {
  query: string;
  collection_name: string;
  top_k: number;
  score_threshold: number;
}

const DEFAULTS: VectorSearchConfigData = {
  query: '',
  collection_name: 'documents',
  top_k: 5,
  score_threshold: 0.7,
};

// ============================================
// Component
// ============================================

export default function VectorSearchConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<VectorSearchConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Database}
          {...TOOL_HEADER_PRESETS.database}
          title="Vector Search"
          description="Semantic search in Milvus"
          badge="Popular"
        />

        {/* Query */}
        <TextareaField
          label="Search Query"
          value={config.query}
          onChange={(v) => updateField('query', v)}
          placeholder="What are you looking for? Use {{input}} for dynamic queries..."
          rows={3}
          required
          icon={Search}
          hint="The text to search for in your vector database"
          tooltip="벡터 데이터베이스에서 의미적으로 유사한 문서를 검색합니다. {{input}}을 사용하여 동적 쿼리를 만들 수 있습니다."
        />

        {/* Collection Name */}
        <TextField
          label="Collection Name"
          value={config.collection_name}
          onChange={(v) => updateField('collection_name', v)}
          placeholder="documents"
          hint="Milvus collection to search in"
          tooltip="검색할 Milvus 컬렉션 이름입니다."
        />

        {/* Top K */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Number of Results</Label>
            <Badge variant="outline">{config.top_k}</Badge>
          </div>
          <Slider
            value={[config.top_k]}
            onValueChange={([v]) => updateField('top_k', v)}
            min={1}
            max={20}
            step={1}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground">
            Maximum number of results to return (1-20)
          </p>
        </div>

        {/* Score Threshold */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Score Threshold</Label>
            <Badge variant="outline">{config.score_threshold.toFixed(2)}</Badge>
          </div>
          <Slider
            value={[config.score_threshold]}
            onValueChange={([v]) => updateField('score_threshold', v)}
            min={0}
            max={1}
            step={0.05}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Loose (0.0)</span>
            <span>Strict (1.0)</span>
          </div>
        </div>
      </div>
    </TooltipProvider>
  );
}
