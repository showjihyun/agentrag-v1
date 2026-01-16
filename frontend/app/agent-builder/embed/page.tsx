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
  Bot,
  Send,
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
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';
import type { Chatflow } from '@/lib/types/flows';
import { useChatStyleStore } from '@/lib/stores/chat-style-store';

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
  welcomeMessage: 'Hello! How can I help you today?',
  placeholder: 'Type your message...',
  showBranding: true,
  allowFullscreen: true,
  autoOpen: false,
  autoOpenDelay: 3,
};

export default function EmbedPage() {
  const { toast } = useToast();
  const { config: styleConfig, updateConfig: updateStyleConfig } = useChatStyleStore();
  const [config, setConfig] = useState<EmbedConfig>(DEFAULT_CONFIG);
  const [previewOpen, setPreviewOpen] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);
  
  // Preview chat messages (editable)
  const [previewMessages, setPreviewMessages] = useState<Array<{
    id: string;
    role: 'user' | 'assistant';
    content: string;
  }>>([
    { id: '1', role: 'assistant', content: 'Hello! How can I help you today?' },
    { id: '2', role: 'user', content: 'I would like to check my order status' },
    { id: '3', role: 'assistant', content: 'Please provide your order number and I will check it for you.' },
  ]);
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editingContent, setEditingContent] = useState('');

  // Sync embed config with style store
  useEffect(() => {
    updateStyleConfig({
      theme: config.theme,
      primaryColor: config.primaryColor,
      buttonSize: config.buttonSize,
      windowWidth: config.windowWidth,
      windowHeight: config.windowHeight,
      welcomeMessage: config.welcomeMessage,
      placeholder: config.placeholder,
      showBranding: config.showBranding,
      allowFullscreen: config.allowFullscreen,
    });
  }, [config, updateStyleConfig]);

  // Message editing handlers
  const handleEditMessage = (id: string, content: string) => {
    setEditingMessageId(id);
    setEditingContent(content);
  };

  const handleSaveMessage = (id: string) => {
    setPreviewMessages(prev =>
      prev.map(msg => (msg.id === id ? { ...msg, content: editingContent } : msg))
    );
    setEditingMessageId(null);
    setEditingContent('');
  };

  const handleAddMessage = (role: 'user' | 'assistant') => {
    const newMessage = {
      id: Date.now().toString(),
      role,
      content: role === 'user' ? 'New user message' : 'New AI response',
    };
    setPreviewMessages(prev => [...prev, newMessage]);
  };

  const handleDeleteMessage = (id: string) => {
    setPreviewMessages(prev => prev.filter(msg => msg.id !== id));
  };

  const handleResetMessages = () => {
    setPreviewMessages([
      { id: '1', role: 'assistant', content: 'Hello! How can I help you today?' },
      { id: '2', role: 'user', content: 'I would like to check my order status' },
      { id: '3', role: 'assistant', content: 'Please provide your order number and I will check it for you.' },
    ]);
  };

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
      title: 'Copied',
      description: 'Code has been copied to clipboard',
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
            Embed AI chatbot on your website
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
                Select Chatflow
              </CardTitle>
              <CardDescription>Choose a Chatflow to embed</CardDescription>
            </CardHeader>
            <CardContent>
              <Select
                value={config.chatflowId}
                onValueChange={(v) => setConfig({ ...config, chatflowId: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Chatflow..." />
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
                  You must select a Chatflow first to generate embed code
                </p>
              )}
            </CardContent>
          </Card>

          {/* Appearance Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Appearance Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Theme</Label>
                  <Select
                    value={config.theme}
                    onValueChange={(v) => setConfig({ ...config, theme: v as any })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">Light</SelectItem>
                      <SelectItem value="dark">Dark</SelectItem>
                      <SelectItem value="auto">Auto (System)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Position</Label>
                  <Select
                    value={config.position}
                    onValueChange={(v) => setConfig({ ...config, position: v as any })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="bottom-right">Bottom Right</SelectItem>
                      <SelectItem value="bottom-left">Bottom Left</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Primary Color</Label>
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
                <Label>Button Size: {config.buttonSize}px</Label>
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
                  <Label>Window Width: {config.windowWidth}px</Label>
                  <Slider
                    value={[config.windowWidth]}
                    onValueChange={([v]) => setConfig({ ...config, windowWidth: v ?? 400 })}
                    min={300}
                    max={600}
                    step={20}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Window Height: {config.windowHeight}px</Label>
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
                Behavior Settings
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Welcome Message</Label>
                <Textarea
                  value={config.welcomeMessage}
                  onChange={(e) => setConfig({ ...config, welcomeMessage: e.target.value })}
                  rows={2}
                />
              </div>

              <div className="space-y-2">
                <Label>Input Placeholder</Label>
                <Input
                  value={config.placeholder}
                  onChange={(e) => setConfig({ ...config, placeholder: e.target.value })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Show Branding</Label>
                  <p className="text-xs text-muted-foreground">Display "Powered by AgenticRAG"</p>
                </div>
                <Switch
                  checked={config.showBranding}
                  onCheckedChange={(v) => setConfig({ ...config, showBranding: v })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Allow Fullscreen</Label>
                  <p className="text-xs text-muted-foreground">Users can expand to fullscreen</p>
                </div>
                <Switch
                  checked={config.allowFullscreen}
                  onCheckedChange={(v) => setConfig({ ...config, allowFullscreen: v })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto Open</Label>
                  <p className="text-xs text-muted-foreground">Automatically open chat after page load</p>
                </div>
                <Switch
                  checked={config.autoOpen}
                  onCheckedChange={(v) => setConfig({ ...config, autoOpen: v })}
                />
              </div>

              {config.autoOpen && (
                <div className="space-y-2">
                  <Label>Auto Open Delay: {config.autoOpenDelay}s</Label>
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
                  Preview
                </CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleResetMessages}
                  >
                    Reset
                  </Button>
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
              </div>
            </CardHeader>
            {previewOpen && (
              <CardContent className="space-y-4">
                {/* Interactive Chat Preview */}
                <div
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden border"
                  style={{
                    width: '100%',
                    maxWidth: config.windowWidth,
                    height: Math.min(config.windowHeight, 500),
                    margin: '0 auto',
                  }}
                >
                  {/* Header */}
                  <div
                    className="p-4 text-white flex items-center justify-between"
                    style={{ backgroundColor: config.primaryColor }}
                  >
                    <div className="flex items-center gap-2">
                      <Bot className="h-5 w-5" />
                      <div>
                        <p className="font-semibold text-sm">AI Assistant</p>
                        <p className="text-xs opacity-80">Online</p>
                      </div>
                    </div>
                    {config.allowFullscreen && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-white hover:bg-white/20 h-8 w-8 p-0"
                      >
                        <Maximize2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>

                  {/* Messages Area */}
                  <ScrollArea className="h-[calc(100%-120px)] p-4">
                    <div className="space-y-3">
                      {previewMessages.map((message) => (
                        <div
                          key={message.id}
                          className={`flex ${
                            message.role === 'user' ? 'justify-end' : 'justify-start'
                          } group`}
                        >
                          <div className="flex flex-col max-w-[80%] gap-1">
                            <div
                              className={`rounded-lg px-3 py-2 text-sm ${
                                message.role === 'user'
                                  ? 'text-white'
                                  : 'bg-muted'
                              }`}
                              style={{
                                backgroundColor:
                                  message.role === 'user' ? config.primaryColor : undefined,
                              }}
                            >
                              {editingMessageId === message.id ? (
                                <div className="space-y-2">
                                  <Textarea
                                    value={editingContent}
                                    onChange={(e) => setEditingContent(e.target.value)}
                                    className="min-h-[60px] text-sm"
                                    autoFocus
                                  />
                                  <div className="flex gap-2">
                                    <Button
                                      size="sm"
                                      onClick={() => handleSaveMessage(message.id)}
                                    >
                                      <Check className="h-3 w-3 mr-1" />
                                      Save
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => setEditingMessageId(null)}
                                    >
                                      Cancel
                                    </Button>
                                  </div>
                                </div>
                              ) : (
                                <p className="whitespace-pre-wrap">{message.content}</p>
                              )}
                            </div>
                            {/* Edit/Delete buttons */}
                            {editingMessageId !== message.id && (
                              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 px-2 text-xs"
                                  onClick={() => handleEditMessage(message.id, message.content)}
                                >
                                  Edit
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  className="h-6 px-2 text-xs text-red-500 hover:text-red-600"
                                  onClick={() => handleDeleteMessage(message.id)}
                                >
                                  Delete
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>

                  {/* Input Area */}
                  <div className="p-3 border-t bg-background">
                    <div className="flex gap-2">
                      <Input
                        placeholder={config.placeholder}
                        className="flex-1"
                        disabled
                      />
                      <Button
                        size="icon"
                        style={{ backgroundColor: config.primaryColor }}
                        disabled
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                    {config.showBranding && (
                      <p className="text-xs text-center text-muted-foreground mt-2">
                        Powered by AgenticRAG
                      </p>
                    )}
                  </div>
                </div>

                {/* Add Message Buttons */}
                <div className="flex gap-2 justify-center">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAddMessage('user')}
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Add User Message
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleAddMessage('assistant')}
                  >
                    <Bot className="h-4 w-4 mr-2" />
                    Add AI Response
                  </Button>
                </div>

                <div className="text-xs text-muted-foreground text-center">
                  💡 Hover over messages to see edit/delete buttons
                </div>
              </CardContent>
            )}
          </Card>

          {/* Embed Code */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                Embed Code
              </CardTitle>
              <CardDescription>
                Add the code below to your website
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
                    Add this code at the end of the {'<body>'} tag
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
                    First run: npm install @agenticrag/react
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
                    Add the iFrame wherever you want
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
                  <h3 className="font-medium">SDK Documentation</h3>
                  <p className="text-sm text-muted-foreground">
                    Check TypeScript and Python SDK usage
                  </p>
                </div>
                <Button variant="outline" asChild>
                  <a href="/docs/sdk" target="_blank">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    View Docs
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
