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
import { v4 as uuidv4 } from 'uuid';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI, ChatMessage, ChatRequest } from '@/lib/api/flows';
import { useAuth } from '@/contexts/AuthContext';

// Import sessionAPI separately to avoid potential circular dependency issues
import { sessionAPI } from '@/lib/api/flows';

export default function ChatflowChatPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { toast } = useToast();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  
  // Unwrap params using React.use()
  const { id } = React.use(params);
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => uuidv4());
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const [memoryType, setMemoryType] = useState<string>('buffer');
  const [memoryConfig, setMemoryConfig] = useState<any>({
    buffer_size: 20,
    summary_threshold: 50,
    summary_interval: 20,
    vector_top_k: 5,
    max_context_messages: 20,
    hybrid_weights: {
      buffer: 0.4,
      summary: 0.3,
      vector: 0.3
    }
  });
  const [showMemorySettings, setShowMemorySettings] = useState(false);
  const [showLLMSettings, setShowLLMSettings] = useState(false);
  const [llmProvider, setLlmProvider] = useState<string>('ollama');
  const [llmModel, setLlmModel] = useState<string>('llama3.3:70b');
  const [llmConfig, setLlmConfig] = useState<any>({});

  const { data: flowData, isLoading: flowLoading } = useQuery({
    queryKey: ['chatflow', id],
    queryFn: () => flowsAPI.getFlow(id),
  });

  // Query for LLM configuration
  const { data: llmConfiguration, isLoading: llmConfigLoading } = useQuery({
    queryKey: ['llm-configuration'],
    queryFn: async () => {
      const { llmSettingsAPI } = await import('@/lib/api/llm-settings');
      return llmSettingsAPI.getConfiguration();
    },
  });

  // Query for chatflow-specific LLM configuration
  const { data: chatflowLLMConfig, isLoading: chatflowLLMConfigLoading } = useQuery({
    queryKey: ['chatflow-llm-config', id],
    queryFn: async () => {
      const { llmSettingsAPI } = await import('@/lib/api/llm-settings');
      return llmSettingsAPI.getChatflowConfig(id);
    },
    enabled: !!id,
  });

  // Initialize LLM settings from chatflow-specific config or global configuration
  useEffect(() => {
    if (flowData && llmConfiguration) {
      const flowConfig = flowData as any;
      const chatConfig = flowConfig.chat_config || {};
      
      // Priority: chatflow-specific config > flow config > global config
      if (chatflowLLMConfig?.success && chatflowLLMConfig.config) {
        const config = chatflowLLMConfig.config;
        setLlmProvider(config.provider);
        setLlmModel(config.model);
        setLlmConfig({
          temperature: config.temperature,
          max_tokens: config.max_tokens,
          system_prompt: config.system_prompt || '',
        });
      } else {
        // Fallback to flow config or global config
        setLlmProvider(chatConfig.llm_provider || llmConfiguration.provider);
        setLlmModel(chatConfig.llm_model || llmConfiguration.model);
        setLlmConfig({
          temperature: chatConfig.temperature || 0.7,
          max_tokens: chatConfig.max_tokens || 2000,
          system_prompt: chatConfig.system_prompt || '',
        });
      }
    }
  }, [flowData, llmConfiguration, chatflowLLMConfig]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Authentication check - redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      console.log('🔐 User not authenticated, redirecting to login');
      toast({
        title: '로그인 필요',
        description: '채팅을 사용하려면 로그인이 필요합니다.',
        variant: 'destructive',
      });
      router.push('/auth/login');
      return;
    }
  }, [authLoading, isAuthenticated, router, toast]);

  // Load session on mount if sessionId exists in localStorage
  useEffect(() => {
    // Skip session loading if still checking auth
    if (authLoading) return;

    const savedSessionId = localStorage.getItem(`chatflow-session-${id}`);
    if (savedSessionId) {
      setSessionId(savedSessionId);
      loadSessionHistory(savedSessionId);
    }

    // DEBUG: Check token status
    const token = localStorage.getItem('access_token');
    const isDevelopment = process.env.NODE_ENV === 'development';
    
    console.log('🔐 Authentication status:');
    console.log('  - Environment:', isDevelopment ? 'Development' : 'Production');
    console.log('  - User authenticated:', isAuthenticated);
    console.log('  - User email:', user?.email || 'N/A');
    console.log('  - Token exists:', token ? 'YES' : 'NO');
    
    if (token) {
      if (token.startsWith('dev-fake-token-')) {
        console.log('  - Token type: Development fake token');
      } else {
        console.log('  - Token type: Real JWT token');
        console.log('  - Token format valid:', token.split('.').length === 3);
        console.log('  - Token preview:', token.substring(0, 20) + '...');
        
        // Check if token is expired (basic check)
        try {
          const payload = JSON.parse(atob(token.split('.')[1]));
          const exp = payload.exp * 1000; // Convert to milliseconds
          const now = Date.now();
          console.log('  - Token expired:', now > exp);
          console.log('  - Expires at:', new Date(exp).toLocaleString());
        } catch (e) {
          console.log('  - Token decode error:', e.message);
        }
      }
    }
  }, [id, isAuthenticated, authLoading, user]);

  // Save sessionId to localStorage when it changes
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(`chatflow-session-${id}`, sessionId);
    }
  }, [sessionId, id]);

  const loadSessionHistory = async (sessionId: string) => {
    try {
      // Check if sessionAPI is available
      if (!sessionAPI || typeof sessionAPI.getSession !== 'function') {
        console.warn('sessionAPI.getSession is not available');
        return;
      }
      
      const response = await sessionAPI.getSession(sessionId) as any;
      if (response && response.success && response.messages) {
        const loadedMessages = response.messages.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
        }));
        setMessages(loadedMessages);
        console.log(`Loaded ${loadedMessages.length} messages from session history`);
      } else {
        console.log('No messages found in session history');
      }
    } catch (error: any) {
      // Handle 404 errors gracefully - session doesn't exist
      if (error?.status === 404 || error?.message?.includes('Session not found') || error?.message?.includes('not found')) {
        console.log(`Session ${sessionId} not found, starting fresh conversation`);
        // Clear the invalid session ID from localStorage
        localStorage.removeItem(`chatflow-session-${id}`);
        // Generate a new session ID
        const newSessionId = uuidv4();
        setSessionId(newSessionId);
        return;
      }
      
      // Handle 400 errors for invalid UUID format
      if (error?.status === 400 || error?.message?.includes('Invalid session ID format')) {
        console.log(`Invalid session ID format: ${sessionId}, generating new session`);
        // Clear the invalid session ID from localStorage
        localStorage.removeItem(`chatflow-session-${id}`);
        // Generate a new session ID
        const newSessionId = uuidv4();
        setSessionId(newSessionId);
        return;
      }
      
      console.error('Failed to load session history:', error);
      // Don't show error to user for missing session history - it's normal for new sessions
    }
  };

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [eventSource]);

  const handleSend = async () => {
    if (!input.trim() || isLoading || !flowData) return;

    // Check authentication
    if (!isAuthenticated) {
      toast({
        title: '인증 오류',
        description: '로그인이 필요합니다. 페이지를 새로고침해주세요.',
        variant: 'destructive',
      });
      router.push('/auth/login');
      return;
    }

    const flowConfig = flowData as any; // Type assertion for chatflow
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    // Close any existing EventSource
    if (eventSource) {
      eventSource.close();
    }

    // Create assistant message for streaming
    const assistantMessage: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    try {
      setMessages(prev => [...prev, assistantMessage]);

      // Prepare chat request with dynamic LLM settings
      const chatRequest: ChatRequest = {
        message: userMessage.content,
        session_id: sessionId,
        workflow_id: id,
        config: {
          provider: llmProvider,
          model: llmModel,
          temperature: llmConfig.temperature || 0.7,
          max_tokens: llmConfig.max_tokens || 2000,
          system_prompt: llmConfig.system_prompt || flowConfig.chat_config?.system_prompt,
          memory_type: memoryType,
          memory_config: memoryConfig,
        },
      };

      // Fallback function for non-streaming API
      async function fallbackToNonStreaming() {
        try {
          const response = await flowsAPI.sendWorkflowChatMessage(id, chatRequest);
          
          if (response.success && response.response) {
            setMessages(prev => prev.map(msg => 
              msg.id === assistantMessage.id 
                ? { ...msg, content: response.response!, isStreaming: false }
                : msg
            ));
          } else {
            throw new Error(response.error || 'Failed to get response');
          }
          
          setIsLoading(false);
        } catch (error: any) {
          console.error('Non-streaming API error:', error);
          
          // Check if it's an authentication error
          if (error?.status === 401 || error?.message?.includes('Authentication')) {
            toast({
              title: '인증 만료',
              description: '로그인이 만료되었습니다. 다시 로그인해주세요.',
              variant: 'destructive',
            });
            router.push('/auth/login');
            return;
          }
          
          // Update assistant message with error
          setMessages(prev => prev.map(msg => 
            msg.id === assistantMessage.id 
              ? { 
                  ...msg, 
                  content: '죄송합니다. 현재 AI 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.',
                  isStreaming: false 
                }
              : msg
          ));
          
          toast({
            title: '서비스 오류',
            description: 'AI 서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.',
            variant: 'destructive',
          });
          
          setIsLoading(false);
        }
      }

      // Use streaming if enabled
      if (flowConfig.chat_config?.streaming !== false) {
        try {
          const eventSource = flowsAPI.createWorkflowChatStream(id, chatRequest);
          setEventSource(eventSource);

          let hasReceivedData = false;

          eventSource.onmessage = (event) => {
            try {
              hasReceivedData = true;
              const data = JSON.parse(event.data);
              
              if (data.type === 'content') {
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessage.id 
                    ? { ...msg, content: msg.content + data.content }
                    : msg
                ));
              } else if (data.type === 'done') {
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessage.id 
                    ? { ...msg, isStreaming: false }
                    : msg
                ));
                setIsLoading(false);
                eventSource.close();
                setEventSource(null);
              } else if (data.type === 'error') {
                throw new Error(data.error || 'Streaming error occurred');
              }
            } catch (error) {
              console.error('Error parsing SSE data:', error);
            }
          };

          eventSource.onerror = (error) => {
            console.error('EventSource error:', error);
            eventSource.close();
            setEventSource(null);
            
            // If we haven't received any data, fallback to non-streaming
            if (!hasReceivedData) {
              console.log('Falling back to non-streaming API...');
              fallbackToNonStreaming();
            } else {
              setMessages(prev => prev.map(msg => 
                msg.id === assistantMessage.id 
                  ? { ...msg, content: msg.content || '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.', isStreaming: false }
                  : msg
              ));
              setIsLoading(false);
              
              toast({
                title: '연결 오류',
                description: '스트리밍 연결에 문제가 발생했습니다.',
                variant: 'destructive',
              });
            }
          };

          // Timeout fallback after 10 seconds
          setTimeout(() => {
            if (!hasReceivedData && eventSource.readyState !== EventSource.CLOSED) {
              console.log('Streaming timeout, falling back to non-streaming API...');
              eventSource.close();
              setEventSource(null);
              fallbackToNonStreaming();
            }
          }, 10000);

        } catch (error: any) {
          console.error('Failed to create EventSource:', error);
          
          // Check if it's an authentication error
          if (error?.message?.includes('Authentication')) {
            toast({
              title: '인증 오류',
              description: '로그인이 필요합니다. 다시 로그인해주세요.',
              variant: 'destructive',
            });
            router.push('/auth/login');
            return;
          }
          
          fallbackToNonStreaming();
        }
      } else {
        fallbackToNonStreaming();
      }

    } catch (error: any) {
      console.error('Chat error:', error);
      
      // Check if it's an authentication error
      if (error?.status === 401 || error?.message?.includes('Authentication')) {
        toast({
          title: '인증 만료',
          description: '로그인이 만료되었습니다. 다시 로그인해주세요.',
          variant: 'destructive',
        });
        router.push('/auth/login');
        return;
      }
      
      // Update assistant message with error
      setMessages(prev => prev.map(msg => 
        msg.id === assistantMessage.id 
          ? { 
              ...msg, 
              content: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다. 다시 시도해주세요.',
              isStreaming: false 
            }
          : msg
      ));
      
      toast({
        title: '오류',
        description: error.message || '메시지 전송에 실패했습니다',
        variant: 'destructive',
      });
      
      setIsLoading(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  const handleClearChat = async () => {
    try {
      // Clear session on backend
      await flowsAPI.clearChatSession(sessionId);
      
      // Clear local messages
      setMessages([]);
      
      if (flowData) {
        const flowConfig = flowData as any;
        const welcomeMessage = flowConfig.chat_config?.welcome_message || '안녕하세요! 무엇을 도와드릴까요?';
        setMessages([{
          id: 'welcome-new',
          role: 'assistant',
          content: welcomeMessage,
          timestamp: new Date(),
        }]);
      }
      
      toast({
        title: '채팅 초기화',
        description: '채팅 기록이 초기화되었습니다',
      });
    } catch (error: any) {
      console.error('Clear chat error:', error);
      // Still clear local messages even if backend fails
      setMessages([]);
      if (flowData) {
        const flowConfig = flowData as any;
        const welcomeMessage = flowConfig.chat_config?.welcome_message || '안녕하세요! 무엇을 도와드릴까요?';
        setMessages([{
          id: 'welcome-new',
          role: 'assistant',
          content: welcomeMessage,
          timestamp: new Date(),
        }]);
      }
    }
  };

  const handleExportChat = () => {
    const chatData = {
      flowId: id,
      flowName: (flowData as any)?.name,
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
    a.download = `chat-${(flowData as any)?.name || 'chatflow'}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: '내보내기 완료',
      description: '채팅 기록이 다운로드되었습니다',
    });
  };

  if (authLoading) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto p-6 max-w-4xl">
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
      <div className="container mx-auto p-6 max-w-4xl">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!flowData) {
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
            {(flowData as any).name}
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
          <Button variant="outline" size="icon" onClick={() => setShowMemorySettings(!showMemorySettings)}>
            <Settings className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={() => setShowLLMSettings(!showLLMSettings)}>
            <Bot className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" onClick={() => router.push(`/agent-builder/chatflows/${id}`)}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* LLM Settings Panel */}
      {showLLMSettings && (
        <Card className="mb-4 border-green-200 bg-green-50/50 dark:bg-green-950/20">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Bot className="h-5 w-5" />
              LLM 설정
            </CardTitle>
            <CardDescription>
              대화에 사용할 AI 모델을 선택하고 설정을 조정하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {(llmConfigLoading || chatflowLLMConfigLoading) ? (
              <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-10 w-full" />
              </div>
            ) : llmConfiguration ? (
              <>
                <div>
                  <label className="text-sm font-medium mb-2 block">AI 제공업체</label>
                  <select
                    value={llmProvider}
                    onChange={(e) => {
                      const newProvider = e.target.value;
                      setLlmProvider(newProvider);
                      
                      // Find the provider and set the first available model
                      const provider = llmConfiguration.providers.find(p => p.name === newProvider);
                      if (provider && provider.models && provider.models.length > 0) {
                        setLlmModel(provider.models[0] || '');
                      }
                    }}
                    className="w-full p-2 border rounded-md bg-background"
                  >
                    {llmConfiguration.providers
                      .filter(provider => provider.is_available)
                      .map(provider => (
                        <option key={provider.name} value={provider.name}>
                          {provider.display_name}
                          {!provider.is_available && ' (사용 불가)'}
                        </option>
                      ))}
                  </select>
                  {llmConfiguration.providers.find(p => p.name === llmProvider)?.requires_api_key && (
                    <p className="text-xs text-muted-foreground mt-1">
                      💡 이 제공업체는 API 키가 필요합니다. Settings에서 설정해주세요.
                    </p>
                  )}
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">AI 모델</label>
                  <select
                    value={llmModel}
                    onChange={(e) => setLlmModel(e.target.value)}
                    className="w-full p-2 border rounded-md bg-background"
                  >
                    {(llmConfiguration.providers
                      .find(p => p.name === llmProvider)?.models || [])
                      .map(model => (
                        <option key={model} value={model}>
                          {model}
                        </option>
                      ))}
                  </select>
                  <div className="flex items-center gap-2 mt-2">
                    <div className={`w-2 h-2 rounded-full ${
                      llmConfiguration.providers.find(p => p.name === llmProvider)?.is_available 
                        ? 'bg-green-500' 
                        : 'bg-red-500'
                    }`} />
                    <span className="text-xs text-muted-foreground">
                      {llmConfiguration.providers.find(p => p.name === llmProvider)?.is_available 
                        ? '사용 가능' 
                        : '사용 불가'}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    창의성 (Temperature): {llmConfig.temperature || 0.7}
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="0.1"
                    value={llmConfig.temperature || 0.7}
                    onChange={(e) => setLlmConfig({
                      ...llmConfig,
                      temperature: parseFloat(e.target.value)
                    })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>보수적 (0.0)</span>
                    <span>균형 (1.0)</span>
                    <span>창의적 (2.0)</span>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">
                    최대 토큰 수: {llmConfig.max_tokens || 2000}
                  </label>
                  <input
                    type="range"
                    min="100"
                    max="4000"
                    step="100"
                    value={llmConfig.max_tokens || 2000}
                    onChange={(e) => setLlmConfig({
                      ...llmConfig,
                      max_tokens: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-1">
                    <span>짧음 (100)</span>
                    <span>보통 (2000)</span>
                    <span>길음 (4000)</span>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">시스템 프롬프트 (선택사항)</label>
                  <textarea
                    value={llmConfig.system_prompt || ''}
                    onChange={(e) => setLlmConfig({
                      ...llmConfig,
                      system_prompt: e.target.value
                    })}
                    placeholder="AI의 역할이나 행동 방식을 지정하세요..."
                    className="w-full p-2 border rounded-md bg-background min-h-[80px] resize-none"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    시스템 프롬프트는 AI의 전반적인 행동을 정의합니다.
                  </p>
                </div>

                <div className="bg-gradient-to-r from-green-50 to-blue-50 p-3 rounded text-sm text-muted-foreground">
                  <div className="flex items-center gap-2 mb-2">
                    <Bot className="h-4 w-4" />
                    <span className="font-medium">현재 설정</span>
                  </div>
                  <div className="space-y-1">
                    <div>제공업체: <span className="font-mono">{llmProvider}</span></div>
                    <div>모델: <span className="font-mono">{llmModel}</span></div>
                    <div>창의성: <span className="font-mono">{llmConfig.temperature || 0.7}</span></div>
                    <div>최대 토큰: <span className="font-mono">{llmConfig.max_tokens || 2000}</span></div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-4 text-muted-foreground">
                LLM 설정을 불러올 수 없습니다
              </div>
            )}

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowLLMSettings(false)}
              >
                닫기
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (llmConfiguration) {
                    setLlmProvider(llmConfiguration.provider);
                    setLlmModel(llmConfiguration.model);
                    setLlmConfig({
                      temperature: 0.7,
                      max_tokens: 2000,
                      system_prompt: '',
                    });
                    toast({
                      title: '설정 초기화',
                      description: '기본 설정으로 초기화되었습니다',
                    });
                  }
                }}
              >
                초기화
              </Button>
              <Button
                size="sm"
                onClick={async () => {
                  try {
                    const { llmSettingsAPI } = await import('@/lib/api/llm-settings');
                    
                    const configToSave = {
                      provider: llmProvider,
                      model: llmModel,
                      temperature: llmConfig.temperature || 0.7,
                      max_tokens: llmConfig.max_tokens || 2000,
                      system_prompt: llmConfig.system_prompt || undefined,
                    };
                    
                    const response = await llmSettingsAPI.updateChatflowConfig(id, configToSave);
                    
                    if (response.success) {
                      toast({
                        title: '설정 저장됨',
                        description: `${llmProvider}/${llmModel} 설정이 저장되었습니다`,
                      });
                    } else {
                      toast({
                        title: '설정 저장 실패',
                        description: response.message,
                        variant: 'destructive',
                      });
                    }
                  } catch (error: any) {
                    toast({
                      title: '설정 저장 실패',
                      description: error.message || '설정 저장 중 오류가 발생했습니다',
                      variant: 'destructive',
                    });
                  }
                  
                  setShowLLMSettings(false);
                }}
              >
                저장 및 적용
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Memory Settings Panel */}
      {showMemorySettings && (
        <Card className="mb-4 border-blue-200 bg-blue-50/50 dark:bg-blue-950/20">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Settings className="h-5 w-5" />
              메모리 설정
            </CardTitle>
            <CardDescription>
              대화 기억 방식을 설정하여 더 나은 대화 경험을 만들어보세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">메모리 전략</label>
              <select
                value={memoryType}
                onChange={(e) => setMemoryType(e.target.value)}
                className="w-full p-2 border rounded-md bg-background"
              >
                <option value="buffer">Buffer Memory - 최근 N개 메시지 유지</option>
                <option value="summary">Summary Memory - 오래된 대화 요약</option>
                <option value="vector">Vector Memory - 의미적 검색</option>
                <option value="hybrid">Hybrid Memory - 복합 전략 (최고 성능)</option>
              </select>
            </div>

            {memoryType === 'buffer' && (
              <div>
                <label className="text-sm font-medium mb-2 block">
                  버퍼 크기: {memoryConfig.buffer_size}개 메시지
                </label>
                <input
                  type="range"
                  min="5"
                  max="50"
                  value={memoryConfig.buffer_size}
                  onChange={(e) => setMemoryConfig({
                    ...memoryConfig,
                    buffer_size: parseInt(e.target.value)
                  })}
                  className="w-full"
                />
              </div>
            )}

            {memoryType === 'summary' && (
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    요약 시작 메시지 수: {memoryConfig.summary_threshold}개
                  </label>
                  <input
                    type="range"
                    min="20"
                    max="100"
                    value={memoryConfig.summary_threshold}
                    onChange={(e) => setMemoryConfig({
                      ...memoryConfig,
                      summary_threshold: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    요약 주기: {memoryConfig.summary_interval}개 메시지
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="50"
                    value={memoryConfig.summary_interval}
                    onChange={(e) => setMemoryConfig({
                      ...memoryConfig,
                      summary_interval: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>
              </div>
            )}

            {memoryType === 'vector' && (
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    검색할 관련 메시지 수: {memoryConfig.vector_top_k || 5}개
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={memoryConfig.vector_top_k || 5}
                    onChange={(e) => setMemoryConfig({
                      ...memoryConfig,
                      vector_top_k: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    최근 메시지 버퍼: {memoryConfig.buffer_size || 5}개
                  </label>
                  <input
                    type="range"
                    min="3"
                    max="15"
                    value={memoryConfig.buffer_size || 5}
                    onChange={(e) => setMemoryConfig({
                      ...memoryConfig,
                      buffer_size: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>
                <div className="text-sm text-muted-foreground bg-blue-50 p-2 rounded">
                  💡 Vector Memory는 의미적으로 유사한 이전 대화를 찾아 컨텍스트로 제공합니다.
                </div>
              </div>
            )}

            {memoryType === 'hybrid' && (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">전략 가중치</label>
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">Buffer (최근 메시지)</span>
                        <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                          {((memoryConfig.hybrid_weights?.buffer || 0.4) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={memoryConfig.hybrid_weights?.buffer || 0.4}
                        onChange={(e) => setMemoryConfig({
                          ...memoryConfig,
                          hybrid_weights: {
                            ...memoryConfig.hybrid_weights,
                            buffer: parseFloat(e.target.value),
                            summary: memoryConfig.hybrid_weights?.summary || 0.3,
                            vector: memoryConfig.hybrid_weights?.vector || 0.3
                          }
                        })}
                        className="w-full"
                      />
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">Summary (요약)</span>
                        <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                          {((memoryConfig.hybrid_weights?.summary || 0.3) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={memoryConfig.hybrid_weights?.summary || 0.3}
                        onChange={(e) => setMemoryConfig({
                          ...memoryConfig,
                          hybrid_weights: {
                            ...memoryConfig.hybrid_weights,
                            buffer: memoryConfig.hybrid_weights?.buffer || 0.4,
                            summary: parseFloat(e.target.value),
                            vector: memoryConfig.hybrid_weights?.vector || 0.3
                          }
                        })}
                        className="w-full"
                      />
                    </div>
                    
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm">Vector (의미적 검색)</span>
                        <span className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                          {((memoryConfig.hybrid_weights?.vector || 0.3) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={memoryConfig.hybrid_weights?.vector || 0.3}
                        onChange={(e) => setMemoryConfig({
                          ...memoryConfig,
                          hybrid_weights: {
                            ...memoryConfig.hybrid_weights,
                            buffer: memoryConfig.hybrid_weights?.buffer || 0.4,
                            summary: memoryConfig.hybrid_weights?.summary || 0.3,
                            vector: parseFloat(e.target.value)
                          }
                        })}
                        className="w-full"
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    최대 컨텍스트 메시지: {memoryConfig.max_context_messages || 20}개
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="50"
                    value={memoryConfig.max_context_messages || 20}
                    onChange={(e) => setMemoryConfig({
                      ...memoryConfig,
                      max_context_messages: parseInt(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>
                
                <div className="text-sm text-muted-foreground bg-gradient-to-r from-blue-50 to-purple-50 p-3 rounded">
                  🚀 Hybrid Memory는 상황에 따라 최적의 메모리 전략을 자동으로 선택합니다.
                  <br />
                  • 후속 질문: Buffer + Vector 우선
                  <br />
                  • 새로운 주제: Vector + Summary 우선
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowMemorySettings(false)}
              >
                닫기
              </Button>
              <Button
                size="sm"
                onClick={async () => {
                  try {
                    await sessionAPI.updateSessionMemory(sessionId, {
                      strategy: memoryType,
                      ...memoryConfig
                    });
                    toast({
                      title: '설정 저장됨',
                      description: '메모리 설정이 업데이트되었습니다',
                    });
                    setShowMemorySettings(false);
                  } catch (error) {
                    toast({
                      title: '설정 저장 실패',
                      description: '메모리 설정 저장에 실패했습니다',
                      variant: 'destructive',
                    });
                  }
                }}
              >
                저장
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Chat Container */}
      <Card className="flex-1 flex flex-col border-2">
        {/* Chat Header */}
        <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">채팅</CardTitle>
              <CardDescription>
                {(flowData as any).rag_config?.enabled && (
                  <Badge variant="secondary" className="mr-2">
                    RAG 활성화
                  </Badge>
                )}
                <Badge variant="outline" className="mr-2">
                  메모리: {memoryType === 'buffer' ? '버퍼' : memoryType === 'summary' ? '요약' : memoryType}
                </Badge>
                <Badge variant="outline">
                  세션: {sessionId.slice(-8)}
                </Badge>
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
        {(flowData as any).chat_config?.suggested_questions && (flowData as any).chat_config.suggested_questions.length > 0 && messages.length <= 1 && (
          <div className="border-t p-4">
            <p className="text-sm text-muted-foreground mb-2">추천 질문:</p>
            <div className="flex flex-wrap gap-2">
              {(flowData as any).chat_config.suggested_questions.map((question: string, index: number) => (
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