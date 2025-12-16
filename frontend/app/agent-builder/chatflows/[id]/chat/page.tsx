'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Send,
  MessageSquare,
  Bot,
  User,
  Loader2,
  RefreshCw,
  Download,
  Settings,
  Trash,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
}

export default function ChatflowChatPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { toast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Unwrap params using React.use()
  const { id } = React.use(params);
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session-${Date.now()}`);

  const { data: flowData, isLoading: flowLoading } = useQuery({
    queryKey: ['chatflow', id],
    queryFn: () => flowsAPI.getFlow(id),
  });

  const flow = flowData as any;

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Initialize with welcome message
  useEffect(() => {
    if (flow && messages.length === 0) {
      const welcomeMessage = flow.chat_config?.welcome_message || '안녕하세요! 무엇을 도와드릴까요?';
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: welcomeMessage,
        timestamp: new Date(),
      }]);
    }
  }, [flow, messages.length]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Simulate streaming response
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isStreaming: true,
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Simulate AI response with streaming
      const responses = [
        '네, 도움을 드리겠습니다.',
        '질문을 분석하고 있습니다...',
        '관련 정보를 검색 중입니다.',
        flow.rag_config?.enabled ? 'RAG 시스템을 통해 문서를 검색했습니다.' : '',
        '답변을 생성하고 있습니다.',
        `"${userMessage.content}"에 대한 답변입니다: 이것은 시뮬레이션된 응답입니다. 실제 구현에서는 백엔드 API를 호출하여 LLM 응답을 받아옵니다.`,
      ].filter(Boolean);

      for (let i = 0; i < responses.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 800));
        
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessage.id 
            ? { 
                ...msg, 
                content: responses.slice(0, i + 1).join(' '),
                isStreaming: i < responses.length - 1
              }
            : msg
        ));
      }

    } catch (error: any) {
      toast({
        title: '오류',
        description: error.message || '메시지 전송에 실패했습니다',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  const handleClearChat = () => {
    setMessages([]);
    if (flow) {
      const welcomeMessage = flow.chat_config?.welcome_message || '안녕하세요! 무엇을 도와드릴까요?';
      setMessages([{
        id: 'welcome-new',
        role: 'assistant',
        content: welcomeMessage,
        timestamp: new Date(),
      }]);
    }
  };

  const handleExportChat = () => {
    const chatData = {
      flowId: id,
      flowName: flow?.name,
      sessionId,
      messages: messages.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp.toISOString(),
      })),
      exportedAt: new Date().toISOString(),
    };

    const blob = new Blob([JSON.stringify(chatData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-${flow?.name || 'chatflow'}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: '내보내기 완료',
      description: '채팅 기록이 다운로드되었습니다',
    });
  };

  if (flowLoading) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!flow) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-red-500">Chatflow를 불러오는데 실패했습니다</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl h-screen flex flex-col">
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
          <p className="text-muted-foreground mt-1">실시간 채팅</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="icon" onClick={handleClearChat}>
            <Trash className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={handleExportChat}>
            <Download className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={() => router.push(`/agent-builder/chatflows/${id}`)}>
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Chat Container */}
      <Card className="flex-1 flex flex-col border-2">
        {/* Chat Header */}
        <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">채팅</CardTitle>
              <CardDescription>
                {flow.rag_config?.enabled && (
                  <Badge variant="secondary" className="mr-2">
                    RAG 활성화
                  </Badge>
                )}
                {flow.memory_config && (
                  <Badge variant="outline">
                    메모리: {flow.memory_config.type}
                  </Badge>
                )}
              </CardDescription>
            </div>
            <Badge variant="outline">
              {messages.length - 1} 메시지
            </Badge>
          </div>
        </CardHeader>

        {/* Messages */}
        <CardContent className="flex-1 p-0">
          <ScrollArea className="h-full p-4">
            <div className="space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                    </div>
                  )}
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      message.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-800 text-foreground'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {message.isStreaming && (
                      <Loader2 className="h-3 w-3 animate-spin mt-1 opacity-50" />
                    )}
                    <p className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                  {message.role === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                      <User className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>
        </CardContent>

        {/* Suggested Questions */}
        {flow.chat_config?.suggested_questions && flow.chat_config.suggested_questions.length > 0 && messages.length <= 1 && (
          <div className="border-t p-4">
            <p className="text-sm text-muted-foreground mb-2">추천 질문:</p>
            <div className="flex flex-wrap gap-2">
              {flow.chat_config.suggested_questions.map((question: string, index: number) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleSuggestedQuestion(question)}
                  className="text-xs"
                >
                  {question}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="메시지를 입력하세요..."
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              disabled={isLoading}
              className="flex-1"
            />
            <Button 
              onClick={handleSend} 
              disabled={!input.trim() || isLoading}
              className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}