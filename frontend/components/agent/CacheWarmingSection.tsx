'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Zap, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface CacheWarmingSectionProps {
  agentId: string;
}

interface WarmingResult {
  agent_id: string;
  queries_warmed: number;
  duration_seconds: number;
  success: boolean;
  errors?: string[];
}

export function CacheWarmingSection({ agentId }: CacheWarmingSectionProps) {
  const [warming, setWarming] = useState(false);
  const [lastResult, setLastResult] = useState<WarmingResult | null>(null);
  const { toast } = useToast();

  const warmCache = async () => {
    setWarming(true);
    setLastResult(null);

    try {
      const response = await fetch(
        `/api/agent-builder/kb/warm/${agentId}`,
        { 
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to warm cache');
      }

      const result: WarmingResult = await response.json();
      setLastResult(result);

      if (result.success) {
        toast({
          title: 'Cache Warmed Successfully',
          description: `Warmed ${result.queries_warmed} queries in ${result.duration_seconds.toFixed(1)}s`,
        });
      } else {
        toast({
          title: 'Cache Warming Completed with Errors',
          description: `Warmed ${result.queries_warmed} queries, but encountered ${result.errors?.length || 0} errors`,
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Cache Warming Failed',
        description: error instanceof Error ? error.message : 'Unknown error occurred',
        variant: 'destructive',
      });
    } finally {
      setWarming(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-5 h-5" />
          Cache Warming
        </CardTitle>
        <CardDescription>
          Pre-cache common queries for faster response times. This will search your knowledge bases
          with frequently used queries and store the results in cache.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <Button 
            onClick={warmCache}
            disabled={warming}
            size="lg"
          >
            {warming ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Warming Cache...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                Warm Cache Now
              </>
            )}
          </Button>

          {lastResult && (
            <Badge 
              variant={lastResult.success ? 'default' : 'destructive'}
              className="flex items-center gap-1"
            >
              {lastResult.success ? (
                <CheckCircle className="w-3 h-3" />
              ) : (
                <AlertCircle className="w-3 h-3" />
              )}
              {lastResult.success ? 'Success' : 'Partial Success'}
            </Badge>
          )}
        </div>

        {lastResult && (
          <div className="bg-muted/50 rounded-lg p-4 space-y-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Queries Warmed</p>
                <p className="text-2xl font-bold">{lastResult.queries_warmed}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Duration</p>
                <p className="text-2xl font-bold">{lastResult.duration_seconds.toFixed(1)}s</p>
              </div>
            </div>

            {lastResult.errors && lastResult.errors.length > 0 && (
              <div className="mt-3">
                <p className="text-sm font-medium text-destructive mb-1">Errors:</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {lastResult.errors.slice(0, 3).map((error, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                      <span>{error}</span>
                    </li>
                  ))}
                  {lastResult.errors.length > 3 && (
                    <li className="text-xs">
                      ... and {lastResult.errors.length - 3} more errors
                    </li>
                  )}
                </ul>
              </div>
            )}
          </div>
        )}

        <div className="text-sm text-muted-foreground space-y-1">
          <p>💡 <strong>Tip:</strong> Run cache warming:</p>
          <ul className="list-disc list-inside ml-4 space-y-1">
            <li>After adding new documents to knowledge bases</li>
            <li>Before expected high-traffic periods</li>
            <li>When you notice slower response times</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}
