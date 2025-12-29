'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';
import type { Agentflow } from '@/lib/types/flows';

// Import all UX components
import {
  QuickActionBar,
  SmartEmptyState,
  EnhancedSearchFilters,
  ImprovedFlowCard,
  FlowListView,
  CardGridSkeleton,
  TemplateMarketplace,
  VirtualizedFlowGrid,
  UserPreferencesPanel,
  FlowAnalytics
} from '@/components/agent-builder';

// Statistics and UI components
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Users, CheckCircle2, TrendingUp, Zap, BarChart3, Settings } from 'lucide-react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

// User preferences store
import { useUserPreferences } from '@/lib/stores/userPreferences';

interface FilterState {
  status: 'all' | 'active' | 'inactive';
  sortBy: 'name' | 'created_at' | 'updated_at' | 'execution_count';
  tags: string[];
  dateRange: 'all' | 'week' | 'month' | 'quarter';
}

export default function EnhancedAgentflowsPage() {
  const router = useRouter();
  const { toast } = useToast();
  
  // User preferences
  const {
    defaultViewMode,
    defaultSortBy,
    defaultFilterStatus,
    showTemplatesByDefault,
    enableVirtualization,
    enableAnimations,
    addRecentTemplate,
    pinFlow,
    unpinFlow,
    pinnedFlows
  } = useUserPreferences();
  
  // State management
  const [agentflows, setAgentflows] = useState<Agentflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showTemplates, setShowTemplates] = useState(showTemplatesByDefault);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>(defaultViewMode);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [flowToDelete, setFlowToDelete] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('flows');
  const [filters, setFilters] = useState<FilterState>({
    status: defaultFilterStatus,
    sortBy: defaultSortBy,
    tags: [],
    dateRange: 'all'
  });

  // Load data
  useEffect(() => {
    loadAgentflows();
  }, []);

  const loadAgentflows = async () => {
    try {
      setLoading(true);
      const response = await flowsAPI.getAgentflows();
      setAgentflows(response.flows as Agentflow[]);
    } catch (error: any) {
      console.error('Failed to load agentflows:', error);
      toast({
        title: '오류',
        description: error.message || 'Agentflow 목록을 불러오는데 실패했습니다',
        variant: 'destructive',
      });
      setAgentflows([]);
    } finally {
      setLoading(false);
    }
  };

  // Extract available tags from flows
  const availableTags = useMemo(() => {
    const tags = new Set<string>();
    agentflows.forEach(flow => {
      flow.tags?.forEach(tag => tags.add(tag));
    });
    return Array.from(tags);
  }, [agentflows]);

  // Filter and sort flows with pinned flows priority
  const filteredFlows = useMemo(() => {
    const filtered = agentflows
      .filter((flow) => {
        // Search filter
        const matchesSearch = !searchQuery || 
          flow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          flow.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          flow.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

        // Status filter
        const matchesStatus = filters.status === 'all' ||
          (filters.status === 'active' && flow.is_active) ||
          (filters.status === 'inactive' && !flow.is_active);

        // Tags filter
        const matchesTags = filters.tags.length === 0 ||
          filters.tags.some(tag => flow.tags?.includes(tag));

        // Date range filter
        const matchesDateRange = filters.dateRange === 'all' || (() => {
          const flowDate = new Date(flow.created_at);
          const now = new Date();
          const daysDiff = (now.getTime() - flowDate.getTime()) / (1000 * 60 * 60 * 24);
          
          switch (filters.dateRange) {
            case 'week': return daysDiff <= 7;
            case 'month': return daysDiff <= 30;
            case 'quarter': return daysDiff <= 90;
            default: return true;
          }
        })();

        return matchesSearch && matchesStatus && matchesTags && matchesDateRange;
      })
      .sort((a, b) => {
        // Pinned flows first
        const aPinned = pinnedFlows.includes(a.id);
        const bPinned = pinnedFlows.includes(b.id);
        if (aPinned && !bPinned) return -1;
        if (!aPinned && bPinned) return 1;

        // Then sort by selected criteria
        switch (filters.sortBy) {
          case 'name':
            return a.name.localeCompare(b.name);
          case 'created_at':
            return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
          case 'updated_at':
            return new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime();
          case 'execution_count':
            return (b.execution_count || 0) - (a.execution_count || 0);
          default:
            return 0;
        }
      });

    return filtered;
  }, [agentflows, searchQuery, filters, pinnedFlows]);

  // Action handlers
  const handleAction = async (action: string, flowId: string, flow?: Agentflow) => {
    switch (action) {
      case 'view':
        router.push(`/agent-builder/agentflows/${flowId}`);
        break;
      case 'edit':
        router.push(`/agent-builder/agentflows/${flowId}/edit`);
        break;
      case 'execute':
        router.push(`/agent-builder/agentflows/${flowId}/execute`);
        break;
      case 'duplicate':
        if (flow) {
          try {
            const duplicatedFlow = {
              ...flow,
              name: `${flow.name} (복사본)`,
              id: undefined,
            };
            await flowsAPI.createAgentflow(duplicatedFlow);
            toast({
              title: '복제 완료',
              description: `"${flow.name}" 복제가 완료되었습니다`,
            });
            loadAgentflows();
          } catch (error: any) {
            toast({
              title: '오류',
              description: error.message || '복제에 실패했습니다',
              variant: 'destructive',
            });
          }
        }
        break;
      case 'pin':
        pinFlow(flowId);
        toast({
          title: '고정 완료',
          description: '플로우가 목록 상단에 고정되었습니다',
        });
        break;
      case 'unpin':
        unpinFlow(flowId);
        toast({
          title: '고정 해제',
          description: '플로우 고정이 해제되었습니다',
        });
        break;
      case 'delete':
        setFlowToDelete(flowId);
        setDeleteDialogOpen(true);
        break;
    }
  };

  const handleDelete = async () => {
    if (!flowToDelete) return;

    try {
      await flowsAPI.deleteFlow(flowToDelete);
      toast({
        title: '삭제 완료',
        description: 'Agentflow가 삭제되었습니다',
      });
      loadAgentflows();
    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || '삭제에 실패했습니다',
        variant: 'destructive',
      });
    } finally {
      setDeleteDialogOpen(false);
      setFlowToDelete(null);
    }
  };

  const handleTemplateSelect = (template: any) => {
    const templateId = template.id || template;
    addRecentTemplate(templateId);
    router.push(`/agent-builder/agentflows/new?template=${templateId}`);
  };

  // Statistics calculation
  const stats = useMemo(() => {
    const total = agentflows.length;
    const active = agentflows.filter(f => f.is_active).length;
    const totalExecutions = agentflows.reduce((sum, f) => sum + (f.execution_count || 0), 0);
    const avgAgents = total > 0 
      ? Math.round(agentflows.reduce((sum, f) => sum + (f.agents?.length || 0), 0) / total)
      : 0;

    return { total, active, totalExecutions, avgAgents };
  }, [agentflows]);

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Enhanced Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <Users className="h-8 w-8 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
                Agentflows
              </h1>
              <p className="text-muted-foreground text-lg">
                멀티 에이전트 시스템을 구축하고 오케스트레이션하세요
              </p>
            </div>
          </div>
          
          {/* Settings Panel */}
          <UserPreferencesPanel />
        </div>
      </div>

      {/* Tabs Navigation */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="flows" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            플로우 관리
          </TabsTrigger>
          <TabsTrigger value="templates" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            템플릿 마켓플레이스
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            분석 및 인사이트
          </TabsTrigger>
        </TabsList>

        {/* Flows Tab */}
        <TabsContent value="flows" className="space-y-6">
          {/* Quick Action Bar */}
          <QuickActionBar
            type="agentflow"
            onNewFlow={() => router.push('/agent-builder/agentflows/new')}
            onToggleTemplates={() => setShowTemplates(!showTemplates)}
            showTemplates={showTemplates}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
          />

          {/* Enhanced Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Users className="h-4 w-4" />
                  전체 Agentflow
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  활성화
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">{stats.active}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <TrendingUp className="h-4 w-4" />
                  총 실행 횟수
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.totalExecutions}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  평균 에이전트 수
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">{stats.avgAgents}</div>
              </CardContent>
            </Card>
          </div>

          {/* Enhanced Search and Filters */}
          <EnhancedSearchFilters
            type="agentflow"
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            filters={filters}
            onFiltersChange={setFilters}
            availableTags={availableTags}
          />

          {/* Content */}
          {loading ? (
            <CardGridSkeleton count={6} />
          ) : filteredFlows.length === 0 ? (
            <SmartEmptyState
              type="agentflow"
              hasSearch={!!searchQuery || filters.status !== 'all' || filters.tags.length > 0 || filters.dateRange !== 'all'}
              searchQuery={searchQuery}
              onNewFlow={() => router.push('/agent-builder/agentflows/new')}
              onShowTemplates={() => setActiveTab('templates')}
              onClearSearch={() => {
                setSearchQuery('');
                setFilters({
                  status: 'all',
                  sortBy: 'updated_at',
                  tags: [],
                  dateRange: 'all'
                });
              }}
            />
          ) : enableVirtualization && filteredFlows.length > 20 ? (
            <VirtualizedFlowGrid
              flows={filteredFlows}
              type="agentflow"
              onAction={handleAction}
              containerHeight={600}
              containerWidth={1200}
            />
          ) : viewMode === 'grid' ? (
            <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 ${enableAnimations ? 'animate-in fade-in duration-300' : ''}`}>
              {filteredFlows.map((flow) => (
                <ImprovedFlowCard
                  key={flow.id}
                  flow={flow}
                  type="agentflow"
                  onAction={handleAction}
                />
              ))}
            </div>
          ) : (
            <FlowListView
              flows={filteredFlows}
              type="agentflow"
              onAction={handleAction}
            />
          )}
        </TabsContent>

        {/* Templates Tab */}
        <TabsContent value="templates">
          <TemplateMarketplace
            {...({onSelectTemplate: handleTemplateSelect} as any)}
          />
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics">
          <FlowAnalytics
            flows={agentflows}
            type="agentflow"
            timeRange="month"
          />
        </TabsContent>
      </Tabs>

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Agentflow 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              이 Agentflow를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>취소</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              삭제
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}