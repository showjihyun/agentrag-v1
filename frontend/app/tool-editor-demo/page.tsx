"use client";

/**
 * Tool Editor Demo Page
 * 
 * Premium Tool Editor 컴포넌트 데모 및 테스트 페이지
 */

import React, { useState } from "react";
import { PremiumToolEditor } from "@/components/common/ToolEditor";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ToolConfig } from "@/components/common/ToolEditor/types";

export default function ToolEditorDemoPage() {
  const [showEditor, setShowEditor] = useState(false);
  const [selectedTool, setSelectedTool] = useState<ToolConfig | null>(null);
  const [savedConfig, setSavedConfig] = useState<Record<string, any>>({});

  // Demo tools
  const demoTools: ToolConfig[] = [
    {
      id: 'google_search',
      name: 'Google Search',
      description: 'Search the web using Google Search API',
      category: 'search',
      bg_color: '#4285F4',
      icon: '🔍',
      version: '1.0.0',
      docs_link: 'https://developers.google.com/custom-search',
      tags: ['search', 'web', 'google'],
      params: {
        query: {
          type: 'string',
          description: 'Search query string',
          required: true,
          placeholder: 'Enter your search query...',
          helpText: 'Use quotes for exact matches, - to exclude terms',
          group: 'basic',
          order: 1,
        },
        max_results: {
          type: 'number',
          description: 'Maximum number of results to return',
          default: 10,
          min: 1,
          max: 100,
          group: 'basic',
          order: 2,
        },
        safe_search: {
          type: 'boolean',
          description: 'Enable safe search filtering',
          default: true,
          group: 'basic',
          order: 3,
        },
        language: {
          type: 'select',
          description: 'Search language',
          enum: ['en', 'ko', 'ja', 'zh', 'es', 'fr', 'de'],
          default: 'en',
          group: 'advanced',
          order: 1,
        },
        date_range: {
          type: 'select',
          description: 'Filter by date range',
          enum: ['any', 'past_day', 'past_week', 'past_month', 'past_year'],
          default: 'any',
          group: 'advanced',
          order: 2,
        },
      },
      outputs: {
        results: { type: 'array', description: 'Search results' },
        total: { type: 'number', description: 'Total results found' },
      },
      examples: [
        {
          name: 'Basic Search',
          description: 'Simple search with default settings',
          config: {
            query: '{{ workflow.input.query }}',
            max_results: 10,
            safe_search: true,
          },
        },
        {
          name: 'Advanced Search',
          description: 'Search with language and date filters',
          config: {
            query: '{{ workflow.input.query }}',
            max_results: 50,
            safe_search: false,
            language: 'en',
            date_range: 'past_month',
          },
        },
      ],
    },
    {
      id: 'openai_chat',
      name: 'OpenAI Chat',
      description: 'Generate text using OpenAI GPT models',
      category: 'ai',
      bg_color: '#10A37F',
      icon: '🤖',
      version: '2.0.0',
      docs_link: 'https://platform.openai.com/docs',
      tags: ['ai', 'llm', 'openai', 'gpt'],
      params: {
        api_key: {
          type: 'password',
          description: 'OpenAI API key',
          required: true,
          placeholder: 'sk-...',
          helpText: 'Get your API key from OpenAI dashboard',
          group: 'authentication',
          order: 1,
        },
        model: {
          type: 'string',  // 'string'으로 변경하면 자동으로 AI 모델 옵션 제공
          description: 'GPT model to use',
          required: true,
          group: 'basic',
          order: 1,
        },
        prompt: {
          type: 'textarea',
          description: 'Prompt for the model',
          required: true,
          placeholder: 'Enter your prompt...',
          group: 'basic',
          order: 2,
        },
        temperature: {
          type: 'number',  // 'temperature' 키워드로 자동 옵션 제공
          description: 'Sampling temperature (0-2)',
          default: 0.7,
          helpText: 'Higher values make output more random',
          group: 'advanced',
          order: 1,
        },
        max_tokens: {
          type: 'number',  // 'max_tokens' 키워드로 자동 옵션 제공
          description: 'Maximum tokens to generate',
          default: 1000,
          group: 'advanced',
          order: 2,
        },
        system_message: {
          type: 'textarea',
          description: 'System message to set behavior',
          placeholder: 'You are a helpful assistant...',
          group: 'advanced',
          order: 3,
        },
      },
      outputs: {
        text: { type: 'string', description: 'Generated text' },
        tokens_used: { type: 'number', description: 'Tokens consumed' },
      },
      examples: [
        {
          name: 'Chat Completion',
          description: 'Standard chat completion',
          config: {
            model: 'gpt-4',
            prompt: '{{ workflow.input.message }}',
            temperature: 0.7,
            max_tokens: 1000,
          },
        },
        {
          name: 'Code Generation',
          description: 'Generate code with low temperature',
          config: {
            model: 'gpt-4',
            prompt: 'Write a function to {{ workflow.input.task }}',
            temperature: 0.2,
            max_tokens: 2000,
            system_message: 'You are an expert programmer.',
          },
        },
      ],
    },
    {
      id: 'http_request',
      name: 'HTTP Request',
      description: 'Make HTTP requests to any API',
      category: 'developer',
      bg_color: '#FF6B6B',
      icon: '🌐',
      version: '1.5.0',
      tags: ['http', 'api', 'rest'],
      params: {
        url: {
          type: 'url',
          description: 'Request URL',
          required: true,
          placeholder: 'https://api.example.com/endpoint',
          group: 'basic',
          order: 1,
        },
        method: {
          type: 'string',  // 'method' 키워드로 자동으로 HTTP 메소드 옵션 제공
          description: 'HTTP method',
          default: 'GET',
          required: true,
          group: 'basic',
          order: 2,
        },
        headers: {
          type: 'json',
          description: 'Request headers',
          placeholder: '{"Content-Type": "application/json"}',
          group: 'basic',
          order: 3,
        },
        body: {
          type: 'json',
          description: 'Request body',
          placeholder: '{"key": "value"}',
          group: 'basic',
          order: 4,
          showIf: (config) => ['POST', 'PUT', 'PATCH'].includes(config.method),
        },
        timeout: {
          type: 'number',  // 'timeout' 키워드로 자동 옵션 제공
          description: 'Request timeout (seconds)',
          default: 30,
          group: 'advanced',
          order: 1,
        },
      },
      outputs: {
        status: { type: 'number', description: 'HTTP status code' },
        data: { type: 'object', description: 'Response data' },
      },
      examples: [
        {
          name: 'GET Request',
          description: 'Simple GET request',
          config: {
            url: 'https://api.example.com/data',
            method: 'GET',
            headers: { 'Accept': 'application/json' },
          },
        },
        {
          name: 'POST Request',
          description: 'POST with JSON body',
          config: {
            url: 'https://api.example.com/create',
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: { name: '{{ workflow.input.name }}' },
          },
        },
      ],
    },
  ];

  const handleOpenEditor = (tool: ToolConfig) => {
    setSelectedTool(tool);
    setShowEditor(true);
  };

  const handleSave = (config: Record<string, any>) => {
    setSavedConfig(config);
    setShowEditor(false);
    console.log('Saved config:', config);
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold">Premium Tool Editor Demo</h1>
        <p className="text-muted-foreground">
          고급스럽고 재사용 가능한 Tool 편집 컴포넌트 데모
        </p>
      </div>

      {/* Features */}
      <Card>
        <CardHeader>
          <CardTitle>✨ 주요 기능</CardTitle>
          <CardDescription>
            새로운 Tool Editor의 강력한 기능들
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <div className="text-2xl">🎨</div>
              <p className="text-sm font-medium">고급 UI/UX</p>
              <p className="text-xs text-muted-foreground">
                모던하고 직관적인 인터페이스
              </p>
            </div>
            <div className="space-y-1">
              <div className="text-2xl">✅</div>
              <p className="text-sm font-medium">스마트 검증</p>
              <p className="text-xs text-muted-foreground">
                실시간 입력 검증 및 제안
              </p>
            </div>
            <div className="space-y-1">
              <div className="text-2xl">📋</div>
              <p className="text-sm font-medium">템플릿</p>
              <p className="text-xs text-muted-foreground">
                사전 구성된 설정 템플릿
              </p>
            </div>
            <div className="space-y-1">
              <div className="text-2xl">👁️</div>
              <p className="text-sm font-medium">미리보기</p>
              <p className="text-xs text-muted-foreground">
                실시간 설정 미리보기
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Demo Tools */}
      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">All Tools</TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
          <TabsTrigger value="ai">AI</TabsTrigger>
          <TabsTrigger value="developer">Developer</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {demoTools.map((tool) => (
              <Card key={tool.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start gap-3">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                      style={{ backgroundColor: tool.bg_color }}
                    >
                      {tool.icon}
                    </div>
                    <div className="flex-1">
                      <CardTitle className="text-base">{tool.name}</CardTitle>
                      <CardDescription className="text-xs">
                        {tool.description}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-1">
                    {tool.tags?.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{Object.keys(tool.params).length} parameters</span>
                    <span>v{tool.version}</span>
                  </div>

                  <Button
                    className="w-full"
                    onClick={() => handleOpenEditor(tool)}
                  >
                    Configure Tool
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {['search', 'ai', 'developer'].map((category) => (
          <TabsContent key={category} value={category} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {demoTools
                .filter((tool) => tool.category === category)
                .map((tool) => (
                  <Card key={tool.id} className="cursor-pointer hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start gap-3">
                        <div
                          className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                          style={{ backgroundColor: tool.bg_color }}
                        >
                          {tool.icon}
                        </div>
                        <div className="flex-1">
                          <CardTitle className="text-base">{tool.name}</CardTitle>
                          <CardDescription className="text-xs">
                            {tool.description}
                          </CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <Button
                        className="w-full"
                        onClick={() => handleOpenEditor(tool)}
                      >
                        Configure Tool
                      </Button>
                    </CardContent>
                  </Card>
                ))}
            </div>
          </TabsContent>
        ))}
      </Tabs>

      {/* Saved Config Display */}
      {Object.keys(savedConfig).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Last Saved Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-xs">
              {JSON.stringify(savedConfig, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      {/* Tool Editor Modal */}
      {showEditor && selectedTool && (
        <PremiumToolEditor
          tool={selectedTool}
          initialConfig={savedConfig}
          onSave={handleSave}
          onClose={() => setShowEditor(false)}
          mode="modal"
          showPreview={true}
          showTemplates={true}
          showAdvanced={true}
          autoSave={false}
        />
      )}
    </div>
  );
}
