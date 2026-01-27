'use client';

import React, { useState } from 'react';
import { ExternalLink, Database, Globe, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface Source {
  content: string;
  metadata: Record<string, any>;
  source_type: string;
  relevance_score: number;
  url?: string;
}

interface SourceRelevanceDisplayProps {
  sources: Source[];
}

export function SourceRelevanceDisplay({ sources }: SourceRelevanceDisplayProps) {
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set([0]));

  const toggleSource = (index: number) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSources(newExpanded);
  };

  const getSourceIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'vector':
        return <Database className="h-4 w-4" />;
      case 'web':
        return <Globe className="h-4 w-4" />;
      default:
        return <FileText className="h-4 w-4" />;
    }
  };

  const getSourceColor = (type: string) => {
    switch (type.toLowerCase()) {
      case 'vector':
        return 'text-blue-600 bg-blue-50 dark:bg-blue-950';
      case 'web':
        return 'text-green-600 bg-green-50 dark:bg-green-950';
      default:
        return 'text-gray-600 bg-gray-50 dark:bg-gray-950';
    }
  };

  const getRelevanceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-blue-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRelevanceLabel = (score: number) => {
    if (score >= 0.8) return 'Highly Relevant';
    if (score >= 0.6) return 'Relevant';
    if (score >= 0.4) return 'Moderately Relevant';
    return 'Low Relevance';
  };

  // Sort sources by relevance score
  const sortedSources = [...sources].sort((a, b) => b.relevance_score - a.relevance_score);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Retrieved Sources</span>
          <Badge variant="outline">{sources.length} sources</Badge>
        </CardTitle>
        <CardDescription>
          Sources ranked by relevance score
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {sortedSources.map((source, index) => {
            const isExpanded = expandedSources.has(index);
            const relevancePercentage = source.relevance_score * 100;

            return (
              <div
                key={index}
                className="border rounded-lg overflow-hidden hover:border-primary/50 transition-colors"
              >
                {/* Source Header */}
                <div
                  className="p-4 cursor-pointer hover:bg-muted/50"
                  onClick={() => toggleSource(index)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      {/* Source Type and Title */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className={cn('flex items-center gap-1', getSourceColor(source.source_type))}>
                          {getSourceIcon(source.source_type)}
                          {source.source_type}
                        </Badge>
                        {source.metadata.title && (
                          <span className="text-sm font-medium">{source.metadata.title}</span>
                        )}
                        {source.url && (
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <ExternalLink className="h-3 w-3" />
                            View
                          </a>
                        )}
                      </div>

                      {/* Relevance Score */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className={cn('font-medium', getRelevanceColor(source.relevance_score))}>
                            {getRelevanceLabel(source.relevance_score)}
                          </span>
                          <span className="text-muted-foreground">
                            {relevancePercentage.toFixed(0)}%
                          </span>
                        </div>
                        <Progress value={relevancePercentage} className="h-2" />
                      </div>

                      {/* Preview */}
                      {!isExpanded && (
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {source.content}
                        </p>
                      )}
                    </div>

                    {/* Expand/Collapse Button */}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="shrink-0"
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                </div>

                {/* Expanded Content */}
                {isExpanded && (
                  <div className="px-4 pb-4 space-y-3">
                    <div className="border-t pt-3">
                      <div className="prose dark:prose-invert prose-sm max-w-none">
                        <p className="text-sm whitespace-pre-wrap">{source.content}</p>
                      </div>
                    </div>

                    {/* Metadata */}
                    {Object.keys(source.metadata).length > 0 && (
                      <div className="border-t pt-3">
                        <div className="text-xs font-medium text-muted-foreground mb-2">
                          Metadata
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          {Object.entries(source.metadata).map(([key, value]) => (
                            <div key={key} className="flex gap-2">
                              <span className="font-medium text-muted-foreground">{key}:</span>
                              <span className="truncate">{String(value)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Summary Stats */}
        <div className="mt-4 grid grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg">
          <div className="text-center">
            <div className="text-lg font-bold">
              {sortedSources.filter(s => s.relevance_score >= 0.8).length}
            </div>
            <div className="text-xs text-muted-foreground">High Relevance</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold">
              {(sortedSources.reduce((sum, s) => sum + s.relevance_score, 0) / sortedSources.length * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-muted-foreground">Avg Relevance</div>
          </div>
          <div className="text-center">
            <div className="text-lg font-bold">
              {new Set(sortedSources.map(s => s.source_type)).size}
            </div>
            <div className="text-xs text-muted-foreground">Source Types</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
