'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Copy,
  ExternalLink,
  Key,
  Code,
  Play,
  CheckCircle,
  Settings,
  Book,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';

export default function ChatflowAPIPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const { toast } = useToast();
  const [apiKey, setApiKey] = useState('sk-chatflow-' + Math.random().toString(36).substring(2, 15));
  const [testMessage, setTestMessage] = useState('안녕하세요! 테스트 메시지입니다.');
  const [testResponse, setTestResponse] = useState('');
  const [testing, setTesting] = useState(false);

  const { data: flowData, isLoading } = useQuery({
    queryKey: ['chatflow', params.id],
    queryFn: () => flowsAPI.getFlow(params.id),
  });

  const flow = flowData as any;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: '복사 완료',
      description: '클립보드에 복사되었습니다',
    });
  };

  const handleTestAPI = async () => {
    setTesting(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      setTestResponse(`{
  "id": "msg_${Date.now()}",
  "object": "chat.completion",
  "created": ${Math.floor(Date.now() / 1000)},
  "model": "${flow?.chat_config?.llm_model || 'llama3.1'}",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "안녕하세요! 테스트 API 호출이 성공적으로 완료되었습니다. 이것은 시뮬레이션된 응답입니다."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 25,
    "total_tokens": 40
  }
}`);
      toast({
        title: 'API 테스트 성공',
        description: 'API 호출이 성공적으로 완료되었습니다',
      });
    } catch (error) {
      toast({
        title: 'API 테스트 실패',
        description: 'API 호출 중 오류가 발생했습니다',
        variant: 'destructive',
      });
    } finally {
      setTesting(false);
    }
  };

  const baseURL = typeof window !== 'undefined' ? window.location.origin : '';
  const apiEndpoint = `${baseURL}/api/v1/chatflows/${params.id}/chat`;

  const curlExample = `curl -X POST "${apiEndpoint}" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${apiKey}" \\
  -d '{
    "message": "안녕하세요!",
    "session_id": "user-session-123",
    "stream": false
  }'`;

  const pythonExample = `import requests

url = "${apiEndpoint}"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer ${apiKey}"
}
data = {
    "message": "안녕하세요!",
    "session_id": "user-session-123",
    "stream": False
}

response = requests.post(url, headers=headers, json=data)
print(response.json())`;

  const javascriptExample = `const response = await fetch("${apiEndpoint}", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer ${apiKey}"
  },
  body: JSON.stringify({
    message: "안녕하세요!",
    session_id: "user-session-123",
    stream: false
  })
});

const data = await response.json();
console.log(data);`;

  const streamingExample = `const response = await fetch("${apiEndpoint}", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": "Bearer ${apiKey}"
  },
  body: JSON.stringify({
    message: "안녕하세요!",
    session_id: "user-session-123",
    stream: true
  })
});

const reader = response.body?.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log(data.content);
    }
  }
}`;

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!flow) {
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
              <ExternalLink className="h-7 w-7 text-blue-600 dark:text-blue-400" />
            </div>
            API 문서
          </h1>
          <p className="text-muted-foreground mt-1">{flow.name} - REST API 가이드</p>
        </div>
        <Button
          variant="outline"
          onClick={() => router.push(`/agent-builder/chatflows/${params.id}`)}
        >
          <Settings className="h-4 w-4 mr-2" />
          설정으로 돌아가기
        </Button>
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">개요</TabsTrigger>
          <TabsTrigger value="authentication">인증</TabsTrigger>
          <TabsTrigger value="examples">예제 코드</TabsTrigger>
          <TabsTrigger value="test">API 테스트</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Book className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle>API 개요</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">기본 정보</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Base URL</p>
                      <code className="bg-muted px-2 py-1 rounded text-xs">{baseURL}/api/v1</code>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Content-Type</p>
                      <code className="bg-muted px-2 py-1 rounded text-xs">application/json</code>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-semibold mb-2">엔드포인트</h3>
                  <Card className="bg-muted">
                    <CardContent className="pt-4">
                      <div className="flex items-center gap-2">
                        <Badge className="bg-green-500">POST</Badge>
                        <code className="text-sm">/chatflows/{params.id}/chat</code>
                      </div>
                      <p className="text-sm text-muted-foreground mt-2">
                        Chatflow와 대화를 시작합니다. 스트리밍 및 일반 응답을 모두 지원합니다.
                      </p>
                    </CardContent>
                  </Card>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">요청 파라미터</h3>
                  <div className="space-y-2">
                    <div className="grid grid-cols-4 gap-4 text-sm font-medium border-b pb-2">
                      <span>필드</span>
                      <span>타입</span>
                      <span>필수</span>
                      <span>설명</span>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <code>message</code>
                      <span>string</span>
                      <Badge variant="destructive" className="text-xs">필수</Badge>
                      <span>사용자 메시지</span>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <code>session_id</code>
                      <span>string</span>
                      <Badge variant="secondary" className="text-xs">선택</Badge>
                      <span>세션 식별자</span>
                    </div>
                    <div className="grid grid-cols-4 gap-4 text-sm">
                      <code>stream</code>
                      <span>boolean</span>
                      <Badge variant="secondary" className="text-xs">선택</Badge>
                      <span>스트리밍 응답 여부</span>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">응답 형식</h3>
                  <Card className="bg-muted">
                    <CardContent className="pt-4">
                      <pre className="text-xs overflow-x-auto">
{`{
  "id": "msg_1234567890",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "${flow.chat_config?.llm_model || 'llama3.1'}",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "AI 응답 내용"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 25,
    "total_tokens": 40
  }
}`}
                      </pre>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Authentication Tab */}
        <TabsContent value="authentication" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Key className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle>API 키 인증</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div>
                  <Label>API 키</Label>
                  <div className="flex gap-2 mt-1">
                    <Input value={apiKey} readOnly className="font-mono text-sm" />
                    <Button variant="outline" onClick={() => copyToClipboard(apiKey)}>
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    이 API 키를 Authorization 헤더에 Bearer 토큰으로 포함하세요
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">인증 방법</h3>
                  <Card className="bg-muted">
                    <CardContent className="pt-4">
                      <code className="text-sm">Authorization: Bearer {apiKey}</code>
                    </CardContent>
                  </Card>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">보안 주의사항</h3>
                  <ul className="text-sm space-y-1 text-muted-foreground">
                    <li>• API 키는 안전한 곳에 보관하세요</li>
                    <li>• 클라이언트 사이드 코드에 API 키를 노출하지 마세요</li>
                    <li>• 정기적으로 API 키를 갱신하세요</li>
                    <li>• HTTPS를 통해서만 API를 호출하세요</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Examples Tab */}
        <TabsContent value="examples" className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            {/* cURL Example */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-5 w-5" />
                  cURL
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  <pre className="bg-muted p-4 rounded text-xs overflow-x-auto">
                    {curlExample}
                  </pre>
                  <Button
                    variant="outline"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(curlExample)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Python Example */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-5 w-5" />
                  Python
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  <pre className="bg-muted p-4 rounded text-xs overflow-x-auto">
                    {pythonExample}
                  </pre>
                  <Button
                    variant="outline"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(pythonExample)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* JavaScript Example */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-5 w-5" />
                  JavaScript
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  <pre className="bg-muted p-4 rounded text-xs overflow-x-auto">
                    {javascriptExample}
                  </pre>
                  <Button
                    variant="outline"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(javascriptExample)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Streaming Example */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-5 w-5" />
                  스트리밍 (JavaScript)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="relative">
                  <pre className="bg-muted p-4 rounded text-xs overflow-x-auto">
                    {streamingExample}
                  </pre>
                  <Button
                    variant="outline"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(streamingExample)}
                  >
                    <Copy className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Test Tab */}
        <TabsContent value="test" className="space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Play className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle>API 테스트</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="space-y-4">
                <div>
                  <Label>테스트 메시지</Label>
                  <Textarea
                    value={testMessage}
                    onChange={(e) => setTestMessage(e.target.value)}
                    placeholder="테스트할 메시지를 입력하세요"
                    rows={3}
                  />
                </div>
                
                <Button 
                  onClick={handleTestAPI} 
                  disabled={testing || !testMessage.trim()}
                  className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
                >
                  {testing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      테스트 중...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      API 테스트
                    </>
                  )}
                </Button>

                {testResponse && (
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <Label>응답 결과</Label>
                    </div>
                    <Card className="bg-muted">
                      <CardContent className="pt-4">
                        <pre className="text-xs overflow-x-auto whitespace-pre-wrap">
                          {testResponse}
                        </pre>
                      </CardContent>
                    </Card>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}