'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Activity,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Zap,
  Plus,
  Play,
  Layers,
  GitBranch,
  Database,
  ArrowRight,
  Users,
  MessageSquare,
  Sparkles,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { DarkModeOptimizedChart } from '@/components/agent-builder/DarkModeOptimizedChart';
import { AccessibleCard } from '@/components/agent-builder/AccessibleCard';
import { SkipToContent } from '@/components/agent-builder/SkipToContent';
import { KeyboardShortcutsDialog } from '@/components/agent-builder/KeyboardShortcutsDialog';
import { EmptyState } from '@/components/agent-builder/EmptyState';
import { ProgressiveLoader } from '@/components/agent-builder/ProgressiveLoader';
import { MarketplaceIntegration } from '@/components/agent-builder/MarketplaceIntegration';
import { ExecutionMonitor } from '@/components/agent-builder/ExecutionMonitor';
import { Toaster } from '@/components/ui/toaster';
import { toast } from 'sonner';

// Memoized components for performance
const StatsCard = React.memo(({ stats }: { stats: any }) => {
  const totalResources = React.useMemo(() => {
    return (
      (stats?.resources?.agents || stats?.total_agents || 0) +
      (stats?.resources?.blocks || 0) +
      (stats?.resources?.workflows || stats?.total_workflows || 0)
    );
  }, [stats]);

  const formatDuration = React.useCallback((seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  }, []);

  const executions = stats?.executions || {};
  const resources = stats?.resources || {};
  const successRate = executions.success_rate ?? stats?.success_rate ?? 0;

  return (
    <>
      <AccessibleCard
        title="Total Executions"
        value={executions.total ?? stats?.total_executions ?? 0}
        subtitle={`${executions.last_24h ?? 0} in last 24h`}
        icon={<Activity className="h-4 w-4" />}
        ariaLabel={`Total executions: ${executions.total ?? stats?.total_executions ?? 0}, with ${executions.last_24h ?? 0} in the last 24 hours`}
      />
      <AccessibleCard
        title="Success Rate"
        value={`${successRate}%`}
        subtitle={`${executions.running ?? 0} currently running`}
        icon={<TrendingUp className="h-4 w-4" />}
        trend={successRate >= 90 ? 'up' : successRate >= 70 ? 'neutral' : 'down'}
        ariaLabel={`Success rate: ${successRate}%, with ${executions.running ?? 0} currently running`}
      />
      <AccessibleCard
        title="Avg Duration"
        value={formatDuration(executions.avg_duration_seconds ?? 0)}
        subtitle="per execution"
        icon={<Clock className="h-4 w-4" />}
        ariaLabel={`Average duration: ${formatDuration(executions.avg_duration_seconds ?? 0)} per execution`}
      />
      <AccessibleCard
        title="Resources"
        value={totalResources}
        subtitle={`${resources.agents ?? stats?.total_agents ?? 0} agents, ${resources.blocks ?? 0} blocks`}
        icon={<Zap className="h-4 w-4" />}
        ariaLabel={`Total resources: ${totalResources}`}
      />
    </>
  );
});
StatsCard.displayName = 'StatsCard';

