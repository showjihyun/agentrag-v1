'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/Toast';
import { agentBuilderAPI, type Agent } from '@/lib/api/agent-builder';
import { AgentTemplateSelector } from '@/components/agent-builder/AgentTemplateSelector';
import { AgentBatchActions } from '@/components/agent-builder/AgentBatchActions';
import { AgentAdvancedFilters, type AgentFilters } from '@/components/agent-builder/AgentAdvancedFilters';
import { AgentMetricsDashboard } from '@/components/agent-builder/AgentMetricsDashboard';
import { AgentSharingDialog } from '@/components/agent-builder/AgentSharingDialog';
import {
  Plus,
  MoreVertical,
  Edit,
  Copy,
  Download,
  Trash,
  Play,
  Search,
  Inbox,
  X,
  Bot,
  Sparkles,
  BarChart3,
  Star,
  StarOff,
  Share,
  TrendingUp,
  Users,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function AgentsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterType, setFilterType] = React.useState('all');
  const [filterStatus, setFilterStatus] = React.useState('all');
  const [sortBy, setSortBy] = React.useState('updated_desc');
  const [debouncedSearch, setDebouncedSearch] = React.useState('');
  const [selectedAgents, setSelectedAgents] = React.useState<string[]>([]);
  const [showMetrics, setShowMetrics] = React.useState(false);
  const [favoriteAgents, setFavoriteAgents] = React.useState<Set<string>>(new Set());
  const [showRecommendations, setShowRecommendations] = React.useState(false);
  const [trendingAgents, setTrendingAgents] = React.useState<any[]>([]);
  const [personalizedRecommendations, setPersonalizedRecommendations] = React.useState<any[]>([]);
  
  // Advanced filters state
  const [advancedFilters, setAdvancedFilters] = React.useState<AgentFilters>({
    search: '',
    agent_type: [],
    llm_provider: [],
    tags: [],
    is_public: null,
    is_favorite: null,
    created_date_from: null,
    created_date_to: null,
    updated_date_from: null,
    updated_date_to: null,
    has_tools: null,
    has_knowledgebases: null,
    execution_status: [],
    complexity: [],
    orchestration_compatibility: [],
  });

  // Debounce search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['agents', debouncedSearch, filterType, filterStatus, sortBy],
    queryFn: () =>
      agentBuilderAPI.getAgents({
        ...(debouncedSearch && { search: debouncedSearch }),
        ...(filterType !== 'all' && { agent_type: filterType }),
      }),
  });

  // Fetch stats for each agent
  const [agentStats, setAgentStats] = React.useState<Record<string, any>>({});
  const [loadingStats, setLoadingStats] = React.useState(false);

  React.useEffect(() => {
    const fetchStats = async () => {
      if (data?.agents) {
        setLoadingStats(true);
        const stats: Record<string, any> = {};
        await Promise.all(
          data.agents.map(async (agent: Agent) => {
            try {
              const agentStat = await agentBuilderAPI.getAgentStats(agent.id);
              stats[agent.id] = agentStat;
            } catch (error) {
              // Ignore errors for individual agents
              stats[agent.id] = {
                total_runs: 0,
                success_rate: 0,
                avg_duration_ms: 0,
              };
            }
          })
        );
        setAgentStats(stats);
        setLoadingStats(false);
      }
    };
    fetchStats();
  }, [data?.agents]);

  // Fetch trending agents and recommendations
  React.useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const [trendingResponse, personalizedResponse] = await Promise.all([
          agentBuilderAPI.getTrendingAgents('7d', 5),
          agentBuilderAPI.getPersonalizedRecommendations(undefined, 5)
        ]);
        
        setTrendingAgents(trendingResponse || []);
        setPersonalizedRecommendations(personalizedResponse || []);
      } catch (error) {
        console.error('Failed to fetch recommendations:', error);
      }
    };

    if (showRecommendations) {
      fetchRecommendations();
    }
  }, [showRecommendations]);
  // Client-side filtering and sorting
  const filteredAndSortedAgents = React.useMemo(() => {
    let result = [...(data?.agents || [])];

    // Filter by status (based on statistics)
    if (filterStatus !== 'all') {
      result = result.filter((agent: Agent) => {
        const stats = agentStats[agent.id];
        if (!stats) return true; // Show all agents without stats
        
        // Determine status based on statistics
        if (filterStatus === 'active') {
          // Active: has runs and good success rate
          return stats.total_runs > 0 && stats.success_rate >= 50;
        } else if (filterStatus === 'archived') {
          // Archived: has runs but low success rate or not used recently
          return stats.total_runs > 0 && stats.success_rate < 50;
        }
        return true;
      });
    }

    // Sort
    result.sort((a: Agent, b: Agent) => {
      switch (sortBy) {
        case 'name_asc':
          return a.name.localeCompare(b.name);
        case 'name_desc':
          return b.name.localeCompare(a.name);
        case 'created_asc':
          return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
        case 'created_desc':
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
        case 'updated_asc':
          return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
        case 'updated_desc':
        default:
          return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      }
    });

    return result;
  }, [data?.agents, filterStatus, sortBy, agentStats]);

  const agents = filteredAndSortedAgents;

  const handleCreateAgent = () => {
    router.push('/agent-builder/agents/new');
  };

  const handleCreateFromTemplate = (template: any) => {
    // 템플릿 데이터를 쿼리 파라미터로 전달하여 새 Agent 생성 페이지로 이동
    const templateData = encodeURIComponent(JSON.stringify(template));
    router.push(`/agent-builder/agents/new?template=${templateData}`);
  };

  const handleToggleFavorite = async (agentId: string) => {
    try {
      const isFavorite = favoriteAgents.has(agentId);
      // API call to toggle favorite (mock for now)
      // await agentBuilderAPI.toggleFavorite(agentId, !isFavorite);
      
      const newFavorites = new Set(favoriteAgents);
      if (isFavorite) {
        newFavorites.delete(agentId);
      } else {
        newFavorites.add(agentId);
      }
      setFavoriteAgents(newFavorites);
      
      toast({
        title: isFavorite ? '즐겨찾기 해제' : '즐겨찾기 추가',
        description: `${isFavorite ? '즐겨찾기에서 제거' : '즐겨찾기에 추가'}되었습니다`,
      });
    } catch (error) {
      toast({
        title: '오류',
        description: '즐겨찾기 설정에 실패했습니다',
        variant: 'destructive',
      });
    }
  };

  const handleEdit = (agentId: string) => {
    router.push(`/agent-builder/agents/${agentId}/edit`);
  };

  const handleClone = async (agentId: string) => {
    try {
      const clonedAgent = await agentBuilderAPI.cloneAgent(agentId);
      toast({
        title: 'Agent cloned',
        description: 'The agent has been cloned successfully. Redirecting to edit...',
      });
      
      // Redirect to edit page after a short delay
      setTimeout(() => {
        router.push(`/agent-builder/agents/${clonedAgent.id}/edit`);
      }, 1000);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to clone agent.',
      });
    }
  };

  const handleExport = async (agentId: string) => {
    try {
      const data = await agentBuilderAPI.exportAgent(agentId);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `agent-${agentId}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast({
        title: 'Agent exported',
        description: 'The agent has been exported successfully.',
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to export agent.',
      });
    }
  };

  const handleDelete = async (agentId: string) => {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    
    try {
      await agentBuilderAPI.deleteAgent(agentId);
      toast({
        title: 'Agent deleted',
        description: 'The agent has been deleted successfully.',
      });
      refetch();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to delete agent.',
      });
    }
  };

  const handleTest = (agentId: string) => {
    router.push(`/agent-builder/agents/${agentId}/test`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            Agents
          </h1>
          <p className="text-muted-foreground">
            AI 에이전트를 생성하고 관리하여 강력한 워크플로우를 구축하세요
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            size="lg"
            onClick={() => setShowRecommendations(!showRecommendations)}
            className="shadow-md hover:shadow-lg transition-all"
          >
            <TrendingUp className="mr-2 h-4 w-4" />
            {showRecommendations ? 'AI 추천 숨기기' : 'AI 추천 보기'}
          </Button>
          <Button
            variant="outline"
            size="lg"
            onClick={() => setShowMetrics(!showMetrics)}
            className="shadow-md hover:shadow-lg transition-all"
          >
            <BarChart3 className="mr-2 h-4 w-4" />
            {showMetrics ? '메트릭 숨기기' : '메트릭 보기'}
          </Button>
          <AgentTemplateSelector
            onSelect={handleCreateFromTemplate}
            trigger={
              <Button variant="outline" size="lg" className="shadow-md hover:shadow-lg transition-all">
                <Sparkles className="mr-2 h-4 w-4" />
                템플릿에서 생성
              </Button>
            }
          />
          <Button onClick={handleCreateAgent} size="lg" className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-md hover:shadow-lg transition-all">
            <Plus className="mr-2 h-4 w-4" />
            새 Agent 생성
          </Button>
        </div>
      </div>

      {/* Metrics Dashboard */}
      {showMetrics && (
        <Card className="border-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              성능 대시보드
            </CardTitle>
            <CardDescription>
              전체 에이전트의 성능 메트릭과 사용 통계를 확인하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            <AgentMetricsDashboard />
          </CardContent>
        </Card>
      )}

      {/* AI Recommendations */}
      {showRecommendations && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Trending Agents */}
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                인기 상승 에이전트
              </CardTitle>
              <CardDescription>
                최근 7일간 가장 많이 사용되고 있는 에이전트들
              </CardDescription>
            </CardHeader>
            <CardContent>
              {trendingAgents.length > 0 ? (
                <div className="space-y-3">
                  {trendingAgents.map((item, index) => (
                    <div key={item.agent.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-gradient-to-r from-orange-500 to-red-500 text-white text-xs font-bold">
                        {index + 1}
                      </div>
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="text-xs">
                          {item.agent.name.substring(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{item.agent.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {item.execution_count}회 실행 • {Math.round(item.success_rate)}% 성공률
                        </p>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {item.agent.agent_type}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground">
                  <TrendingUp className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>트렌딩 데이터를 불러오는 중...</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Personalized Recommendations */}
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                맞춤 추천
              </CardTitle>
              <CardDescription>
                사용 패턴을 기반으로 추천하는 에이전트들
              </CardDescription>
            </CardHeader>
            <CardContent>
              {personalizedRecommendations.length > 0 ? (
                <div className="space-y-3">
                  {personalizedRecommendations.map((item) => (
                    <div key={item.agent.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 text-white text-xs font-bold">
                        {Math.round(item.score * 100)}
                      </div>
                      <Avatar className="h-8 w-8">
                        <AvatarFallback className="text-xs">
                          {item.agent.name.substring(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{item.agent.name}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {item.reasons.slice(0, 2).join(', ')}
                        </p>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        {item.agent.llm_provider}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground">
                  <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>추천 데이터를 불러오는 중...</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Advanced Filters */}
      <Card>
        <CardContent className="pt-6">
          <AgentAdvancedFilters
            filters={advancedFilters}
            onFiltersChange={setAdvancedFilters}
            availableTags={['AI', '분석', '콘텐츠', '검색', '번역', '관리', '자동화']}
            availableOrchestrationTypes={['sequential', 'parallel', 'hierarchical', 'consensus', 'adaptive']}
          />
        </CardContent>
      </Card>

      {/* Batch Actions */}
      <AgentBatchActions
        agents={agents}
        selectedAgents={selectedAgents}
        onSelectionChange={setSelectedAgents}
        onAgentsUpdated={refetch}
      />

      {/* Agent Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-center border-2 border-dashed rounded-lg">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900/20 dark:to-blue-900/20 rounded-full blur-3xl opacity-60" />
            <div className="relative rounded-full bg-muted p-6 mb-6">
              <Bot className="h-12 w-12 text-purple-500" />
            </div>
          </div>
          <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            첫 번째 Agent를 만들어보세요
          </h3>
          <p className="text-muted-foreground mb-6 max-w-md">
            템플릿을 사용하여 빠르게 시작하거나, 처음부터 직접 만들어보세요.<br />
            강력한 AI 워크플로우의 첫 걸음입니다.
          </p>
          <div className="flex gap-4">
            <AgentTemplateSelector
              onSelect={handleCreateFromTemplate}
              trigger={
                <Button variant="outline" size="lg" className="shadow-md hover:shadow-lg transition-all">
                  <Sparkles className="mr-2 h-4 w-4" />
                  템플릿에서 생성
                </Button>
              }
            />
            <Button onClick={handleCreateAgent} size="lg" className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-md hover:shadow-lg transition-all">
              <Plus className="mr-2 h-4 w-4" />
              새 Agent 생성
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent: Agent) => {
            const isSelected = selectedAgents.includes(agent.id);
            const isFavorite = favoriteAgents.has(agent.id);
            
            return (
              <Card 
                key={agent.id} 
                className={`hover:shadow-lg transition-all hover:scale-[1.02] group relative ${
                  isSelected ? 'ring-2 ring-purple-500 bg-purple-50 dark:bg-purple-950/20' : ''
                }`}
              >
                {/* Selection Checkbox */}
                <div className="absolute top-3 left-3 z-10">
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedAgents([...selectedAgents, agent.id]);
                      } else {
                        setSelectedAgents(selectedAgents.filter(id => id !== agent.id));
                      }
                    }}
                    className="bg-white dark:bg-gray-900 border-2"
                  />
                </div>

                {/* Favorite Button */}
                <div className="absolute top-3 right-12 z-10">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleFavorite(agent.id);
                    }}
                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    {isFavorite ? (
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ) : (
                      <StarOff className="h-4 w-4" />
                    )}
                  </Button>
                </div>

                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3 flex-1 ml-8">
                      <Avatar className="h-12 w-12 border-2 border-primary/20">
                        <AvatarFallback className="bg-gradient-to-br from-primary/20 to-primary/10 text-primary font-semibold">
                          {agent.name.substring(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <CardTitle className="text-base truncate">{agent.name}</CardTitle>
                          <Badge variant="outline" className="text-xs">
                            {agent.agent_type}
                          </Badge>
                          {isFavorite && (
                            <Badge className="text-xs bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300">
                              <Star className="h-3 w-3 mr-1" />
                              즐겨찾기
                            </Badge>
                          )}
                          {(() => {
                            const stats = agentStats[agent.id];
                            if (!stats || stats.total_runs === 0) {
                              return <Badge variant="secondary" className="text-xs">New</Badge>;
                            } else if (stats.success_rate >= 50) {
                              return <Badge variant="default" className="text-xs bg-green-600">Active</Badge>;
                            } else {
                              return <Badge variant="destructive" className="text-xs">Issues</Badge>;
                            }
                          })()}
                        </div>
                        <CardDescription className="text-xs mt-1">
                          {agent.llm_provider} • {agent.llm_model}
                        </CardDescription>
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleEdit(agent.id)}>
                          <Edit className="mr-2 h-4 w-4" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleClone(agent.id)}>
                          <Copy className="mr-2 h-4 w-4" />
                          Clone
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleExport(agent.id)}>
                          <Download className="mr-2 h-4 w-4" />
                          Export
                        </DropdownMenuItem>
                        <AgentSharingDialog
                          agentId={agent.id}
                          agentName={agent.name}
                          isPublic={agent.is_public}
                          trigger={
                            <DropdownMenuItem>
                              <Share className="mr-2 h-4 w-4" />
                              Share
                            </DropdownMenuItem>
                          }
                        />
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          onClick={() => handleDelete(agent.id)}
                          className="text-destructive"
                        >
                          <Trash className="mr-2 h-4 w-4" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground line-clamp-2 min-h-[40px]">
                  {agent.description || 'No description provided'}
                </p>

                {/* Tools */}
                {agent.tools && agent.tools.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {agent.tools.slice(0, 3).map((tool, index) => (
                      <Badge key={tool.id || index} variant="secondary" className="text-xs">
                        {tool.name || 'Tool'}
                      </Badge>
                    ))}
                    {agent.tools.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{agent.tools.length - 3} more
                      </Badge>
                    )}
                  </div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 pt-2 border-t">
                  {loadingStats ? (
                    <>
                      <div className="text-center">
                        <Skeleton className="h-6 w-12 mx-auto mb-1" />
                        <div className="text-xs text-muted-foreground">Runs</div>
                      </div>
                      <div className="text-center">
                        <Skeleton className="h-6 w-12 mx-auto mb-1" />
                        <div className="text-xs text-muted-foreground">Success</div>
                      </div>
                      <div className="text-center">
                        <Skeleton className="h-6 w-12 mx-auto mb-1" />
                        <div className="text-xs text-muted-foreground">Avg Time</div>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-primary">
                          {agentStats[agent.id]?.total_runs ?? 0}
                        </div>
                        <div className="text-xs text-muted-foreground">Runs</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-green-600">
                          {agentStats[agent.id]?.success_rate ?? 0}%
                        </div>
                        <div className="text-xs text-muted-foreground">Success</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-semibold text-blue-600">
                          {agentStats[agent.id]?.avg_duration_ms 
                            ? `${(agentStats[agent.id].avg_duration_ms / 1000).toFixed(1)}s`
                            : '0s'}
                        </div>
                        <div className="text-xs text-muted-foreground">Avg Time</div>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between items-center pt-4 border-t">
                <div className="flex items-center gap-2">
                  <div className="text-xs text-muted-foreground">
                    {formatDate(agent.updated_at)}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleTest(agent.id)}
                    className="gap-1"
                  >
                    <Play className="h-3 w-3" />
                    Test
                  </Button>
                </div>
              </CardFooter>
            </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
