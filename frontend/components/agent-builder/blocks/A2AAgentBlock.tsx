'use client';

/**
 * A2A Agent Block Component
 * 
 * 워크플로우에서 외부 A2A 에이전트를 호출하는 블록
 */

import React, { useState, useEffect } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Globe, Settings, Zap, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface A2AAgent {
  id: string;
  name: string;
  description?: string;
  status: 'connected' | 'disconnected' | 'error';
  skills?: Array<{ id: string; name: string }>;
}

interface A2AAgentBlockData {
  label: string;
  agentConfigId?: string;
  inputType: 'text' | 'json';
  message: string;
  jsonData: string;
  streaming: boolean;
  blocking: boolean;
  timeout: number;
  // Runtime state
  agents?: A2AAgent[];
  selectedAgent?: A2AAgent;
}

const defaultData: A2AAgentBlockData = {
  label: 'A2A Agent',
  inputType: 'text',
  message: '{{input}}',
  jsonData: '{}',
  streaming: false,
  blocking: true,
  timeout: 60,
};

export default function A2AAgentBlock({ 
  data, 
  selected,
  id,
}: NodeProps<A2AAgentBlockData>) {
  const blockData = { ...defaultData, ...data };
  const [agents, setAgents] = useState<A2AAgent[]>(blockData.agents || []);
  const [loading, setLoading] = useState(false);
  
  // Fetch available A2A agents
  useEffect(() => {
    fetchAgents();
  }, []);
  
  const fetchAgents = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/agent-builder/a2a/agents?enabled_only=true');
      if (res.ok) {
        const data = await res.json();
        setAgents(data.agents.map((a: any) => ({
          id: a.config.id,
          name: a.config.name,
          description: a.config.description,
          status: a.status,
          skills: a.agentCard?.skills,
        })));
      }
    } catch (error) {
      console.error('Failed to fetch A2A agents:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const selectedAgent = agents.find(a => a.id === blockData.agentConfigId);
  
  return (
    <div 
      className={`
        bg-white rounded-lg shadow-md border-2 min-w-[280px]
        ${selected ? 'border-indigo-500' : 'border-gray-200'}
      `}
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 bg-indigo-500 rounded-t-lg">
        <Globe className="w-4 h-4 text-white" />
        <span className="text-white font-medium text-sm">{blockData.label}</span>
        {blockData.streaming && (
          <Badge variant="secondary" className="ml-auto text-xs">
            <Zap className="w-3 h-3 mr-1" />
            Stream
          </Badge>
        )}
      </div>
      
      {/* Content */}
      <div className="p-3 space-y-3">
        {/* Agent Selection */}
        <div className="space-y-1">
          <Label className="text-xs text-gray-500">A2A 에이전트</Label>
          <Select 
            value={blockData.agentConfigId || ''} 
          >
            <SelectTrigger className="h-8 text-sm" disabled={loading}>
              <SelectValue placeholder={loading ? '로딩 중...' : '에이전트 선택'} />
            </SelectTrigger>
            <SelectContent>
              {agents.map(agent => (
                <SelectItem key={agent.id} value={agent.id}>
                  <div className="flex items-center gap-2">
                    <span 
                      className={`w-2 h-2 rounded-full ${
                        agent.status === 'connected' ? 'bg-green-500' :
                        agent.status === 'error' ? 'bg-red-500' : 'bg-gray-400'
                      }`} 
                    />
                    {agent.name}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        {/* Selected Agent Info */}
        {selectedAgent && (
          <div className="text-xs text-gray-500 bg-gray-50 p-2 rounded">
            {selectedAgent.description && (
              <p className="mb-1">{selectedAgent.description}</p>
            )}
            {selectedAgent.skills && selectedAgent.skills.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedAgent.skills.slice(0, 3).map(skill => (
                  <Badge key={skill.id} variant="outline" className="text-xs">
                    {skill.name}
                  </Badge>
                ))}
                {selectedAgent.skills.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{selectedAgent.skills.length - 3}
                  </Badge>
                )}
              </div>
            )}
          </div>
        )}
        
        {/* No agents warning */}
        {!loading && agents.length === 0 && (
          <div className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 p-2 rounded">
            <AlertCircle className="w-4 h-4" />
            <span>연결된 A2A 에이전트가 없습니다</span>
          </div>
        )}
        
        {/* Input Type */}
        <div className="space-y-1">
          <Label className="text-xs text-gray-500">입력 타입</Label>
          <Select value={blockData.inputType}>
            <SelectTrigger className="h-8 text-sm">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="text">텍스트</SelectItem>
              <SelectItem value="json">JSON</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        {/* Message Input */}
        {blockData.inputType === 'text' ? (
          <div className="space-y-1">
            <Label className="text-xs text-gray-500">메시지</Label>
            <Textarea 
              value={blockData.message}
              placeholder="메시지 입력 (변수: {{input}})"
              className="text-sm min-h-[60px] resize-none"
              readOnly
            />
          </div>
        ) : (
          <div className="space-y-1">
            <Label className="text-xs text-gray-500">JSON 데이터</Label>
            <Textarea 
              value={blockData.jsonData}
              placeholder='{"key": "value"}'
              className="text-sm min-h-[60px] resize-none font-mono text-xs"
              readOnly
            />
          </div>
        )}
        
        {/* Options */}
        <div className="flex items-center justify-between pt-2 border-t">
          <div className="flex items-center gap-2">
            <Switch 
              id={`streaming-${id}`}
              checked={blockData.streaming}
              className="scale-75"
            />
            <Label htmlFor={`streaming-${id}`} className="text-xs">스트리밍</Label>
          </div>
          <div className="flex items-center gap-2">
            <Switch 
              id={`blocking-${id}`}
              checked={blockData.blocking}
              className="scale-75"
            />
            <Label htmlFor={`blocking-${id}`} className="text-xs">완료 대기</Label>
          </div>
        </div>
      </div>
      
      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-indigo-500 border-2 border-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-indigo-500 border-2 border-white"
      />
    </div>
  );
}

// Block configuration for registry
export const A2AAgentBlockConfig = {
  type: 'a2a_agent',
  name: 'A2A Agent',
  description: '외부 A2A 에이전트를 호출합니다',
  category: 'tools',
  icon: Globe,
  color: '#6366F1',
  component: A2AAgentBlock,
  defaultData,
};
