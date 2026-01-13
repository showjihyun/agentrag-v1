/**
 * Agent Execution Block Component
 * 
 * 워크플로우에서 단일 Agent를 실행하는 블록 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { Handle, Position } from 'reactflow';
import { Bot, Settings, Play, AlertCircle, CheckCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface AgentExecutionBlockProps {
  id: string;
  data: {
    agent_type?: string;
    input_data?: string;
    config?: any;
    result?: any;
    status?: 'idle' | 'running' | 'success' | 'error';
    error?: string;
  };
  selected?: boolean;
  onDataChange?: (id: string, data: any) => void;
  onExecute?: (id: string) => void;
}

interface AgentInfo {
  agent_type: string;
  agent_id: string;
  capabilities: Array<{
    name: string;
    description: string;
    input_schema: any;
    output_schema: any;
  }>;
  health_status: {
    status: string;
    initialized: boolean;
  };
}

const AgentExecutionBlock: React.FC<AgentExecutionBlockProps> = ({
  id,
  data,
  selected,
  onDataChange,
  onExecute
}) => {
  const [availableAgents, setAvailableAgents] = useState<AgentInfo[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentInfo | null>(null);
  const [inputData, setInputData] = useState(data.input_data || '{}');
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Agent 목록 로드
  useEffect(() => {
    loadAvailableAgents();
  }, []);

  // 선택된 Agent 정보 업데이트
  useEffect(() => {
    if (data.agent_type && availableAgents.length > 0) {
      const agent = availableAgents.find(a => a.agent_type === data.agent_type);
      setSelectedAgent(agent || null);
    }
  }, [data.agent_type, availableAgents]);

  const loadAvailableAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/agent-plugins/agents');
      if (response.ok) {
        const agents = await response.json();
        setAvailableAgents(agents);
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAgentTypeChange = (agentType: string) => {
    const agent = availableAgents.find(a => a.agent_type === agentType);
    setSelectedAgent(agent || null);
    
    onDataChange?.(id, {
      ...data,
      agent_type: agentType,
      config: { ...data.config, agent_type: agentType }
    });
  };

  const handleInputDataChange = (value: string) => {
    setInputData(value);
    
    try {
      const parsedData = JSON.parse(value);
      onDataChange?.(id, {
        ...data,
        input_data: value,
        config: { ...data.config, input_data: parsedData }
      });
    } catch (error) {
      // Invalid JSON - don't update config
    }
  };

  const handleExecute = () => {
    if (onExecute && data.agent_type && data.input_data) {
      onExecute(id);
    }
  };

  const getStatusIcon = () => {
    switch (data.status) {
      case 'running':
        return <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Bot className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (data.status) {
      case 'running':
        return 'border-blue-500 bg-blue-50';
      case 'success':
        return 'border-green-500 bg-green-50';
      case 'error':
        return 'border-red-500 bg-red-50';
      default:
        return selected ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-white';
    }
  };

  const isValidJson = (str: string) => {
    try {
      JSON.parse(str);
      return true;
    } catch {
      return false;
    }
  };

  return (
    <TooltipProvider>
      <div className="relative">
        {/* Input Handle */}
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-gray-400 border-2 border-white"
        />

        <Card className={`w-80 transition-all duration-200 ${getStatusColor()}`}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getStatusIcon()}
                <CardTitle className="text-sm font-medium">Agent 실행</CardTitle>
              </div>
              <div className="flex items-center gap-1">
                {selectedAgent?.health_status.status === 'healthy' && (
                  <Badge variant="outline" className="text-xs bg-green-100 text-green-700">
                    활성
                  </Badge>
                )}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setIsConfigOpen(!isConfigOpen)}
                    >
                      <Settings className="w-3 h-3" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>설정</TooltipContent>
                </Tooltip>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-3">
            {/* Agent 선택 */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-700">Agent 타입</label>
              <Select
                value={data.agent_type || ''}
                onValueChange={handleAgentTypeChange}
                disabled={loading || data.status === 'running'}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Agent를 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  {availableAgents.map((agent) => (
                    <SelectItem key={agent.agent_type} value={agent.agent_type}>
                      <div className="flex items-center gap-2">
                        <span>{agent.agent_id}</span>
                        {agent.health_status.status === 'healthy' ? (
                          <CheckCircle className="w-3 h-3 text-green-500" />
                        ) : (
                          <AlertCircle className="w-3 h-3 text-red-500" />
                        )}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* 입력 데이터 */}
            {isConfigOpen && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">입력 데이터 (JSON)</label>
                <Textarea
                  value={inputData}
                  onChange={(e) => handleInputDataChange(e.target.value)}
                  placeholder='{"query": "검색할 내용"}'
                  className={`h-20 text-xs font-mono ${
                    !isValidJson(inputData) ? 'border-red-300 bg-red-50' : ''
                  }`}
                  disabled={data.status === 'running'}
                />
                {!isValidJson(inputData) && (
                  <p className="text-xs text-red-500">유효한 JSON 형식이 아닙니다</p>
                )}
              </div>
            )}

            {/* Agent 능력 정보 */}
            {selectedAgent && isConfigOpen && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">Agent 능력</label>
                <div className="space-y-1">
                  {selectedAgent.capabilities.slice(0, 2).map((capability, index) => (
                    <Tooltip key={index}>
                      <TooltipTrigger asChild>
                        <Badge variant="secondary" className="text-xs cursor-help">
                          {capability.name}
                        </Badge>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs">{capability.description}</p>
                      </TooltipContent>
                    </Tooltip>
                  ))}
                  {selectedAgent.capabilities.length > 2 && (
                    <Badge variant="outline" className="text-xs">
                      +{selectedAgent.capabilities.length - 2} more
                    </Badge>
                  )}
                </div>
              </div>
            )}

            {/* 실행 결과 */}
            {data.result && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">실행 결과</label>
                <div className="p-2 bg-gray-50 rounded text-xs font-mono max-h-20 overflow-y-auto">
                  {data.status === 'success' ? (
                    <span className="text-green-700">
                      {typeof data.result === 'string' 
                        ? data.result 
                        : JSON.stringify(data.result, null, 2)
                      }
                    </span>
                  ) : (
                    <span className="text-red-700">{data.error || '실행 실패'}</span>
                  )}
                </div>
              </div>
            )}

            {/* 실행 버튼 */}
            <div className="flex justify-end pt-2">
              <Button
                size="sm"
                onClick={handleExecute}
                disabled={
                  !data.agent_type || 
                  !data.input_data || 
                  !isValidJson(inputData) ||
                  data.status === 'running'
                }
                className="h-7 text-xs"
              >
                <Play className="w-3 h-3 mr-1" />
                실행
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Output Handle */}
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-gray-400 border-2 border-white"
        />
      </div>
    </TooltipProvider>
  );
};

export default AgentExecutionBlock;