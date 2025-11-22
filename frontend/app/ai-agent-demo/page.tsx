"use client";

/**
 * AI Agent Tool Demo Page
 * 
 * Demonstrates the enhanced AI Agent configuration with:
 * - LLM provider and model selection
 * - Real-time chat UI
 * - Memory management
 */

import React, { useState } from "react";
import { AIAgentConfig, AIAgentChatUI } from "@/components/agent-builder/tool-configs";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Settings, MessageSquare, Code } from "lucide-react";

export default function AIAgentDemoPage() {
  const [showConfig, setShowConfig] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [config, setConfig] = useState<Record<string, any>>({
    provider: "ollama",
    model: "llama3.3:70b",
    system_prompt: "You are a helpful AI assistant.",
    enable_memory: true,
    memory_type: "short_term",
    temperature: 0.7,
  });
  const [credentials, setCredentials] = useState<Record<string, any>>({});

  const handleSaveConfig = (newConfig: Record<string, any>, newCredentials: Record<string, any>) => {
    setConfig(newConfig);
    setCredentials(newCredentials);
    setShowConfig(false);
    alert("Configuration saved successfully!");
  };

  const handleTestChat = async (message: string): Promise<string> => {
    // Mock implementation - in production, this would call the actual API
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(`[${config.provider}/${config.model}] Echo: ${message}\n\nThis is a test response. Configure the tool with real API keys to enable actual AI responses.`);
      }, 1000);
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-4xl font-bold flex items-center gap-3">
          <span className="text-5xl">🤖</span>
          AI Agent Tool Demo
        </h1>
        <p className="text-lg text-muted-foreground">
          Enhanced AI Agent configuration with LLM selection and real-time chat UI
        </p>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3">
        <Button onClick={() => setShowConfig(!showConfig)} size="lg">
          <Settings className="h-5 w-5 mr-2" />
          {showConfig ? "Hide" : "Show"} Configuration
        </Button>
        <Button onClick={() => setShowChat(!showChat)} variant="outline" size="lg">
          <MessageSquare className="h-5 w-5 mr-2" />
          {showChat ? "Hide" : "Show"} Chat UI
        </Button>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="features">Features</TabsTrigger>
          <TabsTrigger value="examples">Examples</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Current Configuration</CardTitle>
              <CardDescription>Active AI Agent settings</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Provider</div>
                  <div className="text-lg font-semibold">{config.provider || "Not set"}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Model</div>
                  <div className="text-lg font-semibold">{config.model || "Not set"}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Temperature</div>
                  <div className="text-lg font-semibold">{config.temperature || 0.7}</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground">Memory</div>
                  <div className="text-lg font-semibold">
                    {config.enable_memory ? `Enabled (${config.memory_type})` : "Disabled"}
                  </div>
                </div>
              </div>
              
              {config.system_prompt && (
                <div className="mt-4">
                  <div className="text-sm font-medium text-muted-foreground mb-2">System Prompt</div>
                  <div className="bg-muted p-3 rounded-md text-sm">
                    {config.system_prompt}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Supported LLM Providers</CardTitle>
              <CardDescription>Choose from multiple AI providers</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-3xl mb-2">🦙</div>
                  <div className="font-medium">Ollama</div>
                  <div className="text-xs text-muted-foreground">Local</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-3xl mb-2">🤖</div>
                  <div className="font-medium">OpenAI</div>
                  <div className="text-xs text-muted-foreground">Cloud</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-3xl mb-2">🧠</div>
                  <div className="font-medium">Claude</div>
                  <div className="text-xs text-muted-foreground">Cloud</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-3xl mb-2">✨</div>
                  <div className="font-medium">Gemini</div>
                  <div className="text-xs text-muted-foreground">Cloud</div>
                </div>
                <div className="text-center p-4 border rounded-lg">
                  <div className="text-3xl mb-2">⚡</div>
                  <div className="font-medium">Grok</div>
                  <div className="text-xs text-muted-foreground">Cloud</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Features Tab */}
        <TabsContent value="features" className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  Dynamic Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">LLM Provider Selection</div>
                    <div className="text-sm text-muted-foreground">
                      Choose from Ollama, OpenAI, Claude, Gemini, or Grok
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Model Selection</div>
                    <div className="text-sm text-muted-foreground">
                      Dynamic model list based on selected provider
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Generation Parameters</div>
                    <div className="text-sm text-muted-foreground">
                      Temperature, max tokens, top-p, penalties
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Real-time Chat UI
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Interactive Chat Interface</div>
                    <div className="text-sm text-muted-foreground">
                      Real-time conversation with AI agent
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Flexible Positioning</div>
                    <div className="text-sm text-muted-foreground">
                      Right panel, bottom, modal, or inline display
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Chat History</div>
                    <div className="text-sm text-muted-foreground">
                      Export conversations as JSON
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code className="h-5 w-5" />
                  Memory Management
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Short-term Memory</div>
                    <div className="text-sm text-muted-foreground">
                      Current session conversation history
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Mid-term Memory</div>
                    <div className="text-sm text-muted-foreground">
                      Session context and summaries
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Long-term Memory</div>
                    <div className="text-sm text-muted-foreground">
                      Persistent knowledge base
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Advanced Options</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Response Formats</div>
                    <div className="text-sm text-muted-foreground">
                      Text, JSON, or structured output
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">JSON Extraction</div>
                    <div className="text-sm text-muted-foreground">
                      Auto-parse JSON from responses
                    </div>
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="text-green-500 mt-1">✓</div>
                  <div>
                    <div className="font-medium">Metadata & Usage Stats</div>
                    <div className="text-sm text-muted-foreground">
                      Token usage and performance metrics
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Examples Tab */}
        <TabsContent value="examples" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Usage Examples</CardTitle>
              <CardDescription>Common AI Agent configurations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <div className="font-medium mb-1">Simple Chat Assistant</div>
                <div className="text-sm text-muted-foreground mb-2">
                  Basic conversational AI with memory
                </div>
                <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
{`{
  "provider": "ollama",
  "model": "llama3.3:70b",
  "system_prompt": "You are a helpful assistant.",
  "enable_memory": true,
  "memory_type": "short_term",
  "temperature": 0.7
}`}
                </pre>
              </div>

              <div className="border-l-4 border-green-500 pl-4">
                <div className="font-medium mb-1">JSON Data Extractor</div>
                <div className="text-sm text-muted-foreground mb-2">
                  Extract structured data from text
                </div>
                <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
{`{
  "provider": "openai",
  "model": "gpt-4o",
  "system_prompt": "Extract key information as JSON.",
  "response_format": "json_object",
  "extract_json": true,
  "temperature": 0.3
}`}
                </pre>
              </div>

              <div className="border-l-4 border-purple-500 pl-4">
                <div className="font-medium mb-1">Creative Writing Assistant</div>
                <div className="text-sm text-muted-foreground mb-2">
                  High creativity for content generation
                </div>
                <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
{`{
  "provider": "claude",
  "model": "claude-4.5-sonnet",
  "system_prompt": "You are a creative writer.",
  "temperature": 1.2,
  "max_tokens": 2000,
  "enable_memory": false
}`}
                </pre>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Configuration Panel */}
      {showConfig && (
        <Card className="border-2 border-primary">
          <CardHeader>
            <CardTitle>AI Agent Configuration</CardTitle>
            <CardDescription>Configure your AI agent settings</CardDescription>
          </CardHeader>
          <CardContent>
            <AIAgentConfig
              initialConfig={config}
              initialCredentials={credentials}
              onSave={handleSaveConfig}
              onCancel={() => setShowConfig(false)}
            />
          </CardContent>
        </Card>
      )}

      {/* Chat UI */}
      {showChat && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl h-[80vh]">
            <AIAgentChatUI
              position="inline"
              onClose={() => setShowChat(false)}
              onSendMessage={handleTestChat}
              sessionId={`demo-${Date.now()}`}
              systemPrompt={config.system_prompt}
              provider={config.provider}
              model={config.model}
            />
          </div>
        </div>
      )}
    </div>
  );
}
