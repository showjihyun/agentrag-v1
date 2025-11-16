'use client';

import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  Database,
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface KBStats {
  cache_hit_rate: number;
  avg_search_time: number;
  error_rate: number;
  total_searches: number;
  cache_size: number;
  profiles: Array<{
    kb_id: string;
    kb_name: string;
    avg_search_time: number;
    cache_hit_rate: number;
    total_searches: number;
  }>;
}

export default function KBMonitoringPage() {
  const { data: optimizerStats, isLoading: optimizerLoading, refetch: refetchOptimizer } = useQuery<KBStats>({
    queryKey: ['kb-optimizer-stats'],
    queryFn: async () => {
      const res = await fetch('/api/agent-builder/kb/optimizer/stats');
      if (!res.ok) throw new Error('Failed to fetch optimizer stats');
      return res.json();
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: warmerStats, isLoading: warmerLoading, refetch: refetchWarmer } = useQuery({
    queryKey: ['kb-warmer-stats'],
    queryFn: async () => {
      const res = await fetch('/api/agent-builder/kb/warmer/stats');
      if (!res.ok) throw new Error('Failed to fetch warmer stats');
      return res.json();
    },
    refetchInterval: 30000,
  });

  const handleRefresh = () => {
    refetchOptimizer();
    refetchWarmer();
  };

  if (optimizerLoading || warmerLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">KB Performance Monitoring</h1>
          <p className="text-muted-foreground mt-1">
            Real-time knowledge base search performance metrics
          </p>
        </div>
        <Button onClick={handleRefresh} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Cache Hit Rate"
          value={`${((optimizerStats?.cache_hit_rate || 0) * 100).toFixed(1)}%`}
          target={70}
          current={(optimizerStats?.cache_hit_rate || 0) * 100}
          icon={<Activity className="w-4 h-4" />}
          trend="up"
        />
        
        <MetricCard
          title="Avg Search Time"
          value={`${((optimizerStats?.avg_search_time || 0) * 1000).toFixed(0)}ms`}
          target={300}
          current={(optimizerStats?.avg_search_time || 0) * 1000}
          icon={<Clock className="w-4 h-4" />}
          trend="down"
          inverse={true}
        />
        
        <MetricCard
          title="Error Rate"
          value={`${((optimizerStats?.error_rate || 0) * 100).toFixed(2)}%`}
          target={1}
          current={(optimizerStats?.error_rate || 0) * 100}
          icon={<AlertCircle className="w-4 h-4" />}
          trend="down"
          inverse={true}
        />
        
        <MetricCard
          title="Total Searches"
          value={optimizerStats?.total_searches?.toLocaleString() || '0'}
          icon={<Database className="w-4 h-4" />}
        />
      </div>

      {/* Cache Warmer Stats */}
      {warmerStats && (
        <Card>
          <CardHeader>
            <CardTitle>Cache Warmer Status</CardTitle>
            <CardDescription>Automatic cache warming statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Warmed</p>
                <p className="text-2xl font-bold">{warmerStats.total_warmed || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Last Run</p>
                <p className="text-2xl font-bold">
                  {warmerStats.last_run ? new Date(warmerStats.last_run).toLocaleTimeString() : 'Never'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Success Rate</p>
                <p className="text-2xl font-bold">
                  {warmerStats.success_rate ? `${(warmerStats.success_rate * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Avg Duration</p>
                <p className="text-2xl font-bold">
                  {warmerStats.avg_duration ? `${warmerStats.avg_duration.toFixed(1)}s` : 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KB Profiles Table */}
      {optimizerStats?.profiles && optimizerStats.profiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Knowledge Base Profiles</CardTitle>
            <CardDescription>Performance breakdown by knowledge base</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">Knowledge Base</th>
                    <th className="text-right py-3 px-4">Searches</th>
                    <th className="text-right py-3 px-4">Avg Time</th>
                    <th className="text-right py-3 px-4">Cache Hit Rate</th>
                  </tr>
                </thead>
                <tbody>
                  {optimizerStats.profiles.map((profile) => (
                    <tr key={profile.kb_id} className="border-b hover:bg-muted/50">
                      <td className="py-3 px-4">
                        <div>
                          <p className="font-medium">{profile.kb_name || 'Unknown KB'}</p>
                          <p className="text-xs text-muted-foreground">{profile.kb_id}</p>
                        </div>
                      </td>
                      <td className="text-right py-3 px-4">
                        {profile.total_searches?.toLocaleString() || 0}
                      </td>
                      <td className="text-right py-3 px-4">
                        <Badge variant={profile.avg_search_time < 0.3 ? 'default' : 'secondary'}>
                          {(profile.avg_search_time * 1000).toFixed(0)}ms
                        </Badge>
                      </td>
                      <td className="text-right py-3 px-4">
                        <Badge variant={profile.cache_hit_rate > 0.7 ? 'default' : 'secondary'}>
                          {(profile.cache_hit_rate * 100).toFixed(1)}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string;
  target?: number;
  current?: number;
  icon: React.ReactNode;
  trend?: 'up' | 'down';
  inverse?: boolean; // If true, lower is better
}

function MetricCard({ title, value, target, current, icon, trend, inverse }: MetricCardProps) {
  const isGood = target && current !== undefined
    ? inverse 
      ? current <= target 
      : current >= target
    : undefined;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {target !== undefined && (
          <div className="flex items-center gap-2 mt-2">
            {isGood !== undefined && (
              <>
                {isGood ? (
                  <TrendingUp className="w-4 h-4 text-green-600" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                )}
              </>
            )}
            <p className={cn(
              'text-xs',
              isGood ? 'text-green-600' : 'text-red-600'
            )}>
              Target: {inverse ? '≤' : '≥'} {target}{title.includes('Rate') ? '%' : title.includes('Time') ? 'ms' : ''}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
