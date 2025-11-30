"use client";

/**
 * AI Agent Tool Configuration Component
 * 
 * Enhanced configuration with:
 * - Dynamic LLM provider and model selection
 * - Real-time chat UI integration
 * - Memory management settings
 */

import React, { useState, useEffect } from "react";
import { AIAgentChatUI } from "./AIAgentChatUI";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MessageSquare, Settings, Brain, Zap } from "lucide-react";
import { LLM_PROVIDERS, getModelsForProvider } from "@/lib/llm-models";

interface AIAgentConfigProps {
  initialConfig?: Record<string, any>;
  initialCredentials?: Record<string, any>;
  onSave: (config: Record<string, any>, credentials: Record<string, any>) => void;
  onCancel: () => void;
}

export function AIAgentConfig({
  initialConfig = {},
  initialCredentials = {},
  onSave,
  onCancel,
}: AIAgentConfigProps) {
  // Core settings (handle both frontend and backend field names)
  const [provider, setProvider] = useState(initialConfig.llm_provider || initialConfig.provider || "ollama");
  const [model, setModel] = useState(initialConfig.model || "llama3.3:70b");
  const [systemPrompt, setSystemPrompt] = useState(initialConfig.system_prompt || "");
  const [userMessage, setUserMessage] = useState(initialConfig.user_message || "");

  // Chat UI settings
  const [enableChatUI, setEnableChatUI] = useState(initialConfig.enable_chat_ui || false);
  const [chatUIPosition, setChatUIPosition] = useState(initialConfig.chat_ui_position || "right");
  const [showChatUI, setShowChatUI] = useState(false);

  // Memory settings
  const [enableMemory, setEnableMemory] = useState(initialConfig.enable_memory ?? true);
  const [memoryType, setMemoryType] = useState(initialConfig.memory_type || "short_term");
  const [memoryWindow, setMemoryWindow] = useState(initialConfig.memory_window || "10");
  const [sessionId, setSessionId] = useState(initialConfig.session_id || `session-${Date.now()}`);

  // Generation parameters
  const [temperature, setTemperature] = useState(initialConfig.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(initialConfig.max_tokens || 1000);
  const [topP, setTopP] = useState(initialConfig.top_p || 1);
  const [frequencyPenalty, setFrequencyPenalty] = useState(initialConfig.frequency_penalty || 0);
  const [presencePenalty, setPresencePenalty] = useState(initialConfig.presence_penalty || 0);

  // Advanced settings
  const [responseFormat, setResponseFormat] = useState(initialConfig.response_format || "text");
  const [timeout, setTimeout] = useState(initialConfig.timeout || "60");
  const [extractJson, setExtractJson] = useState(initialConfig.extract_json || false);
  const [returnMetadata, setReturnMetadata] = useState(initialConfig.return_metadata ?? true);

  // Credentials
  const [apiKey, setApiKey] = useState(initialCredentials.api_key || "");

  // Get available models for selected provider
  const availableModels = getModelsForProvider(provider);
  const selectedProvider = LLM_PROVIDERS.find((p) => p.id === provider);

  // Update model when provider changes
  useEffect(() => {
    const models = getModelsForProvider(provider);
    if (models.length > 0 && !models.find((m) => m.id === model)) {
      setModel(models[0].id);
    }
  }, [provider]);

  const handleSave = () => {
    const config = {
      // Backend expects these field names (all required fields must be present)
      llm_provider: provider || "ollama",
      model: model || "llama3.1:8b",
      memory_type: memoryType || "short_term",
      system_prompt: systemPrompt || "You are a helpful AI assistant.",
      user_message: userMessage,
      enable_chat_ui: enableChatUI,
      chat_ui_position: chatUIPosition,
      enable_memory: enableMemory,
      memory_window: parseInt(memoryWindow) || 10,
      session_id: sessionId,
      temperature: parseFloat(temperature.toString()) || 0.7,
      max_tokens: parseInt(maxTokens.toString()) || 2000,
      top_p: parseFloat(topP.toString()) || 1.0,
      frequency_penalty: parseFloat(frequencyPenalty.toString()) || 0,
      presence_penalty: parseFloat(presencePenalty.toString()) || 0,
      response_format: responseFormat || "text",
      timeout: parseInt(timeout) || 60,
      extract_json: extractJson || false,
      return_metadata: returnMetadata ?? true,
      enable_web_search: true,
      enable_vector_search: true,
      max_iterations: 10,
      // Also keep frontend field names for compatibility
      provider: provider || "ollama",
      // Include API key in config for workflow execution
      ...(selectedProvider?.requiresApiKey && apiKey ? { api_key: apiKey } : {}),
    };

    const credentials = selectedProvider?.requiresApiKey
      ? { api_key: apiKey }
      : {};

    onSave(config, credentials);
  };

  const handleTestChat = async (message: string): Promise<string> => {
    // Mock implementation - in production, this would call the actual API
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(`Echo: ${message}\n\n(This is a test response. Configure the tool and save to enable real AI responses.)`);
      }, 1000);
    });
  };

  return (
    <div className="flex gap-4 h-[calc(100vh-200px)]">
      {/* Configuration Panel */}
      <div className="flex-1 overflow-y-auto">
        <Tabs defaultValue="core" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="core">
              <Settings className="h-4 w-4 mr-2" />
              Core
            </TabsTrigger>
            <TabsTrigger value="memory">
              <Brain className="h-4 w-4 mr-2" />
              Memory
            </TabsTrigger>
            <TabsTrigger value="generation">
              <Zap className="h-4 w-4 mr-2" />
              Generation
            </TabsTrigger>
            <TabsTrigger value="advanced">
              Advanced
            </TabsTrigger>
          </TabsList>

          {/* Core Settings */}
          <TabsContent value="core" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>LLM Provider</Label>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {LLM_PROVIDERS.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      <div className="flex items-center gap-2">
                        <span>{p.icon}</span>
                        <span>{p.name}</span>
                        <span className="text-xs text-gray-500">({p.type})</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">{selectedProvider?.description}</p>
            </div>

            <div className="space-y-2">
              <Label>Model</Label>
              <Select value={model} onValueChange={setModel}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((m) => (
                    <SelectItem key={m.id} value={m.id}>
                      <div>
                        <div>{m.name}</div>
                        {m.description && (
                          <div className="text-xs text-gray-500">{m.description}</div>
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedProvider?.requiresApiKey && (
              <div className="space-y-2">
                <Label>API Key</Label>
                <Input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                />
                <p className="text-xs text-gray-500">
                  Required for {selectedProvider.name}
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label>System Prompt</Label>
              <Textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="You are a helpful AI assistant..."
                rows={4}
              />
              <p className="text-xs text-gray-500">
                Define the agent's behavior and personality
              </p>
            </div>

            <div className="space-y-2">
              <Label>User Message</Label>
              <Textarea
                value={userMessage}
                onChange={(e) => setUserMessage(e.target.value)}
                placeholder="Enter your message or use {{input.message}}"
                rows={3}
              />
              <p className="text-xs text-gray-500">
                Use variables like {`{{input.message}}`} for dynamic content
              </p>
            </div>

            <div className="space-y-4 border-t pt-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Enable Real-time Chat UI</Label>
                  <p className="text-xs text-gray-500">
                    Show interactive chat interface
                  </p>
                </div>
                <Switch checked={enableChatUI} onCheckedChange={setEnableChatUI} />
              </div>

              {enableChatUI && (
                <>
                  <div className="space-y-2">
                    <Label>Chat UI Position</Label>
                    <Select value={chatUIPosition} onValueChange={setChatUIPosition}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="right">Right Panel</SelectItem>
                        <SelectItem value="bottom">Bottom Panel</SelectItem>
                        <SelectItem value="modal">Modal Dialog</SelectItem>
                        <SelectItem value="inline">Inline</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button
                    onClick={() => setShowChatUI(true)}
                    variant="outline"
                    className="w-full"
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Test Chat Interface
                  </Button>
                </>
              )}
            </div>
          </TabsContent>

          {/* Memory Settings */}
          <TabsContent value="memory" className="space-y-4 mt-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enable Memory</Label>
                <p className="text-xs text-gray-500">
                  Use conversation memory
                </p>
              </div>
              <Switch checked={enableMemory} onCheckedChange={setEnableMemory} />
            </div>

            {enableMemory && (
              <>
                <div className="space-y-2">
                  <Label>Memory Type</Label>
                  <Select value={memoryType} onValueChange={setMemoryType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="short_term">Short Term (Current session)</SelectItem>
                      <SelectItem value="mid_term">Mid Term (Session context)</SelectItem>
                      <SelectItem value="long_term">Long Term (Persistent)</SelectItem>
                      <SelectItem value="all">All (Combined)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Memory Window</Label>
                  <Select value={memoryWindow} onValueChange={setMemoryWindow}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="5">5 messages</SelectItem>
                      <SelectItem value="10">10 messages</SelectItem>
                      <SelectItem value="20">20 messages</SelectItem>
                      <SelectItem value="50">50 messages</SelectItem>
                      <SelectItem value="100">100 messages</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Session ID</Label>
                  <Input
                    value={sessionId}
                    onChange={(e) => setSessionId(e.target.value)}
                    placeholder="auto-generated or custom"
                  />
                  <p className="text-xs text-gray-500">
                    Unique identifier for this conversation
                  </p>
                </div>
              </>
            )}
          </TabsContent>

          {/* Generation Parameters */}
          <TabsContent value="generation" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Temperature: {temperature}</Label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500">
                0 = deterministic, 2 = very creative
              </p>
            </div>

            <div className="space-y-2">
              <Label>Max Tokens</Label>
              <Input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                min="1"
                max="4096"
              />
            </div>

            <div className="space-y-2">
              <Label>Top P: {topP}</Label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={topP}
                onChange={(e) => setTopP(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <Label>Frequency Penalty: {frequencyPenalty}</Label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={frequencyPenalty}
                onChange={(e) => setFrequencyPenalty(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500">Reduce repetition</p>
            </div>

            <div className="space-y-2">
              <Label>Presence Penalty: {presencePenalty}</Label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={presencePenalty}
                onChange={(e) => setPresencePenalty(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500">Encourage new topics</p>
            </div>
          </TabsContent>

          {/* Advanced Settings */}
          <TabsContent value="advanced" className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Response Format</Label>
              <Select value={responseFormat} onValueChange={setResponseFormat}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="text">Text</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                  <SelectItem value="json_object">JSON Object</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Timeout (seconds)</Label>
              <Select value={timeout} onValueChange={setTimeout}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="30">30s</SelectItem>
                  <SelectItem value="60">60s</SelectItem>
                  <SelectItem value="120">120s</SelectItem>
                  <SelectItem value="300">300s</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Extract JSON from Response</Label>
                <p className="text-xs text-gray-500">
                  Parse JSON from markdown code blocks
                </p>
              </div>
              <Switch checked={extractJson} onCheckedChange={setExtractJson} />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Return Metadata</Label>
                <p className="text-xs text-gray-500">
                  Include usage stats and metadata
                </p>
              </div>
              <Switch checked={returnMetadata} onCheckedChange={setReturnMetadata} />
            </div>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Configuration
          </Button>
        </div>
      </div>

      {/* Chat UI Preview */}
      {showChatUI && (
        <div className="w-96">
          <AIAgentChatUI
            position="inline"
            onClose={() => setShowChatUI(false)}
            onSendMessage={handleTestChat}
            sessionId={sessionId}
            systemPrompt={systemPrompt}
            provider={provider}
            model={model}
          />
        </div>
      )}
    </div>
  );
}
