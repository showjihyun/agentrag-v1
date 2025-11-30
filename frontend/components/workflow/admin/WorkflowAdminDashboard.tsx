'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Activity,
  RefreshCw,
  Trash2,
  Play,
  XCircle,
  TrendingUp,
  Server,
} from 'lucide-react';

interface SystemStats {
  workflows: { total: number };
  executions: {
    total: number;
    last_24h: number;
    failed_24h: number;
    success_rate: number;
  };
  dlq: { pending: number; total: number };
  circuit_breakers: { total: number; open: number };
}

interface DLQEntry {
  id: string;
  execution_id: string;
  workflow_id: string;
  error_message: string;
  error_type: string;
  status: string;
  retry_count: number;
  max_retries: number;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function WorkflowAdminDashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [dlqEntries, setDlqEntries] = useState<DLQEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/api/agent-builder/admin/stats/overview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        setStats(await response.json());
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchDLQ = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`${API_BASE}/api/agent-builder/admin/dlq/entries?limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setDlqEntries(data.entries || []);
      }
    } catch (error) {
      console.error('Failed to fetch DLQ:', error);
    }
  };

  const retryDLQEntry = async (entryId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`${API_BASE}/api/agent-builder/admin/dlq/entries/${entryId}/retry`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchDLQ();
    } catch (error) {
      console.error('Failed to retry:', error);
    }
  };

  const resolveDLQEntry = async (entryId: string, discard: boolean = false) => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(
        `${API_BASE}/api/agent-builder/admin/dlq/entries/${entryId}/resolve?discard=${discard}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      fetchDLQ();
    } catch (error) {
      console.error('Failed to resolve:', error);
    }
  };

  const runCleanup = async () => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`${API_BASE}/api/agent-builder/admin/maintenance/cleanup`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchStats();
      fetchDLQ();
    } catch (error) {
      console.error('Failed to run cleanup:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchStats(), fetchDLQ()]);
      setLoading(false);
    };
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">워크플로우 관리자 대시보드</h1>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => { fetchStats(); fetchDLQ(); }}>
            <RefreshCw className="h-4 w-4 mr-2" />
            새로고침
          </Button>
          <Button variant="outline" onClick={runCleanup}>
            <Trash2 className="h-4 w-4 mr-2" />
            정리 실행
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="dlq">
            Dead Letter Queue
            {dlqEntries.filter(e => e.status === 'pending').length > 0 && (
              <Badge variant="destructive" className="ml-2">
                {dlqEntries.filter(e => e.status === 'pending').length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="circuit-breakers">서킷 브레이커</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">총 워크플로우</CardTitle>
                <Server className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.workflows.total || 0}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">24시간 실행</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.executions.last_24h || 0}</div>
                <p className="text-xs text-muted-foreground">
                  총 {stats?.executions.total || 0}회
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">성공률</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {stats?.executions.success_rate || 100}%
                </div>
                <p className="text-xs text-muted-foreground">
                  실패: {stats?.executions.failed_24h || 0}건
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">DLQ 대기</CardTitle>
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats?.dlq.pending || 0}</div>
                <p className="text-xs text-muted-foreground">
                  총 {stats?.dlq.total || 0}건
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Circuit Breaker Status */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">서킷 브레이커 상태</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span>정상: {(stats?.circuit_breakers.total || 0) - (stats?.circuit_breakers.open || 0)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span>열림: {stats?.circuit_breakers.open || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dlq" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Dead Letter Queue</CardTitle>
            </CardHeader>
            <CardContent>
              {dlqEntries.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  대기 중인 항목이 없습니다
                </p>
              ) : (
                <div className="space-y-3">
                  {dlqEntries.map((entry) => (
                    <div
                      key={entry.id}
                      className="flex items-center justify-between p-4 border rounded-lg"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant={
                              entry.status === 'pending'
                                ? 'destructive'
                                : entry.status === 'resolved'
                                ? 'default'
                                : 'secondary'
                            }
                          >
                            {entry.status}
                          </Badge>
                          <span className="text-sm font-medium">{entry.error_type}</span>
                        </div>
                        <p className="text-sm text-muted-foreground truncate max-w-md">
                          {entry.error_message}
                        </p>
                        <div className="flex items-center gap-4 mt-1 text-xs text-muted-foreground">
                          <span>재시도: {entry.retry_count}/{entry.max_retries}</span>
                          <span>
                            <Clock className="h-3 w-3 inline mr-1" />
                            {new Date(entry.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                      {entry.status === 'pending' && (
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => retryDLQEntry(entry.id)}
                            disabled={entry.retry_count >= entry.max_retries}
                          >
                            <Play className="h-4 w-4 mr-1" />
                            재시도
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => resolveDLQEntry(entry.id, true)}
                          >
                            <XCircle className="h-4 w-4 mr-1" />
                            무시
                          </Button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="circuit-breakers">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">서킷 브레이커 상세</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">
                서킷 브레이커 상세 정보는 /api/agent-builder/admin/health/circuit-breakers 에서 확인할 수 있습니다.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default WorkflowAdminDashboard;
