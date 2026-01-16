'use client';

/**
 * MCPServerSelector Component
 * 
 * MCP 서버를 선택하고 관리하는 직관적인 UI 컴포넌트
 * - 대표 MCP 서버 카드 목록
 * - 원클릭 선택/해제
 * - 연결 상태 표시
 */

import React, { useState, useEffect } from 'react';
import {
  Server,
  Check,
  X,
  Search,
  RefreshCw,
  Settings,
  ExternalLink,
  Zap,
  Database,
  Globe,
  FileText,
  Github,
  MessageSquare,
  Cloud,
  Code,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';

// MCP 서버 정의
export interface MCPServer {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  category: 'data' | 'communication' | 'development' | 'ai' | 'utility';
  command: string;
  args: string[];
  env?: Record<string, string>;
  requiresConfig?: boolean;
  configFields?: ConfigField[];
  popular?: boolean;
}

interface ConfigField {
  name: string;
  label: string;
  type: 'text' | 'password' | 'select';
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
}

export interface SelectedMCPServer {
  serverId: string;
  config: Record<string, string>;
  status: 'pending' | 'connecting' | 'connected' | 'error';
  error?: string;
}

// 대표 MCP 서버 목록
const POPULAR_MCP_SERVERS: MCPServer[] = [
  {
    id: 'filesystem',
    name: 'Filesystem',
    description: '로컬 파일 시스템 접근 및 관리',
    icon: <FileText className="h-5 w-5" />,
    category: 'utility',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/allowed/dir'],
    popular: true,
  },
  {
    id: 'github',
    name: 'GitHub',
    description: 'GitHub 저장소 및 이슈 관리',
    icon: <Github className="h-5 w-5" />,
    category: 'development',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-github'],
    requiresConfig: true,
    configFields: [
      { name: 'GITHUB_TOKEN', label: 'GitHub Token', type: 'password', required: true, placeholder: 'ghp_...' },
    ],
    popular: true,
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Slack 메시지 및 채널 관리',
    icon: <MessageSquare className="h-5 w-5" />,
    category: 'communication',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-slack'],
    requiresConfig: true,
    configFields: [
      { name: 'SLACK_BOT_TOKEN', label: 'Slack Bot Token', type: 'password', required: true, placeholder: 'xoxb-...' },
    ],
    popular: true,
  },
  {
    id: 'postgres',
    name: 'PostgreSQL',
    description: 'PostgreSQL 데이터베이스 쿼리',
    icon: <Database className="h-5 w-5" />,
    category: 'data',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-postgres'],
    requiresConfig: true,
    configFields: [
      { name: 'DATABASE_URL', label: 'Database URL', type: 'text', required: true, placeholder: 'postgresql://...' },
    ],
    popular: true,
  },
  {
    id: 'brave-search',
    name: 'Brave Search',
    description: '웹 검색 및 정보 수집',
    icon: <Globe className="h-5 w-5" />,
    category: 'utility',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-brave-search'],
    requiresConfig: true,
    configFields: [
      { name: 'BRAVE_API_KEY', label: 'Brave API Key', type: 'password', required: true },
    ],
    popular: true,
  },
  {
    id: 'puppeteer',
    name: 'Puppeteer',
    description: '웹 브라우저 자동화 및 스크래핑',
    icon: <Code className="h-5 w-5" />,
    category: 'development',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-puppeteer'],
  },
  {
    id: 'memory',
    name: 'Memory',
    description: '지식 그래프 기반 메모리 저장',
    icon: <Zap className="h-5 w-5" />,
    category: 'ai',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-memory'],
  },
  {
    id: 'sqlite',
    name: 'SQLite',
    description: 'SQLite 데이터베이스 관리',
    icon: <Database className="h-5 w-5" />,
    category: 'data',
    command: 'uvx',
    args: ['mcp-server-sqlite', '--db-path', '/path/to/db.sqlite'],
    requiresConfig: true,
    configFields: [
      { name: 'DB_PATH', label: 'Database Path', type: 'text', required: true, placeholder: '/path/to/database.sqlite' },
    ],
  },
];

const CATEGORY_LABELS: Record<string, { label: string; icon: React.ReactNode }> = {
  all: { label: '전체', icon: <Server className="h-4 w-4" /> },
  data: { label: '데이터', icon: <Database className="h-4 w-4" /> },
  communication: { label: '커뮤니케이션', icon: <MessageSquare className="h-4 w-4" /> },
  development: { label: '개발', icon: <Code className="h-4 w-4" /> },
  ai: { label: 'AI', icon: <Zap className="h-4 w-4" /> },
  utility: { label: '유틸리티', icon: <Settings className="h-4 w-4" /> },
};

interface MCPServerSelectorProps {
  selectedServers: SelectedMCPServer[];
  onServersChange: (servers: SelectedMCPServer[]) => void;
}

export function MCPServerSelector({
  selectedServers,
  onServersChange,
}: MCPServerSelectorProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [configServer, setConfigServer] = useState<MCPServer | null>(null);
  const [configValues, setConfigValues] = useState<Record<string, string>>({});

  const filteredServers = POPULAR_MCP_SERVERS.filter(server => {
    const matchesSearch = 
      server.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      server.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || server.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const isServerSelected = (serverId: string) => 
    selectedServers.some(s => s.serverId === serverId);

  const getServerStatus = (serverId: string) => 
    selectedServers.find(s => s.serverId === serverId)?.status;

  const handleToggleServer = (server: MCPServer) => {
    if (isServerSelected(server.id)) {
      // 선택 해제
      onServersChange(selectedServers.filter(s => s.serverId !== server.id));
    } else {
      // 선택 - 설정이 필요한 경우 다이얼로그 표시
      if (server.requiresConfig) {
        setConfigServer(server);
        setConfigValues({});
        setConfigDialogOpen(true);
      } else {
        onServersChange([
          ...selectedServers,
          { serverId: server.id, config: {}, status: 'pending' }
        ]);
      }
    }
  };

  const handleSaveConfig = () => {
    if (!configServer) return;
    
    onServersChange([
      ...selectedServers,
      { serverId: configServer.id, config: configValues, status: 'pending' }
    ]);
    
    setConfigDialogOpen(false);
    setConfigServer(null);
    setConfigValues({});
  };

  const getStatusIcon = (status?: SelectedMCPServer['status']) => {
    switch (status) {
      case 'connected':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'connecting':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              MCP 서버
            </CardTitle>
            <CardDescription>
              Agent가 사용할 MCP 서버를 선택하세요
            </CardDescription>
          </div>
          {selectedServers.length > 0 && (
            <Badge variant="secondary">
              {selectedServers.length}개 선택됨
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* 선택된 서버 요약 */}
        {selectedServers.length > 0 && (
          <div className="p-3 bg-primary/5 border border-primary/20 rounded-lg">
            <p className="text-sm font-medium mb-2">선택된 MCP 서버</p>
            <div className="flex flex-wrap gap-2">
              {selectedServers.map(selected => {
                const server = POPULAR_MCP_SERVERS.find(s => s.id === selected.serverId);
                return (
                  <Badge 
                    key={selected.serverId} 
                    variant="secondary"
                    className="gap-1 pr-1"
                  >
                    {getStatusIcon(selected.status)}
                    {server?.name || selected.serverId}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-4 w-4 ml-1 hover:bg-destructive/20"
                      onClick={() => onServersChange(selectedServers.filter(s => s.serverId !== selected.serverId))}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                );
              })}
            </div>
          </div>
        )}

        {/* 검색 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="MCP 서버 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* 카테고리 필터 */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {Object.entries(CATEGORY_LABELS).map(([key, { label, icon }]) => (
            <Button
              key={key}
              variant={selectedCategory === key ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(key)}
              className="flex-shrink-0"
            >
              {icon}
              <span className="ml-1">{label}</span>
            </Button>
          ))}
        </div>

        {/* 서버 목록 */}
        <ScrollArea className="h-[350px] pr-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {filteredServers.map(server => {
              const isSelected = isServerSelected(server.id);
              const status = getServerStatus(server.id);
              
              return (
                <TooltipProvider key={server.id}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Card
                        className={cn(
                          "cursor-pointer transition-all hover:shadow-md",
                          isSelected 
                            ? "border-primary bg-primary/5" 
                            : "hover:border-primary/50"
                        )}
                        onClick={() => handleToggleServer(server)}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start gap-3">
                            <div className={cn(
                              "p-2 rounded-lg",
                              isSelected 
                                ? "bg-primary text-primary-foreground" 
                                : "bg-muted"
                            )}>
                              {server.icon}
                            </div>
                            
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2">
                                <h4 className="font-medium text-sm">{server.name}</h4>
                                {server.popular && (
                                  <Badge variant="secondary" className="text-xs">인기</Badge>
                                )}
                                {isSelected && getStatusIcon(status)}
                              </div>
                              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                {server.description}
                              </p>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant="outline" className="text-xs">
                                  {CATEGORY_LABELS[server.category]?.label}
                                </Badge>
                                {server.requiresConfig && (
                                  <Badge variant="outline" className="text-xs">
                                    <Settings className="h-3 w-3 mr-1" />
                                    설정 필요
                                  </Badge>
                                )}
                              </div>
                            </div>
                            
                            {isSelected && (
                              <Check className="h-5 w-5 text-primary flex-shrink-0" />
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>클릭하여 {isSelected ? '해제' : '선택'}</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              );
            })}
          </div>
        </ScrollArea>

        {/* 설정 다이얼로그 */}
        <Dialog open={configDialogOpen} onOpenChange={setConfigDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {configServer?.icon}
                {configServer?.name} 설정
              </DialogTitle>
              <DialogDescription>
                {configServer?.description}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4 py-4">
              {configServer?.configFields?.map(field => (
                <div key={field.name}>
                  <label className="text-sm font-medium">
                    {field.label}
                    {field.required && <span className="text-destructive ml-1">*</span>}
                  </label>
                  <Input
                    type={field.type === 'password' ? 'password' : 'text'}
                    placeholder={field.placeholder}
                    value={configValues[field.name] || ''}
                    onChange={(e) => setConfigValues({
                      ...configValues,
                      [field.name]: e.target.value
                    })}
                    className="mt-1"
                  />
                </div>
              ))}
            </div>
            
            <DialogFooter>
              <Button variant="outline" onClick={() => setConfigDialogOpen(false)}>
                취소
              </Button>
              <Button onClick={handleSaveConfig}>
                추가
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}

export default MCPServerSelector;
