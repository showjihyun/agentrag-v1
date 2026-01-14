'use client';

import React, { useState } from 'react';
import {
  Users,
  Plus,
  Trash,
  Play,
  ChevronDown,
  ChevronRight,
  Bot,
  Target,
  BookOpen,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface Agent {
  id: string;
  name: string;
  role: string;
  goal: string;
  backstory: string;
  tools: string[];
  llm_model: string;
  temperature: number;
  allow_delegation: boolean;
  delegate_to: string[];
}

interface Task {
  id: string;
  description: string;
  agent_id: string;
  expected_output: string;
  context_from: string[];
  human_input: boolean;
}

interface AgentTeam {
  id?: string;
  name: string;
  description: string;
  agents: Agent[];
  tasks: Task[];
  execution_mode: 'sequential' | 'parallel' | 'hierarchical';
  manager_agent_id?: string;
}

interface ExecutionResult {
  success: boolean;
  results: Record<string, any>;
  task_results: any[];
  error?: string;
}

const AGENT_ROLES = [
  { value: 'researcher', label: 'Researcher', icon: '🔍' },
  { value: 'writer', label: 'Writer', icon: '✍️' },
  { value: 'editor', label: 'Editor', icon: '📝' },
  { value: 'analyst', label: 'Analyst', icon: '📊' },
  { value: 'coder', label: 'Developer', icon: '💻' },
  { value: 'reviewer', label: 'Reviewer', icon: '👀' },
  { value: 'manager', label: 'Manager', icon: '👔' },
  { value: 'custom', label: 'Custom', icon: '⚙️' },
];

const EXECUTION_MODES = [
  { value: 'sequential', label: 'Sequential', description: 'Execute tasks in order' },
  { value: 'parallel', label: 'Parallel', description: 'Execute independent tasks simultaneously' },
  { value: 'hierarchical', label: 'Hierarchical', description: 'Manager agent coordinates' },
];

const LLM_MODELS = [
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet' },
  { value: 'claude-3-haiku', label: 'Claude 3 Haiku' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
  { value: 'llama3.1', label: 'Llama 3.1 (Local)' },
];

const DEFAULT_AGENT: Omit<Agent, 'id'> = {
  name: '',
  role: 'researcher',
  goal: '',
  backstory: '',
  tools: [],
  llm_model: 'gpt-4o-mini',
  temperature: 0.7,
  allow_delegation: false,
  delegate_to: [],
};

const DEFAULT_TASK: Omit<Task, 'id'> = {
  description: '',
  agent_id: '',
  expected_output: '',
  context_from: [],
  human_input: false,
};

interface AgentTeamBuilderProps {
  initialTeam?: AgentTeam;
  onSave?: (team: AgentTeam) => void;
  onExecute?: (team: AgentTeam, inputs: Record<string, any>) => Promise<ExecutionResult>;
}

export const AgentTeamBuilder: React.FC<AgentTeamBuilderProps> = ({
  initialTeam,
  onSave,
  onExecute,
}) => {
  const [team, setTeam] = useState<AgentTeam>(initialTeam || {
    name: '',
    description: '',
    agents: [],
    tasks: [],
    execution_mode: 'sequential',
  });
  
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [inputs, setInputs] = useState<Record<string, any>>({});

  const generateId = () => `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const addAgent = () => {
    const newAgent: Agent = { ...DEFAULT_AGENT, id: generateId(), name: `에이전트 ${team.agents.length + 1}` };
    setTeam(prev => ({ ...prev, agents: [...prev.agents, newAgent] }));
    setExpandedAgents(prev => new Set([...prev, newAgent.id]));
  };

  const updateAgent = (id: string, updates: Partial<Agent>) => {
    setTeam(prev => ({ ...prev, agents: prev.agents.map(a => a.id === id ? { ...a, ...updates } : a) }));
  };

  const removeAgent = (id: string) => {
    setTeam(prev => ({
      ...prev,
      agents: prev.agents.filter(a => a.id !== id),
      tasks: prev.tasks.map(t => ({ ...t, agent_id: t.agent_id === id ? '' : t.agent_id })),
    }));
  };

  const addTask = () => {
    const newTask: Task = { ...DEFAULT_TASK, id: generateId(), agent_id: team.agents[0]?.id || '' };
    setTeam(prev => ({ ...prev, tasks: [...prev.tasks, newTask] }));
    setExpandedTasks(prev => new Set([...prev, newTask.id]));
  };

  const updateTask = (id: string, updates: Partial<Task>) => {
    setTeam(prev => ({ ...prev, tasks: prev.tasks.map(t => t.id === id ? { ...t, ...updates } : t) }));
  };

  const removeTask = (id: string) => {
    setTeam(prev => ({ ...prev, tasks: prev.tasks.filter(t => t.id !== id) }));
  };

  const toggleExpand = (type: 'agent' | 'task', id: string) => {
    const setter = type === 'agent' ? setExpandedAgents : setExpandedTasks;
    setter(prev => { const next = new Set(prev); next.has(id) ? next.delete(id) : next.add(id); return next; });
  };

  const handleExecute = async () => {
    if (!onExecute) return;
    setExecuting(true);
    setExecutionResult(null);
    try {
      const result = await onExecute(team, inputs);
      setExecutionResult(result);
    } catch (error) {
      setExecutionResult({ success: false, results: {}, task_results: [], error: error instanceof Error ? error.message : 'Execution failed' });
    } finally {
      setExecuting(false);
    }
  };

  const getRoleIcon = (role: string) => AGENT_ROLES.find(r => r.value === role)?.icon || '🤖';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-100"><Users className="h-6 w-6 text-purple-600" /></div>
          <div>
            <h2 className="text-xl font-bold">Agent Team Builder</h2>
            <p className="text-sm text-muted-foreground">멀티 에이전트 협업 시스템</p>
          </div>
        </div>
        <div className="flex gap-2">
          {onSave && <Button variant="outline" onClick={() => onSave(team)}>저장</Button>}
          <Button onClick={handleExecute} disabled={executing || team.agents.length === 0 || team.tasks.length === 0}>
            {executing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Play className="h-4 w-4 mr-2" />}
            실행
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base">팀 정보</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>이름</Label>
              <Input placeholder="팀 이름" value={team.name} onChange={(e) => setTeam(prev => ({ ...prev, name: e.target.value }))} />
            </div>
            <div className="space-y-2">
              <Label>실행 모드</Label>
              <Select value={team.execution_mode} onValueChange={(v: any) => setTeam(prev => ({ ...prev, execution_mode: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {EXECUTION_MODES.map(mode => (
                    <SelectItem key={mode.value} value={mode.value}>{mode.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label>설명</Label>
            <Textarea placeholder="팀 설명" value={team.description} onChange={(e) => setTeam(prev => ({ ...prev, description: e.target.value }))} rows={2} />
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="agents" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="agents">에이전트 ({team.agents.length})</TabsTrigger>
          <TabsTrigger value="tasks">태스크 ({team.tasks.length})</TabsTrigger>
          <TabsTrigger value="execution">실행 결과</TabsTrigger>
        </TabsList>

        <TabsContent value="agents" className="space-y-4">
          <Button variant="outline" onClick={addAgent} className="w-full"><Plus className="h-4 w-4 mr-2" />에이전트 추가</Button>
          {team.agents.map((agent, index) => (
            <Card key={agent.id}>
              <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50" onClick={() => toggleExpand('agent', agent.id)}>
                <div className="flex items-center gap-3">
                  {expandedAgents.has(agent.id) ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  <span className="text-xl">{getRoleIcon(agent.role)}</span>
                  <div>
                    <div className="font-medium">{agent.name || `에이전트 ${index + 1}`}</div>
                    <div className="text-xs text-muted-foreground">{AGENT_ROLES.find(r => r.value === agent.role)?.label} • {agent.llm_model}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {agent.allow_delegation && <Badge variant="secondary">위임 가능</Badge>}
                  <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); removeAgent(agent.id); }}><Trash className="h-4 w-4" /></Button>
                </div>
              </div>
              {expandedAgents.has(agent.id) && (
                <CardContent className="border-t space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2"><Label>이름</Label><Input value={agent.name} onChange={(e) => updateAgent(agent.id, { name: e.target.value })} /></div>
                    <div className="space-y-2">
                      <Label>역할</Label>
                      <Select value={agent.role} onValueChange={(v) => updateAgent(agent.id, { role: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>{AGENT_ROLES.map(role => <SelectItem key={role.value} value={role.value}>{role.icon} {role.label}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="space-y-2"><Label className="flex items-center gap-2"><Target className="h-4 w-4" />목표</Label><Textarea placeholder="에이전트 목표" value={agent.goal} onChange={(e) => updateAgent(agent.id, { goal: e.target.value })} rows={2} /></div>
                  <div className="space-y-2"><Label className="flex items-center gap-2"><BookOpen className="h-4 w-4" />배경</Label><Textarea placeholder="에이전트 배경" value={agent.backstory} onChange={(e) => updateAgent(agent.id, { backstory: e.target.value })} rows={3} /></div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>LLM 모델</Label>
                      <Select value={agent.llm_model} onValueChange={(v) => updateAgent(agent.id, { llm_model: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>{LLM_MODELS.map(m => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2"><Label>Temperature: {agent.temperature}</Label><Input type="range" min="0" max="2" step="0.1" value={agent.temperature} onChange={(e) => updateAgent(agent.id, { temperature: parseFloat(e.target.value) })} /></div>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <div><Label>위임 허용</Label><p className="text-xs text-muted-foreground">실패 시 다른 에이전트에게 위임</p></div>
                    <Switch checked={agent.allow_delegation} onCheckedChange={(v) => updateAgent(agent.id, { allow_delegation: v })} />
                  </div>
                </CardContent>
              )}
            </Card>
          ))}
          {team.agents.length === 0 && <div className="text-center py-8 text-muted-foreground"><Bot className="h-12 w-12 mx-auto mb-2 opacity-50" /><p>에이전트를 추가하세요</p></div>}
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <Button variant="outline" onClick={addTask} className="w-full" disabled={team.agents.length === 0}><Plus className="h-4 w-4 mr-2" />태스크 추가</Button>
          {team.tasks.map((task, index) => {
            const assignedAgent = team.agents.find(a => a.id === task.agent_id);
            return (
              <Card key={task.id}>
                <div className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50" onClick={() => toggleExpand('task', task.id)}>
                  <div className="flex items-center gap-3">
                    {expandedTasks.has(task.id) ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    <Badge variant="outline">#{index + 1}</Badge>
                    <div>
                      <div className="font-medium truncate max-w-md">{task.description || `태스크 ${index + 1}`}</div>
                      <div className="text-xs text-muted-foreground">{assignedAgent ? `${getRoleIcon(assignedAgent.role)} ${assignedAgent.name}` : <span className="text-destructive">에이전트 미지정</span>}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {task.human_input && <Badge variant="secondary">사람 입력</Badge>}
                    <Button variant="ghost" size="icon" onClick={(e) => { e.stopPropagation(); removeTask(task.id); }}><Trash className="h-4 w-4" /></Button>
                  </div>
                </div>
                {expandedTasks.has(task.id) && (
                  <CardContent className="border-t space-y-4">
                    <div className="space-y-2"><Label>설명</Label><Textarea placeholder="태스크 설명" value={task.description} onChange={(e) => updateTask(task.id, { description: e.target.value })} rows={3} /></div>
                    <div className="space-y-2">
                      <Label>담당 에이전트</Label>
                      <Select value={task.agent_id} onValueChange={(v) => updateTask(task.id, { agent_id: v })}>
                        <SelectTrigger><SelectValue placeholder="에이전트 선택" /></SelectTrigger>
                        <SelectContent>{team.agents.map(a => <SelectItem key={a.id} value={a.id}>{getRoleIcon(a.role)} {a.name}</SelectItem>)}</SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2"><Label>예상 출력</Label><Textarea placeholder="예상 결과물" value={task.expected_output} onChange={(e) => updateTask(task.id, { expected_output: e.target.value })} rows={2} /></div>
                    <div className="flex items-center justify-between py-2">
                      <div><Label>사람 입력 필요</Label><p className="text-xs text-muted-foreground">실행 중 사람의 확인 요청</p></div>
                      <Switch checked={task.human_input} onCheckedChange={(v) => updateTask(task.id, { human_input: v })} />
                    </div>
                  </CardContent>
                )}
              </Card>
            );
          })}
          {team.tasks.length === 0 && <div className="text-center py-8 text-muted-foreground"><Clock className="h-12 w-12 mx-auto mb-2 opacity-50" /><p>태스크를 추가하세요</p></div>}
        </TabsContent>

        <TabsContent value="execution" className="space-y-4">
          <Card>
            <CardHeader><CardTitle className="text-base">입력 변수</CardTitle></CardHeader>
            <CardContent>
              <Textarea placeholder='{"topic": "AI trends"}' value={JSON.stringify(inputs, null, 2)} onChange={(e) => { try { setInputs(JSON.parse(e.target.value)); } catch {} }} rows={4} className="font-mono text-sm" />
            </CardContent>
          </Card>
          {executionResult && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  {executionResult.success ? <CheckCircle className="h-5 w-5 text-green-500" /> : <XCircle className="h-5 w-5 text-red-500" />}
                  실행 결과
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {executionResult.error && <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">{executionResult.error}</div>}
                {executionResult.task_results?.map((result: any, index: number) => (
                  <div key={index} className="p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">태스크 #{index + 1}</Badge>
                      <Badge variant={result.status === 'completed' ? 'default' : 'destructive'}>{result.status}</Badge>
                    </div>
                    <pre className="text-sm whitespace-pre-wrap">{typeof result.output === 'string' ? result.output : JSON.stringify(result.output, null, 2)}</pre>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default AgentTeamBuilder;
