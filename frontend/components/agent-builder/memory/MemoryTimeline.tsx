'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { Clock, Circle } from 'lucide-react';

interface MemoryTimelineProps {
  agentId: string;
}

interface TimelineEvent {
  id: string;
  type: 'created' | 'accessed' | 'updated' | 'consolidated';
  memory_id: string;
  memory_content: string;
  memory_type: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export function MemoryTimeline({ agentId }: MemoryTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTimeline();
  }, [agentId]);

  const loadTimeline = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getMemoryTimeline(agentId, {
        limit: 100,
      });
      setEvents(data.events || []);
    } catch (error) {
      console.error('Failed to load timeline:', error);
    } finally {
      setLoading(false);
    }
  };

  const getEventColor = (type: string) => {
    const colors: Record<string, string> = {
      created: 'bg-green-500',
      accessed: 'bg-blue-500',
      updated: 'bg-yellow-500',
      consolidated: 'bg-purple-500',
    };
    return colors[type] || 'bg-gray-500';
  };

  const getEventLabel = (type: string) => {
    const labels: Record<string, string> = {
      created: 'Created',
      accessed: 'Accessed',
      updated: 'Updated',
      consolidated: 'Consolidated',
    };
    return labels[type] || type;
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-muted-foreground">
          <Clock className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>No memory events yet</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <ScrollArea className="h-[500px]">
      <div className="relative pl-8 space-y-6">
        {/* Timeline line */}
        <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-border" />

        {events.map((event, index) => (
          <div key={event.id} className="relative">
            {/* Timeline dot */}
            <div
              className={`absolute left-[-1.75rem] top-2 w-3 h-3 rounded-full ${getEventColor(
                event.type
              )} border-2 border-background`}
            />

            <Card>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{getEventLabel(event.type)}</Badge>
                    <Badge variant="secondary" className="text-xs">
                      {event.memory_type}
                    </Badge>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>
                <p className="text-sm line-clamp-2">{event.memory_content}</p>
                {event.metadata && Object.keys(event.metadata).length > 0 && (
                  <details className="mt-2">
                    <summary className="text-xs text-muted-foreground cursor-pointer">
                      View metadata
                    </summary>
                    <pre className="text-xs mt-2 p-2 bg-muted rounded-md overflow-auto">
                      {JSON.stringify(event.metadata, null, 2)}
                    </pre>
                  </details>
                )}
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
