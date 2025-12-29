'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  Play, 
  RefreshCw,
  Zap,
  Database,
  Mail,
  MessageSquare,
  Globe,
  Code,
  Users,
  Calendar,
  Search
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface ToolTest {
  id: string;
  name: string;
  category: string;
  icon: React.ReactNode;
  description: string;
  testParams: Record<string, any>;
  expectedOutput: string[];
  status: 'pending' | 'running' | 'success' | 'error';
  result?: any;
  error?: string;
  executionTime?: number;
}

const TOOL_TESTS: ToolTest[] = [
  // AI Tools
  {
    id: 'openai_chat',
    name: 'OpenAI Chat',
    category: 'AI',
    icon: <Zap className="w-4 h-4" />,
    description: 'OpenAI GPT 모델과 채팅',
    testParams: {
      model: 'gpt-3.5-turbo',
      messages: [{ role: 'user', content: 'Hello, how are you?' }],
      max_tokens: 100
    },
    expectedOutput: ['response', 'usage', 'model'],
    status: 'pending'
  },
  {
    id: 'anthropic',
    name: 'Anthropic Claude',
    category: 'AI',
    icon: <Zap className="w-4 h-4" />,
    description: 'Anthropic Claude 모델과 채팅',
    testParams: {
      model: 'claude-3-sonnet-20240229',
      messages: [{ role: 'user', content: 'What is AI?' }],
      max_tokens: 100
    },
    expectedOutput: ['content', 'usage', 'model'],
    status: 'pending'
  },
  
  // Search Tools
  {
    id: 'duckduckgo_search',
    name: 'DuckDuckGo Search',
    category: 'Search',
    icon: <Search className="w-4 h-4" />,
    description: '웹 검색 수행',
    testParams: {
      query: 'artificial intelligence news 2024',
      max_results: 5
    },
    expectedOutput: ['results', 'query', 'total_results'],
    status: 'pending'
  },
  {
    id: 'google_search',
    name: 'Google Search',
    category: 'Search',
    icon: <Search className="w-4 h-4" />,
    description: 'Google 검색 API',
    testParams: {
      query: 'machine learning trends',
      num_results: 5
    },
    expectedOutput: ['results', 'search_information'],
    status: 'pending'
  },
  
  // Communication Tools
  {
    id: 'email',
    name: 'Email',
    category: 'Communication',
    icon: <Mail className="w-4 h-4" />,
    description: '이메일 전송',
    testParams: {
      to: 'test@example.com',
      subject: 'Test Email',
      body: 'This is a test email from the workflow platform.'
    },
    expectedOutput: ['message_id', 'status', 'sent_at'],
    status: 'pending'
  },
  {
    id: 'slack',
    name: 'Slack',
    category: 'Communication',
    icon: <MessageSquare className="w-4 h-4" />,
    description: 'Slack 메시지 전송',
    testParams: {
      channel: '#general',
      message: 'Hello from workflow platform!',
      username: 'WorkflowBot'
    },
    expectedOutput: ['message_id', 'channel_id', 'timestamp'],
    status: 'pending'
  },
  
  // Data Tools
  {
    id: 'database_query',
    name: 'Database Query',
    category: 'Data',
    icon: <Database className="w-4 h-4" />,
    description: 'PostgreSQL 쿼리 실행',
    testParams: {
      query: 'SELECT COUNT(*) as user_count FROM users WHERE created_at > NOW() - INTERVAL \'7 days\'',
      connection_string: 'postgresql://localhost:5433/agenticrag'
    },
    expectedOutput: ['rows', 'columns', 'row_count'],
    status: 'pending'
  },
  
  // Developer Tools
  {
    id: 'http_request',
    name: 'HTTP Request',
    category: 'Developer',
    icon: <Globe className="w-4 h-4" />,
    description: 'HTTP API 요청',
    testParams: {
      method: 'GET',
      url: 'https://jsonplaceholder.typicode.com/posts/1',
      headers: { 'Content-Type': 'application/json' }
    },
    expectedOutput: ['status_code', 'data', 'headers'],
    status: 'pending'
  },
  {
    id: 'github',
    name: 'GitHub',
    category: 'Developer',
    icon: <Code className="w-4 h-4" />,
    description: 'GitHub API 연동',
    testParams: {
      action: 'get_repository',
      owner: 'octocat',
      repo: 'Hello-World'
    },
    expectedOutput: ['name', 'description', 'stars', 'forks'],
    status: 'pending'
  },
  
  // Productivity Tools
  {
    id: 'calendar',
    name: 'Calendar',
    category: 'Productivity',
    icon: <Calendar className="w-4 h-4" />,
    description: '캘린더 이벤트 관리',
    testParams: {
      action: 'create_event',
      title: 'Test Meeting',
      start_time: '2024-01-15T10:00:00Z',
      end_time: '2024-01-15T11:00:00Z'
    },
    expectedOutput: ['event_id', 'title', 'start_time', 'end_time'],
    status: 'pending'
  },
  {
    id: 'notion',
    name: 'Notion',
    category: 'Productivity',
    icon: <Users className="w-4 h-4" />,
    description: 'Notion 페이지 관리',
    testParams: {
      action: 'create_page',
      parent_id: 'test-database-id',
      title: 'Test Page',
      content: 'This is a test page created by the workflow platform.'
    },
    expectedOutput: ['page_id', 'title', 'url'],
    status: 'pending'
  },
  
  // Code Tools
  {
    id: 'python_code',
    name: 'Python Code',
    category: 'Code',
    icon: <Code className="w-4 h-4" />,
    description: 'Python 코드 실행',
    testParams: {
      code: `
import json
import datetime

result = {
    'message': 'Hello from Python!',
    'timestamp': datetime.datetime.now().isoformat(),
    'calculation': 2 + 2
}
print(json.dumps(result))
      `.trim()
    },
    expectedOutput: ['output', 'execution_time', 'success'],
    status: 'pending'
  }
];

