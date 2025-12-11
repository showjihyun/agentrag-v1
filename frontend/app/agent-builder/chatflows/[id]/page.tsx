'use client';

import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Edit,
  Play,
  Copy,
  Trash,
  MessageSquare,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  Settings,
  MoreVertical,
  Database,
  Brain,
  Wrench,
  Code,
  ExternalLink,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
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
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';
import { useState } from 'react';

export default function ChatflowDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const { data: flowData, isLoading, error } = useQuery({
    queryKey: ['chatflow', params.id],
    queryFn: () => flowsAPI.getFlow(params.id),
  });

  const flow = flowData as any;

  const { data: executions, isLoading: executionsLoading } = useQuery({
    queryKey: ['chatflow-executions', params.id],
    queryFn: async () => {
      // Mock data for now - replace with actual API call when available
      return { executions: [] };
    },
  });

  const handleDelete = async () => {
    try {
      await flowsAPI.deleteFlow(params.id);
      toast({
        title: '삭제 완료',
        description: 'Chatflow가 삭제되었습니다',
      });
      router.push('/agent-builder/chatflows');
    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || '삭제에 실패했습니다',
        variant: 'destructive',
      });
    }
  };

  const handleDuplicate = async () => {
    try {
      const duplicated = {
        ...flow,
        name: `${flow.name} (복사본)`,
        id: undefined,
      };
      await flowsAPI.createChatflow(duplicated);
      toast({
        title: '복제 완료',
        description: 'Chatflow가 복제되었습니다',
      });
      router.push('/agent-builder/chatflows');
    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || '복제에 실패했습니다',
        variant: 'destructive',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !flow) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-red-500">Chatflow를 불러오는데 실패했습니다</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
              <MessageSquare className="h-7 w-7 text-blue-600 dark:text-blue-400" />
            </div>
            {flow.name}
          </h1>
          <p className="text-muted-foreground mt-1">{flow.description || '설명 없음'}</p>
        </div>
        <Button
          size="lg"
          onClick={() => router.push(`/agent-builder/chatflows/${params.id}/chat`)}
          className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
        >
          <Play className="h-5 w-5 mr-2" />
          채팅 시작
        </Button>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon">
              <MoreVertical className="h-5 w-5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>작업</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => router.push(`/agent-builder/chatflows/${params.id}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              편집
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push(`/agent-builder/chatflows/${params.id}/embed`)}>
              <Code className="mr-2 h-4 w-4" />
              임베드 코드
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push(`/agent-builder/chatflows/${params.id}/api`)}>
              <ExternalLink className="mr-2 h-4 w-4" />
              API 문서
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleDuplicate}>
              <Copy className="mr-2 h-4 w-4" />
              복제
            </DropdownMenuItem>
            <DropdownMenuItem className="text-destructive" onClick={() => setDeleteDialogOpen(true)}>
              <Trash className="mr-2 h-4 w-4" />
              삭제
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">총 대화 수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{flow.execution_count || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">도구 수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{flow.tools?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">RAG</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {flow.rag_config?.enabled ? '✓' : '—'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">상태</CardTitle>
          </CardHeader>
          <CardContent>
            {flow.is_active ? (
              <Badge className="bg-green-500">활성</Badge>
            ) : (
              <Badge variant="secondary">비활성</Badge>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3 lg:w-[500px]">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="config">설정</TabsTrigger>
          <TabsTrigger value="history">대화 히스토리</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle>기본 정보</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">LLM 제공자</p>
                  <p className="font-medium">{flow.chat_config?.llm_provider || 'ollama'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">모델</p>
                  <p className="font-medium">{flow.chat_config?.llm_model || 'llama3.1'}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">생성일</p>
                  <p className="font-medium">{new Date(flow.created_at).toLocaleString()}</p>
                </div>
                {flow.updated_at && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">수정일</p>
                    <p className="font-medium">{new Date(flow.updated_at).toLocaleString()}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className={flow.rag_config?.enabled ? 'border-purple-500' : ''}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Database className="h-5 w-5 text-purple-600" />
                  <CardTitle className="text-base">RAG</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                {flow.rag_config?.enabled ? (
                  <div className="space-y-2">
                    <Badge className="bg-purple-500">활성화</Badge>
                    <p className="text-sm text-muted-foreground">
                      {flow.rag_config.knowledgebase_ids?.length || 0}개 지식베이스
                    </p>
                  </div>
                ) : (
                  <Badge variant="secondary">비활성화</Badge>
                )}
              </CardContent>
            </Card>

            <Card className={flow.memory_config ? 'border-blue-500' : ''}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Brain className="h-5 w-5 text-blue-600" />
                  <CardTitle className="text-base">메모리</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                {flow.memory_config ? (
                  <div className="space-y-2">
                    <Badge className="bg-blue-500">{flow.memory_config.type}</Badge>
                    <p className="text-sm text-muted-foreground">
                      최대 {flow.memory_config.max_messages || 20}개 메시지
                    </p>
                  </div>
                ) : (
                  <Badge variant="secondary">없음</Badge>
                )}
              </CardContent>
            </Card>

            <Card className={flow.tools && flow.tools.length > 0 ? 'border-green-500' : ''}>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Wrench className="h-5 w-5 text-green-600" />
                  <CardTitle className="text-base">도구</CardTitle>
                </div>
              </CardHeader>
              <CardContent>
                {flow.tools && flow.tools.length > 0 ? (
                  <div className="space-y-2">
                    <Badge className="bg-green-500">{flow.tools.length}개</Badge>
                    <p className="text-sm text-muted-foreground">도구 연동됨</p>
                  </div>
                ) : (
                  <Badge variant="secondary">없음</Badge>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Config Tab */}
        <TabsContent value="config" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Settings className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle>LLM 설정</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">시스템 프롬프트</p>
                  <Card className="bg-muted">
                    <CardContent className="pt-4">
                      <p className="text-sm whitespace-pre-wrap">
                        {flow.chat_config?.system_prompt || 'You are a helpful assistant.'}
                      </p>
                    </CardContent>
                  </Card>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Temperature</p>
                    <p className="font-medium">{flow.chat_config?.temperature || 0.7}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Max Tokens</p>
                    <p className="font-medium">{flow.chat_config?.max_tokens || 2048}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-1">Streaming</p>
                    <Badge>{flow.chat_config?.streaming ? '활성' : '비활성'}</Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4">
          {executionsLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : executions && executions.executions?.length > 0 ? (
            executions.executions.map((execution: any) => (
              <Card
                key={execution.id}
                className="border-2 hover:shadow-lg transition-all cursor-pointer"
                onClick={() => router.push(`/agent-builder/executions/${execution.id}`)}
              >
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {execution.status === 'completed' ? (
                        <CheckCircle className="h-8 w-8 text-green-500" />
                      ) : execution.status === 'failed' ? (
                        <XCircle className="h-8 w-8 text-red-500" />
                      ) : (
                        <Activity className="h-8 w-8 text-blue-500 animate-pulse" />
                      )}
                      <div>
                        <p className="font-medium">
                          {new Date(execution.started_at).toLocaleString()}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {execution.duration ? `${execution.duration.toFixed(1)}초` : '진행 중'}
                        </p>
                      </div>
                    </div>
                    <Badge
                      variant={
                        execution.status === 'completed'
                          ? 'default'
                          : execution.status === 'failed'
                          ? 'destructive'
                          : 'secondary'
                      }
                    >
                      {execution.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                <Clock className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>대화 히스토리가 없습니다</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Chatflow 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 Chatflow를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
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
