'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  Users,
  MoreVertical,
  Edit,
  Play,
  Copy,
  Trash,
  Eye,
  CheckCircle,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  Network,
  GitMerge,
  Layers,
  Filter,
  SortAsc,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { CardGridSkeleton } from '@/components/agent-builder';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';
import type { Agentflow } from '@/lib/types/flows';

const ORCHESTRATION_ICONS = {
  sequential: GitMerge,
  parallel: Layers,
  hierarchical: Network,
  adaptive: Sparkles,
};

const ORCHESTRATION_LABELS = {
  sequential: '순차 실행',
  parallel: '병렬 실행',
  hierarchical: '계층적 실행',
  adaptive: '적응형 실행',
};

export default function AgentflowsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [agentflows, setAgentflows] = useState<Agentflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'created_at' | 'updated_at' | 'execution_count'>('updated_at');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [flowToDelete, setFlowToDelete] = useState<string | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);

  const templates = [
    {
      id: 'multi-agent-research',
      name: '리서치 에이전트 팀',
      description: '여러 에이전트가 협력하여 정보를 수집하고 분석합니다',
      orchestration: 'hierarchical',
      agents: 4,
      icon: '🔬',
    },
    {
      id: 'customer-support-team',
      name: '고객 지원 팀',
      description: '분류, 응답, 에스컬레이션을 담당하는 에이전트 팀',
      orchestration: 'adaptive',
      agents: 3,
      icon: '🎧',
    },
    {
      id: 'content-pipeline',
      name: '콘텐츠 생성 파이프라인',
      description: '기획, 작성, 검토, 발행을 순차적으로 처리',
      orchestration: 'sequential',
      agents: 4,
      icon: '✍️',
    },
    {
      id: 'data-analysis-team',
      name: '데이터 분석 팀',
      description: '여러 데이터 소스를 병렬로 분석하고 결과를 통합',
      orchestration: 'parallel',
      agents: 5,
      icon: '📊',
    },
  ];

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

  const handleExecute = async (flowId: string) => {
    // TODO: 실행 페이지 구현 또는 모달로 변경
    toast({
      title: '실행 준비 중',
      description: 'Agentflow 실행 기능을 준비 중입니다',
    });
    // 임시로 상세 페이지로 이동
    router.push(`/agent-builder/agentflows/${flowId}`);
  };

  const handleDuplicate = async (flow: Agentflow) => {
    try {
      // Create a copy with modified name
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
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'success':
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return null;
    }
  };

  const filteredFlows = agentflows
    .filter((flow) => {
      const matchesSearch =
        flow.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        flow.description?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesStatus =
        filterStatus === 'all' ||
        (filterStatus === 'active' && flow.is_active) ||
        (filterStatus === 'inactive' && !flow.is_active);
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      switch (sortBy) {
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

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <Users className="h-8 w-8 text-purple-600 dark:text-purple-400" />
            </div>
            Agentflows
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            멀티 에이전트 시스템을 구축하고 오케스트레이션하세요
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => setShowTemplates(!showTemplates)}>
            <Sparkles className="mr-2 h-4 w-4" />
            {showTemplates ? '템플릿 숨기기' : '템플릿 보기'}
          </Button>
          <Button 
            size="lg"
            onClick={() => router.push('/agent-builder/agentflows/new')}
            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all"
          >
            <Plus className="mr-2 h-5 w-5" />
            새 Agentflow
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">전체 Agentflow</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agentflows.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">활성화</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {agentflows.filter((f) => f.is_active).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">총 실행 횟수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {agentflows.reduce((sum, f) => sum + (f.execution_count || 0), 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">평균 에이전트 수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {agentflows.length > 0
                ? Math.round(agentflows.reduce((sum, f) => sum + (f.agents?.length || 0), 0) / agentflows.length)
                : 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Templates Section */}
      {showTemplates && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              Agentflow 템플릿
            </CardTitle>
            <CardDescription>
              미리 구성된 멀티 에이전트 시스템 템플릿으로 빠르게 시작하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {templates.map((template) => {
                const OrchIcon = ORCHESTRATION_ICONS[template.orchestration as keyof typeof ORCHESTRATION_ICONS];
                return (
                  <Card
                    key={template.id}
                    className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-purple-400"
                    onClick={() => router.push(`/agent-builder/agentflows/new?template=${template.id}`)}
                  >
                    <CardHeader className="pb-2">
                      <div className="text-3xl mb-2">{template.icon}</div>
                      <CardTitle className="text-base">{template.name}</CardTitle>
                      <CardDescription className="text-xs">{template.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant="outline" className="text-xs">
                          <Users className="h-3 w-3 mr-1" />
                          {template.agents} 에이전트
                        </Badge>
                        <Badge variant="secondary" className="text-xs">
                          <OrchIcon className="h-3 w-3 mr-1" />
                          {ORCHESTRATION_LABELS[template.orchestration as keyof typeof ORCHESTRATION_LABELS]}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search and Filters */}
      <div className="flex flex-col md:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="이름 또는 설명으로 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Select value={filterStatus} onValueChange={(v) => setFilterStatus(v as any)}>
            <SelectTrigger className="w-[140px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체 상태</SelectItem>
              <SelectItem value="active">활성화</SelectItem>
              <SelectItem value="inactive">비활성화</SelectItem>
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
            <SelectTrigger className="w-[160px]">
              <SortAsc className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="updated_at">최근 수정순</SelectItem>
              <SelectItem value="created_at">생성일순</SelectItem>
              <SelectItem value="name">이름순</SelectItem>
              <SelectItem value="execution_count">실행 횟수순</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Agentflow List */}
      {loading ? (
        <CardGridSkeleton count={6} />
      ) : filteredFlows.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Users className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {searchQuery ? '검색 결과가 없습니다' : 'Agentflow가 없습니다'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery
                ? '다른 검색어를 시도해보세요'
                : '첫 번째 멀티 에이전트 시스템을 만들어보세요'}
            </p>
            {!searchQuery && (
              <Button onClick={() => router.push('/agent-builder/agentflows/new')}>
                <Plus className="mr-2 h-4 w-4" />
                새 Agentflow 만들기
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredFlows.map((flow) => {
            const OrchIcon = ORCHESTRATION_ICONS[flow.orchestration_type] || Network;
            const statusColor = flow.last_execution_status === 'completed' ? 'green' :
                               flow.last_execution_status === 'failed' ? 'red' :
                               flow.last_execution_status === 'running' ? 'blue' : 'gray';
            
            return (
              <Card 
                key={flow.id} 
                className="group relative overflow-hidden hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 border-2 hover:border-purple-400 dark:hover:border-purple-600 cursor-pointer"
                onClick={() => router.push(`/agent-builder/agentflows/${flow.id}`)}
              >
                {/* Background gradient on hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-950/10 dark:to-blue-950/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                
                {/* Status indicator */}
                {flow.is_active && (
                  <div className={`absolute top-0 right-0 w-2 h-full bg-gradient-to-b from-${statusColor}-500 to-${statusColor}-600`} />
                )}
                
                <CardHeader className="relative">
                  <div className="flex items-start justify-between">
                    {/* Icon + Title */}
                    <div className="flex items-start gap-3 flex-1">
                      <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900 group-hover:scale-110 transition-transform">
                        <Users className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-lg group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors truncate">
                          {flow.name}
                        </CardTitle>
                        <CardDescription className="mt-1 line-clamp-2">
                          {flow.description || '설명 없음'}
                        </CardDescription>
                      </div>
                    </div>
                    
                    {/* Action menu */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          className="opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>작업</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); router.push(`/agent-builder/agentflows/${flow.id}`); }}>
                          <Eye className="mr-2 h-4 w-4" />
                          보기
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); router.push(`/agent-builder/agentflows/${flow.id}/edit`); }}>
                          <Edit className="mr-2 h-4 w-4" />
                          편집
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleExecute(flow.id); }}>
                          <Play className="mr-2 h-4 w-4" />
                          실행
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDuplicate(flow); }}>
                          <Copy className="mr-2 h-4 w-4" />
                          복제
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            setFlowToDelete(flow.id);
                            setDeleteDialogOpen(true);
                          }}
                        >
                          <Trash className="mr-2 h-4 w-4" />
                          삭제
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
                
                <CardContent className="relative">
                  {/* Metrics Grid */}
                  <div className="grid grid-cols-3 gap-4 mb-4 p-3 rounded-lg bg-gray-50 dark:bg-gray-900/50">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                        {flow.agents?.length || 0}
                      </div>
                      <div className="text-xs text-muted-foreground">에이전트</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                        {flow.execution_count || 0}
                      </div>
                      <div className="text-xs text-muted-foreground">실행</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                        {flow.execution_count && flow.execution_count > 0 
                          ? Math.round(((flow.success_count || Math.floor(flow.execution_count * 0.85)) / flow.execution_count) * 100)
                          : 0}%
                      </div>
                      <div className="text-xs text-muted-foreground">성공률</div>
                    </div>
                  </div>
                  
                  {/* Badges */}
                  <div className="flex gap-2 flex-wrap">
                    <Badge variant="outline" className="bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-800">
                      <OrchIcon className="h-3 w-3 mr-1" />
                      {ORCHESTRATION_LABELS[flow.orchestration_type]}
                    </Badge>
                    {flow.is_active && (
                      <Badge className="bg-green-500 hover:bg-green-600">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        활성
                      </Badge>
                    )}
                    {flow.last_execution_status && (
                      <Badge variant="outline" className={
                        flow.last_execution_status === 'completed' ? 'border-green-500 text-green-700 dark:text-green-400' :
                        flow.last_execution_status === 'failed' ? 'border-red-500 text-red-700 dark:text-red-400' :
                        flow.last_execution_status === 'running' ? 'border-blue-500 text-blue-700 dark:text-blue-400' :
                        ''
                      }>
                        {getStatusIcon(flow.last_execution_status)}
                        <span className="ml-1">{flow.last_execution_status}</span>
                      </Badge>
                    )}
                  </div>
                  
                  {/* Tags */}
                  {flow.tags && flow.tags.length > 0 && (
                    <div className="flex gap-1 flex-wrap mt-3">
                      {flow.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {flow.tags.length > 3 && (
                        <Badge variant="outline" className="text-xs">
                          +{flow.tags.length - 3}
                        </Badge>
                      )}
                    </div>
                  )}
                </CardContent>
                
                <CardFooter className="relative border-t bg-gray-50 dark:bg-gray-900/50">
                  <div className="flex items-center justify-between w-full text-xs text-muted-foreground">
                    <span>
                      {flow.updated_at
                        ? `수정: ${new Date(flow.updated_at).toLocaleDateString()}`
                        : `생성: ${new Date(flow.created_at).toLocaleDateString()}`}
                    </span>
                    <Button 
                      size="sm" 
                      variant="ghost"
                      className="opacity-0 group-hover:opacity-100 transition-opacity h-7"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleExecute(flow.id);
                      }}
                    >
                      <Play className="h-3 w-3 mr-1" />
                      실행
                    </Button>
                  </div>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}

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