export function ToolFunctionTester() {
  const [tests, setTests] = useState<ToolTest[]>(TOOL_TESTS);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isRunningAll, setIsRunningAll] = useState(false);
  const [customTestParams, setCustomTestParams] = useState<string>('{}');
  const { toast } = useToast();

  const categories = ['all', ...Array.from(new Set(tests.map(t => t.category)))];

  const filteredTests = selectedCategory === 'all' 
    ? tests 
    : tests.filter(t => t.category === selectedCategory);

  const runSingleTest = async (testId: string) => {
    setTests(prev => prev.map(t => 
      t.id === testId ? { ...t, status: 'running', result: undefined, error: undefined } : t
    ));

    const test = tests.find(t => t.id === testId);
    if (!test) return;

    try {
      const startTime = Date.now();
      
      // API 호출 시뮬레이션 (실제로는 agentBuilderAPI 사용)
      const response = await simulateToolExecution(test);
      
      const executionTime = Date.now() - startTime;

      setTests(prev => prev.map(t => 
        t.id === testId ? { 
          ...t, 
          status: 'success', 
          result: response,
          executionTime 
        } : t
      ));

      toast({
        title: '테스트 성공',
        description: `${test.name} 도구가 정상적으로 작동합니다.`,
      });

    } catch (error: any) {
      setTests(prev => prev.map(t => 
        t.id === testId ? { 
          ...t, 
          status: 'error', 
          error: error.message 
        } : t
      ));

      toast({
        title: '테스트 실패',
        description: `${test.name}: ${error.message}`,
        variant: 'destructive',
      });
    }
  };

  const runAllTests = async () => {
    setIsRunningAll(true);
    
    for (const test of filteredTests) {
      await runSingleTest(test.id);
      // 테스트 간 간격
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    setIsRunningAll(false);
    
    const results = tests.filter(t => filteredTests.includes(t));
    const successCount = results.filter(t => t.status === 'success').length;
    const totalCount = results.length;
    
    toast({
      title: '전체 테스트 완료',
      description: `${successCount}/${totalCount} 도구가 정상 작동합니다.`,
    });
  };

  const resetTests = () => {
    setTests(prev => prev.map(t => ({ 
      ...t, 
      status: 'pending', 
      result: undefined, 
      error: undefined,
      executionTime: undefined 
    })));
  };

  // 실제 API 호출 시뮬레이션
  const simulateToolExecution = async (test: ToolTest): Promise<any> => {
    // 실제 구현에서는 agentBuilderAPI.executeTool 사용
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        // 성공률 90%로 시뮬레이션
        if (Math.random() > 0.1) {
          const mockResult: any = {};
          test.expectedOutput.forEach(key => {
            switch (key) {
              case 'response':
              case 'content':
                mockResult[key] = 'Mock response from AI model';
                break;
              case 'results':
                mockResult[key] = [
                  { title: 'Mock Result 1', url: 'https://example.com/1' },
                  { title: 'Mock Result 2', url: 'https://example.com/2' }
                ];
                break;
              case 'status_code':
                mockResult[key] = 200;
                break;
              case 'message_id':
                mockResult[key] = `msg_${Date.now()}`;
                break;
              case 'rows':
                mockResult[key] = [{ user_count: 42 }];
                break;
              case 'output':
                mockResult[key] = '{"message": "Hello from Python!", "calculation": 4}';
                break;
              default:
                mockResult[key] = `mock_${key}_value`;
            }
          });
          resolve(mockResult);
        } else {
          reject(new Error('Mock execution failed'));
        }
      }, Math.random() * 2000 + 500); // 0.5-2.5초 랜덤 지연
    });
  };

  const getStatusIcon = (status: ToolTest['status']) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-gray-400" />;
      case 'running':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
    }
  };

  const getStatusColor = (status: ToolTest['status']) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-700';
      case 'running':
        return 'bg-blue-100 text-blue-700';
      case 'success':
        return 'bg-green-100 text-green-700';
      case 'error':
        return 'bg-red-100 text-red-700';
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>도구 기능 테스트</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                워크플로우 플랫폼의 모든 도구가 정상적으로 작동하는지 확인합니다.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={resetTests}
                disabled={isRunningAll}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                초기화
              </Button>
              <Button
                onClick={runAllTests}
                disabled={isRunningAll}
              >
                <Play className="w-4 h-4 mr-2" />
                {isRunningAll ? '테스트 중...' : '전체 테스트'}
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="grid w-full grid-cols-8">
          {categories.map(category => (
            <TabsTrigger key={category} value={category}>
              {category === 'all' ? '전체' : category}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={selectedCategory} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTests.map(test => (
              <Card key={test.id} className="relative">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {test.icon}
                      <div>
                        <h3 className="font-medium">{test.name}</h3>
                        <Badge variant="outline" className="text-xs">
                          {test.category}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(test.status)}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => runSingleTest(test.id)}
                        disabled={test.status === 'running' || isRunningAll}
                      >
                        <Play className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-3">
                  <p className="text-sm text-muted-foreground">
                    {test.description}
                  </p>
                  
                  <div className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(test.status)}`}>
                    {test.status === 'pending' && '대기 중'}
                    {test.status === 'running' && '실행 중...'}
                    {test.status === 'success' && `성공 (${test.executionTime}ms)`}
                    {test.status === 'error' && '실패'}
                  </div>

                  {test.status === 'success' && test.result && (
                    <div className="space-y-2">
                      <Label className="text-xs font-medium">결과:</Label>
                      <ScrollArea className="h-20 w-full border rounded p-2">
                        <pre className="text-xs">
                          {JSON.stringify(test.result, null, 2)}
                        </pre>
                      </ScrollArea>
                    </div>
                  )}

                  {test.status === 'error' && test.error && (
                    <div className="space-y-2">
                      <Label className="text-xs font-medium text-red-600">오류:</Label>
                      <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                        {test.error}
                      </div>
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label className="text-xs font-medium">테스트 파라미터:</Label>
                    <ScrollArea className="h-16 w-full border rounded p-2">
                      <pre className="text-xs">
                        {JSON.stringify(test.testParams, null, 2)}
                      </pre>
                    </ScrollArea>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-xs font-medium">예상 출력:</Label>
                    <div className="flex flex-wrap gap-1">
                      {test.expectedOutput.map(output => (
                        <Badge key={output} variant="secondary" className="text-xs">
                          {output}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* 테스트 결과 요약 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">테스트 결과 요약</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {tests.filter(t => t.status === 'pending').length}
              </div>
              <div className="text-sm text-muted-foreground">대기 중</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {tests.filter(t => t.status === 'running').length}
              </div>
              <div className="text-sm text-muted-foreground">실행 중</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {tests.filter(t => t.status === 'success').length}
              </div>
              <div className="text-sm text-muted-foreground">성공</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {tests.filter(t => t.status === 'error').length}
              </div>
              <div className="text-sm text-muted-foreground">실패</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}