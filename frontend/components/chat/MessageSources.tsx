'use client';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { BookOpen, Globe, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Source {
  id: string;
  document_id?: string;
  document_name?: string;
  text: string;
  score: number;
  metadata?: {
    source?: string;
    kb_id?: string;
    kb_name?: string;
    chunk_index?: number;
  };
}

interface MessageSourcesProps {
  sources: Source[];
  className?: string;
}

export function MessageSources({ sources, className }: MessageSourcesProps) {
  if (!sources || sources.length === 0) return null;

  // Separate KB sources from general sources
  const kbSources = sources.filter(s => 
    s.metadata?.source?.startsWith('kb:') || s.metadata?.kb_id
  );
  const generalSources = sources.filter(s => 
    !s.metadata?.source?.startsWith('kb:') && !s.metadata?.kb_id
  );

  return (
    <div className={cn('space-y-3 mt-3', className)}>
      {/* KB Sources */}
      {kbSources.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Badge variant="default" className="bg-blue-600">
              <BookOpen className="w-3 h-3 mr-1" />
              From Your Documents ({kbSources.length})
            </Badge>
          </div>
          <div className="space-y-2">
            {kbSources.map((source, idx) => (
              <SourceCard 
                key={source.id || idx} 
                source={source}
                highlight={true}
              />
            ))}
          </div>
        </div>
      )}

      {/* General Sources */}
      {generalSources.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Badge variant="secondary">
              <Globe className="w-3 h-3 mr-1" />
              General Knowledge ({generalSources.length})
            </Badge>
          </div>
          <div className="space-y-2">
            {generalSources.map((source, idx) => (
              <SourceCard 
                key={source.id || idx} 
                source={source}
                highlight={false}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

interface SourceCardProps {
  source: Source;
  highlight: boolean;
}

function SourceCard({ source, highlight }: SourceCardProps) {
  const confidence = Math.round(source.score * 100);
  
  return (
    <Card className={cn(
      'transition-all hover:shadow-md',
      highlight && 'border-blue-300 bg-blue-50/50 dark:bg-blue-950/20'
    )}>
      <CardContent className="p-3">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {source.document_name || source.metadata?.kb_name || 'Unknown Document'}
              </p>
              {source.metadata?.kb_name && (
                <p className="text-xs text-muted-foreground">
                  KB: {source.metadata.kb_name}
                </p>
              )}
            </div>
          </div>
          <Badge 
            variant={confidence >= 80 ? 'default' : confidence >= 60 ? 'secondary' : 'outline'}
            className="flex-shrink-0"
          >
            {confidence}%
          </Badge>
        </div>
        
        <p className="text-sm text-muted-foreground line-clamp-2">
          {source.text}
        </p>
        
        {source.metadata?.chunk_index !== undefined && (
          <p className="text-xs text-muted-foreground mt-1">
            Chunk {source.metadata.chunk_index + 1}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
