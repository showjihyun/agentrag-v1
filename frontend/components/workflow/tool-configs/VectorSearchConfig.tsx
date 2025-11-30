'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Database, Search } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function VectorSearchConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    query: data.query || '',
    collection_name: data.collection_name || 'documents',
    top_k: data.top_k || 5,
    score_threshold: data.score_threshold || 0.7,
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-green-100 dark:bg-green-950">
          <Database className="h-5 w-5 text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h3 className="font-semibold">Vector Search</h3>
          <p className="text-sm text-muted-foreground">Semantic search in Milvus</p>
        </div>
        <Badge variant="secondary" className="ml-auto">Popular</Badge>
      </div>

      {/* Query */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Search className="h-4 w-4" />
          Search Query *
        </Label>
        <Textarea
          placeholder="What are you looking for? Use {{input}} for dynamic queries..."
          value={config.query}
          onChange={(e) => updateConfig('query', e.target.value)}
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          The text to search for in your vector database
        </p>
      </div>

      {/* Collection Name */}
      <div className="space-y-2">
        <Label>Collection Name</Label>
        <Input
          placeholder="documents"
          value={config.collection_name}
          onChange={(e) => updateConfig('collection_name', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Milvus collection to search in
        </p>
      </div>

      {/* Top K */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label>Number of Results</Label>
          <Badge variant="outline">{config.top_k}</Badge>
        </div>
        <Slider
          value={[config.top_k]}
          onValueChange={([v]) => updateConfig('top_k', v)}
          min={1}
          max={20}
          step={1}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          Maximum number of results to return
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
          onValueChange={([v]) => updateConfig('score_threshold', v)}
          min={0}
          max={1}
          step={0.05}
          className="w-full"
        />
        <p className="text-xs text-muted-foreground">
          Minimum similarity score (0-1). Higher = more strict
        </p>
      </div>
    </div>
  );
}
