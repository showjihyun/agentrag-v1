'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Activity,
  TrendingUp,
  Clock,
  BarChart3,
  MoreVertical,
  Eye,
  RotateCcw,
  XCircle,
  X,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Execution, ExecutionStats, Agent } from '@/lib/api/agent-builder';

export default function ExecutionMonitorPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [stats, setStats] = useState<ExecutionStats>({
    active: 0,
    total: 0,
    successRate: 0,
    avgDuration: 0,
  });
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterAgent, setFilterAgent] = useState<string>('all');
  const [filterTimeRange, setFilterTimeRange] = useState<string>('24h');

  useEffect(() => {
    loadData();
    // Poll for updates every 5 seconds
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [filterStatus, filterAgent, filterTimeRange]);

  const loadData = async () => {
    try {
      const [executionsData, statsData, agentsData] = await Promise.all([
        agentBuilderAPI.getExecutions({
          ...(filterStatus !== 'all' && { status: filterStatus }),
          ...(filterAgent !== 'all' && { agent_id: filterAgent }),
          time_range: filterTimeRange,
        }),
        agentBuilderAPI.getExecutionStats(),
        agentBuilderAPI.getAgents(),
      ]);

      setExecutions(executionsData.executions);
      setStats(statsData);
      setAgents(agentsData.agents);
    } catch (error) {
      console.error('Failed to load executions:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load executions',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (executionId: string) => {
    router.push(`/agent-builder/executions/${executionId}`);
  };

  const handleReplay = async (executionId: string) => {
    try {
      await agentBuilderAPI.replayExecution(executionId);
      toast({
        title: 'Execution replayed',
        description: 'The execution has been replayed successfully',
      });
      loadData();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to replay execution',
      });
    }
  };

  const handleCancel = async (executionId: string) => {
    try {
      await agentBuilderAPI.cancelExecution(executionId);
      toast({
        title: 'Execution cancelled',
        description: 'The execution has been cancelled',
      });
      loadData();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to cancel execution',
      });
    }
  };

  const handleResetFilters = () => {
    setFilterStatus('all');
    setFilterAgent('all');
    setFilterTimeRange('24h');
  };

  const formatRelativeTime = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header with Stats */}
      <div>
        <h1 className="text-3xl font-bold mb-6">Execution Monitor</h1>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Active Executions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold">{stats.active}</div>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Success Rate</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold">{stats.successRate}%</div>
                <TrendingUp className="h-4 w-4 text-green-500" />
              </div>
              <Progress value={stats.successRate} className="mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Avg Duration</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold">{stats.avgDuration}s</div>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Executions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="text-2xl font-bold">{stats.total}</div>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Label className="text-xs mb-2">Status</Label>
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="running">Running</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="timeout">Timeout</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1 min-w-[200px]">
              <Label className="text-xs mb-2">Agent</Label>
              <Select value={filterAgent} onValueChange={setFilterAgent}>
                <SelectTrigger>
                  <SelectValue placeholder="All agents" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Agents</SelectItem>
                  {agents.map((agent) => (
                    <SelectItem key={agent.id} value={agent.id}>
                      {agent.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex-1 min-w-[200px]">
              <Label className="text-xs mb-2">Time Range</Label>
              <Select value={filterTimeRange} onValueChange={setFilterTimeRange}>
                <SelectTrigger>
                  <SelectValue placeholder="Last 24 hours" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">Last Hour</SelectItem>
                  <SelectItem value="24h">Last 24 Hours</SelectItem>
                  <SelectItem value="7d">Last 7 Days</SelectItem>
                  <SelectItem value="30d">Last 30 Days</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-end">
              <Button variant="outline" onClick={handleResetFilters}>
                <X className="mr-2 h-4 w-4" />
                Reset
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Executions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Executions</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Execution ID</TableHead>
                <TableHead>Agent</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Started</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {executions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground">
                    No executions found
                  </TableCell>
                </TableRow>
              ) : (
                executions.map((execution) => (
                  <TableRow key={execution.id}>
                    <TableCell className="font-mono text-xs">
                      {execution.id.substring(0, 8)}...
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Avatar className="h-6 w-6">
                          <AvatarFallback className="text-xs">
                            {execution.agent_name?.substring(0, 2).toUpperCase() || 'AG'}
                          </AvatarFallback>
                        </Avatar>
                        <span className="text-sm">{execution.agent_name || 'Unknown'}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          execution.status === 'completed'
                            ? 'default'
                            : execution.status === 'running'
                            ? 'secondary'
                            : execution.status === 'failed'
                            ? 'destructive'
                            : 'outline'
                        }
                      >
                        {execution.status === 'running' && (
                          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                        )}
                        {execution.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">
                      {execution.duration_ms ? `${(execution.duration_ms / 1000).toFixed(2)}s` : '-'}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatRelativeTime(execution.started_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewDetails(execution.id)}>
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleReplay(execution.id)}>
                            <RotateCcw className="mr-2 h-4 w-4" />
                            Replay
                          </DropdownMenuItem>
                          {execution.status === 'running' && (
                            <DropdownMenuItem
                              onClick={() => handleCancel(execution.id)}
                              className="text-destructive"
                            >
                              <XCircle className="mr-2 h-4 w-4" />
                              Cancel
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
