'use client';

/**
 * A2A Protocol Settings Component
 * 
 * Google A2A 프로토콜을 통한 외부 에이전트 연동 설정 UI
 */

import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Trash2, 
  RefreshCw, 
  ExternalLink, 
  Check, 
  X, 
  Settings,
  Globe,
  Server,
  Key,
  Shield,
  Zap,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';


// Types
interface A2AAgentConfig {
  id: string;
  name: string;
  description?: string;
  agentCardUrl: string;
  baseUrl?: string;
  protocolBinding: 'JSONRPC' | 'GRPC' | 'HTTP+JSON';
  authType: 'none' | 'api_key' | 'bearer' | 'oauth2';
  authConfig?: Record<string, unknown>;
  headers?: Record<string, string>;
  timeoutSeconds: number;
  retryCount: number;
  enabled: boolean;
  createdAt?: string;
  updatedAt?: string;
}

interface AgentCard {
  protocolVersion?: string;
  name: string;
  description: string;
  version: string;
  capabilities?: {
    streaming?: boolean;
    pushNotifications?: boolean;
  };
  skills?: Array<{
    id: string;
    name: string;
    description: string;
    tags: string[];
  }>;
}

interface A2AAgentConfigResponse {
  config: A2AAgentConfig;
  agentCard?: AgentCard;
  status: 'connected' | 'disconnected' | 'error';
  lastError?: string;
}

interface A2AServerConfig {
  id: string;
  agentId?: string;
  workflowId?: string;
  name: string;
  description: string;
  version: string;
  skills: Array<{
    id: string;
    name: string;
    description: string;
    tags: string[];
  }>;
  streamingEnabled: boolean;
  pushNotificationsEnabled: boolean;
  requireAuth: boolean;
  allowedAuthSchemes: string[];
  rateLimitPerMinute: number;
  enabled: boolean;
}

interface A2AServerConfigResponse {
  config: A2AServerConfig;
  agentCardUrl: string;
  endpointUrl: string;
}

// API functions
const API_BASE = '/api/agent-builder/a2a';

async function fetchAgentConfigs(): Promise<A2AAgentConfigResponse[]> {
  try {
    const res = await fetch(`${API_BASE}/agents`);
    console.log('A2A API Response:', res.status, res.statusText);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('A2A API Error:', errorText);
      throw new Error(`Failed to fetch agent configs: ${res.status} ${res.statusText}`);
    }
    
    const data = await res.json();
    return data.agents;
  } catch (error) {
    console.error('fetchAgentConfigs error:', error);
    throw error;
  }
}

