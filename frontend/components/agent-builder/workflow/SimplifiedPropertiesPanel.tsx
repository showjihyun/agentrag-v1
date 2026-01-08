'use client';

/**
 * Simplified Properties Panel
 * 
 * Unified design system with:
 * - Tailwind CSS (no inline styles)
 * - Accessible form controls
 * - Consistent dark mode support
 * - Keyboard navigation
 */

import { useState, useEffect, Suspense, useCallback } from 'react';
import { Node } from 'reactflow';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Save, X, Trash, Bot, Zap, Brain, AlertTriangle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { LLM_PROVIDERS, getModelsForProvider, getAvailableProviders } from '@/lib/llm-models';
import { getToolConfig } from '@/components/workflow/tool-configs/ToolConfigRegistry';
import { cn } from '@/lib/utils';

interface SimplifiedPropertiesPanelProps {
  node: Node | null;
  isOpen?: boolean;
  onClose: () => void;
  onUpdate?: (nodeId: string, updates: Partial<Node['data']>) => void;
  onChange?: (updates: Partial<Node['data']>) => void;
}

// Loading fallback component
function ConfigLoadingFallback() {
  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      <span className="ml-2 text-sm text-muted-foreground">Loading configuration...</span>
    </div>
  );
}


export const SimplifiedPropertiesPanel = ({
  node,
  isOpen = true,
  onClose,
  onUpdate,
  onChange,
}: SimplifiedPropertiesPanelProps) => {
  const [localData, setLocalData] = useState<any>({});
  const [activeTab, setActiveTab] = useState('basic');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (node) {
      const nodeData = node.data || {};
      
      // Auto-load API key from localStorage if not set
      if (nodeData.parameters?.provider && !nodeData.parameters?.api_key) {
        try {
          const savedApiKeys = localStorage.getItem('llm_api_keys');
          if (savedApiKeys) {
            const apiKeys = JSON.parse(savedApiKeys);
            const provider = nodeData.parameters.provider;
            if (apiKeys[provider]) {
              nodeData.parameters = {
                ...nodeData.parameters,
                api_key: apiKeys[provider]
              };
            }
          }
        } catch (e) {
          console.error('Failed to parse saved API keys:', e);
        }
      }
      
      setLocalData(nodeData);
      setActiveTab('basic');
      setHasUnsavedChanges(false);
    }
  }, [node, isOpen]);

  const handleSave = useCallback(async () => {
    if (!node) return;
    
    setIsSaving(true);
    try {
      if (onUpdate) {
        onUpdate(node.id, localData);
      } else if (onChange) {
        onChange(localData);
      }
      setHasUnsavedChanges(false);
      onClose();
    } finally {
      setIsSaving(false);
    }
  }, [node, localData, onUpdate, onChange, onClose]);

  const updateField = useCallback((field: string, value: any) => {
    setLocalData((prev: any) => ({ ...prev, [field]: value }));
    setHasUnsavedChanges(true);
  }, []);

  const updateParameter = useCallback((paramName: string, value: any) => {
    setLocalData((prev: any) => {
      const configFieldMap: Record<string, string> = {
        'provider': 'llm_provider',
        'model': 'model',
        'system_prompt': 'system_prompt',
        'temperature': 'temperature',
        'max_tokens': 'max_tokens',
        'memory_type': 'memory_type',
        'enable_memory': 'enable_memory',
        'memory_window': 'memory_window',
        'user_message': 'user_message',
      };
      
      const configFieldName = configFieldMap[paramName] || paramName;
      
      const updated = {
        ...prev,
        parameters: {
          ...(prev.parameters || {}),
          [paramName]: value
        },
        config: {
          ...(prev.config || {}),
          [configFieldName]: value,
          ...(paramName === 'provider' ? { llm_provider: value } : {}),
        },
        [configFieldName]: value,
      };
      
      // Save API key to localStorage
      if (paramName === 'api_key' && value && prev.parameters?.provider) {
        try {
          const savedApiKeys = localStorage.getItem('llm_api_keys');
          const apiKeys = savedApiKeys ? JSON.parse(savedApiKeys) : {};
          apiKeys[prev.parameters.provider] = value;
          localStorage.setItem('llm_api_keys', JSON.stringify(apiKeys));
        } catch (e) {
          console.error('Failed to save API key:', e);
        }
      }
      
      return updated;
    });
    setHasUnsavedChanges(true);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;
      
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
      if (e.key === 'Escape') {
        onClose();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleSave, onClose]);

  // Check node types
  const isToolNode = node?.type === 'tool' || 
    (node?.type === 'block' && (
      localData.tool_id || 
      localData.tool_name || 
      localData.category === 'ai' ||
      localData.type === 'tool'
    ));

  const isAIAgentTool = isToolNode && (
    localData.type === 'tool_ai_agent' || 
    localData.tool_id === 'ai_agent' ||
    localData.id === 'ai_agent' ||
    localData.tool_name === 'AI Agent' ||
    localData.name === 'AI Agent' ||
    localData.label === 'AI Agent' ||
    localData.label?.includes('AI Agent') ||
    localData.name?.includes('AI Agent') ||
    (localData.category === 'ai' && (localData.name?.includes('Agent') || localData.label?.includes('Agent')))
  );

  if (!node || !isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9998] animate-in fade-in duration-200"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Configure ${localData.label || localData.name || node.type} node`}
        className={cn(
          "fixed right-0 top-0 bottom-0 z-[9999]",
          "w-[480px] max-w-[90vw]",
          "bg-background dark:bg-zinc-950",
          "border-l border-border dark:border-zinc-800",
          "shadow-2xl",
          "flex flex-col overflow-hidden",
          "animate-in slide-in-from-right duration-300"
        )}
      >
        {/* Header */}
        <div className="px-5 py-4 border-b border-border dark:border-zinc-800 bg-muted/30 dark:bg-zinc-900/50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge 
                variant="outline" 
                className="capitalize text-xs font-medium"
              >
                {node.type}
              </Badge>
              <h2 className="text-sm font-semibold text-foreground">
                Node Properties
              </h2>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onClose}
              className="h-8 w-8 p-0"
              aria-label="Close panel"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="flex-1">
          <div className="p-5">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className={cn(
                "grid w-full mb-5 h-10",
                isToolNode ? "grid-cols-2" : "grid-cols-3"
              )}>
                <TabsTrigger value="basic" className="text-xs font-medium">
                  Basic
                </TabsTrigger>
                <TabsTrigger value="config" className="text-xs font-medium">
                  Config
                </TabsTrigger>
                {!isToolNode && (
                  <TabsTrigger value="advanced" className="text-xs font-medium">
                    Advanced
                  </TabsTrigger>
                )}
              </TabsList>

              {/* Basic Tab */}
              <TabsContent value="basic" className="space-y-4 mt-0">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Essential Settings</CardTitle>
                    <CardDescription className="text-xs">
                      Configure the basic properties
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="node-name" className="text-xs font-medium">
                        Node Name <span className="text-destructive">*</span>
                      </Label>
                      <Input
                        id="node-name"
                        value={localData.label || localData.name || ''}
                        onChange={(e) => updateField('label', e.target.value)}
                        placeholder="Enter node name"
                        className="h-9"
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="node-description" className="text-xs font-medium">
                        Description
                      </Label>
                      <Textarea
                        id="node-description"
                        value={localData.description || ''}
                        onChange={(e) => updateField('description', e.target.value)}
                        placeholder="Describe what this node does"
                        rows={2}
                        className="resize-none text-sm"
                      />
                    </div>

                    <div className="flex items-center justify-between py-2">
                      <div>
                        <Label htmlFor="node-enabled" className="text-xs font-medium cursor-pointer">
                          Enabled
                        </Label>
                        <p className="text-xs text-muted-foreground">Skip if disabled</p>
                      </div>
                      <Switch
                        id="node-enabled"
                        checked={!localData.disabled}
                        onCheckedChange={(checked) => updateField('disabled', !checked)}
                      />
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              {/* Config Tab */}
              <TabsContent value="config" className="space-y-4 mt-0">
                {/* Tool-specific config */}
                {(() => {
                  const configKey = localData.tool_id || node?.type;
                  const ToolConfigComponent = configKey ? getToolConfig(configKey) : null;
                  
                  if (ToolConfigComponent && !isAIAgentTool) {
                    return (
                      <Suspense fallback={<ConfigLoadingFallback />}>
                        <ToolConfigComponent
                          data={localData.parameters || localData}
                          onChange={(updates: any) => {
                            setLocalData((prev: any) => ({
                              ...prev,
                              parameters: { ...prev.parameters, ...updates }
                            }));
                            setHasUnsavedChanges(true);
                          }}
                        />
                      </Suspense>
                    );
                  }
                  return null;
                })()}

                {/* AI Agent Config */}
                {(isAIAgentTool || !getToolConfig(localData.tool_id || node?.type)) && (
                  <>
                    {/* LLM Configuration */}
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Bot className="h-4 w-4" aria-hidden="true" />
                          LLM Configuration
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Select the AI model and provider
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="provider" className="text-xs font-medium">
                            LLM Provider <span className="text-destructive">*</span>
                          </Label>
                          <Select
                            value={localData.parameters?.provider || 'ollama'}
                            onValueChange={(value) => updateParameter('provider', value)}
                          >
                            <SelectTrigger id="provider" className="h-9">
                              <SelectValue placeholder="Select provider" />
                            </SelectTrigger>
                            <SelectContent>
                              {getAvailableProviders().map((provider) => (
                                <SelectItem key={provider.id} value={provider.id}>
                                  <span className="flex items-center gap-2">
                                    <span>{provider.icon}</span>
                                    <span>{provider.name}</span>
                                    <span className="text-xs text-muted-foreground">({provider.type})</span>
                                  </span>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="model" className="text-xs font-medium">
                            Model <span className="text-destructive">*</span>
                          </Label>
                          <Select
                            value={localData.parameters?.model || 'llama3.3:70b'}
                            onValueChange={(value) => updateParameter('model', value)}
                          >
                            <SelectTrigger id="model" className="h-9">
                              <SelectValue placeholder="Select model" />
                            </SelectTrigger>
                            <SelectContent>
                              {getModelsForProvider(localData.parameters?.provider || 'ollama').map((model) => (
                                <SelectItem key={model.id} value={model.id}>
                                  {model.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        {/* API Key info */}
                        {localData.parameters?.provider && localData.parameters.provider !== 'ollama' && (
                          <div className="p-3 rounded-lg bg-muted/50 border border-border">
                            <p className="text-xs text-muted-foreground flex items-center gap-2">
                              <span>🔑</span>
                              API Key is managed in User Settings or environment variables
                            </p>
                          </div>
                        )}

                        <div className="space-y-2">
                          <Label htmlFor="system-prompt" className="text-xs font-medium">
                            System Prompt
                          </Label>
                          <Textarea
                            id="system-prompt"
                            value={localData.parameters?.system_prompt || ''}
                            onChange={(e) => updateParameter('system_prompt', e.target.value)}
                            placeholder="You are a helpful AI assistant..."
                            rows={3}
                            className="resize-none text-sm"
                          />
                          <p className="text-xs text-muted-foreground">
                            Define the agent's behavior and personality
                          </p>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Memory Settings */}
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Brain className="h-4 w-4" aria-hidden="true" />
                          Memory Settings
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Configure conversation memory
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <Label htmlFor="enable-memory" className="text-xs font-medium cursor-pointer">
                              Enable Memory
                            </Label>
                            <p className="text-xs text-muted-foreground">Remember conversation history</p>
                          </div>
                          <Switch
                            id="enable-memory"
                            checked={localData.parameters?.enable_memory ?? true}
                            onCheckedChange={(checked) => updateParameter('enable_memory', checked)}
                          />
                        </div>

                        {(localData.parameters?.enable_memory ?? true) && (
                          <>
                            <div className="space-y-2">
                              <Label htmlFor="memory-type" className="text-xs font-medium">
                                Memory Type
                              </Label>
                              <Select
                                value={localData.parameters?.memory_type || 'long_term'}
                                onValueChange={(value) => updateParameter('memory_type', value)}
                              >
                                <SelectTrigger id="memory-type" className="h-9">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="short_term">Short Term</SelectItem>
                                  <SelectItem value="mid_term">Mid Term</SelectItem>
                                  <SelectItem value="long_term">Long Term</SelectItem>
                                  <SelectItem value="all">All</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="memory-window" className="text-xs font-medium">
                                Memory Window
                              </Label>
                              <Select
                                value={String(localData.parameters?.memory_window || '10')}
                                onValueChange={(value) => updateParameter('memory_window', value)}
                              >
                                <SelectTrigger id="memory-window" className="h-9">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {['5', '10', '20', '50', '100'].map((val) => (
                                    <SelectItem key={val} value={val}>
                                      {val} messages
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                            </div>
                          </>
                        )}
                      </CardContent>
                    </Card>

                    {/* Generation Parameters */}
                    <Card>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-sm flex items-center gap-2">
                          <Zap className="h-4 w-4" aria-hidden="true" />
                          Generation Parameters
                        </CardTitle>
                        <CardDescription className="text-xs">
                          Fine-tune AI response generation
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="temperature" className="text-xs font-medium">
                              Temperature
                            </Label>
                            <span className="text-xs text-muted-foreground font-mono">
                              {localData.parameters?.temperature || 0.7}
                            </span>
                          </div>
                          <Slider
                            id="temperature"
                            min={0}
                            max={2}
                            step={0.1}
                            value={[localData.parameters?.temperature || 0.7]}
                            onValueChange={([value]) => updateParameter('temperature', value)}
                            className="w-full"
                            aria-label="Temperature"
                          />
                          <p className="text-xs text-muted-foreground">
                            0 = deterministic, 2 = very creative
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="max-tokens" className="text-xs font-medium">
                            Max Tokens
                          </Label>
                          <Input
                            id="max-tokens"
                            type="number"
                            min={1}
                            max={4096}
                            value={localData.parameters?.max_tokens || 1000}
                            onChange={(e) => updateParameter('max_tokens', parseInt(e.target.value))}
                            className="h-9"
                          />
                          <p className="text-xs text-muted-foreground">
                            Maximum length of response (1-4096)
                          </p>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                )}
              </TabsContent>

              {/* Advanced Tab */}
              {!isToolNode && (
                <TabsContent value="advanced" className="space-y-4 mt-0">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm">Advanced Settings</CardTitle>
                      <CardDescription className="text-xs">
                        Raw node data (JSON)
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Textarea
                        value={JSON.stringify(localData, null, 2)}
                        onChange={(e) => {
                          try {
                            const parsed = JSON.parse(e.target.value);
                            setLocalData(parsed);
                            setHasUnsavedChanges(true);
                          } catch {
                            // Invalid JSON, ignore
                          }
                        }}
                        rows={15}
                        className="font-mono text-xs resize-none"
                        spellCheck={false}
                      />
                    </CardContent>
                  </Card>
                </TabsContent>
              )}
            </Tabs>
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-border dark:border-zinc-800 bg-muted/30 dark:bg-zinc-900/50 space-y-3">
          {hasUnsavedChanges && (
            <div className="flex items-center gap-2 text-xs text-amber-600 dark:text-amber-400" role="status">
              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
              <span>You have unsaved changes</span>
            </div>
          )}
          
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1"
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              className="flex-1 gap-2"
              disabled={isSaving || !hasUnsavedChanges}
            >
              {isSaving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Save
              <kbd className="ml-auto text-xs opacity-60 hidden sm:inline">⌘S</kbd>
            </Button>
          </div>
        </div>
      </div>
    </>
  );
};
