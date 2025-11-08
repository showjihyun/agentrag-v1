'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { Brain, Database, Clock, Zap, TrendingUp } from 'lucide-react';
import { MemoryBrowser } from './MemoryBrowser';
import { MemorySearch } from './MemorySearch';
import { MemoryTimeline } from './MemoryTimeline';
import { MemorySettings } from './MemorySettings';

interface MemoryDashboardProps {
  agentId: string;
}

interface MemoryStats {
  short_term: {
    count: number;
    size_bytes: number;
    retention_hours: number;
  };
  long_term: {
    count: number;
    size_bytes: number;
  };
  episodic: {
    count: number;
    recent_episodes: number;
  };
  semantic: {
    count: number;
    categories: number;
  };
  total_size_bytes: number;
  compression_ratio: number;
  retrieval_speed_ms: number;
}

export function MemoryDashboard({ agentId }: MemoryDashboardProps) {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [agentId]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getMemoryStats(agentId);
      setStats(data);
    } catch (error) {
      console.error('Failed to load memory stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!stats) {
    return (
      <Card>
        <CardContent className="p-12 text-center text-muted-foreground">
          No memory data available
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Zap className="h-4 w-4" />
              Short-term Memory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.short_term.count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {formatBytes(stats.short_term.size_bytes)}
            </p>
            <p className="text-xs text-muted-foreground">
              {stats.short_term.retention_hours}h retention
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              Long-term Memory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.long_term.count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {formatBytes(stats.long_term.size_bytes)}
            </p>
            <p className="text-xs text-muted-foreground">
              Permanent storage
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Episodic Memory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.episodic.count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.episodic.recent_episodes} recent
            </p>
            <p className="text-xs text-muted-foreground">
              Event sequences
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription className="flex items-center gap-2">
              <Brain className="h-4 w-4" />
              Semantic Memory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.semantic.count}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.semantic.categories} categories
            </p>
            <p className="text-xs text-muted-foreground">
              Knowledge base
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Memory Size</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatBytes(stats.total_size_bytes)}
            </div>
            <Progress value={65} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-1">
              65% of allocated space
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Compression Ratio</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.compression_ratio.toFixed(1)}x
            </div>
            <div className="flex items-center gap-2 mt-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-xs text-muted-foreground">
                Efficient storage
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Retrieval Speed</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.retrieval_speed_ms}ms
            </div>
            <Badge variant="default" className="mt-2">
              Fast
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Views */}
      <Card>
        <CardHeader>
          <CardTitle>Memory Management</CardTitle>
          <CardDescription>
            Browse, search, and manage agent memory
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="browser" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="browser">Browser</TabsTrigger>
              <TabsTrigger value="search">Search</TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
              <TabsTrigger value="settings">Settings</TabsTrigger>
            </TabsList>

            <TabsContent value="browser">
              <MemoryBrowser agentId={agentId} />
            </TabsContent>

            <TabsContent value="search">
              <MemorySearch agentId={agentId} />
            </TabsContent>

            <TabsContent value="timeline">
              <MemoryTimeline agentId={agentId} />
            </TabsContent>

            <TabsContent value="settings">
              <MemorySettings agentId={agentId} onUpdate={loadStats} />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
