'use client';

import { useState, useEffect, useRef } from 'react';
import { Node } from 'reactflow';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Save, X, Trash, Bot, Zap, Brain } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { LLM_PROVIDERS, getModelsForProvider } from '@/lib/llm-models';

interface SimplifiedPropertiesPanelProps {
  node: Node | null;
  isOpen?: boolean;
  onClose: () => void;
  onUpdate?: (nodeId: string, updates: Partial<Node['data']>) => void;
  onChange?: (updates: Partial<Node['data']>) => void;
}

// Dark theme styles
const darkStyles = {
  input: {
    backgroundColor: '#1a1a1a',
    borderColor: '#3a3a3a',
    color: '#e0e0e0',
  },
  select: {
    backgroundColor: '#1a1a1a',
    borderColor: '#3a3a3a',
    color: '#e0e0e0',
  },
  card: {
    backgroundColor: '#0f0f0f',
    borderColor: '#2a2a2a',
  },
  label: {
    color: '#b0b0b0',
    fontSize: '13px',
    fontWeight: 500,
  },
  helpText: {
    color: '#707070',
    fontSize: '11px',
  },
};

export const SimplifiedPropertiesPanel = ({
  node,
  isOpen = true,
  onClose,
  onUpdate,
  onChange,
}: SimplifiedPropertiesPanelProps) => {
  const [localData, setLocalData] = useState<any>({});
  const [activeTab, setActiveTab] = useState('basic');

  useEffect(() => {
    console.log('📋 SimplifiedPropertiesPanel mounted/updated:', {
      hasNode: !!node,
      nodeId: node?.id,
      nodeType: node?.type,
      isOpen,
      nodeData: node?.data
    });
    
    if (node) {
      setLocalData(node.data || {});
      setActiveTab('basic');
    }
  }, [node, isOpen]);

  const handleSave = () => {
    if (node) {
      if (onUpdate) {
        onUpdate(node.id, localData);
      } else if (onChange) {
        onChange(localData);
      }
      onClose();
    }
  };

  const updateField = (field: string, value: any) => {
    setLocalData((prev: any) => ({ ...prev, [field]: value }));
  };

  const updateParameter = (paramName: string, value: any) => {
    setLocalData((prev: any) => ({
      ...prev,
      parameters: {
        ...(prev.parameters || {}),
        [paramName]: value
      }
    }));
  };

  // Check if this is an AI Agent tool
  const isAIAgentTool = localData.type === 'tool_ai_agent' || 
                        localData.tool_id === 'ai_agent' ||
                        localData.tool_name === 'AI Agent';

  if (!node) {
    console.log('⚠️ SimplifiedPropertiesPanel: No node provided');
    return null;
  }

  console.log('✅ SimplifiedPropertiesPanel rendering:', {
    nodeId: node.id,
    nodeType: node.type,
    isOpen,
    hasData: !!node.data,
    localData
  });

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(2px)',
          zIndex: 9998,
        }}
        onClick={onClose}
      />

      {/* Panel */}
      <div
        style={{
          position: 'fixed',
          right: 0,
          top: 0,
          bottom: 0,
          width: '380px',
          maxWidth: '90vw',
          backgroundColor: '#0a0a0a',
          borderLeft: '1px solid #2a2a2a',
          boxShadow: '-8px 0 32px rgba(0, 0, 0, 0.5)',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{ 
          padding: '14px 18px', 
          borderBottom: '1px solid #2a2a2a',
          background: 'linear-gradient(to bottom, #1a1a1a, #0f0f0f)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Badge 
                variant="outline" 
                className="capitalize text-xs"
                style={{
                  backgroundColor: '#1a1a1a',
                  borderColor: '#3a3a3a',
                  color: '#808080',
                  padding: '2px 8px'
                }}
              >
                {node.type}
              </Badge>
              <h2 style={{ 
                fontSize: '14px', 
                fontWeight: 600,
                color: '#e0e0e0',
                letterSpacing: '-0.01em'
              }}>
                Node Properties
              </h2>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onClose}
              style={{
                color: '#808080',
                padding: '4px',
                height: 'auto'
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div style={{ 
          flex: 1, 
          overflow: 'auto', 
          padding: '14px',
          backgroundColor: '#0a0a0a'
        }}>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList 
              className="grid w-full mb-4"
              style={{
                backgroundColor: '#000000',
                border: '1px solid #2a2a2a',
                padding: '2px',
                height: '36px',
                gridTemplateColumns: isAIAgentTool ? 'repeat(2, 1fr)' : 'repeat(3, 1fr)'
              }}
            >
              <TabsTrigger 
                value="basic"
                style={{
                  color: activeTab === 'basic' ? '#ffffff' : '#606060',
                  backgroundColor: activeTab === 'basic' ? '#1a1a1a' : 'transparent',
                  fontSize: '12px',
                  fontWeight: 500,
                  transition: 'all 0.2s'
                }}
              >
                Basic
              </TabsTrigger>
              <TabsTrigger 
                value="config"
                style={{
                  color: activeTab === 'config' ? '#ffffff' : '#606060',
                  backgroundColor: activeTab === 'config' ? '#1a1a1a' : 'transparent',
                  fontSize: '12px',
                  fontWeight: 500,
                  transition: 'all 0.2s'
                }}
              >
                Config
              </TabsTrigger>
              {!isAIAgentTool && (
                <TabsTrigger 
                  value="advanced"
                  style={{
                    color: activeTab === 'advanced' ? '#ffffff' : '#606060',
                    backgroundColor: activeTab === 'advanced' ? '#1a1a1a' : 'transparent',
                    fontSize: '12px',
                    fontWeight: 500,
                    transition: 'all 0.2s'
                  }}
                >
                  Advanced
                </TabsTrigger>
              )}
            </TabsList>



            {/* Basic Tab */}
            {activeTab === 'basic' && (
              <div className="space-y-3">
                <Card style={darkStyles.card}>
                  <CardHeader style={{ padding: '12px 14px' }}>
                    <CardTitle style={{ fontSize: '13px', color: '#e0e0e0', fontWeight: 600 }}>
                      Essential Settings
                    </CardTitle>
                    <CardDescription style={{ fontSize: '11px', color: '#707070', marginTop: '2px' }}>
                      Configure the basic properties
                    </CardDescription>
                  </CardHeader>
                  <CardContent style={{ padding: '0 14px 14px' }} className="space-y-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="node-name" style={darkStyles.label}>Node Name *</Label>
                      <Input
                        id="node-name"
                        value={localData.label || localData.name || ''}
                        onChange={(e) => updateField('label', e.target.value)}
                        placeholder="Enter node name"
                        style={{
                          ...darkStyles.input,
                          height: '36px',
                          fontSize: '13px'
                        }}
                      />
                    </div>

                    <div className="space-y-1.5">
                      <Label htmlFor="node-description" style={darkStyles.label}>Description</Label>
                      <Textarea
                        id="node-description"
                        value={localData.description || ''}
                        onChange={(e) => updateField('description', e.target.value)}
                        placeholder="Describe what this node does"
                        rows={2}
                        style={{
                          ...darkStyles.input,
                          fontSize: '12px',
                          resize: 'none'
                        }}
                      />
                    </div>

                    <div className="flex items-center justify-between pt-1">
                      <div>
                        <Label htmlFor="node-enabled" style={darkStyles.label}>Enabled</Label>
                        <p style={darkStyles.helpText}>Skip if disabled</p>
                      </div>
                      <Switch
                        id="node-enabled"
                        checked={!localData.disabled}
                        onCheckedChange={(checked) => updateField('disabled', !checked)}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Config Tab */}
            {activeTab === 'config' && (
              <div className="space-y-3">
                {isAIAgentTool ? (
                  <>
                    {/* LLM Configuration */}
                    <Card style={darkStyles.card}>
                      <CardHeader style={{ padding: '12px 14px' }}>
                        <CardTitle style={{ fontSize: '13px', color: '#e0e0e0', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Bot className="h-3.5 w-3.5" />
                          LLM Configuration
                        </CardTitle>
                        <CardDescription style={{ fontSize: '11px', color: '#707070', marginTop: '2px' }}>
                          Select the AI model and provider
                        </CardDescription>
                      </CardHeader>
                      <CardContent style={{ padding: '0 14px 14px' }} className="space-y-3">
                        <div className="space-y-1.5">
                          <Label htmlFor="provider" style={darkStyles.label}>LLM Provider *</Label>
                          <Select
                            value={localData.parameters?.provider || 'ollama'}
                            onValueChange={(value) => updateParameter('provider', value)}
                          >
                            <SelectTrigger 
                              id="provider"
                              style={{
                                ...darkStyles.select,
                                height: '36px',
                                fontSize: '13px'
                              }}
                            >
                              <SelectValue placeholder="Select provider" />
                            </SelectTrigger>
                            <SelectContent style={{ backgroundColor: '#1a1a1a', borderColor: '#3a3a3a' }}>
                              {LLM_PROVIDERS.map((provider) => (
                                <SelectItem 
                                  key={provider.id} 
                                  value={provider.id}
                                  style={{ color: '#e0e0e0', fontSize: '13px' }}
                                >
                                  {provider.icon} {provider.name} ({provider.type})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-1.5">
                          <Label htmlFor="model" style={darkStyles.label}>Model *</Label>
                          <Select
                            value={localData.parameters?.model || 'llama3.3:70b'}
                            onValueChange={(value) => updateParameter('model', value)}
                          >
                            <SelectTrigger 
                              id="model"
                              style={{
                                ...darkStyles.select,
                                height: '36px',
                                fontSize: '13px'
                              }}
                            >
                              <SelectValue placeholder="Select model" />
                            </SelectTrigger>
                            <SelectContent style={{ backgroundColor: '#1a1a1a', borderColor: '#3a3a3a' }}>
                              {getModelsForProvider(localData.parameters?.provider || 'ollama').map((model) => (
                                <SelectItem 
                                  key={model.id} 
                                  value={model.id}
                                  style={{ color: '#e0e0e0', fontSize: '13px' }}
                                >
                                  {model.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-1.5">
                          <Label htmlFor="system-prompt" style={darkStyles.label}>System Prompt</Label>
                          <Textarea
                            id="system-prompt"
                            value={localData.parameters?.system_prompt || ''}
                            onChange={(e) => updateParameter('system_prompt', e.target.value)}
                            placeholder="You are a helpful AI assistant..."
                            rows={3}
                            style={{
                              ...darkStyles.input,
                              fontSize: '12px',
                              resize: 'none'
                            }}
                          />
                          <p style={darkStyles.helpText}>Define the agent's behavior and personality</p>
                        </div>
                      </CardContent>
                    </Card>

                    {/* Memory Settings */}
                    <Card style={darkStyles.card}>
                      <CardHeader style={{ padding: '12px 14px' }}>
                        <CardTitle style={{ fontSize: '13px', color: '#e0e0e0', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Brain className="h-3.5 w-3.5" />
                          Memory Settings
                        </CardTitle>
                        <CardDescription style={{ fontSize: '11px', color: '#707070', marginTop: '2px' }}>
                          Configure conversation memory
                        </CardDescription>
                      </CardHeader>
                      <CardContent style={{ padding: '0 14px 14px' }} className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <Label htmlFor="enable-memory" style={darkStyles.label}>Enable Memory</Label>
                            <p style={darkStyles.helpText}>Remember conversation history</p>
                          </div>
                          <Switch
                            id="enable-memory"
                            checked={localData.parameters?.enable_memory ?? true}
                            onCheckedChange={(checked) => updateParameter('enable_memory', checked)}
                          />
                        </div>

                        {(localData.parameters?.enable_memory ?? true) && (
                          <>
                            <div className="space-y-1.5">
                              <Label htmlFor="memory-type" style={darkStyles.label}>Memory Type</Label>
                              <Select
                                value={localData.parameters?.memory_type || 'long_term'}
                                onValueChange={(value) => updateParameter('memory_type', value)}
                              >
                                <SelectTrigger 
                                  id="memory-type"
                                  style={{
                                    ...darkStyles.select,
                                    height: '36px',
                                    fontSize: '13px'
                                  }}
                                >
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent style={{ backgroundColor: '#1a1a1a', borderColor: '#3a3a3a' }}>
                                  <SelectItem value="short_term" style={{ color: '#e0e0e0', fontSize: '13px' }}>Short Term</SelectItem>
                                  <SelectItem value="mid_term" style={{ color: '#e0e0e0', fontSize: '13px' }}>Mid Term</SelectItem>
                                  <SelectItem value="long_term" style={{ color: '#e0e0e0', fontSize: '13px' }}>Long Term</SelectItem>
                                  <SelectItem value="all" style={{ color: '#e0e0e0', fontSize: '13px' }}>All</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>

                            <div className="space-y-1.5">
                              <Label htmlFor="memory-window" style={darkStyles.label}>Memory Window</Label>
                              <Select
                                value={String(localData.parameters?.memory_window || '10')}
                                onValueChange={(value) => updateParameter('memory_window', value)}
                              >
                                <SelectTrigger 
                                  id="memory-window"
                                  style={{
                                    ...darkStyles.select,
                                    height: '36px',
                                    fontSize: '13px'
                                  }}
                                >
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent style={{ backgroundColor: '#1a1a1a', borderColor: '#3a3a3a' }}>
                                  {['5', '10', '20', '50', '100'].map((val) => (
                                    <SelectItem key={val} value={val} style={{ color: '#e0e0e0', fontSize: '13px' }}>
                                      {val}
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
                    <Card style={darkStyles.card}>
                      <CardHeader style={{ padding: '12px 14px' }}>
                        <CardTitle style={{ fontSize: '13px', color: '#e0e0e0', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Zap className="h-3.5 w-3.5" />
                          Generation Parameters
                        </CardTitle>
                        <CardDescription style={{ fontSize: '11px', color: '#707070', marginTop: '2px' }}>
                          Fine-tune AI response generation
                        </CardDescription>
                      </CardHeader>
                      <CardContent style={{ padding: '0 14px 14px' }} className="space-y-3">
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between">
                            <Label htmlFor="temperature" style={darkStyles.label}>Temperature</Label>
                            <span style={{ fontSize: '12px', color: '#909090' }}>
                              {localData.parameters?.temperature || 0.7}
                            </span>
                          </div>
                          <input
                            id="temperature"
                            type="range"
                            min="0"
                            max="2"
                            step="0.1"
                            value={localData.parameters?.temperature || 0.7}
                            onChange={(e) => updateParameter('temperature', parseFloat(e.target.value))}
                            style={{
                              width: '100%',
                              height: '4px',
                              borderRadius: '2px',
                              background: '#2a2a2a',
                              outline: 'none',
                              accentColor: '#3b82f6'
                            }}
                          />
                          <p style={darkStyles.helpText}>0 = deterministic, 2 = very creative</p>
                        </div>

                        <div className="space-y-1.5">
                          <Label htmlFor="max-tokens" style={darkStyles.label}>Max Tokens</Label>
                          <Input
                            id="max-tokens"
                            type="number"
                            min="1"
                            max="4096"
                            value={localData.parameters?.max_tokens || 1000}
                            onChange={(e) => updateParameter('max_tokens', parseInt(e.target.value))}
                            style={{
                              ...darkStyles.input,
                              height: '36px',
                              fontSize: '13px'
                            }}
                          />
                          <p style={darkStyles.helpText}>Maximum length of response</p>
                        </div>
                      </CardContent>
                    </Card>
                  </>
                ) : (
                  <Card style={darkStyles.card}>
                    <CardHeader style={{ padding: '12px 14px' }}>
                      <CardTitle style={{ fontSize: '13px', color: '#e0e0e0' }}>Configuration</CardTitle>
                    </CardHeader>
                    <CardContent style={{ padding: '0 14px 14px' }}>
                      <div style={{ fontSize: '12px', color: '#909090', fontFamily: 'monospace', padding: '8px', backgroundColor: '#1a1a1a', borderRadius: '4px' }}>
                        {node.type}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}



            {/* Advanced Tab (non-AI Agent tools) */}
            {activeTab === 'advanced' && !isAIAgentTool && (
              <div className="space-y-3">
                <Card style={darkStyles.card}>
                  <CardHeader style={{ padding: '12px 14px' }}>
                    <CardTitle style={{ fontSize: '13px', color: '#e0e0e0' }}>Advanced Settings</CardTitle>
                    <CardDescription style={{ fontSize: '11px', color: '#707070', marginTop: '2px' }}>
                      Raw node data (JSON)
                    </CardDescription>
                  </CardHeader>
                  <CardContent style={{ padding: '0 14px 14px' }}>
                    <Textarea
                      value={JSON.stringify(localData, null, 2)}
                      onChange={(e) => {
                        try {
                          const parsed = JSON.parse(e.target.value);
                          setLocalData(parsed);
                        } catch {
                          // Invalid JSON
                        }
                      }}
                      rows={12}
                      style={{
                        ...darkStyles.input,
                        fontSize: '11px',
                        fontFamily: 'monospace',
                        resize: 'none'
                      }}
                    />
                  </CardContent>
                </Card>
              </div>
            )}
          </Tabs>
        </div>

        {/* Footer */}
        <div style={{ 
          padding: '12px 18px', 
          borderTop: '1px solid #2a2a2a', 
          display: 'flex', 
          gap: '8px', 
          justifyContent: 'space-between',
          backgroundColor: '#0f0f0f'
        }}>
          <Button
            onClick={() => {
              if (window.confirm(`Delete "${localData.label || localData.name || 'this node'}"?`)) {
                if (node && onUpdate) {
                  onUpdate(node.id, { _delete: true } as any);
                }
                onClose();
              }
            }}
            style={{
              backgroundColor: '#dc2626',
              color: 'white',
              border: 'none',
              height: '34px',
              fontSize: '12px',
              padding: '0 14px'
            }}
          >
            <Trash className="mr-1.5 h-3.5 w-3.5" />
            Delete
          </Button>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button 
              onClick={onClose}
              style={{
                backgroundColor: 'transparent',
                borderColor: '#3a3a3a',
                color: '#909090',
                height: '34px',
                fontSize: '12px',
                padding: '0 14px'
              }}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleSave}
              style={{
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                height: '34px',
                fontSize: '12px',
                padding: '0 14px'
              }}
            >
              <Save className="mr-1.5 h-3.5 w-3.5" />
              Save
            </Button>
          </div>
        </div>
      </div>


    </>
  );
};
