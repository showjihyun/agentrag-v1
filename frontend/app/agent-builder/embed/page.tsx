'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Code,
  Copy,
  ExternalLink,
  Palette,
  Settings,
  Eye,
  MessageSquare,
  Maximize2,
  Minimize2,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';
import type { Chatflow } from '@/lib/types/flows';

interface EmbedConfig {
  chatflowId: string;
  theme: 'light' | 'dark' | 'auto';
  primaryColor: string;
  position: 'bottom-right' | 'bottom-left';
  buttonSize: number;
  windowWidth: number;
  windowHeight: number;
  welcomeMessage: string;
  placeholder: string;
  showBranding: boolean;
  allowFullscreen: boolean;
  autoOpen: boolean;
  autoOpenDelay: number;
}

const DEFAULT_CONFIG: EmbedConfig = {
  chatflowId: '',
  theme: 'auto',
  primaryColor: '#6366f1',
  position: 'bottom-right',
  buttonSize: 60,
  windowWidth: 400,
  windowHeight: 600,
  welcomeMessage: '안녕하세요! 무엇을 도와드릴까요?',
  placeholder: '메시지를 입력하세요...',
  showBranding: true,
  allowFullscreen: true,
  autoOpen: false,
  autoOpenDelay: 3,
};

export default function EmbedPage() {
  const { toast } = useToast();
  const [config, setConfig] = useState<EmbedConfig>(DEFAULT_CONFIG);
  const [previewOpen, setPreviewOpen] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);

  // Fetch chatflows
  const { data: chatflowsData, isLoading } = useQuery({
    queryKey: ['chatflows-for-embed'],
    queryFn: () => flowsAPI.getChatflows(),
  });

  const chatflows = (chatflowsData?.flows || []) as Chatflow[];

  const generateScriptCode = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return `<script>
  (function() {
    var script = document.createElement('script');
    script.src = '${apiUrl}/embed/chatbot.js';
    script.async = true;
    script.onload = function() {
      window.AgenticRAG.init({
        chatflowId: '${config.chatflowId}',
        theme: '${config.theme}',
        primaryColor: '${config.primaryColor}',
        position: '${config.position}',
        buttonSize: ${config.buttonSize},
        windowWidth: ${config.windowWidth},
        windowHeight: ${config.windowHeight},
        welcomeMessage: '${config.welcomeMessage}',
        placeholder: '${config.placeholder}',
        showBranding: ${config.showBranding},
        allowFullscreen: ${config.allowFullscreen},
        autoOpen: ${config.autoOpen},
        autoOpenDelay: ${config.autoOpenDelay}
      });
    };
    document.head.appendChild(script);
  })();
</script>`;
  };

  const generateReactCode = () => {
    return `import { ChatWidget } from '@agenticrag/react';

function App() {
  return (
    <ChatWidget
      chatflowId="${config.chatflowId}"
      theme="${config.theme}"
      primaryColor="${config.primaryColor}"
      position="${config.position}"
      buttonSize={${config.buttonSize}}
      windowWidth={${config.windowWidth}}
      windowHeight={${config.windowHeight}}
      welcomeMessage="${config.welcomeMessage}"
      placeholder="${config.placeholder}"
      showBranding={${config.showBranding}}
      allowFullscreen={${config.allowFullscreen}}
      autoOpen={${config.autoOpen}}
      autoOpenDelay={${config.autoOpenDelay}}
    />
  );
}`;
  };

  const generateIframeCode = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const params = new URLSearchParams({
      theme: config.theme,
      primaryColor: config.primaryColor,
    });
    return `<iframe
  src="${apiUrl}/embed/chatbot/${config.chatflowId}?${params.toString()}"
  width="${config.windowWidth}"
  height="${config.windowHeight}"
  frameborder="0"
  allow="microphone"
  style="border: none; border-radius: 12px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);"
></iframe>`;
  };

  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
    toast({
      title: '복사됨',
      description: '코드가 클립보드에 복사되었습니다',
    });
  };

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Code className="h-8 w-8 text-indigo-500" />
            Embed Widget
          </h1>
          <p className="text-muted-foreground mt-1">
            웹사이트에 AI 챗봇을 임베드하세요
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Panel */}
        <div className="space-y-6">
          {/* Chatflow Selection */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Chatflow 선택
              </CardTitle>
              <CardDescription>임베드할 Chatflow를 선택하세요</CardDescription>
            </CardHeader>
            <CardContent>
              <Select
                value={config.chatflowId}
                onValueChange={(v) => setConfig({ ...config, chatflowId: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Chatflow 선택..." />
                </SelectTrigger>
                <SelectContent>
                  {chatflows.map((flow) => (
                    <SelectItem key={flow.id} value={flow.id}>
                      {flow.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!config.chatflowId && (
                <p className="text-sm text-muted-foreground mt-2">
                  먼저 Chatflow를 선택해야 임베드 코드를 생성할 수 있습니다
                </p>
              )}
            </CardContent>
          </Card>

          {/* Appearance Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                외관 설정
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>테마</Label>
                  <Select
                    value={config.theme}
                    onValueChange={(v) => setConfig({ ...config, theme: v as any })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">라이트</SelectItem>
                      <SelectItem value="dark">다크</SelectItem>
                      <SelectItem value="auto">자동 (시스템)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>위치</Label>
                  <Select
                    value={config.position}
                    onValueChange={(v) => setConfig({ ...config, position: v as any })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="bottom-right">우측 하단</SelectItem>
                      <SelectItem value="bottom-left">좌측 하단</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>메인 색상</Label>
                <div className="flex gap-2">
                  <Input
                    type="color"
                    value={config.primaryColor}
                    onChange={(e) => setConfig({ ...config, primaryColor: e.target.value })}
                    className="w-12 h-10 p-1 cursor-pointer"
                  />
                  <Input
                    value={config.primaryColor}
                    onChange={(e) => setConfig({ ...config, primaryColor: e.target.value })}
                    className="flex-1"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>버튼 크기: {config.buttonSize}px</Label>
                <Slider
                  value={[config.buttonSize]}
                  onValueChange={([v]) => setConfig({ ...config, buttonSize: v ?? 60 })}
                  min={40}
                  max={80}
                  step={4}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>창 너비: {config.windowWidth}px</Label>
                  <Slider
                    value={[config.windowWidth]}
                    onValueChange={([v]) => setConfig({ ...config, windowWidth: v ?? 400 })}
                    min={300}
                    max={600}
                    step={20}
                  />
                </div>
                <div className="space-y-2">
                  <Label>창 높이: {config.windowHeight}px</Label>
                  <Slider
                    value={[config.windowHeight]}
                    onValueChange={([v]) => setConfig({ ...config, windowHeight: v ?? 600 })}
                    min={400}
                    max={800}
                    step={20}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Behavior Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                동작 설정
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>환영 메시지</Label>
                <Textarea
                  value={config.welcomeMessage}
                  onChange={(e) => setConfig({ ...config, welcomeMessage: e.target.value })}
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label>입력 플레이스홀더</Label>
                <Input
                  value={config.placeholder}
                  onChange={(e) => setConfig({ ...config, placeholder: e.target.value })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>브랜딩 표시</Label>
                  <p className="text-xs text-muted-foreground">Powered by AgenticRAG 표시</p>
                </div>
                <Switch
                  checked={config.showBranding}
                  onCheckedChange={(v) => setConfig({ ...config, showBranding: v })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>전체화면 허용</Label>
                  <p className="text-xs text-muted-foreground">사용자가 전체화면으로 확장 가능</p>
                </div>
                <Switch
                  checked={config.allowFullscreen}
                  onCheckedChange={(v) => setConfig({ ...config, allowFullscreen: v })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>자동 열기</Label>
                  <p className="text-xs text-muted-foreground">페이지 로드 후 자동으로 채팅창 열기</p>
                </div>
                <Switch
                  checked={config.autoOpen}
                  onCheckedChange={(v) => setConfig({ ...config, autoOpen: v })}
                />
              </div>

              {config.autoOpen && (
                <div className="space-y-2">
                  <Label>자동 열기 지연: {config.autoOpenDelay}초</Label>
                  <Slider
                    value={[config.autoOpenDelay]}
                    onValueChange={([v]) => setConfig({ ...config, autoOpenDelay: v ?? 3 })}
                    min={0}
                    max={10}
                    step={1}
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Preview & Code Panel */}
        <div className="space-y-6">
          {/* Preview */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  미리보기
                </CardTitle>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPreviewOpen(!previewOpen)}
                >
                  {previewOpen ? (
                    <Minimize2 className="h-4 w-4" />
                  ) : (
                    <Maximize2 className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </CardHeader>
            {previewOpen && (
              <CardContent>
                <div
                  className="relative bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-800 dark:to-gray-900 rounded-lg overflow-hidden"
                  style={{ height: '400px' }}
                >
                  {/* Mock Website */}
                  <div className="absolute inset-0 p-4">
                    <div className="h-8 bg-white dark:bg-gray-700 rounded mb-4" />
                    <div className="space-y-2">
                      <div className="h-4 bg-white/50 dark:bg-gray-600/50 rounded w-3/4" />
                      <div className="h-4 bg-white/50 dark:bg-gray-600/50 rounded w-1/2" />
                      <div className="h-4 bg-white/50 dark:bg-gray-600/50 rounded w-2/3" />
                    </div>
                  </div>

                  {/* Chat Button */}
                  <div
                    className={`absolute ${
                      config.position === 'bottom-right' ? 'right-4' : 'left-4'
                    } bottom-4`}
                  >
                    <button
                      className="rounded-full shadow-lg flex items-center justify-center text-white transition-transform hover:scale-105"
                      style={{
                        width: config.buttonSize,
                        height: config.buttonSize,
                        backgroundColor: config.primaryColor,
                      }}
                    >
                      <MessageSquare className="h-6 w-6" />
                    </button>
                  </div>

                  {/* Chat Window Preview */}
                  <div
                    className={`absolute ${
                      config.position === 'bottom-right' ? 'right-4' : 'left-4'
                    } bottom-20 bg-white dark:bg-gray-800 rounded-xl shadow-2xl overflow-hidden`}
                    style={{
                      width: Math.min(config.windowWidth, 350),
                      height: Math.min(config.windowHeight, 300),
                    }}
                  >
                    {/* Header */}
                    <div
                      className="p-3 text-white"
                      style={{ backgroundColor: config.primaryColor }}
                    >
                      <p className="font-medium text-sm">AI Assistant</p>
                    </div>
                    {/* Messages */}
                    <div className="p-3 space-y-2 text-sm">
                      <div
                        className="p-2 rounded-lg max-w-[80%] text-white"
                        style={{ backgroundColor: config.primaryColor }}
                      >
                        {config.welcomeMessage}
                      </div>
                    </div>
                    {/* Input */}
                    <div className="absolute bottom-0 left-0 right-0 p-2 border-t">
                      <div className="flex gap-2">
                        <div className="flex-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-full text-xs text-muted-foreground">
                          {config.placeholder}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            )}
          </Card>

          {/* Embed Code */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                임베드 코드
              </CardTitle>
              <CardDescription>
                아래 코드를 웹사이트에 추가하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="script">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="script">Script</TabsTrigger>
                  <TabsTrigger value="react">React</TabsTrigger>
                  <TabsTrigger value="iframe">iFrame</TabsTrigger>
                </TabsList>

                <TabsContent value="script" className="mt-4">
                  <div className="relative">
                    <pre className="p-4 bg-muted rounded-lg overflow-x-auto text-xs">
                      <code>{generateScriptCode()}</code>
                    </pre>
                    <Button
                      variant="outline"
                      size="sm"
                      className="absolute top-2 right-2"
                      onClick={() => copyToClipboard(generateScriptCode(), 'script')}
                      disabled={!config.chatflowId}
                    >
                      {copied === 'script' ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    이 코드를 {'<body>'} 태그 끝에 추가하세요
                  </p>
                </TabsContent>

                <TabsContent value="react" className="mt-4">
                  <div className="relative">
                    <pre className="p-4 bg-muted rounded-lg overflow-x-auto text-xs">
                      <code>{generateReactCode()}</code>
                    </pre>
                    <Button
                      variant="outline"
                      size="sm"
                      className="absolute top-2 right-2"
                      onClick={() => copyToClipboard(generateReactCode(), 'react')}
                      disabled={!config.chatflowId}
                    >
                      {copied === 'react' ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    먼저 npm install @agenticrag/react 를 실행하세요
                  </p>
                </TabsContent>

                <TabsContent value="iframe" className="mt-4">
                  <div className="relative">
                    <pre className="p-4 bg-muted rounded-lg overflow-x-auto text-xs">
                      <code>{generateIframeCode()}</code>
                    </pre>
                    <Button
                      variant="outline"
                      size="sm"
                      className="absolute top-2 right-2"
                      onClick={() => copyToClipboard(generateIframeCode(), 'iframe')}
                      disabled={!config.chatflowId}
                    >
                      {copied === 'iframe' ? (
                        <Check className="h-4 w-4" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    iFrame을 원하는 위치에 추가하세요
                  </p>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* SDK Documentation Link */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">SDK 문서</h3>
                  <p className="text-sm text-muted-foreground">
                    TypeScript, Python SDK 사용법 확인
                  </p>
                </div>
                <Button variant="outline" asChild>
                  <a href="/docs/sdk" target="_blank">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    문서 보기
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
