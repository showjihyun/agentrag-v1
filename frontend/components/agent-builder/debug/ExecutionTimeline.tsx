'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Clock, Zap, AlertCircle, CheckCircle2 } from 'lucide-react';

interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'start' | 'step' | 'tool_call' | 'llm_call' | 'end' | 'error';
  name: string;
  duration?: number;
  details?: string;
  metadata?: Record<string, any>;
}

interface ExecutionTimelineProps {
  events: TimelineEvent[];
  totalDuration?: number;
}

export function ExecutionTimeline({ events, totalDuration }: ExecutionTimelineProps) {
  const getEventIcon = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'start':
        return <Zap className="h-4 w-4 text-blue-500" />;
      case 'end':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getEventColor = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'start':
        return 'border-blue-500';
      case 'end':
        return 'border-green-500';
      case 'error':
        return 'border-red-500';
      case 'llm_call':
        return 'border-purple-500';
      case 'tool_call':
        return 'border-orange-500';
      default:
        return 'border-border';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Execution Timeline</CardTitle>
            <CardDescription>
              Detailed timeline of execution events
            </CardDescription>
          </div>
          {totalDuration && (
            <Badge variant="outline">
              Total: {formatDuration(totalDuration)}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px] w-full">
          <div className="relative space-y-4 pl-8">
            {/* Timeline line */}
            <div className="absolute left-4 top-0 bottom-0 w-px bg-border" />

            {events.map((event, index) => (
              <div key={event.id} className="relative">
                {/* Timeline dot */}
                <div className="absolute -left-8 top-2 flex items-center justify-center">
                  <div className={`rounded-full border-2 bg-background p-1 ${getEventColor(event.type)}`}>
                    {getEventIcon(event.type)}
                  </div>
                </div>

                {/* Event card */}
                <div className={`border rounded-lg p-3 space-y-2 ${getEventColor(event.type)}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm">{event.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {event.type}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {formatTimestamp(event.timestamp)}
                    </div>
                  </div>

                  {event.duration && (
                    <div className="text-xs text-muted-foreground">
                      Duration: {formatDuration(event.duration)}
                    </div>
                  )}

                  {event.details && (
                    <div className="text-sm text-muted-foreground">
                      {event.details}
                    </div>
                  )}

                  {event.metadata && Object.keys(event.metadata).length > 0 && (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                        Metadata
                      </summary>
                      <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-x-auto">
                        {JSON.stringify(event.metadata, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
