'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Plus,
  Search,
  MessageSquare,
  MoreVertical,
  Edit,
  Play,
  Copy,
  Trash,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  Sparkles,
  Database,
  Wrench,
  Brain,
  Filter,
  SortAsc,
  Code,
  ExternalLink,
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
import type { Chatflow } from '@/lib/types/flows';

export default function ChatflowsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [chatflows, setChatflows] = useState<Chatflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'active' | 'inactive'>('all');
  const [sortBy, setSortBy] = useState<'name' | 'created_at' | 'updated_at' | 'execution_count'>('updated_at');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [flowToDelete, setFlowToDelete] = useState<string | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);

  const templates = [
    {
      id: 'rag-chatbot',
      name: 'RAG 챗봇',
      description: '문서 기반 질의응답 챗봇 (지식베이스 연동)',
      features: ['RAG', 'Memory'],
      icon: '📚',
    },
    {
      id: 'customer-support',
      name: '고객 지원 챗봇',
      description: 'FAQ 및 티켓 생성 기능이 포함된 지원 봇',
      features: ['Tools', 'Memory'],
      icon: '🎧',
    },
    {
      id: 'code-assistant',
      name: '코드 어시스턴트',
      description: '코드 작성, 리뷰, 디버깅을 도와주는 AI',
      features: ['Tools', 'Code'],
      icon: '💻',
    },
    {
      id: 'research-assistant',
      name: '리서치 어시스턴트',
      description: '웹 검색과 문서 분석을 통한 리서치 지원',
      features: ['RAG', 'Web Search'],
      icon: '🔬',
    },
  ];

  useEffect(() => {
    loadChatflows();
  }, []);

  const loadChatflows = async () => {
    try {
      setLoading(true);
      const response = await flowsAPI.getChatflows();
      setChatflows(response.flows as Chatflow[]);
    } catch (error: any) {
      console.error('Failed to load chatflows:', error);
      toast({
        title: '오류',
        description: error.message || 'Chatflow 목록을 불러오는데 실패했습니다',
        variant: 'destructive',
      });
      setChatflows([]);
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
        description: 'Chatflow가 삭제되었습니다',
      });
      loadChatflows();
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

  const handleChat = (flowId: string) => {
    router.push(`/agent-builder/chatflows/${flowId}/chat`);
  };

  const handleDuplicate = async (flow: Chatflow) => {
    try {
      const duplicatedFlow = {
        ...flow,
        name: `${flow.name} (복사본)`,
        id: undefined,
      };
      await flowsAPI.createChatflow(duplicatedFlow);
      toast({
        title: '복제 완료',
        description: `"${flow.name}" 복제가 완료되었습니다`,
      });
      loadChatflows();
    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || '복제에 실패했습니다',
        variant: 'destructive',
      });
    }
  };

  const handleEmbed = (flowId: string) => {
    router.push(`/agent-builder/chatflows/${flowId}/embed`);
  };

  const handleAPI = (flowId: string) => {
    router.push(`/agent-builder/chatflows/${flowId}/api`);
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

  const filteredFlows = chatflows
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
      {/* Header - Enhanced Visual Hierarchy */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
              <MessageSquare className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
            Chatflows
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">
            RAG 기반 챗봇과 AI 어시스턴트를 구축하세요
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => setShowTemplates(!showTemplates)}>
            <Sparkles className="mr-2 h-4 w-4" />
            {showTemplates ? '템플릿 숨기기' : '템플릿 보기'}
          </Button>
          <Button 
            size="lg"
            onClick={() => router.push('/agent-builder/chatflows/new')}
            className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-lg hover:shadow-xl transition-all"
          >
            <Plus className="mr-2 h-5 w-5" />
            새 Chatflow
          </Button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">전체 Chatflow</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{chatflows.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">활성화</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {chatflows.filter((f) => f.is_active).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">총 대화 수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {chatflows.reduce((sum, f) => sum + (f.execution_count || 0), 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">RAG 연동</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {chatflows.filter((f) => f.rag_config?.enabled).length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Templates Section */}
      {showTemplates && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-500" />
              Chatflow 템플릿
            </CardTitle>
            <CardDescription>
              미리 구성된 챗봇 템플릿으로 빠르게 시작하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {templates.map((template) => (
                <Card
                  key={template.id}
                  className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-blue-400"
                  onClick={() => router.push(`/agent-builder/chatflows/new?template=${template.id}`)}
                >
                  <CardHeader className="pb-2">
                    <div className="text-3xl mb-2">{template.icon}</div>
                    <CardTitle className="text-base">{template.name}</CardTitle>
                    <CardDescription className="text-xs">{template.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 flex-wrap">
                      {template.features.map((feature) => (
                        <Badge key={feature} variant="secondary" className="text-xs">
                          {feature === 'RAG' && <Database className="h-3 w-3 mr-1" />}
                          {feature === 'Tools' && <Wrench className="h-3 w-3 mr-1" />}
                          {feature === 'Memory' && <Brain className="h-3 w-3 mr-1" />}
                          {feature === 'Code' && <Code className="h-3 w-3 mr-1" />}
                          {feature}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
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
              <SelectItem value="execution_count">대화 수순</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Chatflow List */}
      {loading ? (
        <CardGridSkeleton count={6} />
      ) : filteredFlows.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <MessageSquare className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {searchQuery ? '검색 결과가 없습니다' : 'Chatflow가 없습니다'}
            </h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery
                ? '다른 검색어를 시도해보세요'
                : '첫 번째 AI 챗봇을 만들어보세요'}
            </p>
            {!searchQuery && (
              <Button onClick={() => router.push('/agent-builder/chatflows/new')}>
                <Plus className="mr-2 h-4 w-4" />
                새 Chatflow 만들기
              </Button>
            )}
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredFlows.map((flow) => (
            <Card 
              key={flow.id} 
              className="group relative overflow-hidden hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 border-2 hover:border-blue-400 dark:hover:border-blue-600 cursor-pointer"
              onClick={() => router.push(`/agent-builder/chatflows/${flow.id}`)}
            >
              {/* Background gradient on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950/10 dark:to-cyan-950/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              
              {/* Status indicator */}
              {flow.is_active && (
                <div className="absolute top-0 right-0 w-2 h-full bg-gradient-to-b from-green-500 to-green-600" />
              )}
              
              <CardHeader className="relative">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900 group-hover:scale-110 transition-transform">
                      <MessageSquare className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <CardTitle className="text-lg group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate">
                        {flow.name}
                      </CardTitle>
                      <CardDescription className="mt-1 line-clamp-2">
                        {flow.description || '설명 없음'}
                      </CardDescription>
                    </div>
                  </div>
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
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleChat(flow.id); }}>
                        <Play className="mr-2 h-4 w-4" />
                        채팅 시작
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); router.push(`/agent-builder/chatflows/${flow.id}`); }}>
                        <Eye className="mr-2 h-4 w-4" />
                        보기
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); router.push(`/agent-builder/chatflows/${flow.id}/edit`); }}>
                        <Edit className="mr-2 h-4 w-4" />
                        편집
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleEmbed(flow.id); }}>
                        <Code className="mr-2 h-4 w-4" />
                        임베드 코드
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleAPI(flow.id); }}>
                        <ExternalLink className="mr-2 h-4 w-4" />
                        API 문서
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleDuplicate(flow); }}>
                        <Copy className="mr-2 h-4 w-4" />
                        복제
                      </DropdownMenuItem>
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
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {flow.execution_count || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">대화</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {flow.tools?.length || 0}
                    </div>
                    <div className="text-xs text-muted-foreground">도구</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {flow.rag_config?.enabled ? '✓' : '—'}
                    </div>
                    <div className="text-xs text-muted-foreground">RAG</div>
                  </div>
                </div>
                
                {/* Badges */}
                <div className="flex gap-2 flex-wrap mb-3">
                  <Badge variant="outline" className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800 text-xs">
                    {flow.chat_config?.llm_provider || 'ollama'}
                  </Badge>
                  {flow.rag_config?.enabled && (
                    <Badge className="bg-purple-500 hover:bg-purple-600 text-xs">
                      <Database className="h-3 w-3 mr-1" />
                      RAG
                    </Badge>
                  )}
                  {flow.memory_config && (
                    <Badge variant="secondary" className="text-xs">
                      <Brain className="h-3 w-3 mr-1" />
                      {flow.memory_config.type}
                    </Badge>
                  )}
                  {flow.is_active && (
                    <Badge className="bg-green-500 hover:bg-green-600 text-xs">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      활성
                    </Badge>
                  )}
                </div>
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
                      handleChat(flow.id);
                    }}
                  >
                    <Play className="h-3 w-3 mr-1" />
                    채팅
                  </Button>
                </div>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Chatflow 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              이 Chatflow를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
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
