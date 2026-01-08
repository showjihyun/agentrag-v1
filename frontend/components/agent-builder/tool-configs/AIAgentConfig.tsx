"use client";

/**
 * AI Agent Tool Configuration Component
 * 
 * Enhanced configuration with:
 * - Dynamic LLM provider and model selection
 * - Real-time chat UI integration
 * - Memory management settings
 */

import React, { useState, useEffect, useMemo, useCallback, memo } from "react";
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
import { Slider } from "@/components/ui/slider";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { MessageSquare, Settings, Brain, Zap, AlertCircle, RefreshCw, Loader2, HelpCircle, RotateCcw, Sparkles, Copy, Check } from "lucide-react";
import { LLM_PROVIDERS, getModelsForProvider, getAvailableProviders } from "@/lib/llm-models";

// ============================================
// Constants (moved outside component for performance)
// ============================================

const DEFAULT_SYSTEM_PROMPT = "You are a helpful AI assistant. Answer questions accurately and concisely.";

const PROMPT_TEMPLATES = [
  { id: 'assistant', name: '🤖 기본 어시스턴트', prompt: 'You are a helpful AI assistant. Answer questions accurately and concisely.' },
  { id: 'korean', name: '🇰🇷 한국어 전문가', prompt: '당신은 한국어에 능통한 AI 어시스턴트입니다. 모든 응답을 자연스러운 한국어로 제공하고, 존댓말을 사용하세요.' },
  { id: 'coder', name: '💻 코드 전문가', prompt: 'You are an expert programmer. Provide clean, well-documented code with explanations. Follow best practices and consider edge cases.' },
  { id: 'analyst', name: '📊 데이터 분석가', prompt: 'You are a data analyst. Analyze information systematically, provide insights with supporting evidence, and present findings clearly.' },
  { id: 'writer', name: '✍️ 콘텐츠 작성자', prompt: '당신은 전문 콘텐츠 작성자입니다. 명확하고 매력적인 글을 작성하며, 독자의 관심을 끌 수 있는 표현을 사용하세요.' },
] as const;

const PRESETS = [
  { id: 'creative', name: '🎨 Creative', temperature: 1.2, topP: 0.95, description: '창의적인 응답' },
  { id: 'balanced', name: '⚖️ Balanced', temperature: 0.7, topP: 1.0, description: '균형 잡힌 응답' },
  { id: 'precise', name: '🎯 Precise', temperature: 0.2, topP: 0.8, description: '정확한 응답' },
  { id: 'code', name: '💻 Code', temperature: 0.1, topP: 0.95, description: '코드 생성 최적화' },
] as const;

// ============================================
// Types
// ============================================

interface AIAgentConfigData {
  llm_provider?: string;
  provider?: string;
  model?: string;
  system_prompt?: string;
  user_message?: string;
  enable_chat_ui?: boolean;
  chat_ui_position?: string;
  enable_memory?: boolean;
  memory_type?: string;
  memory_window?: string | number;
  session_id?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  response_format?: string;
  timeout?: string | number;
  extract_json?: boolean;
  return_metadata?: boolean;
}

interface AIAgentCredentials {
  api_key?: string;
}

// ============================================
// Memoized Sub-components
// ============================================

const InfoTooltip = memo(({ content }: { content: string }) => (
  <Tooltip>
    <TooltipTrigger asChild>
      <HelpCircle className="h-3.5 w-3.5 text-muted-foreground cursor-help ml-1" />
    </TooltipTrigger>
    <TooltipContent className="max-w-xs">
      <p className="text-xs">{content}</p>
    </TooltipContent>
  </Tooltip>
));
InfoTooltip.displayName = 'InfoTooltip';

// ============================================
// Main Component
// ============================================

