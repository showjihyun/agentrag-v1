/**
 * Agent Node Configuration Panel
 * Advanced settings for agent nodes
 */

import React, { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
// import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Plus, X, Sparkles } from 'lucide-react';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { RetryConfig } from '../RetryConfig';

interface AgentNodeConfigProps {
  data: any;
  onChange: (data: any) => void;
}

export function AgentNodeConfig({ data, onChange }: AgentNodeConfigProps) {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState(data.agentId || '');
  const [temperature, setTemperature] = useState(data.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(data.maxTokens || 1000);
  const [systemPrompt, setSystemPrompt] = useState(data.systemPrompt || '');
  const [variables, setVariables] = useState(data.variables || []);
  const [streamResponse, setStreamResponse] = useState(data.streamResponse || false);

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    try {
      const response = await agentBuilderAPI.getAgents();
      const agentsList = Array.isArray(response) ? response : response.agents || [];
      console.log('Loaded agents:', agentsList.length);
      setAgents(agentsList);
    } catch (error) {
      console.error('Failed to load agents:', error);
      // Set empty array on error to prevent crashes
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAgentChange = (agentId: string) => {
    setSelectedAgent(agentId);
    const agent = agents.find(a => a.id === agentId);
    onChange({ 
      ...data, 
      agentId,
      agentName: agent?.name,
      agentType: agent?.agent_type,
    });
  };

  const handleTemperatureChange = (value: number[]) => {
    setTemperature(value[0]);
    onChange({ ...data, temperature: value[0] });
  };

  const handleMaxTokensChange = (value: string) => {
    const tokens = parseInt(value) || 1000;
    setMaxTokens(tokens);
    onChange({ ...data, maxTokens: tokens });
  };

  const handleSystemPromptChange = (value: string) => {
    setSystemPrompt(value);
    onChange({ ...data, systemPrompt: value });
  };

  const handleStreamResponseChange = (checked: boolean) => {
    setStreamResponse(checked);
    onChange({ ...data, streamResponse: checked });
  };

  const addVariable = () => {
    const newVariables = [...variables, { key: '', value: '', type: 'string' }];
    setVariables(newVariables);
    onChange({ ...data, variables: newVariables });
  };

  const updateVariable = (index: number, field: string, value: string) => {
    const newVariables = [...variables];
    newVariables[index] = { ...newVariables[index], [field]: value };
    setVariables(newVariables);
    onChange({ ...data, variables: newVariables });
  };

  const removeVariable = (index: number) => {
    const newVariables = variables.filter((_: any, i: number) => i !== index);
    setVariables(newVariables);
    onChange({ ...data, variables: newVariables });
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            Agent Selection
          </CardTitle>
          <CardDescription>
            Choose which AI agent to use for this node
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="agent">Agent</Label>
            {loading ? (
              <div className="text-sm text-muted-foreground">Loading agents...</div>
            ) : (
              <Select value={selectedAgent} onValueChange={handleAgentChange}>
                <SelectTrigger id="agent">
                  <SelectValue placeholder="Select an agent" />
                </SelectTrigger>
                <SelectContent>
                  {agents.length === 0 ? (
                    <div className="p-2 text-sm text-muted-foreground">
                      No agents available
                    </div>
                  ) : (
                    agents.map((agent) => (
                      <SelectItem key={agent.id} value={agent.id}>
                        <div className="flex items-center gap-2">
                          <span>{agent.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {agent.agent_type}
                          </Badge>
                        </div>
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            )}
          </div>

          {selectedAgent && (
            <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
              {agents.find(a => a.id === selectedAgent)?.description || 'No description'}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">LLM Parameters</CardTitle>
          <CardDescription>
            Configure the language model behavior
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="temperature">Temperature</Label>
              <span className="text-sm text-muted-foreground">{temperature.toFixed(2)}</span>
            </div>
            <Input
              id="temperature"
              type="range"
              min={0}
              max={2}
              step={0.1}
              value={temperature}
              onChange={(e) => handleTemperatureChange([parseFloat(e.target.value)])}
              className="w-full"
            />
            <p className="text-xs text-muted-foreground">
              Lower = more focused, Higher = more creative
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="maxTokens">Max Tokens</Label>
            <Input
              id="maxTokens"
              type="number"
              value={maxTokens}
              onChange={(e) => handleMaxTokensChange(e.target.value)}
              min={100}
              max={4000}
            />
            <p className="text-xs text-muted-foreground">
              Maximum length of the response
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="stream">Stream Response</Label>
              <p className="text-xs text-muted-foreground">
                Enable real-time streaming
              </p>
            </div>
            <Switch
              id="stream"
              checked={streamResponse}
              onCheckedChange={handleStreamResponseChange}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">System Prompt</CardTitle>
          <CardDescription>
            Override the default system prompt
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            value={systemPrompt}
            onChange={(e) => handleSystemPromptChange(e.target.value)}
            placeholder="You are a helpful assistant that..."
            rows={4}
            className="text-sm"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Variables</CardTitle>
          <CardDescription>
            Map input data to agent variables
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {variables.map((variable: any, index: number) => (
            <div key={index} className="flex items-center gap-2 p-3 border rounded-lg">
              <div className="flex-1 grid grid-cols-3 gap-2">
                <Input
                  placeholder="Key"
                  value={variable.key}
                  onChange={(e) => updateVariable(index, 'key', e.target.value)}
                  className="h-8 text-sm"
                />
                <Input
                  placeholder="Value"
                  value={variable.value}
                  onChange={(e) => updateVariable(index, 'value', e.target.value)}
                  className="h-8 text-sm"
                />
                <Select
                  value={variable.type}
                  onValueChange={(value) => updateVariable(index, 'type', value)}
                >
                  <SelectTrigger className="h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="string">String</SelectItem>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="boolean">Boolean</SelectItem>
                    <SelectItem value="json">JSON</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => removeVariable(index)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}

          <Button
            variant="outline"
            size="sm"
            onClick={addVariable}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Variable
          </Button>
        </CardContent>
      </Card>

      {/* Retry Configuration */}
      <RetryConfig 
        data={data} 
        onChange={(field, value) => {
          const newData = { ...data, [field]: value };
          onChange(newData);
        }} 
      />
    </div>
  );
}
