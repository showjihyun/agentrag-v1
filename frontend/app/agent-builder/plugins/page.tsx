'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Puzzle,
  Plus,
  Settings,
  Activity,
  Trash2,
  RefreshCw,
  Upload,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
  Brain,
  Search,
  Filter,
  Loader2,
  Eye,
  BarChart3,
  Terminal,
  MoreVertical,
  Play,
  Pause,
  Download,
} from 'lucide-react';
import { toast } from 'sonner';
import { usePluginStore } from '@/lib/stores/plugin-store';
import { usePluginWebSocket } from '@/hooks/usePluginWebSocket';
import { PluginConfigWizard, PluginConfigSchema } from '@/components/agent-builder/plugins/PluginConfigWizard';
import { PluginInstallationWizard } from '@/components/agent-builder/plugins/PluginInstallationWizard';
import { PluginDetailMonitoring } from '@/components/agent-builder/plugins/PluginDetailMonitoring';
import { ExecutionLogViewer } from '@/components/agent-builder/plugins/ExecutionLogViewer';

interface AgentPlugin {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
  version: string;
  created_at: string;
  last_used: string;
  execution_count: number;
  success_rate: number;
}

interface SystemHealth {
  status: 'healthy' | 'warning' | 'error';
  active_plugins: number;
  total_executions: number;
  average_response_time: number;
  error_rate: number;
}