interface AIAgentConfigProps {
  initialConfig?: AIAgentConfigData;
  initialCredentials?: AIAgentCredentials;
  onSave: (config: AIAgentConfigData & Record<string, unknown>, credentials: AIAgentCredentials) => void;
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
  const [loadingModels, setLoadingModels] = useState(false);

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
  const [timeoutValue, setTimeoutValue] = useState(initialConfig.timeout || "60");
  const [extractJson, setExtractJson] = useState(initialConfig.extract_json || false);
  const [returnMetadata, setReturnMetadata] = useState(initialConfig.return_metadata ?? true);

  // Credentials
  const [apiKey, setApiKey] = useState(initialCredentials.api_key || "");

  // UI State
  const [modelError, setModelError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState("core");

  // Tab completion status
  const tabStatus = useMemo(() => ({
    core: !!(model && model !== 'no-models'),
    memory: true, // Always valid with defaults
    generation: true, // Always valid with defaults
    advanced: true, // Always valid with defaults
  }), [model]);

  // Track if config has been modified
  const isDirty = useMemo(() => {
    return (
      provider !== (initialConfig.llm_provider || initialConfig.provider || "ollama") ||
      model !== (initialConfig.model || "llama3.3:70b") ||
      systemPrompt !== (initialConfig.system_prompt || "") ||
      temperature !== (initialConfig.temperature || 0.7) ||
      maxTokens !== (initialConfig.max_tokens || 1000)
    );
  }, [provider, model, systemPrompt, temperature, maxTokens, initialConfig]);

  // Get available models for selected provider
  const availableModels = getModelsForProvider(provider);
  const selectedProvider = LLM_PROVIDERS.find((p) => p.id === provider);

  // Fetch Ollama models from API if not in localStorage
  const fetchOllamaModels = useCallback(async () => {
    setLoadingModels(true);
    setModelError(null);
    try {
      // Get Ollama base URL from localStorage or use default
      const llmConfig = localStorage.getItem('llm_config');
      const ollamaBaseUrl = llmConfig 
        ? JSON.parse(llmConfig).ollama?.baseUrl || 'http://localhost:11434'
        : 'http://localhost:11434';
      
      const response = await fetch(`${ollamaBaseUrl}/api/tags`, {
        signal: AbortSignal.timeout(5000), // 5 second timeout
      });
      
      if (response.ok) {
        const data = await response.json();
        const models = data.models?.map((m: { name: string }) => m.name) || [];
        
        if (models.length === 0) {
          setModelError('No models installed in Ollama. Run "ollama pull llama3.1" to install a model.');
          return;
        }
        
        // Save to localStorage
        localStorage.setItem('ollama_models', JSON.stringify(models));
        
        // Update model if current one is not in the list
        if (models.length > 0 && !models.includes(model)) {
          setModel(models[0]);
        }
      } else {
        setModelError(`Ollama returned error: ${response.status}`);
      }
    } catch (error: any) {
      console.error('Failed to fetch Ollama models:', error);
      if (error.name === 'TimeoutError') {
        setModelError('Connection timeout. Is Ollama running?');
      } else {
        setModelError('Cannot connect to Ollama. Make sure it is running on localhost:11434');
      }
    } finally {
      setLoadingModels(false);
    }
  }, [model]);

  // Auto-fetch Ollama models on mount if provider is ollama and no models in localStorage
  useEffect(() => {
    if (provider === 'ollama') {
      const savedModels = localStorage.getItem('ollama_models');
      if (!savedModels || JSON.parse(savedModels).length === 0) {
        fetchOllamaModels();
      }
    }
  }, [provider, fetchOllamaModels]);

  // Update model when provider changes
  useEffect(() => {
    const models = getModelsForProvider(provider);
    if (models.length > 0 && !models.find((m) => m.id === model)) {
      setModel(models[0].id);
    }
  }, [provider, model]);

  const handleSave = useCallback(() => {
    // Validation
    const errors: string[] = [];
    
    if (!model || model === 'no-models') {
      errors.push('Please select a valid model');
    }
    
    if (selectedProvider?.requiresApiKey && !apiKey.trim()) {
      errors.push(`API Key is required for ${selectedProvider.name}`);
    }
    
    if (errors.length > 0) {
      setValidationErrors(errors);
      return;
    }
    
    setValidationErrors([]);
    
    // Use default system prompt if empty
    const finalSystemPrompt = systemPrompt.trim() || DEFAULT_SYSTEM_PROMPT;
    
    const config = {
      // Backend expects these field names (all required fields must be present)
      llm_provider: provider || "ollama",
      model: model || "llama3.1:8b",
      memory_type: memoryType || "short_term",
      system_prompt: finalSystemPrompt,
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
      timeout: parseInt(timeoutValue) || 60,
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
  }, [
    provider, model, memoryType, systemPrompt, userMessage, enableChatUI,
    chatUIPosition, enableMemory, memoryWindow, sessionId, temperature,
    maxTokens, topP, frequencyPenalty, presencePenalty, responseFormat,
    timeoutValue, extractJson, returnMetadata, apiKey, selectedProvider, onSave
  ]);

  // Test chat handler
  const handleTestChat = useCallback(async (message: string): Promise<string> => {
    // Mock implementation - in production, this would call the actual API
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(`Echo: ${message}\n\n(This is a test response. Configure the tool and save to enable real AI responses.)`);
      }, 1000);
    });
  }, []);

  // Apply preset configuration
  const applyPreset = useCallback((presetId: string) => {
    const preset = PRESETS.find(p => p.id === presetId);
    if (preset) {
      setTemperature(preset.temperature);
      setTopP(preset.topP);
      setActiveTab("generation");
    }
  }, []);

  // Reset to default values
  const resetToDefaults = useCallback(() => {
    setTemperature(0.7);
    setTopP(1.0);
    setFrequencyPenalty(0);
    setPresencePenalty(0);
    setMaxTokens(1000);
  }, []);

  // Copy configuration to clipboard
  const copyConfig = useCallback(async () => {
    const config = {
      provider,
      model,
      temperature,
      topP,
      maxTokens,
      systemPrompt: systemPrompt || DEFAULT_SYSTEM_PROMPT,
    };
    await navigator.clipboard.writeText(JSON.stringify(config, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [provider, model, temperature, topP, maxTokens, systemPrompt]);

  return (
    <TooltipProvider>
    <div className="flex gap-4 h-[calc(100vh-200px)]">
      {/* Configuration Panel */}
      <div className="flex-1 overflow-y-auto pr-2">
        {/* Header with Quick Actions */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium">AI Agent 설정</h3>
            {isDirty && (
              <Badge variant="outline" className="text-xs bg-amber-50 text-amber-700 border-amber-200">
                변경됨
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={copyConfig}>
                  {copied ? <Check className="h-3.5 w-3.5 text-green-500" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>설정 복사</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={resetToDefaults}>
                  <RotateCcw className="h-3.5 w-3.5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>기본값으로 초기화</TooltipContent>
            </Tooltip>
          </div>
        </div>

        {/* Quick Presets */}
        <div className="flex gap-2 mb-4 flex-wrap">
          {PRESETS.map((preset) => (
            <Tooltip key={preset.id}>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={() => applyPreset(preset.id)}
                >
                  {preset.name}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{preset.description}</TooltipContent>
            </Tooltip>
          ))}
        </div>

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <Alert variant="destructive" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <ul className="list-disc list-inside">
                {validationErrors.map((error, i) => (
                  <li key={i}>{error}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="core" className="relative">
              <Settings className="h-4 w-4 mr-2" />
              Core
              {tabStatus.core && <span className="absolute -top-1 -right-1 h-2 w-2 bg-green-500 rounded-full" />}
            </TabsTrigger>
            <TabsTrigger value="memory" className="relative">
              <Brain className="h-4 w-4 mr-2" />
              Memory
              {tabStatus.memory && enableMemory && <span className="absolute -top-1 -right-1 h-2 w-2 bg-green-500 rounded-full" />}
            </TabsTrigger>
            <TabsTrigger value="generation" className="relative">
              <Zap className="h-4 w-4 mr-2" />
              Generation
              {tabStatus.generation && <span className="absolute -top-1 -right-1 h-2 w-2 bg-green-500 rounded-full" />}
            </TabsTrigger>
            <TabsTrigger value="advanced">
              Advanced
            </TabsTrigger>
          </TabsList>

          {/* Core Settings */}
          <TabsContent value="core" className="space-y-4 mt-4">
            <div className="space-y-2">
              <div className="flex items-center">
                <Label>LLM Provider</Label>
                <InfoTooltip content="AI 모델을 제공하는 서비스를 선택합니다. Ollama는 로컬에서 실행되며, 다른 옵션은 API 키가 필요합니다." />
              </div>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {getAvailableProviders().map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      <div className="flex items-center gap-2">
                        <span>{p.icon}</span>
                        <span>{p.name}</span>
                        <Badge variant={p.type === 'local' ? 'secondary' : 'outline'} className="text-[10px] h-4">
                          {p.type === 'local' ? '로컬' : '클라우드'}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">{selectedProvider?.description}</p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Model {selectedProvider?.requiresApiKey && <span className="text-red-500">*</span>}</Label>
                {provider === 'ollama' && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={fetchOllamaModels}
                    disabled={loadingModels}
                    className="h-7 text-xs gap-1"
                  >
                    {loadingModels ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Loading...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-3 w-3" />
                        Refresh
                      </>
                    )}
                  </Button>
                )}
              </div>
              
              {loadingModels ? (
                <Skeleton className="h-10 w-full" />
              ) : (
                <Select value={model} onValueChange={setModel}>
                  <SelectTrigger className={!model || model === 'no-models' ? 'border-red-500' : ''}>
                    <SelectValue placeholder="Select a model" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableModels.length > 0 ? (
                      availableModels.map((m) => (
                        <SelectItem key={m.id} value={m.id}>
                          <div className="flex items-center gap-2">
                            <span>{m.name}</span>
                            {m.description && (
                              <span className="text-xs text-muted-foreground">- {m.description}</span>
                            )}
                          </div>
                        </SelectItem>
                      ))
                    ) : (
                      <SelectItem value="no-models">
                        No models available
                      </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              )}
              
              {/* Model Error/Warning Messages */}
              {modelError && (
                <Alert variant="destructive" className="py-2">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    {modelError}
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0 ml-2 text-xs"
                      onClick={fetchOllamaModels}
                    >
                      Retry
                    </Button>
                  </AlertDescription>
                </Alert>
              )}
              
              {provider === 'ollama' && !modelError && availableModels.length === 0 && !loadingModels && (
                <p className="text-xs text-amber-600">
                  ⚠️ No Ollama models found. Click Refresh or configure in LLM Settings.
                </p>
              )}
            </div>

            {selectedProvider?.requiresApiKey && (
              <div className="space-y-2">
                <Label>
                  API Key <span className="text-red-500">*</span>
                </Label>
                <Input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                  className={!apiKey.trim() ? 'border-amber-500' : ''}
                />
                <p className="text-xs text-muted-foreground">
                  Required for {selectedProvider.name}. Get your key from the provider's dashboard.
                </p>
              </div>
            )}

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Label>System Prompt</Label>
                  <InfoTooltip content="AI의 역할과 행동 방식을 정의합니다. 템플릿을 선택하거나 직접 작성하세요." />
                </div>
                {!systemPrompt && (
                  <Badge variant="outline" className="text-xs">Using default</Badge>
                )}
              </div>
              {/* Prompt Template Selector */}
              <Select onValueChange={(templateId) => {
                const template = PROMPT_TEMPLATES.find(t => t.id === templateId);
                if (template) setSystemPrompt(template.prompt);
              }}>
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="📝 템플릿 선택..." />
                </SelectTrigger>
                <SelectContent>
                  {PROMPT_TEMPLATES.map((template) => (
                    <SelectItem key={template.id} value={template.id} className="text-xs">
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder={DEFAULT_SYSTEM_PROMPT}
                rows={4}
                className="font-mono text-sm"
              />
              <div className="flex justify-between items-center">
                <p className="text-xs text-muted-foreground">
                  에이전트의 역할과 성격을 정의합니다
                </p>
                {systemPrompt && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 text-xs text-muted-foreground"
                    onClick={() => setSystemPrompt('')}
                  >
                    초기화
                  </Button>
                )}
              </div>
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
          <TabsContent value="generation" className="space-y-6 mt-4">
            {/* Quick preset reminder */}
            <div className="flex items-center gap-2 p-2 bg-muted/50 rounded-md">
              <Sparkles className="h-4 w-4 text-purple-500" />
              <span className="text-xs text-muted-foreground">
                상단의 프리셋 버튼으로 빠르게 설정할 수 있습니다
              </span>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Label>Temperature</Label>
                  <InfoTooltip content="높을수록 창의적이고 다양한 응답, 낮을수록 일관되고 예측 가능한 응답을 생성합니다. 권장: 0.7" />
                </div>
                <Badge variant="secondary" className="font-mono">{temperature.toFixed(1)}</Badge>
              </div>
              <Slider
                value={[temperature]}
                onValueChange={(v) => setTemperature(v[0])}
                min={0}
                max={2}
                step={0.1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>🎯 정확함 (0.0)</span>
                <span className="text-purple-500">권장 (0.7)</span>
                <span>🎨 창의적 (2.0)</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center">
                <Label>Max Tokens</Label>
                <InfoTooltip content="응답의 최대 길이를 토큰 단위로 제한합니다. 1토큰 ≈ 한글 0.5~1글자, 영어 0.75단어" />
              </div>
              <Input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value) || 1000)}
                min="1"
                max="128000"
              />
              <p className="text-xs text-muted-foreground">최대 응답 길이 (1-128,000) · 권장: 1,000~4,000</p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Label>Top P (Nucleus Sampling)</Label>
                  <InfoTooltip content="확률 분포에서 상위 P%의 토큰만 고려합니다. Temperature와 함께 사용하면 응답 다양성을 조절할 수 있습니다." />
                </div>
                <Badge variant="secondary" className="font-mono">{topP.toFixed(2)}</Badge>
              </div>
              <Slider
                value={[topP]}
                onValueChange={(v) => setTopP(v[0])}
                min={0}
                max={1}
                step={0.05}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">다양성 제어 · 권장: 0.9~1.0</p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Label>Frequency Penalty</Label>
                  <InfoTooltip content="이미 사용된 토큰의 반복을 줄입니다. 높을수록 같은 단어/표현의 반복이 줄어듭니다." />
                </div>
                <Badge variant="secondary" className="font-mono">{frequencyPenalty.toFixed(1)}</Badge>
              </div>
              <Slider
                value={[frequencyPenalty]}
                onValueChange={(v) => setFrequencyPenalty(v[0])}
                min={0}
                max={2}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">반복 감소 · 권장: 0.0~0.5</p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Label>Presence Penalty</Label>
                  <InfoTooltip content="새로운 주제로 전환하도록 유도합니다. 높을수록 다양한 주제를 다루게 됩니다." />
                </div>
                <Badge variant="secondary" className="font-mono">{presencePenalty.toFixed(1)}</Badge>
              </div>
              <Slider
                value={[presencePenalty]}
                onValueChange={(v) => setPresencePenalty(v[0])}
                min={0}
                max={2}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">주제 다양성 · 권장: 0.0~0.5</p>
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
              <Select value={timeoutValue} onValueChange={setTimeoutValue}>
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
        <div className="flex justify-between items-center mt-6 pt-4 border-t">
          <div className="text-xs text-muted-foreground">
            {isDirty && "저장하지 않은 변경사항이 있습니다"}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onCancel}>
              취소
            </Button>
            <Button onClick={handleSave} className="min-w-[120px]">
              {isDirty ? "💾 설정 저장" : "설정 저장"}
            </Button>
          </div>
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
    </TooltipProvider>
  );
}