async function createAgentConfig(config: Partial<A2AAgentConfig>): Promise<A2AAgentConfigResponse> {
  const res = await fetch(`${API_BASE}/agents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('Failed to create agent config');
  return res.json();
}

async function updateAgentConfig(id: string, config: Partial<A2AAgentConfig>): Promise<A2AAgentConfigResponse> {
  const res = await fetch(`${API_BASE}/agents/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('Failed to update agent config');
  return res.json();
}

async function deleteAgentConfig(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/agents/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete agent config');
}

async function testAgentConnection(id: string): Promise<A2AAgentConfigResponse> {
  const res = await fetch(`${API_BASE}/agents/${id}/test`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to test connection');
  return res.json();
}

async function fetchServerConfigs(): Promise<A2AServerConfigResponse[]> {
  try {
    const res = await fetch(`${API_BASE}/servers`);
    console.log('A2A Server API Response:', res.status, res.statusText);
    
    if (!res.ok) {
      const errorText = await res.text();
      console.error('A2A Server API Error:', errorText);
      throw new Error(`Failed to fetch server configs: ${res.status} ${res.statusText}`);
    }
    
    const data = await res.json();
    return data.servers;
  } catch (error) {
    console.error('fetchServerConfigs error:', error);
    throw error;
  }
}

async function createServerConfig(config: Partial<A2AServerConfig>): Promise<A2AServerConfigResponse> {
  const res = await fetch(`${API_BASE}/servers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('Failed to create server config');
  return res.json();
}

async function deleteServerConfig(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/servers/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete server config');
}


// Status Badge Component
function StatusBadge({ status }: { status: 'connected' | 'disconnected' | 'error' }) {
  const variants = {
    connected: { color: 'bg-green-500', text: '연결됨' },
    disconnected: { color: 'bg-gray-500', text: '연결 안됨' },
    error: { color: 'bg-red-500', text: '오류' },
  };
  const { color, text } = variants[status];
  
  return (
    <Badge variant="outline" className="gap-1">
      <span className={`w-2 h-2 rounded-full ${color}`} />
      {text}
    </Badge>
  );
}

// External Agent Card Component
function ExternalAgentCard({ 
  agent, 
  onTest, 
  onDelete, 
  onToggle,
  testing,
}: { 
  agent: A2AAgentConfigResponse;
  onTest: () => void;
  onDelete: () => void;
  onToggle: (enabled: boolean) => void;
  testing: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Globe className="w-5 h-5 text-blue-500" />
            <div>
              <CardTitle className="text-lg">{agent.config.name}</CardTitle>
              {agent.config.description && (
                <CardDescription>{agent.config.description}</CardDescription>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={agent.status} />
            <Switch 
              checked={agent.config.enabled} 
              onCheckedChange={onToggle}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <ExternalLink className="w-4 h-4" />
            <span className="truncate">{agent.config.agentCardUrl}</span>
          </div>
          
          {agent.agentCard && (
            <div className="flex flex-wrap gap-2">
              {agent.agentCard.capabilities?.streaming && (
                <Badge variant="secondary">
                  <Zap className="w-3 h-3 mr-1" />
                  스트리밍
                </Badge>
              )}
              {agent.agentCard.skills?.map(skill => (
                <Badge key={skill.id} variant="outline">
                  {skill.name}
                </Badge>
              ))}
            </div>
          )}
          
          {agent.lastError && (
            <div className="text-sm text-red-500 bg-red-50 p-2 rounded">
              {agent.lastError}
            </div>
          )}
          
          <div className="flex gap-2 pt-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={onTest}
              disabled={testing}
            >
              {testing ? (
                <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-1" />
              )}
              연결 테스트
            </Button>
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              <Settings className="w-4 h-4 mr-1" />
              상세 설정
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onDelete}
              className="text-red-500 hover:text-red-600"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
          
          {expanded && agent.agentCard && (
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <h4 className="font-medium mb-2">Agent Card 정보</h4>
              <div className="text-sm space-y-1">
                <p><strong>버전:</strong> {agent.agentCard.version}</p>
                <p><strong>프로토콜:</strong> {agent.agentCard.protocolVersion}</p>
                <p><strong>설명:</strong> {agent.agentCard.description}</p>
              </div>
              {agent.agentCard.skills && agent.agentCard.skills.length > 0 && (
                <div className="mt-3">
                  <h5 className="font-medium mb-1">스킬</h5>
                  <ul className="text-sm space-y-1">
                    {agent.agentCard.skills.map(skill => (
                      <li key={skill.id} className="flex items-start gap-2">
                        <span className="font-medium">{skill.name}:</span>
                        <span className="text-muted-foreground">{skill.description}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}


// Server Config Card Component
function ServerConfigCard({ 
  server, 
  onDelete,
  onToggle,
}: { 
  server: A2AServerConfigResponse;
  onDelete: () => void;
  onToggle: (enabled: boolean) => void;
}) {
  const [copied, setCopied] = useState<string | null>(null);
  
  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };
  
  return (
    <Card className="mb-4">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Server className="w-5 h-5 text-green-500" />
            <div>
              <CardTitle className="text-lg">{server.config.name}</CardTitle>
              <CardDescription>{server.config.description}</CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={server.config.enabled ? 'default' : 'secondary'}>
              {server.config.enabled ? '활성' : '비활성'}
            </Badge>
            <Switch 
              checked={server.config.enabled} 
              onCheckedChange={onToggle}
            />
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <Label className="text-muted-foreground">Agent Card URL</Label>
              <div className="flex items-center gap-2 mt-1">
                <code className="flex-1 p-2 bg-muted rounded text-xs truncate">
                  {server.agentCardUrl}
                </code>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => copyToClipboard(server.agentCardUrl, 'card')}
                >
                  {copied === 'card' ? <Check className="w-4 h-4" /> : '복사'}
                </Button>
              </div>
            </div>
            <div>
              <Label className="text-muted-foreground">Endpoint URL</Label>
              <div className="flex items-center gap-2 mt-1">
                <code className="flex-1 p-2 bg-muted rounded text-xs truncate">
                  {server.endpointUrl}
                </code>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => copyToClipboard(server.endpointUrl, 'endpoint')}
                >
                  {copied === 'endpoint' ? <Check className="w-4 h-4" /> : '복사'}
                </Button>
              </div>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {server.config.streamingEnabled && (
              <Badge variant="secondary">
                <Zap className="w-3 h-3 mr-1" />
                스트리밍
              </Badge>
            )}
            {server.config.requireAuth && (
              <Badge variant="secondary">
                <Shield className="w-3 h-3 mr-1" />
                인증 필요
              </Badge>
            )}
            <Badge variant="outline">
              v{server.config.version}
            </Badge>
          </div>
          
          {server.config.skills.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {server.config.skills.map(skill => (
                <Badge key={skill.id} variant="outline" className="text-xs">
                  {skill.name}
                </Badge>
              ))}
            </div>
          )}
          
          <div className="flex gap-2 pt-2">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onDelete}
              className="text-red-500 hover:text-red-600"
            >
              <Trash2 className="w-4 h-4 mr-1" />
              삭제
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


// Add External Agent Dialog
function AddExternalAgentDialog({ 
  open, 
  onOpenChange, 
  onAdd 
}: { 
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd: (config: Partial<A2AAgentConfig>) => Promise<void>;
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    agentCardUrl: '',
    protocolBinding: 'HTTP+JSON' as const,
    authType: 'none' as const,
    apiKey: '',
    bearerToken: '',
    timeoutSeconds: 30,
    retryCount: 3,
  });
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const authConfig: Record<string, unknown> = {};
      if (formData.authType === 'api_key') {
        authConfig.api_key = formData.apiKey;
        authConfig.header_name = 'X-API-Key';
      } else if (formData.authType === 'bearer') {
        authConfig.token = formData.bearerToken;
      }
      
      await onAdd({
        name: formData.name,
        description: formData.description,
        agentCardUrl: formData.agentCardUrl,
        protocolBinding: formData.protocolBinding,
        authType: formData.authType,
        authConfig: Object.keys(authConfig).length > 0 ? authConfig : undefined,
        timeoutSeconds: formData.timeoutSeconds,
        retryCount: formData.retryCount,
        enabled: true,
      });
      
      onOpenChange(false);
      setFormData({
        name: '',
        description: '',
        agentCardUrl: '',
        protocolBinding: 'HTTP+JSON',
        authType: 'none',
        apiKey: '',
        bearerToken: '',
        timeoutSeconds: 30,
        retryCount: 3,
      });
    } catch (error) {
      console.error('Failed to add agent:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>외부 A2A 에이전트 추가</DialogTitle>
          <DialogDescription>
            Google A2A 프로토콜을 지원하는 외부 에이전트에 연결합니다.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">이름 *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="에이전트 이름"
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="description">설명</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="에이전트 설명"
              rows={2}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="agentCardUrl">Agent Card URL *</Label>
            <Input
              id="agentCardUrl"
              value={formData.agentCardUrl}
              onChange={e => setFormData(prev => ({ ...prev, agentCardUrl: e.target.value }))}
              placeholder="https://example.com/.well-known/agent-card.json"
              required
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>프로토콜</Label>
              <Select 
                value={formData.protocolBinding}
                onValueChange={v => setFormData(prev => ({ 
                  ...prev, 
                  protocolBinding: v as typeof formData.protocolBinding 
                }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="HTTP+JSON">HTTP+JSON</SelectItem>
                  <SelectItem value="JSONRPC">JSON-RPC</SelectItem>
                  <SelectItem value="GRPC">gRPC</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>인증 방식</Label>
              <Select 
                value={formData.authType}
                onValueChange={v => setFormData(prev => ({ 
                  ...prev, 
                  authType: v as typeof formData.authType 
                }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">없음</SelectItem>
                  <SelectItem value="api_key">API Key</SelectItem>
                  <SelectItem value="bearer">Bearer Token</SelectItem>
                  <SelectItem value="oauth2">OAuth 2.0</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          {formData.authType === 'api_key' && (
            <div className="space-y-2">
              <Label htmlFor="apiKey">API Key</Label>
              <Input
                id="apiKey"
                type="password"
                value={formData.apiKey}
                onChange={e => setFormData(prev => ({ ...prev, apiKey: e.target.value }))}
                placeholder="API Key 입력"
              />
            </div>
          )}
          
          {formData.authType === 'bearer' && (
            <div className="space-y-2">
              <Label htmlFor="bearerToken">Bearer Token</Label>
              <Input
                id="bearerToken"
                type="password"
                value={formData.bearerToken}
                onChange={e => setFormData(prev => ({ ...prev, bearerToken: e.target.value }))}
                placeholder="Bearer Token 입력"
              />
            </div>
          )}
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              취소
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? '추가 중...' : '추가'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}


// Add Server Config Dialog
function AddServerConfigDialog({ 
  open, 
  onOpenChange, 
  onAdd,
  agents,
  workflows,
}: { 
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd: (config: Partial<A2AServerConfig>) => Promise<void>;
  agents: Array<{ id: string; name: string }>;
  workflows: Array<{ id: string; name: string }>;
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    sourceType: 'agent' as 'agent' | 'workflow',
    sourceId: '',
    name: '',
    description: '',
    version: '1.0.0',
    streamingEnabled: true,
    requireAuth: true,
    rateLimitPerMinute: 60,
  });
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await onAdd({
        agentId: formData.sourceType === 'agent' ? formData.sourceId : undefined,
        workflowId: formData.sourceType === 'workflow' ? formData.sourceId : undefined,
        name: formData.name,
        description: formData.description,
        version: formData.version,
        streamingEnabled: formData.streamingEnabled,
        requireAuth: formData.requireAuth,
        rateLimitPerMinute: formData.rateLimitPerMinute,
        skills: [],
        enabled: true,
      });
      
      onOpenChange(false);
      setFormData({
        sourceType: 'agent',
        sourceId: '',
        name: '',
        description: '',
        version: '1.0.0',
        streamingEnabled: true,
        requireAuth: true,
        rateLimitPerMinute: 60,
      });
    } catch (error) {
      console.error('Failed to add server config:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const sources = formData.sourceType === 'agent' ? agents : workflows;
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>A2A 서버 설정 추가</DialogTitle>
          <DialogDescription>
            로컬 에이전트 또는 워크플로우를 A2A 프로토콜로 외부에 노출합니다.
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>소스 타입</Label>
              <Select 
                value={formData.sourceType}
                onValueChange={v => setFormData(prev => ({ 
                  ...prev, 
                  sourceType: v as typeof formData.sourceType,
                  sourceId: '',
                }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="agent">에이전트</SelectItem>
                  <SelectItem value="workflow">워크플로우</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>소스 선택 *</Label>
              <Select 
                value={formData.sourceId}
                onValueChange={v => setFormData(prev => ({ ...prev, sourceId: v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="선택..." />
                </SelectTrigger>
                <SelectContent>
                  {sources.map(s => (
                    <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="serverName">A2A 에이전트 이름 *</Label>
            <Input
              id="serverName"
              value={formData.name}
              onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="외부에 노출될 에이전트 이름"
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="serverDescription">설명 *</Label>
            <Textarea
              id="serverDescription"
              value={formData.description}
              onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
              placeholder="에이전트 설명"
              rows={2}
              required
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="version">버전</Label>
              <Input
                id="version"
                value={formData.version}
                onChange={e => setFormData(prev => ({ ...prev, version: e.target.value }))}
                placeholder="1.0.0"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="rateLimit">Rate Limit (요청/분)</Label>
              <Input
                id="rateLimit"
                type="number"
                value={formData.rateLimitPerMinute}
                onChange={e => setFormData(prev => ({ 
                  ...prev, 
                  rateLimitPerMinute: parseInt(e.target.value) || 60 
                }))}
              />
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Switch 
                id="streaming"
                checked={formData.streamingEnabled}
                onCheckedChange={v => setFormData(prev => ({ ...prev, streamingEnabled: v }))}
              />
              <Label htmlFor="streaming">스트리밍 활성화</Label>
            </div>
            
            <div className="flex items-center gap-2">
              <Switch 
                id="auth"
                checked={formData.requireAuth}
                onCheckedChange={v => setFormData(prev => ({ ...prev, requireAuth: v }))}
              />
              <Label htmlFor="auth">인증 필요</Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              취소
            </Button>
            <Button type="submit" disabled={loading || !formData.sourceId}>
              {loading ? '추가 중...' : '추가'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}


// Main Component
export default function A2ASettings() {
  const [activeTab, setActiveTab] = useState('external');
  const [externalAgents, setExternalAgents] = useState<A2AAgentConfigResponse[]>([]);
  const [serverConfigs, setServerConfigs] = useState<A2AServerConfigResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [testingId, setTestingId] = useState<string | null>(null);
  
  // Dialogs
  const [addAgentOpen, setAddAgentOpen] = useState(false);
  const [addServerOpen, setAddServerOpen] = useState(false);
  
  // Mock data for agents/workflows (should come from API)
  const [localAgents] = useState([
    { id: 'agent-1', name: 'Research Assistant' },
    { id: 'agent-2', name: 'Code Helper' },
  ]);
  const [localWorkflows] = useState([
    { id: 'workflow-1', name: 'Document Processing' },
    { id: 'workflow-2', name: 'Data Analysis' },
  ]);
  
  // Load data
  useEffect(() => {
    loadData();
  }, []);
  
  const loadData = async () => {
    setLoading(true);
    try {
      const [agents, servers] = await Promise.all([
        fetchAgentConfigs(),
        fetchServerConfigs(),
      ]);
      setExternalAgents(agents);
      setServerConfigs(servers);
    } catch (error) {
      console.error('Failed to load A2A data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // External agent handlers
  const handleAddAgent = async (config: Partial<A2AAgentConfig>) => {
    const result = await createAgentConfig(config);
    setExternalAgents(prev => [...prev, result]);
  };
  
  const handleTestAgent = async (id: string) => {
    setTestingId(id);
    try {
      const result = await testAgentConnection(id);
      setExternalAgents(prev => 
        prev.map(a => a.config.id === id ? result : a)
      );
    } finally {
      setTestingId(null);
    }
  };
  
  const handleToggleAgent = async (id: string, enabled: boolean) => {
    const result = await updateAgentConfig(id, { enabled });
    setExternalAgents(prev => 
      prev.map(a => a.config.id === id ? result : a)
    );
  };
  
  const handleDeleteAgent = async (id: string) => {
    if (!confirm('이 에이전트 연결을 삭제하시겠습니까?')) return;
    await deleteAgentConfig(id);
    setExternalAgents(prev => prev.filter(a => a.config.id !== id));
  };
  
  // Server config handlers
  const handleAddServer = async (config: Partial<A2AServerConfig>) => {
    const result = await createServerConfig(config);
    setServerConfigs(prev => [...prev, result]);
  };
  
  const handleToggleServer = async (id: string, enabled: boolean) => {
    // TODO: Implement update
    setServerConfigs(prev => 
      prev.map(s => s.config.id === id 
        ? { ...s, config: { ...s.config, enabled } } 
        : s
      )
    );
  };
  
  const handleDeleteServer = async (id: string) => {
    if (!confirm('이 서버 설정을 삭제하시겠습니까?')) return;
    await deleteServerConfig(id);
    setServerConfigs(prev => prev.filter(s => s.config.id !== id));
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }
  
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">A2A 프로토콜 설정</h1>
        <p className="text-muted-foreground mt-1">
          Google A2A 프로토콜을 통해 외부 에이전트와 연동하거나, 
          로컬 에이전트를 외부에 노출할 수 있습니다.
        </p>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="mb-4">
          <TabsTrigger value="external" className="gap-2">
            <Globe className="w-4 h-4" />
            외부 에이전트 연결
          </TabsTrigger>
          <TabsTrigger value="server" className="gap-2">
            <Server className="w-4 h-4" />
            A2A 서버 노출
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="external">
          <div className="mb-4 flex justify-between items-center">
            <p className="text-sm text-muted-foreground">
              외부 A2A 에이전트에 연결하여 기능을 활용합니다.
            </p>
            <Button onClick={() => setAddAgentOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              에이전트 추가
            </Button>
          </div>
          
          {externalAgents.length === 0 ? (
            <Card className="p-8 text-center">
              <Globe className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="font-medium mb-2">연결된 외부 에이전트가 없습니다</h3>
              <p className="text-sm text-muted-foreground mb-4">
                A2A 프로토콜을 지원하는 외부 에이전트를 추가하세요.
              </p>
              <Button onClick={() => setAddAgentOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                첫 에이전트 추가
              </Button>
            </Card>
          ) : (
            externalAgents.map(agent => (
              <ExternalAgentCard
                key={agent.config.id}
                agent={agent}
                onTest={() => handleTestAgent(agent.config.id)}
                onDelete={() => handleDeleteAgent(agent.config.id)}
                onToggle={(enabled) => handleToggleAgent(agent.config.id, enabled)}
                testing={testingId === agent.config.id}
              />
            ))
          )}
        </TabsContent>
        
        <TabsContent value="server">
          <div className="mb-4 flex justify-between items-center">
            <p className="text-sm text-muted-foreground">
              로컬 에이전트/워크플로우를 A2A 프로토콜로 외부에 노출합니다.
            </p>
            <Button onClick={() => setAddServerOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              서버 설정 추가
            </Button>
          </div>
          
          {serverConfigs.length === 0 ? (
            <Card className="p-8 text-center">
              <Server className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="font-medium mb-2">A2A 서버 설정이 없습니다</h3>
              <p className="text-sm text-muted-foreground mb-4">
                로컬 에이전트를 외부에서 접근할 수 있도록 노출하세요.
              </p>
              <Button onClick={() => setAddServerOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                첫 서버 설정 추가
              </Button>
            </Card>
          ) : (
            serverConfigs.map(server => (
              <ServerConfigCard
                key={server.config.id}
                server={server}
                onDelete={() => handleDeleteServer(server.config.id)}
                onToggle={(enabled) => handleToggleServer(server.config.id, enabled)}
              />
            ))
          )}
        </TabsContent>
      </Tabs>
      
      <AddExternalAgentDialog
        open={addAgentOpen}
        onOpenChange={setAddAgentOpen}
        onAdd={handleAddAgent}
      />
      
      <AddServerConfigDialog
        open={addServerOpen}
        onOpenChange={setAddServerOpen}
        onAdd={handleAddServer}
        agents={localAgents}
        workflows={localWorkflows}
      />
    </div>
  );
}
