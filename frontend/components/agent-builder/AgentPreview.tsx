"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  Bot, 
  Send, 
  Loader2, 
  FileText, 
  Folder, 
  Link as LinkIcon, 
  Server,
  CheckCircle2,
  XCircle,
  Brain
} from 'lucide-react';

import { ThinkingBlock, ThinkingIndicator, type ThinkingStep } from './chat/ThinkingBlock';
import { useChatStyleStore } from '@/lib/stores/chat-style-store';

interface ContextItem {
  id: string;
  type: 'file' | 'folder' | 'url' | 'text';
  name: string;
  value: string;
  enabled: boolean;
}

interface MCPServer {
  id: string;
  name: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  enabled: boolean;
}

interface AgentPreviewProps {
  agentName: string;
  agentDescription?: string;
  llmProvider: string;
  llmModel: string;
  contextItems: ContextItem[];
  mcpServers: MCPServer[];
  promptTemplate?: string;
}

export function AgentPreview({
  agentName,
  agentDescription,
  llmProvider,
  llmModel,
  contextItems,
  mcpServers,
  promptTemplate
}: AgentPreviewProps) {
  const { config: styleConfig } = useChatStyleStore();
  const [testMessage, setTestMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState<Array<{ 
    role: 'user' | 'assistant'; 
    content: string;
    thinkingSteps?: ThinkingStep[];
  }>>([]);
  const [showThinking, setShowThinking] = useState(true);
  const [currentThinkingSteps, setCurrentThinkingSteps] = useState<ThinkingStep[]>([]);

  const handleSendTest = async () => {
    if (!testMessage.trim()) return;

    setIsLoading(true);
    const userMessage = testMessage;
    setTestMessage('');

    // Add user message to chat
    setChatHistory(prev => [...prev, { role: 'user', content: userMessage }]);

    // Simulate thinking process
    const thinkingSteps: ThinkingStep[] = [];
    setCurrentThinkingSteps([]);

    // Step 1: Analyzing
    await new Promise(resolve => setTimeout(resolve, 300));
    const step1: ThinkingStep = {
      id: '1',
      type: 'analyzing',
      content: '사용자 메시지를 분석하고 있습니다...',
      timestamp: new Date(),
      status: 'completed'
    };
    thinkingSteps.push(step1);
    setCurrentThinkingSteps([...thinkingSteps]);

    // Step 2: Context check
    await new Promise(resolve => setTimeout(resolve, 300));
    const enabledContexts = contextItems.filter(c => c.enabled).length;
    const step2: ThinkingStep = {
      id: '2',
      type: 'searching',
      content: enabledContexts > 0 
        ? `${enabledContexts}개의 컨텍스트에서 관련 정보를 검색하고 있습니다...`
        : '컨텍스트가 설정되지 않았습니다. 기본 지식으로 응답합니다.',
      timestamp: new Date(),
      status: 'completed'
    };
    thinkingSteps.push(step2);
    setCurrentThinkingSteps([...thinkingSteps]);

    // Step 3: Planning - 질문 복잡도에 따라 결정
    await new Promise(resolve => setTimeout(resolve, 300));
    const enabledMcpServers = mcpServers.filter(m => m.enabled).length;
    const isComplexQuery = userMessage.length > 20 || userMessage.includes('?') || userMessage.includes('어떻게') || userMessage.includes('무엇');
    
    if (isComplexQuery || enabledMcpServers > 0 || enabledContexts > 0) {
      let planningContent = '응답 전략을 수립하고 있습니다...';
      
      if (enabledMcpServers > 0) {
        planningContent = `${enabledMcpServers}개의 MCP 서버를 활용한 응답 전략을 수립하고 있습니다...`;
      } else if (enabledContexts > 0) {
        planningContent = `컨텍스트 정보를 활용한 응답 전략을 수립하고 있습니다...`;
      } else if (isComplexQuery) {
        planningContent = '복잡한 질문에 대한 단계별 응답 전략을 수립하고 있습니다...';
      }
      
      const step3: ThinkingStep = {
        id: '3',
        type: 'planning',
        content: planningContent,
        timestamp: new Date(),
        status: 'completed'
      };
      thinkingSteps.push(step3);
      setCurrentThinkingSteps([...thinkingSteps]);
      await new Promise(resolve => setTimeout(resolve, 300));
    }

    // Step 4: Reasoning
    const step4: ThinkingStep = {
      id: '4',
      type: 'reasoning',
      content: `${llmProvider}/${llmModel} 모델을 사용하여 최적의 응답을 생성하고 있습니다...`,
      timestamp: new Date(),
      status: 'completed'
    };
    thinkingSteps.push(step4);
    setCurrentThinkingSteps([...thinkingSteps]);
    await new Promise(resolve => setTimeout(resolve, 300));

    // Step 5: Synthesizing
    const step5: ThinkingStep = {
      id: '5',
      type: 'synthesizing',
      content: '최종 응답을 종합하고 있습니다...',
      timestamp: new Date(),
      status: 'completed'
    };
    thinkingSteps.push(step5);
    setCurrentThinkingSteps([...thinkingSteps]);
    await new Promise(resolve => setTimeout(resolve, 300));

    // Generate response
    let responseMessage = `안녕하세요! 저는 **"${agentName}"** 에이전트입니다. 👋\n\n`;
    
    // Add a personalized greeting based on the message
    if (userMessage.toLowerCase().includes('안녕') || userMessage.toLowerCase().includes('hello')) {
      responseMessage += `반갑습니다! 무엇을 도와드릴까요?\n\n`;
    } else {
      responseMessage += `"${userMessage.length > 50 ? userMessage.substring(0, 50) + '...' : userMessage}"에 대해 답변드리겠습니다.\n\n`;
    }
    
    responseMessage += `### 📋 현재 설정\n\n`;
    responseMessage += `- **LLM 모델**: ${llmProvider}/${llmModel}\n`;
    
    if (enabledContexts > 0) {
      const contextList = contextItems.filter(c => c.enabled).map(c => c.name).slice(0, 3).join(', ');
      responseMessage += `- **Context**: ${enabledContexts}개 활성화 (${contextList}${contextItems.filter(c => c.enabled).length > 3 ? '...' : ''})\n`;
    } else {
      responseMessage += `- **Context**: 없음\n`;
    }
    
    if (enabledMcpServers > 0) {
      const mcpList = mcpServers.filter(m => m.enabled).map(m => m.name).slice(0, 3).join(', ');
      responseMessage += `- **MCP 서버**: ${enabledMcpServers}개 연결 (${mcpList}${mcpServers.filter(m => m.enabled).length > 3 ? '...' : ''})\n`;
    } else {
      responseMessage += `- **MCP 서버**: 없음\n`;
    }
    
    responseMessage += `\n---\n\n`;
    
    if (enabledContexts === 0 && enabledMcpServers === 0) {
      responseMessage += `💡 **추천**: Step 3의 **Context**와 **MCP** 탭에서 추가 기능을 설정하면 더 강력한 Agent를 만들 수 있습니다!\n\n`;
      responseMessage += `- **Context**: 파일, 문서, URL을 추가하여 Agent에게 배경 지식 제공\n`;
      responseMessage += `- **MCP**: 외부 도구(검색, 데이터베이스 등)를 연결하여 실시간 정보 활용\n\n`;
    } else {
      responseMessage += `✅ 설정이 완료되었습니다! Agent 생성 후 실제 대화를 시작할 수 있습니다.\n\n`;
    }
    
    responseMessage += `📝 **참고**: 이것은 시뮬레이션입니다. Agent를 생성하면 실제 LLM 모델과 대화할 수 있습니다.`;
    
    setChatHistory(prev => [
      ...prev,
      {
        role: 'assistant',
        content: responseMessage,
        thinkingSteps: thinkingSteps
      }
    ]);
    setCurrentThinkingSteps([]);
    setIsLoading(false);
  };

  const getContextIcon = (type: string) => {
    switch (type) {
      case 'file': return <FileText className="h-4 w-4" />;
      case 'folder': return <Folder className="h-4 w-4" />;
      case 'url': return <LinkIcon className="h-4 w-4" />;
      default: return <FileText className="h-4 w-4" />;
    }
  };

  return (
    <div className="h-full flex flex-col space-y-4">
      {/* Agent Info */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">{agentName || 'Untitled Agent'}</CardTitle>
          </div>
          {agentDescription && (
            <CardDescription className="text-sm">{agentDescription}</CardDescription>
          )}
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-2 text-sm">
            <Badge variant="secondary">{llmProvider}</Badge>
            <Badge variant="outline">{llmModel}</Badge>
          </div>
          
          {/* Context Items */}
          {contextItems.length > 0 ? (
            <div className="space-y-2">
              <div className="text-sm font-medium flex items-center gap-2">
                <span>Context</span>
                <Badge variant="secondary" className="text-xs">
                  {contextItems.filter(c => c.enabled).length}/{contextItems.length}
                </Badge>
              </div>
              <div className="space-y-1">
                {contextItems.slice(0, 3).map((item, index) => (
                  <div key={`${item.id}-${index}`} className="flex items-center gap-2 text-xs">
                    {getContextIcon(item.type)}
                    <span className={item.enabled ? 'text-foreground' : 'text-muted-foreground line-through'}>
                      {item.name}
                    </span>
                    {item.enabled ? (
                      <CheckCircle2 className="h-3 w-3 text-green-500 ml-auto" />
                    ) : (
                      <XCircle className="h-3 w-3 text-muted-foreground ml-auto" />
                    )}
                  </div>
                ))}
                {contextItems.length > 3 && (
                  <div className="text-xs text-muted-foreground">
                    +{contextItems.length - 3} more
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">Context</div>
              <div className="text-xs text-muted-foreground bg-muted/50 rounded-md p-2 border border-dashed">
                💡 Step 3의 Context 탭에서 파일, 폴더, URL을 추가하세요
              </div>
            </div>
          )}

          {/* MCP Servers */}
          {mcpServers.length > 0 ? (
            <div className="space-y-2">
              <div className="text-sm font-medium flex items-center gap-2">
                <span>MCP Servers</span>
                <Badge variant="secondary" className="text-xs">
                  {mcpServers.filter(m => m.enabled).length}/{mcpServers.length}
                </Badge>
              </div>
              <div className="space-y-1">
                {mcpServers.slice(0, 3).map((server, index) => (
                  <div key={`${server.id}-${index}`} className="flex items-center gap-2 text-xs">
                    <Server className="h-4 w-4" />
                    <span className={server.enabled ? 'text-foreground' : 'text-muted-foreground line-through'}>
                      {server.name}
                    </span>
                    {server.enabled ? (
                      <CheckCircle2 className="h-3 w-3 text-green-500 ml-auto" />
                    ) : (
                      <XCircle className="h-3 w-3 text-muted-foreground ml-auto" />
                    )}
                  </div>
                ))}
                {mcpServers.length > 3 && (
                  <div className="text-xs text-muted-foreground">
                    +{mcpServers.length - 3} more
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">MCP Servers</div>
              <div className="text-xs text-muted-foreground bg-muted/50 rounded-md p-2 border border-dashed">
                🔌 Step 3의 MCP 탭에서 외부 도구를 연결하세요
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Test Chat */}
      <Card className="flex-1 flex flex-col" style={{ 
        borderRadius: `${styleConfig.borderRadius}px`,
      }}>
        <CardHeader 
          className="pb-3" 
          style={{ 
            backgroundColor: styleConfig.primaryColor,
            color: 'white',
            borderTopLeftRadius: `${styleConfig.borderRadius}px`,
            borderTopRightRadius: `${styleConfig.borderRadius}px`,
          }}
        >
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base text-white">Test Chat</CardTitle>
              <CardDescription className="text-xs text-white/80">
                Try out your agent configuration
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowThinking(!showThinking)}
              className="text-xs text-white hover:bg-white/20"
            >
              <Brain className="h-3 w-3 mr-1" />
              {showThinking ? 'Hide' : 'Show'} Thinking
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col p-0">
          <ScrollArea className="flex-1 px-4">
            <div className="space-y-4 py-4">
              {chatHistory.length === 0 ? (
                <div className="text-center text-sm text-muted-foreground py-8 space-y-4">
                  <div className="text-5xl mb-3">🤖💬</div>
                  <div>
                    <p className="font-semibold text-base text-foreground mb-2">Agent 설정 테스트</p>
                    <p className="text-xs max-w-md mx-auto leading-relaxed">
                      {styleConfig.welcomeMessage}
                    </p>
                  </div>
                  {contextItems.length === 0 && mcpServers.length === 0 && (
                    <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900 rounded-lg max-w-md mx-auto">
                      <p className="text-xs text-amber-800 dark:text-amber-200 font-medium mb-1">
                        💡 더 강력한 Agent 만들기
                      </p>
                      <p className="text-xs text-amber-700 dark:text-amber-300">
                        Step 3에서 Context와 MCP를 추가하면 Agent가 더 많은 기능을 수행할 수 있습니다!
                      </p>
                    </div>
                  )}
                  <div className="mt-4">
                    <p className="text-xs text-muted-foreground">
                      👇 아래에 메시지를 입력하여 테스트를 시작하세요
                    </p>
                  </div>
                </div>
              ) : (
                chatHistory.map((message, index) => (
                  <div key={index} className="space-y-2">
                    <div
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg px-3 py-2 text-sm whitespace-pre-line`}
                        style={{
                          backgroundColor: message.role === 'user' ? styleConfig.primaryColor : undefined,
                          color: message.role === 'user' ? 'white' : undefined,
                          borderRadius: `${styleConfig.borderRadius}px`,
                          fontSize: `${styleConfig.fontSize}px`,
                        }}
                      >
                        {message.content}
                      </div>
                    </div>
                    
                    {/* Thinking Block for assistant messages */}
                    {message.role === 'assistant' && message.thinkingSteps && showThinking && (
                      <div className="max-w-[80%]">
                        <ThinkingBlock
                          isThinking={false}
                          steps={message.thinkingSteps}
                          defaultExpanded={false}
                        />
                      </div>
                    )}
                  </div>
                ))
              )}
              
              {/* Current thinking indicator */}
              {isLoading && (
                <div className="space-y-2">
                  <div className="flex justify-start">
                    <div 
                      className="bg-muted rounded-lg px-3 py-2"
                      style={{ borderRadius: `${styleConfig.borderRadius}px` }}
                    >
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                  {showThinking && currentThinkingSteps.length > 0 && (
                    <div className="max-w-[80%]">
                      <ThinkingBlock
                        isThinking={true}
                        currentStep={currentThinkingSteps[currentThinkingSteps.length - 1]?.content}
                        steps={currentThinkingSteps}
                        defaultExpanded={true}
                      />
                    </div>
                  )}
                </div>
              )}
            </div>
          </ScrollArea>
          
          <Separator />
          
          <div className="p-4">
            <div className="flex gap-2">
              <Input
                placeholder={styleConfig.placeholder}
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !isLoading && handleSendTest()}
                disabled={isLoading}
                style={{
                  borderRadius: `${styleConfig.borderRadius}px`,
                  fontSize: `${styleConfig.fontSize}px`,
                }}
              />
              <Button
                size="icon"
                onClick={handleSendTest}
                disabled={isLoading || !testMessage.trim()}
                style={{
                  backgroundColor: styleConfig.primaryColor,
                  borderRadius: `${styleConfig.borderRadius}px`,
                }}
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
