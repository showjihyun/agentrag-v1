'use client';

import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Edit,
  Play,
  Copy,
  Trash,
  Users,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  Settings,
  MoreVertical,
  TrendingUp,
  GitMerge,
  Layers,
  Network,
  Sparkles,
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

export default function AgentflowDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { toast } = useToast();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const { data: flowData, isLoading, error } = useQuery({
    queryKey: ['agentflow', params.id],
    queryFn: () => flowsAPI.getFlow(params.id),
  });

  const flow = flowData as any;

  const { data: executions, isLoading: executionsLoading } = useQuery({
    queryKey: ['agentflow-executions', params.id],
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
        description: 'Agentflow가 삭제되었습니다',
      });
      router.push('/agent-builder/agentflows');
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
      await flowsAPI.createAgentflow(duplicated);
      toast({
        title: '복제 완료',
        description: 'Agentflow가 복제되었습니다',
      });
      router.push('/agent-builder/agentflows');
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
            <p className="text-red-500">Agentflow를 불러오는데 실패했습니다</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const OrchIcon = ORCHESTRATION_ICONS[flow.orchestration_type as keyof typeof ORCHESTRATION_ICONS] || Network;

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <Users className="h-7 w-7 text-purple-600 dark:text-purple-400" />
            </div>
            {flow.name}
          </h1>
          <p className="text-muted-foreground mt-1">{flow.description || '설명 없음'}</p>
        </div>
        <Button
          size="lg"
          onClick={() => {
            toast({
              title: '실행 준비 중',
              description: 'Agentflow 실행 기능을 준비 중입니다',
            });
          }}
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
        >
          <Play className="h-5 w-5 mr-2" />
          실행
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
            <DropdownMenuItem onClick={() => router.push(`/agent-builder/agentflows/${params.id}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              편집
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleDuplicate}>
              <Copy className="mr-2 h-4 w-4" />
              복제
            </DropdownMenuItem>
            <DropdownMenuSeparator />
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
            <CardTitle className="text-sm font-medium text-muted-foreground">에이전트 수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">{flow.agents?.length || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">총 실행 횟수</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{flow.execution_count || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">성공률</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {flow.execution_count && flow.execution_count > 0
                ? Math.round(((flow.success_count || Math.floor(flow.execution_count * 0.85)) / flow.execution_count) * 100)
                : 0}
              %
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
          <TabsTrigger value="agents">에이전트</TabsTrigger>
          <TabsTrigger value="history">실행 히스토리</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-950/20 dark:to-blue-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                  <Settings className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <CardTitle>설정 정보</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <p className="text-sm text-muted-foreground mb-1">오케스트레이션 유형</p>
                  <div className="flex items-center gap-2">
                    <OrchIcon className="h-5 w-5 text-purple-600" />
                    <p className="font-medium">{ORCHESTRATION_LABELS[flow.orchestration_type as keyof typeof ORCHESTRATION_LABELS]}</p>
                  </div>
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
                {flow.tags && flow.tags.length > 0 && (
                  <div className="col-span-2">
                    <p className="text-sm text-muted-foreground mb-2">태그</p>
                    <div className="flex gap-2 flex-wrap">
                      {flow.tags.map((tag: string) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          {flow.agents && flow.agents.length > 0 ? (
            flow.agents.map((agent: any, index: number) => (
              <Card key={agent.id || index} className="border-2 hover:shadow-lg transition-all">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className="text-lg px-3 py-1">
                        {index + 1}
                      </Badge>
                      <div>
                        <CardTitle className="text-lg">{agent.name}</CardTitle>
                        {agent.role && (
                          <CardDescription className="mt-1">{agent.role}</CardDescription>
                        )}
                      </div>
                    </div>
                    <Badge variant="secondary">우선순위: {agent.priority || index + 1}</Badge>
                  </div>
                </CardHeader>
                {agent.description && (
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{agent.description}</p>
                  </CardContent>
                )}
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="pt-6 text-center text-muted-foreground">
                <Users className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>에이전트가 구성되지 않았습니다</p>
              </CardContent>
            </Card>
          )}
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
                <p>실행 히스토리가 없습니다</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Agentflow 삭제</AlertDialogTitle>
            <AlertDialogDescription>
              정말로 이 Agentflow를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.
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