const ActivityItem = React.memo(({ activity, onClick }: { activity: any; onClick: (id: string) => void }) => {
  const formatTimeAgo = React.useCallback((dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  }, []);

  const formatDuration = React.useCallback((seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  }, []);

  const getStatusColor = React.useCallback((status: string) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      case 'running': return 'text-blue-500';
      default: return 'text-gray-500';
    }
  }, []);

  const getStatusIcon = React.useCallback((status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="h-4 w-4" />;
      case 'failed': return <AlertCircle className="h-4 w-4" />;
      case 'running': return <Activity className="h-4 w-4 animate-pulse" />;
      default: return <Clock className="h-4 w-4" />;
    }
  }, []);

  const handleClick = React.useCallback(() => {
    onClick(activity.id);
  }, [activity.id, onClick]);

  return (
    <div
      className="flex items-start gap-3 p-3 rounded-lg border hover:bg-accent cursor-pointer transition-colors"
      onClick={handleClick}
    >
      <div className={`mt-0.5 ${getStatusColor(activity.status)}`}>
        {getStatusIcon(activity.status)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">
          {activity.agent_name}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <Badge
            variant={
              activity.status === 'completed'
                ? 'default'
                : activity.status === 'failed'
                ? 'destructive'
                : 'secondary'
            }
            className="text-xs"
          >
            {activity.status}
          </Badge>
          {activity.duration && (
            <span className="text-xs text-muted-foreground">
              {formatDuration(activity.duration)}
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {formatTimeAgo(activity.started_at)}
        </p>
      </div>
    </div>
  );
});
ActivityItem.displayName = 'ActivityItem';

export default function AgentBuilderDashboard() {
  const router = useRouter();

  const formatTimeAgo = React.useCallback((dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  }, []);

  const { data: stats, isLoading: statsLoading, error: statsError } = useQuery({
    queryKey: ['agent-builder-stats'],
    queryFn: () => agentBuilderAPI.getDashboardStats(),
    refetchInterval: 30000,
    staleTime: 20000,
    placeholderData: (previousData) => previousData, // Keep previous data while loading
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  });

  // Show error toast
  React.useEffect(() => {
    if (statsError) {
      toast.error('Failed to load dashboard statistics', {
        action: {
          label: 'Retry',
          onClick: () => window.location.reload(),
        },
      });
    }
  }, [statsError]);

  const { data: recentActivity, isLoading: activityLoading } = useQuery({
    queryKey: ['agent-builder-activity'],
    queryFn: () => agentBuilderAPI.getRecentActivity(10),
    staleTime: 10000,
  });

  const { data: favoriteAgents, isLoading: favoritesLoading } = useQuery({
    queryKey: ['agent-builder-favorites'],
    queryFn: () => agentBuilderAPI.getFavoriteAgents(5),
    staleTime: 30000,
  });

  const { data: trendData, isLoading: trendLoading } = useQuery({
    queryKey: ['agent-builder-trend'],
    queryFn: () => agentBuilderAPI.getExecutionTrend(7),
    staleTime: 60000,
  });

  const { data: systemStatus } = useQuery({
    queryKey: ['agent-builder-status'],
    queryFn: () => agentBuilderAPI.getSystemStatus(),
    refetchInterval: 60000,
    staleTime: 50000,
  });

  // Memoized callbacks
  const handleActivityClick = React.useCallback((executionId: string) => {
    router.push(`/agent-builder/executions/${executionId}`);
  }, [router]);

  const handleViewWorkflows = React.useCallback(() => {
    router.push('/agent-builder/workflows');
  }, [router]);

  const handleAddKnowledgebase = React.useCallback(() => {
    router.push('/agent-builder/knowledgebases');
  }, [router]);

  return (
    <>
      <Toaster />
      <SkipToContent />
      <div className="container mx-auto p-6 space-y-6" id="main-content" tabIndex={-1}>
        {/* Header - Enhanced Visual Hierarchy */}
        <header className="flex items-center justify-between mb-2" role="banner">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              Agent Builder Dashboard
            </h1>
            <p className="text-muted-foreground mt-2 text-lg">
              Overview of your agents, workflows, and executions
            </p>
          </div>
          <div className="flex gap-3">
            <KeyboardShortcutsDialog />
            <Button 
              size="lg"
              onClick={() => router.push('/agent-builder/agentflows/new')}
              aria-label="Create a new agentflow"
              className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all"
            >
              <Plus className="mr-2 h-5 w-5" aria-hidden="true" />
              Create Agentflow
            </Button>
          </div>
        </header>

        {/* System Status Banner */}
        {systemStatus?.status === 'warning' && (
          <Card 
            className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950/50"
            role="alert"
            aria-live="polite"
          >
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <AlertCircle 
                  className="h-5 w-5 text-yellow-600 dark:text-yellow-400" 
                  aria-hidden="true"
                />
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  <span className="sr-only">Warning: </span>
                  {systemStatus.stuck_executions} execution(s) have been running for over an hour
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Stats Cards */}
        <section aria-label="Statistics Overview">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {statsLoading && !stats ? (
              <ProgressiveLoader type="stats" count={4} showShimmer={true} />
            ) : (
              <StatsCard stats={stats} />
            )}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Execution Trend Chart */}
          <Card className="lg:col-span-2" role="region" aria-label="Execution Trend Chart">
            <CardHeader>
              <CardTitle id="trend-chart-title">Execution Trend (7 days)</CardTitle>
              <CardDescription>Daily execution statistics</CardDescription>
            </CardHeader>
            <CardContent>
              {trendLoading ? (
                <Skeleton className="h-[300px] w-full" aria-label="Loading chart data" />
              ) : (
                <div aria-labelledby="trend-chart-title" role="img" aria-label="Line chart showing execution trends over the last 7 days">
                  <DarkModeOptimizedChart data={trendData?.trend || []} />
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions - Enhanced Visual Hierarchy */}
          <Card role="region" aria-label="Quick Actions" className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                  <Zap className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle className="text-lg">Quick Actions</CardTitle>
                  <CardDescription>빠른 시작</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <nav aria-label="Quick action buttons">
                <div className="space-y-3">
                  {/* Primary Actions - Flows with enhanced styling */}
                  <Button
                    size="lg"
                    className="w-full justify-start bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 hover:from-purple-700 hover:via-blue-700 hover:to-cyan-700 text-white shadow-md hover:shadow-lg transition-all"
                    onClick={() => router.push('/agent-builder/wizard')}
                    aria-label="Open workflow creation wizard"
                  >
                    <Sparkles className="mr-3 h-5 w-5" aria-hidden="true" />
                    <div className="flex flex-col items-start">
                      <span className="font-semibold">마법사로 시작하기</span>
                      <span className="text-xs opacity-90">Step-by-step Guide</span>
                    </div>
                  </Button>
                  <Button
                    size="lg"
                    className="w-full justify-start bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white shadow-md hover:shadow-lg transition-all"
                    onClick={() => router.push('/agent-builder/agentflows/new')}
                    aria-label="Create a new Agentflow"
                  >
                    <Users className="mr-3 h-5 w-5" aria-hidden="true" />
                    <div className="flex flex-col items-start">
                      <span className="font-semibold">새 Agentflow</span>
                      <span className="text-xs opacity-90">Multi-Agent System</span>
                    </div>
                  </Button>
                  <Button
                    size="lg"
                    className="w-full justify-start bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-md hover:shadow-lg transition-all"
                    onClick={() => router.push('/agent-builder/chatflows/new')}
                    aria-label="Create a new Chatflow"
                  >
                    <MessageSquare className="mr-3 h-5 w-5" aria-hidden="true" />
                    <div className="flex flex-col items-start">
                      <span className="font-semibold">새 Chatflow</span>
                      <span className="text-xs opacity-90">Conversational AI</span>
                    </div>
                  </Button>
                  
                  <div className="border-t my-4" />
                  
                  {/* Secondary Actions with improved styling */}
                  <Button
                    variant="outline"
                    className="w-full justify-start hover:bg-purple-50 dark:hover:bg-purple-950/20 hover:border-purple-300 dark:hover:border-purple-700 transition-all"
                    onClick={() => router.push('/agent-builder/agents/new')}
                    aria-label="Create a new agent"
                  >
                    <Layers className="mr-2 h-4 w-4 text-purple-600 dark:text-purple-400" aria-hidden="true" />
                    Create Agent
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start hover:bg-blue-50 dark:hover:bg-blue-950/20 hover:border-blue-300 dark:hover:border-blue-700 transition-all"
                    onClick={handleViewWorkflows}
                    aria-label="Design a new workflow"
                  >
                    <GitBranch className="mr-2 h-4 w-4 text-blue-600 dark:text-blue-400" aria-hidden="true" />
                    Design Workflow
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full justify-start hover:bg-green-50 dark:hover:bg-green-950/20 hover:border-green-300 dark:hover:border-green-700 transition-all"
                    onClick={handleAddKnowledgebase}
                    aria-label="Add a new knowledgebase"
                  >
                    <Database className="mr-2 h-4 w-4 text-green-600 dark:text-green-400" aria-hidden="true" />
                    Add Knowledgebase
                  </Button>
                </div>
              </nav>
            </CardContent>
          </Card>
        </div>

      {/* Marketplace Integration */}
      <section aria-label="Template Marketplace">
        <MarketplaceIntegration 
          maxItems={6}
          onItemInstall={(item) => {
            toast.success(`${item.name} 설치 완료`, {
              description: '새로운 템플릿이 성공적으로 설치되었습니다',
            });
          }}
        />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Favorite Agents */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Frequently Used Agents</CardTitle>
                <CardDescription>Your most active agents</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/agent-builder/agents')}
              >
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {favoritesLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : favoriteAgents?.agents.length === 0 ? (
              <EmptyState
                icon={<Layers className="h-16 w-16" />}
                title="No agents yet"
                description="Create your first agent to start building intelligent workflows and automations."
                action={{
                  label: 'Create Agent',
                  onClick: () => router.push('/agent-builder/agents/new'),
                  icon: Plus,
                }}
                secondaryAction={{
                  label: 'Browse Templates',
                  onClick: () => router.push('/agent-builder/marketplace'),
                }}
                links={[
                  { label: 'View Tutorial', href: '/docs/tutorial' },
                  { label: 'API Documentation', href: '/docs/api' },
                ]}
              />
            ) : (
              <ScrollArea className="h-[300px]">
                <div className="space-y-3">
                  {favoriteAgents?.agents.map((agent: any) => (
                    <div
                      key={agent.id}
                      className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent cursor-pointer transition-colors"
                      onClick={() => router.push(`/agent-builder/agents/${agent.id}`)}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium truncate">{agent.name}</p>
                          <Badge variant="secondary" className="text-xs">
                            {agent.execution_count} runs
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground truncate">
                          {agent.description || 'No description'}
                        </p>
                        {agent.last_execution && (
                          <div className="flex items-center gap-1 mt-1">
                            <span className={`text-xs ${
                              agent.last_status === 'completed' ? 'text-green-500' :
                              agent.last_status === 'failed' ? 'text-red-500' :
                              agent.last_status === 'running' ? 'text-blue-500' :
                              'text-gray-500'
                            }`}>
                              {agent.last_status === 'completed' ? <CheckCircle2 className="h-4 w-4" /> :
                               agent.last_status === 'failed' ? <AlertCircle className="h-4 w-4" /> :
                               agent.last_status === 'running' ? <Activity className="h-4 w-4 animate-pulse" /> :
                               <Clock className="h-4 w-4" />}
                            </span>
                            <span className="text-xs text-muted-foreground">
                              {formatTimeAgo(agent.last_execution)}
                            </span>
                          </div>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/agent-builder/agents/${agent.id}/test`);
                        }}
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest executions</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push('/agent-builder/executions')}
              >
                View All
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {activityLoading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : recentActivity?.activities.length === 0 ? (
              <EmptyState
                icon={<Activity className="h-16 w-16" />}
                title="No recent activity"
                description="Your agent executions will appear here once you start running agents."
                action={{
                  label: 'Run an Agent',
                  onClick: () => router.push('/agent-builder/agents'),
                  icon: Play,
                }}
              />
            ) : (
              <ScrollArea className="h-[300px]">
                <div className="space-y-3">
                  {recentActivity?.activities.map((activity: any) => (
                    <ActivityItem
                      key={activity.id}
                      activity={activity}
                      onClick={handleActivityClick}
                    />
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Real-time Execution Monitor */}
      {stats?.executions?.running > 0 && (
        <section aria-label="Real-time Execution Monitor">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-500 animate-pulse" />
                실시간 실행 모니터링
              </CardTitle>
              <CardDescription>
                현재 실행 중인 워크플로우를 실시간으로 모니터링합니다
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ExecutionMonitor 
                autoRefresh={true}
                onExecutionComplete={(execution) => {
                  toast.success('실행 완료', {
                    description: `${execution.flowName} 실행이 완료되었습니다`,
                  });
                }}
              />
            </CardContent>
          </Card>
        </section>
      )}
      </div>
    </>
  );
}