export default function AgentPluginsPage() {
  // Zustand 스토어 사용
  const {
    plugins,
    customAgents,
    systemHealth,
    loading,
    searchTerm,
    filterStatus,
    error,
    setSearchTerm,
    setFilterStatus,
    loadPlugins,
    loadCustomAgents,
    loadSystemHealth,
    registerAsPlugin,
    unregisterPlugin,
    refreshPlugin,
    getFilteredPlugins,
    getFilteredCustomAgents,
  } = usePluginStore();

  // WebSocket 실시간 업데이트
  const {
    isConnected: wsConnected,
    connectionError: wsError,
  } = usePluginWebSocket({
    userId: 'current-user',
    autoReconnect: true
  });

  // 로컬 상태
  const [selectedPlugin, setSelectedPlugin] = useState<AgentPlugin | null>(null);
  const [showInstallDialog, setShowInstallDialog] = useState(false);
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showMonitoringDialog, setShowMonitoringDialog] = useState(false);
  const [showLogsDialog, setShowLogsDialog] = useState(false);
  const [configSchema, setConfigSchema] = useState<PluginConfigSchema | null>(null);

  // 초기 데이터 로드
  useEffect(() => {
    const loadData = async () => {
      await Promise.all([
        loadPlugins(),
        loadCustomAgents(),
        loadSystemHealth(),
      ]);
    };
    loadData();
  }, [loadPlugins, loadCustomAgents, loadSystemHealth]);

  // 에러 토스트 표시
  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  // WebSocket 에러 토스트 표시
  useEffect(() => {
    if (wsError) {
      toast.error(`실시간 연결 오류: ${wsError}`);
    }
  }, [wsError]);

  // 플러그인 설정 스키마 로딩
  const loadConfigSchema = async (pluginId: string) => {
    try {
      const response = await fetch(`/api/agent-builder/plugins/${pluginId}/config-schema`);
      const schema = await response.json();
      setConfigSchema(schema);
    } catch (error) {
      toast.error('Failed to load plugin configuration schema');
    }
  };

  // 플러그인 설치 완료 핸들러
  const handleInstallComplete = (pluginId: string) => {
    toast.success('Plugin installed successfully');
    setShowInstallDialog(false);
    loadPlugins();
  };

  // 플러그인 설치 에러 핸들러
  const handleInstallError = (error: string) => {
    toast.error(`Installation failed: ${error}`);
  };

  // 플러그인 설정 저장
  const handleConfigSave = async (values: Record<string, any>) => {
    if (!selectedPlugin) return;
    
    try {
      await fetch(`/api/agent-builder/plugins/${selectedPlugin.agent_id}/config`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      
      toast.success('Configuration saved successfully');
      setShowConfigDialog(false);
      loadPlugins();
    } catch (error) {
      toast.error('Failed to save configuration');
      throw error;
    }
  };

  // 플러그인 설정 검증
  const handleConfigValidate = async (values: Record<string, any>) => {
    if (!selectedPlugin) return {};
    
    try {
      const response = await fetch(`/api/agent-builder/plugins/${selectedPlugin.agent_id}/validate-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values),
      });
      
      const result = await response.json();
      return result.errors || {};
    } catch (error) {
      console.error('Config validation error:', error);
      return {};
    }
  };

  // 플러그인 등록 핸들러
  const handleRegisterAsPlugin = async (agentId: string) => {
    try {
      await registerAsPlugin(agentId);
      toast.success('에이전트가 플러그인으로 등록되었습니다.');
    } catch (error) {
      toast.error('에이전트 등록에 실패했습니다.');
    }
  };

  // 플러그인 등록 해제 핸들러
  const handleUnregisterPlugin = async (agentId: string) => {
    try {
      await unregisterPlugin(agentId);
      toast.success('플러그인 등록이 해제되었습니다.');
    } catch (error) {
      toast.error('플러그인 등록 해제에 실패했습니다.');
    }
  };

  // 플러그인 새로고침 핸들러
  const handleRefreshPlugin = async (agentId: string) => {
    try {
      await refreshPlugin(agentId);
      toast.success('플러그인이 새로고침되었습니다.');
    } catch (error) {
      toast.error('플러그인 새로고침에 실패했습니다.');
    }
  };

  // 플러그인 설정 다이얼로그 열기
  const openConfigDialog = async (plugin: AgentPlugin) => {
    setSelectedPlugin(plugin);
    await loadConfigSchema(plugin.agent_id);
    setShowConfigDialog(true);
  };

  // 모니터링 다이얼로그 열기
  const openMonitoringDialog = (plugin: AgentPlugin) => {
    setSelectedPlugin(plugin);
    setShowMonitoringDialog(true);
  };

  // 로그 다이얼로그 열기
  const openLogsDialog = (plugin: AgentPlugin) => {
    setSelectedPlugin(plugin);
    setShowLogsDialog(true);
  };

  // 필터링된 데이터 가져오기
  const filteredPlugins = getFilteredPlugins();
  const filteredCustomAgents = getFilteredCustomAgents();

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'inactive':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'inactive':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'error':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center gap-2">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="text-lg text-slate-600">플러그인 로딩 중...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500 to-pink-500">
            <Puzzle className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              Agent Plugins
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              AI 에이전트 플러그인 관리 및 모니터링 - 향상된 설정 및 모니터링 도구
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {wsConnected && (
            <Badge variant="outline" className="text-green-600 border-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-1" />
              실시간 연결됨
            </Badge>
          )}
          <Button onClick={() => setShowInstallDialog(true)} className="gap-2">
            <Plus className="h-4 w-4" />
            플러그인 설치
          </Button>
        </div>
      </div>

      {/* System Health */}
      {systemHealth && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              시스템 상태
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {systemHealth.active_plugins}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">활성 플러그인</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {systemHealth.total_executions.toLocaleString()}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">총 실행 횟수</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {systemHealth.average_response_time}ms
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">평균 응답 시간</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {(systemHealth.error_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-400">오류율</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search and Filter */}
      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="플러그인 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-600" />
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-md text-sm"
          >
            <option value="all">모든 상태</option>
            <option value="active">활성</option>
            <option value="inactive">비활성</option>
            <option value="error">오류</option>
          </select>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="system" className="space-y-4">
        <TabsList>
          <TabsTrigger value="system">시스템 플러그인</TabsTrigger>
          <TabsTrigger value="custom">커스텀 에이전트</TabsTrigger>
        </TabsList>

        <TabsContent value="system" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredPlugins.map((plugin) => (
              <Card key={plugin.agent_id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Brain className="h-5 w-5 text-blue-600" />
                      <div>
                        <CardTitle className="text-lg">{plugin.agent_name}</CardTitle>
                        <CardDescription className="text-sm">
                          {plugin.agent_type} v{plugin.version}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {getStatusIcon(plugin.status)}
                      <Badge className={getStatusColor(plugin.status)}>
                        {plugin.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {plugin.description}
                  </p>
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>실행: {plugin.execution_count}회</span>
                    <span>성공률: {plugin.success_rate}%</span>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => openConfigDialog(plugin)}
                      className="flex-1"
                    >
                      <Settings className="h-3 w-3 mr-1" />
                      설정
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="sm">
                          <MoreVertical className="h-3 w-3" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuLabel>작업</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => openMonitoringDialog(plugin)}>
                          <BarChart3 className="h-4 w-4 mr-2" />
                          모니터링
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => openLogsDialog(plugin)}>
                          <Terminal className="h-4 w-4 mr-2" />
                          로그 보기
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleRefreshPlugin(plugin.agent_id)}>
                          <RefreshCw className="h-4 w-4 mr-2" />
                          새로고침
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem 
                          onClick={() => handleUnregisterPlugin(plugin.agent_id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          등록 해제
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="custom" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredCustomAgents.map((agent) => (
              <Card key={agent.agent_id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Brain className="h-5 w-5 text-purple-600" />
                      <div>
                        <CardTitle className="text-lg">{agent.agent_name}</CardTitle>
                        <CardDescription className="text-sm">
                          Custom Agent
                        </CardDescription>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {getStatusIcon(agent.status)}
                      <Badge className={getStatusColor(agent.status)}>
                        {agent.status}
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {agent.description}
                  </p>
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>실행: {agent.execution_count}회</span>
                    <span>성공률: {agent.success_rate}%</span>
                  </div>
                  <div className="flex gap-2">
                    {agent.status === 'active' ? (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRefreshPlugin(agent.agent_id)}
                        >
                          <RefreshCw className="h-3 w-3 mr-1" />
                          새로고침
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm">
                              <MoreVertical className="h-3 w-3" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent>
                            <DropdownMenuItem onClick={() => openMonitoringDialog(agent)}>
                              <BarChart3 className="h-4 w-4 mr-2" />
                              모니터링
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openLogsDialog(agent)}>
                              <Terminal className="h-4 w-4 mr-2" />
                              로그 보기
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleUnregisterPlugin(agent.agent_id)}
                              className="text-red-600"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              등록 해제
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => handleRegisterAsPlugin(agent.agent_id)}
                        className="flex-1"
                      >
                        <Upload className="h-3 w-3 mr-1" />
                        플러그인 등록
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      
      {/* Installation Wizard */}
      <PluginInstallationWizard
        isOpen={showInstallDialog}
        onClose={() => setShowInstallDialog(false)}
        onComplete={handleInstallComplete}
        onError={handleInstallError}
      />

      {/* Configuration Dialog */}
      <Dialog open={showConfigDialog} onOpenChange={setShowConfigDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>플러그인 설정</DialogTitle>
            <DialogDescription>
              {selectedPlugin?.agent_name} 플러그인의 설정을 구성합니다.
            </DialogDescription>
          </DialogHeader>
          {selectedPlugin && configSchema && (
            <PluginConfigWizard
              pluginId={selectedPlugin.agent_id}
              schema={configSchema}
              onSave={handleConfigSave}
              onValidate={handleConfigValidate}
              onCancel={() => setShowConfigDialog(false)}
              showPreview={true}
              showHistory={true}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Monitoring Dialog */}
      <Dialog open={showMonitoringDialog} onOpenChange={setShowMonitoringDialog}>
        <DialogContent className="max-w-7xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>플러그인 모니터링</DialogTitle>
            <DialogDescription>
              {selectedPlugin?.agent_name} 플러그인의 상세 모니터링 정보입니다.
            </DialogDescription>
          </DialogHeader>
          {selectedPlugin && (
            <PluginDetailMonitoring
              pluginId={selectedPlugin.agent_id}
              pluginName={selectedPlugin.agent_name}
              timeRange="24h"
              showComparison={true}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Logs Dialog */}
      <Dialog open={showLogsDialog} onOpenChange={setShowLogsDialog}>
        <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle>실행 로그</DialogTitle>
            <DialogDescription>
              {selectedPlugin?.agent_name} 플러그인의 실행 로그입니다.
            </DialogDescription>
          </DialogHeader>
          {selectedPlugin && (
            <ExecutionLogViewer
              pluginId={selectedPlugin.agent_id}
              height={600}
              showToolbar={true}
              showFilters={true}
              autoScroll={true}
              realTime={true}
              exportable={true}
              searchable={true}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}