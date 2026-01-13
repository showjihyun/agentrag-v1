/**
 * Agent Orchestration Block Component
 * 
 * 워크플로우에서 다중 Agent 오케스트레이션을 수행하는 블록 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { Handle, Position } from 'reactflow';
import { Network, Settings, Play, AlertCircle, CheckCircle, Users, Zap } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Progress } from '@/components/ui/progress';

interface AgentOrchestrationBlockProps {
  id: string;
  data: {
    pattern?: string;
    agents?: string[];
    task?: string;
    config?: any;
    result?: any;
    status?: 'idle' | 'running' | 'success' | 'error';
    error?: string;
    progress?: number;
    orchestration_log?: Array<{
      timestamp: string;
      agent: string;
      event: string;
      data: any;
    }>;
  };
  selected?: boolean;
  onDataChange?: (id: string, data: any) => void;
  onExecute?: (id: string) => void;
}

interface OrchestrationPattern {
  value: string;
  label: string;
  description: string;
  icon: React.ReactNode;
  complexity: 'simple' | 'medium' | 'complex';
}

interface AgentInfo {
  agent_type: string;
  agent_id: string;
  health_status: {
    status: string;
  };
}

const AgentOrchestrationBlock: React.FC<AgentOrchestrationBlockProps> = ({
  id,
  data,
  selected,
  onDataChange,
  onExecute
}) => {
  const [availableAgents, setAvailableAgents] = useState<AgentInfo[]>([]);
  const [availablePatterns, setAvailablePatterns] = useState<OrchestrationPattern[]>([]);
  const [taskDefinition, setTaskDefinition] = useState(data.task || '{}');
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // 오케스트레이션 패턴 정의
  const orchestrationPatterns: OrchestrationPattern[] = [
    {
      value: 'sequential',
      label: '순차 실행',
      description: 'Agent들을 순서대로 실행합니다',
      icon: <div className="w-3 h-3 bg-blue-500 rounded" />,
      complexity: 'simple'
    },
    {
      value: 'parallel',
      label: '병렬 실행',
      description: '모든 Agent를 동시에 실행합니다',
      icon: <div className="flex gap-0.5"><div className="w-1 h-3 bg-green-500 rounded" /><div className="w-1 h-3 bg-green-500 rounded" /><div className="w-1 h-3 bg-green-500 rounded" /></div>,
      complexity: 'simple'
    },
    {
      value: 'consensus',
      label: '합의 기반',
      description: 'Agent들 간의 투표와 합의를 통해 결정합니다',
      icon: <Users className="w-3 h-3" />,
      complexity: 'complex'
    },
    {
      value: 'swarm',
      label: '군집 지능',
      description: '군집 지능을 활용한 최적화를 수행합니다',
      icon: <Network className="w-3 h-3" />,
      complexity: 'complex'
    },
    {
      value: 'dynamic_routing',
      label: '동적 라우팅',
      description: '실시간 성능 기반으로 Agent를 선택합니다',
      icon: <Zap className="w-3 h-3" />,
      complexity: 'medium'
    }
  ];

  // 데이터 로드
  useEffect(() => {
    loadAvailableAgents();
    loadOrchestrationPatterns();
  }, []);

  const loadAvailableAgents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/agent-plugins/agents');
      if (response.ok) {
        const agents = await response.json();
        setAvailableAgents(agents.filter((agent: AgentInfo) => 
          agent.health_status.status === 'healthy'
        ));
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOrchestrationPatterns = async () => {
    try {
      const response = await fetch('/api/v1/agent-plugins/orchestration/patterns');
      if (response.ok) {
        const patternsData = await response.json();
        const patterns = orchestrationPatterns.filter(p => 
          patternsData.patterns.includes(p.value)
        );
        setAvailablePatterns(patterns);
      }
    } catch (error) {
      console.error('Failed to load patterns:', error);
      setAvailablePatterns(orchestrationPatterns);
    }
  };

  const handlePatternChange = (pattern: string) => {
    onDataChange?.(id, {
      ...data,
      pattern,
      config: { ...data.config, pattern }
    });
  };

  const handleAgentToggle = (agentType: string, checked: boolean) => {
    const currentAgents = data.agents || [];
    const newAgents = checked
      ? [...currentAgents, agentType]
      : currentAgents.filter(a => a !== agentType);

    onDataChange?.(id, {
      ...data,
      agents: newAgents,
      config: { ...data.config, agents: newAgents }
    });
  };

  const handleTaskChange = (value: string) => {
    setTaskDefinition(value);
    
    try {
      const parsedTask = JSON.parse(value);
      onDataChange?.(id, {
        ...data,
        task: value,
        config: { ...data.config, task: parsedTask }
      });
    } catch (error) {
      // Invalid JSON - don't update config
    }
  };

  const handleExecute = () => {
    if (onExecute && data.pattern && data.agents?.length && data.task) {
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
        return <Network className="w-4 h-4 text-gray-500" />;
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

  const getComplexityBadge = (complexity: string) => {
    const colors = {
      simple: 'bg-green-100 text-green-700',
      medium: 'bg-yellow-100 text-yellow-700',
      complex: 'bg-red-100 text-red-700'
    };
    return colors[complexity as keyof typeof colors] || colors.simple;
  };

  const isValidJson = (str: string) => {
    try {
      JSON.parse(str);
      return true;
    } catch {
      return false;
    }
  };

  const selectedPattern = orchestrationPatterns.find(p => p.value === data.pattern);

  return (
    <TooltipProvider>
      <div className="relative">
        {/* Input Handle */}
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-gray-400 border-2 border-white"
        />

        <Card className={`w-96 transition-all duration-200 ${getStatusColor()}`}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getStatusIcon()}
                <CardTitle className="text-sm font-medium">Agent 오케스트레이션</CardTitle>
              </div>
              <div className="flex items-center gap-1">
                {data.agents && data.agents.length > 0 && (
                  <Badge variant="outline" className="text-xs">
                    {data.agents.length} Agents
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
            {/* 오케스트레이션 패턴 선택 */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-700">오케스트레이션 패턴</label>
              <Select
                value={data.pattern || ''}
                onValueChange={handlePatternChange}
                disabled={loading || data.status === 'running'}
              >
                <SelectTrigger className="h-8 text-xs">
                  <SelectValue placeholder="패턴을 선택하세요" />
                </SelectTrigger>
                <SelectContent>
                  {availablePatterns.map((pattern) => (
                    <SelectItem key={pattern.value} value={pattern.value}>
                      <div className="flex items-center gap-2">
                        {pattern.icon}
                        <span>{pattern.label}</span>
                        <Badge className={`text-xs ${getComplexityBadge(pattern.complexity)}`}>
                          {pattern.complexity}
                        </Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {selectedPattern && (
                <p className="text-xs text-gray-500">{selectedPattern.description}</p>
              )}
            </div>

            {/* Agent 선택 */}
            {isConfigOpen && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">참여 Agent</label>
                <div className="space-y-1 max-h-24 overflow-y-auto">
                  {availableAgents.map((agent) => (
                    <div key={agent.agent_type} className="flex items-center space-x-2">
                      <Checkbox
                        id={`agent-${agent.agent_type}`}
                        checked={data.agents?.includes(agent.agent_type) || false}
                        onCheckedChange={(checked) => 
                          handleAgentToggle(agent.agent_type, checked as boolean)
                        }
                        disabled={data.status === 'running'}
                      />
                      <label
                        htmlFor={`agent-${agent.agent_type}`}
                        className="text-xs cursor-pointer flex items-center gap-1"
                      >
                        {agent.agent_id}
                        <CheckCircle className="w-3 h-3 text-green-500" />
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 작업 정의 */}
            {isConfigOpen && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">작업 정의 (JSON)</label>
                <Textarea
                  value={taskDefinition}
                  onChange={(e) => handleTaskChange(e.target.value)}
                  placeholder='{"objective": "작업 목표", "requirements": ["요구사항1", "요구사항2"]}'
                  className={`h-20 text-xs font-mono ${
                    !isValidJson(taskDefinition) ? 'border-red-300 bg-red-50' : ''
                  }`}
                  disabled={data.status === 'running'}
                />
                {!isValidJson(taskDefinition) && (
                  <p className="text-xs text-red-500">유효한 JSON 형식이 아닙니다</p>
                )}
              </div>
            )}

            {/* 실행 진행률 */}
            {data.status === 'running' && data.progress !== undefined && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-700">진행률</span>
                  <span className="text-gray-500">{data.progress}%</span>
                </div>
                <Progress value={data.progress} className="h-2" />
              </div>
            )}

            {/* 오케스트레이션 로그 */}
            {data.orchestration_log && data.orchestration_log.length > 0 && isConfigOpen && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">실행 로그</label>
                <div className="p-2 bg-gray-50 rounded text-xs max-h-20 overflow-y-auto space-y-1">
                  {data.orchestration_log.slice(-3).map((log, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {log.agent}
                      </Badge>
                      <span className="text-gray-600">{log.event}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 실행 결과 */}
            {data.result && (
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-700">오케스트레이션 결과</label>
                <div className="p-2 bg-gray-50 rounded text-xs font-mono max-h-20 overflow-y-auto">
                  {data.status === 'success' ? (
                    <div className="space-y-1">
                      <div className="text-green-700 font-medium">
                        패턴: {data.result.pattern}
                      </div>
                      {data.result.agent_results && (
                        <div className="text-gray-600">
                          Agent 결과: {Object.keys(data.result.agent_results).length}개
                        </div>
                      )}
                    </div>
                  ) : (
                    <span className="text-red-700">{data.error || '오케스트레이션 실패'}</span>
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
                  !data.pattern || 
                  !data.agents?.length || 
                  !data.task || 
                  !isValidJson(taskDefinition) ||
                  data.status === 'running'
                }
                className="h-7 text-xs"
              >
                <Play className="w-3 h-3 mr-1" />
                오케스트레이션 실행
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

export default AgentOrchestrationBlock;