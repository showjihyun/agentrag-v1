/**
 * Custom Agent Execution Block Component
 * 
 * 워크플로우에서 사용자가 생성한 Custom Agent를 실행하는 블록 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { Handle, Position } from 'reactflow';
import { UserCheck, Settings, Play, AlertCircle, CheckCircle, Sparkles } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface CustomAgentExecutionBlockProps {
  id: string;
  data: {
    agent_id?: string;
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

interface CustomAgent {
  agent_id: string;
  agent_name: string;
  agent_type: string;
  description: string;
  capabilities: string[];
  health_status: {
    status: string;
    agent_name: string;
    llm_provider: string;
    llm_model: string;
  };
  is_registered: boolean;
}

const CustomAgentExecutionBlock: React.FC<CustomAgentExecutionBlockProps> = ({
  id,
  data,
  selected,
  onDataChange,
  onExecute
}) => {
  const [availableAgents, setAvailableAgents] = useState<CustomAgent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<CustomAgent | null>(null);
  const [inputData, setInputData] = useState(data.input_data || '{"input": ""}');
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Custom Agent 목록 로드
  useEffect(() => {
    loadCustomAgents();
  }, []);

  // 선택된 Agent 정보 업데이트
  useEffect(() => {
    if (data.agent_id && availableAgents.length > 0) {
      const agent = availableAgents.find(a => a.agent_id === data.agent_id);
      setSelectedAgent(agent || null);
    }
  }, [data.agent_id, availableAgents]);

  const loadCustomAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/agent-plugins/custom-agents');
      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setAvailableAgents(result.agents);
        }
      }
    } catch (error) {
      console.error('Failed to load custom agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAgentChange = (agentId: string) => {
    const agent = availableAgents.find(a => a.agent_id === agentId);
    setSelectedAgent(agent || null);
    
    onDataChange?.(id, {
      ...data,
      agent_id: agentId,
      config: { ...data.config, agent_id: agentId }
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
    if (onExecute && data.agent_id && data.input_data) {
      onExecute(id);
    }
  };

  const getStatusIcon = () => {
    switch (data.status) {
      case 'running':
        return <div className="animate-spin w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <UserCheck className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = () => {
    switch (data.status) {
      case 'running':
        return 'border-purple-500 bg-purple-50';
      case 'success':
        return 'border-green-500 bg-green-50';
      case 'error':
        return 'border-red-500 bg-red-50';
      default:
        return selected ? 'border-purple-400 bg-purple-50' : 'border-gray-200 bg-white';
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

  const getAgentInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
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
                <CardTitle className="text-sm font-medium">Custom Agent</CardTitle>
                <Sparkles className="w-3 h-3 text-purple-500" />
              </div>
              <div className="flex items-center gap-1">
                {selectedAgent?.is_registered && (
                  <Badge variant="outline" className="text-xs bg-purple-100 text-purple-700">
                    등록됨
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
            {/* Custom Agent 선택 */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-700">Custom Agent</label>
              <Select
                value={data.agent_id || ''}
                onValueChange={handleAgentChange}
                disabled={loading || data.status === 'running'}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="Custom Agent를 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  {availableAgents.map((agent) => (
                    <SelectItem key={agent.agent_id} value={agent.agent_id}>
                      <div className="flex items-center gap-2">
                        <Avatar className="w-5 h-5">
                          <AvatarFallback className="text-xs bg-purple-100 text-purple-700">
                            {getAgentInitials(agent.agent_name)}
                          </AvatarFallback>
                        </Avatar>
                        <div className="flex flex-col">
                          <span className="text-xs font-medium">{agent.agent_name}</span>
                          <span className="text-xs text-gray-500 truncate max-w-32">
                            {agent.description}
                          </span>
                        </div>
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

            {/* 선택된 Agent 정보 */}
            {selectedAgent && (
              <div className="p-2 bg-purple-50 rounded-md">
                <div className="flex items-center gap-2 mb-1">
                  <Avatar className="w-6 h-6">
                    <AvatarFallback className="text-xs bg-purple-200 text-purple-800">
                      {getAgentInitials(selectedAgent.agent_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="text-xs font-medium text-purple-800">{selectedAgent.agent_name}</p>
                    <p className="text-xs text-purple-600">
                      {selectedAgent.health_status.llm_provider} • {selectedAgent.health_status.llm_model}
                    </p>
                  </div>
                </div>
                {selectedAgent.description && (
                  <p className="text-xs text-purple-700 mt-1">{selectedAgent.description}</p>
                )}
              </div>
            )}

            {/* 입력 데이터 */}
            {isConfigOpen && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">입력 데이터 (JSON)</label>
                <Textarea
                  value={inputData}
                  onChange={(e) => handleInputDataChange(e.target.value)}
                  placeholder='{"input": "사용자 입력", "context": {}}'
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
            {selectedAgent && isConfigOpen && selectedAgent.capabilities.length > 0 && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">Agent 능력</label>
                <div className="flex flex-wrap gap-1">
                  {selectedAgent.capabilities.slice(0, 3).map((capability, index) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {capability.replace('_', ' ')}
                    </Badge>
                  ))}
                  {selectedAgent.capabilities.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{selectedAgent.capabilities.length - 3} more
                    </Badge>
                  )}
                </div>
              </div>
            )}

            {/* 실행 결과 */}
            {data.result && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">실행 결과</label>
                <div className="p-2 bg-gray-50 rounded text-xs max-h-20 overflow-y-auto">
                  {data.status === 'success' ? (
                    <div className="space-y-1">
                      <div className="text-green-700 font-medium">
                        ✓ {data.result.result?.response || '실행 완료'}
                      </div>
                      {data.result.result?.tool_results?.length > 0 && (
                        <div className="text-gray-600">
                          도구 사용: {data.result.result.tool_results.length}개
                        </div>
                      )}
                      {data.result.result?.kb_results?.length > 0 && (
                        <div className="text-gray-600">
                          지식베이스 검색: {data.result.result.kb_results.length}개 결과
                        </div>
                      )}
                    </div>
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
                  !data.agent_id || 
                  !data.input_data || 
                  !isValidJson(inputData) ||
                  data.status === 'running' ||
                  !selectedAgent?.is_registered
                }
                className="h-7 text-xs bg-purple-600 hover:bg-purple-700"
              >
                <Play className="w-3 h-3 mr-1" />
                실행
              </Button>
            </div>

            {/* 등록되지 않은 Agent 경고 */}
            {selectedAgent && !selectedAgent.is_registered && (
              <div className="p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                <div className="flex items-center gap-1 text-yellow-700">
                  <AlertCircle className="w-3 h-3" />
                  <span>이 Agent는 Plugin으로 등록되지 않았습니다.</span>
                </div>
                <p className="text-yellow-600 mt-1">
                  Agent 설정에서 Plugin으로 등록한 후 사용하세요.
                </p>
              </div>
            )}
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

export default CustomAgentExecutionBlock;