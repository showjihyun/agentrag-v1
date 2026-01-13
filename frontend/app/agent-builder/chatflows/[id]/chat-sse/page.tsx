'use client';

/**
 * Chatflow SSE Chat Page
 * 
 * New chat interface using Server-Sent Events (SSE) for better performance
 * and reliability compared to WebSocket implementation.
 */

import React from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, MessageSquare, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ChatflowSSEInterface } from '@/components/chatflow/ChatflowSSEInterface';
import { flowsAPI } from '@/lib/api/flows';
import { useAuth } from '@/contexts/AuthContext';

interface ChatflowSSEPageProps {
  params: Promise<{ id: string }>;
}

export default function ChatflowSSEPage({ params }: ChatflowSSEPageProps) {
  const router = useRouter();
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  
  // Unwrap params
  const { id } = React.use(params);
  
  // Fetch chatflow data
  const { data: flowData, isLoading: flowLoading, error } = useQuery({
    queryKey: ['chatflow', id],
    queryFn: () => flowsAPI.getFlow(id),
    enabled: !!id && isAuthenticated,
  });
  
  // Authentication check
  React.useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login');
    }
  }, [authLoading, isAuthenticated, router]);
  
  // Loading states
  if (authLoading) {
    return (
      <div className="container mx-auto p-6 max-w-6xl h-screen flex flex-col">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="flex-1 w-full" />
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Card className="border-yellow-500">
          <CardContent className="pt-6">
            <p className="text-yellow-600">로그인이 필요합니다. 잠시 후 로그인 페이지로 이동합니다...</p>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  if (flowLoading) {
    return (
      <div className="container mx-auto p-6 max-w-6xl h-screen flex flex-col">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="flex-1 w-full" />
      </div>
    );
  }
  
  if (error || !flowData) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-red-500">
              Chatflow를 불러오는데 실패했습니다: {error?.message || 'Unknown error'}
            </p>
            <Button 
              variant="outline" 
              onClick={() => router.back()}
              className="mt-4"
            >
              돌아가기
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  const flowConfig = flowData as any;
  
  return (
    <div className="container mx-auto p-6 max-w-6xl h-screen flex flex-col">
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
            {flowConfig.name}
          </h1>
          <p className="text-muted-foreground mt-1 flex items-center gap-2">
            <Zap className="h-4 w-4" />
            SSE 실시간 채팅 (향상된 성능)
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">
            <Zap className="h-3 w-3 mr-1" />
            SSE 스트리밍
          </Badge>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => router.push(`/agent-builder/chatflows/${id}/chat`)}
          >
            기존 채팅으로 이동
          </Button>
          
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => router.push(`/agent-builder/chatflows/${id}`)}
          >
            설정
          </Button>
        </div>
      </div>
      
      {/* Chat Interface */}
      <div className="flex-1 min-h-0">
        <ChatflowSSEInterface
          chatflowId={id}
          className="h-full"
          placeholder={flowConfig.chat_config?.input_placeholder || "메시지를 입력하세요..."}
          showToolCalls={true}
          showThinking={true}
        />
      </div>
      
      {/* Footer Info */}
      <div className="mt-4 text-center">
        <div className="text-xs text-muted-foreground space-x-4">
          <span>💡 SSE 기반 실시간 스트리밍</span>
          <span>🔄 자동 재연결</span>
          <span>⚡ 향상된 성능</span>
          <span>🛡️ 안정적인 연결</span>
        </div>
      </div>
    </div>
  );
}