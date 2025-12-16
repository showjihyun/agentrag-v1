'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Copy,
  Code,
  Eye,
  Settings,
  Palette,
  Monitor,
  Smartphone,
  Tablet,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';

export default function ChatflowEmbedPage({ params }: { params: Promise<{ id: string }> }) {
  // Unwrap params using React.use()
  const { id } = React.use(params);
  const router = useRouter();
  const { toast } = useToast();
  
  const [embedConfig, setEmbedConfig] = useState({
    theme: 'light',
    primaryColor: '#3b82f6',
    width: '400px',
    height: '600px',
    position: 'bottom-right',
    showHeader: true,
    showAvatar: true,
    placeholder: '메시지를 입력하세요...',
    welcomeMessage: '',
    autoOpen: false,
  });
  const [previewDevice, setPreviewDevice] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');

  const { data: flowData, isLoading } = useQuery({
    queryKey: ['chatflow', id],
    queryFn: () => flowsAPI.getFlow(id),
  });

  const flow = flowData as any;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: '복사 완료',
      description: '클립보드에 복사되었습니다',
    });
  };

  const baseURL = typeof window !== 'undefined' ? window.location.origin : '';
  
  const embedScript = `<!-- Chatflow Embed Script -->
<script>
  (function() {
    var chatflowConfig = {
      flowId: '${id}',
      apiUrl: '${baseURL}/api/v1',
      theme: '${embedConfig.theme}',
      primaryColor: '${embedConfig.primaryColor}',
      width: '${embedConfig.width}',
      height: '${embedConfig.height}',
      position: '${embedConfig.position}',
      showHeader: ${embedConfig.showHeader},
      showAvatar: ${embedConfig.showAvatar},
      placeholder: '${embedConfig.placeholder}',
      welcomeMessage: '${embedConfig.welcomeMessage || flow?.chat_config?.welcome_message || ''}',
      autoOpen: ${embedConfig.autoOpen}
    };
    
    var script = document.createElement('script');
    script.src = '${baseURL}/embed/chatflow.js';
    script.onload = function() {
      window.ChatflowWidget.init(chatflowConfig);
    };
    document.head.appendChild(script);
    
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '${baseURL}/embed/chatflow.css';
    document.head.appendChild(link);
  })();
</script>`;

  const iframeEmbed = `<iframe
  src="${baseURL}/embed/chatflow/${id}?theme=${embedConfig.theme}&color=${encodeURIComponent(embedConfig.primaryColor)}"
  width="${embedConfig.width}"
  height="${embedConfig.height}"
  frameborder="0"
  style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);"
  title="${flow?.name || 'Chatflow'}"
></iframe>`;

  const reactComponent = `import React, { useEffect } from 'react';

const ChatflowWidget = () => {
  useEffect(() => {
    const config = {
      flowId: '${id}',
      apiUrl: '${baseURL}/api/v1',
      theme: '${embedConfig.theme}',
      primaryColor: '${embedConfig.primaryColor}',
      width: '${embedConfig.width}',
      height: '${embedConfig.height}',
      position: '${embedConfig.position}',
      showHeader: ${embedConfig.showHeader},
      showAvatar: ${embedConfig.showAvatar},
      placeholder: '${embedConfig.placeholder}',
      welcomeMessage: '${embedConfig.welcomeMessage || flow?.chat_config?.welcome_message || ''}',
      autoOpen: ${embedConfig.autoOpen}
    };

    // Load Chatflow widget
    const script = document.createElement('script');
    script.src = '${baseURL}/embed/chatflow.js';
    script.onload = () => {
      if (window.ChatflowWidget) {
        window.ChatflowWidget.init(config);
      }
    };
    document.head.appendChild(script);

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '${baseURL}/embed/chatflow.css';
    document.head.appendChild(link);

    return () => {
      // Cleanup
      if (window.ChatflowWidget) {
        window.ChatflowWidget.destroy();
      }
    };
  }, []);

  return <div id="chatflow-widget-container" />;
};

export default ChatflowWidget;`;

  const getDeviceClass = () => {
    switch (previewDevice) {
      case 'mobile':
        return 'w-80 h-96';
      case 'tablet':
        return 'w-96 h-[500px]';
      default:
        return 'w-[400px] h-[600px]';
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
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
              <Code className="h-7 w-7 text-blue-600 dark:text-blue-400" />
            </div>
            임베드 코드
          </h1>
          <p className="text-muted-foreground mt-1">{flow.name} - 웹사이트 임베드</p>
        </div>
        <Button
          variant="outline"
          onClick={() => router.push(`/agent-builder/chatflows/${id}`)}
        >
          <Settings className="h-4 w-4 mr-2" />
          설정으로 돌아가기
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Panel */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Palette className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <CardTitle className="text-lg">스타일 설정</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div className="space-y-2">
                <Label>테마</Label>
                <Select
                  value={embedConfig.theme}
                  onValueChange={(v) => setEmbedConfig({ ...embedConfig, theme: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">라이트</SelectItem>
                    <SelectItem value="dark">다크</SelectItem>
                    <SelectItem value="auto">자동</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>기본 색상</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={embedConfig.primaryColor}
                    onChange={(e) => setEmbedConfig({ ...embedConfig, primaryColor: e.target.value })}
                    className="w-16 h-10 p-1"
                  />
                  <Input
                    value={embedConfig.primaryColor}
                    onChange={(e) => setEmbedConfig({ ...embedConfig, primaryColor: e.target.value })}
                    placeholder="#3b82f6"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>너비</Label>
                  <Input
                    value={embedConfig.width}
                    onChange={(e) => setEmbedConfig({ ...embedConfig, width: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>높이</Label>
                  <Input
                    value={embedConfig.height}
                    onChange={(e) => setEmbedConfig({ ...embedConfig, height: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>위치</Label>
                <Select
                  value={embedConfig.position}
                  onValueChange={(v) => setEmbedConfig({ ...embedConfig, position: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="bottom-right">우측 하단</SelectItem>
                    <SelectItem value="bottom-left">좌측 하단</SelectItem>
                    <SelectItem value="top-right">우측 상단</SelectItem>
                    <SelectItem value="top-left">좌측 상단</SelectItem>
                    <SelectItem value="center">중앙</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>플레이스홀더</Label>
                <Input
                  value={embedConfig.placeholder}
                  onChange={(e) => setEmbedConfig({ ...embedConfig, placeholder: e.target.value })}
                />
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label>헤더 표시</Label>
                  <Switch
                    checked={embedConfig.showHeader}
                    onCheckedChange={(v) => setEmbedConfig({ ...embedConfig, showHeader: v })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>아바타 표시</Label>
                  <Switch
                    checked={embedConfig.showAvatar}
                    onCheckedChange={(v) => setEmbedConfig({ ...embedConfig, showAvatar: v })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label>자동 열기</Label>
                  <Switch
                    checked={embedConfig.autoOpen}
                    onCheckedChange={(v) => setEmbedConfig({ ...embedConfig, autoOpen: v })}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Preview and Code Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Preview */}
          <Card className="border-2">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                    <Eye className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <CardTitle className="text-lg">미리보기</CardTitle>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant={previewDevice === 'desktop' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setPreviewDevice('desktop')}
                  >
                    <Monitor className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={previewDevice === 'tablet' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setPreviewDevice('tablet')}
                  >
                    <Tablet className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={previewDevice === 'mobile' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setPreviewDevice('mobile')}
                  >
                    <Smartphone className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="flex justify-center">
                <div className={`${getDeviceClass()} border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50 dark:bg-gray-900`}>
                  <div className="text-center">
                    <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Code className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">Chatflow 위젯 미리보기</p>
                    <Badge style={{ backgroundColor: embedConfig.primaryColor }}>
                      {flow.name}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-2">
                      {embedConfig.width} × {embedConfig.height}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Embed Code */}
          <Tabs defaultValue="script" className="space-y-4">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="script">JavaScript</TabsTrigger>
              <TabsTrigger value="iframe">iframe</TabsTrigger>
              <TabsTrigger value="react">React</TabsTrigger>
            </TabsList>

            <TabsContent value="script">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>JavaScript 임베드</CardTitle>
                      <CardDescription>
                        가장 유연한 방법으로 모든 기능을 사용할 수 있습니다
                      </CardDescription>
                    </div>
                    <Button variant="outline" onClick={() => copyToClipboard(embedScript)}>
                      <Copy className="h-4 w-4 mr-2" />
                      복사
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded text-xs overflow-x-auto">
                    {embedScript}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="iframe">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>iframe 임베드</CardTitle>
                      <CardDescription>
                        간단한 임베드 방법이지만 일부 기능이 제한될 수 있습니다
                      </CardDescription>
                    </div>
                    <Button variant="outline" onClick={() => copyToClipboard(iframeEmbed)}>
                      <Copy className="h-4 w-4 mr-2" />
                      복사
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded text-xs overflow-x-auto">
                    {iframeEmbed}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="react">
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle>React 컴포넌트</CardTitle>
                      <CardDescription>
                        React 애플리케이션에서 사용할 수 있는 컴포넌트입니다
                      </CardDescription>
                    </div>
                    <Button variant="outline" onClick={() => copyToClipboard(reactComponent)}>
                      <Copy className="h-4 w-4 mr-2" />
                      복사
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <pre className="bg-muted p-4 rounded text-xs overflow-x-auto">
                    {reactComponent}
                  </pre>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Usage Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>사용 방법</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm">
                <div>
                  <h4 className="font-semibold mb-2">1. 코드 복사</h4>
                  <p className="text-muted-foreground">
                    위의 탭에서 원하는 임베드 방식을 선택하고 코드를 복사하세요.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">2. 웹사이트에 붙여넣기</h4>
                  <p className="text-muted-foreground">
                    복사한 코드를 웹사이트의 HTML 파일에 붙여넣으세요. JavaScript 방식의 경우 &lt;/body&gt; 태그 직전에 넣는 것을 권장합니다.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold mb-2">3. 테스트</h4>
                  <p className="text-muted-foreground">
                    웹사이트를 새로고침하고 챗봇이 정상적으로 표시되는지 확인하세요.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}