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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/components/Toast';
import { agentBuilderAPI, type Agent } from '@/lib/api/agent-builder';
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
        search: debouncedSearch || undefined,
        agent_type: filterType !== 'all' ? filterType : undefined,
      }),
  });

  // Client-side filtering and sorting
  const filteredAndSortedAgents = React.useMemo(() => {
    let result = [...(data?.agents || [])];

    // Filter by status
    if (filterStatus !== 'all') {
      result = result.filter((agent: Agent) => {
        // You can add status field to Agent model
        // For now, we'll use a simple logic
        return true; // Placeholder
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
  }, [data?.agents, filterStatus, sortBy]);

  const agents = filteredAndSortedAgents;

  const handleCreateAgent = () => {
    router.push('/agent-builder/agents/new');
  };

  const handleEdit = (agentId: string) => {
    router.push(`/agent-builder/agents/${agentId}/edit`);
  };

  const handleClone = async (agentId: string) => {
    try {
      await agentBuilderAPI.cloneAgent(agentId);
      toast({
        title: 'Agent cloned',
        description: 'The agent has been cloned successfully.',
      });
      refetch();
    } catch (error) {
      toast({
        variant: 'destructive',
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
          <h1 className="text-3xl font-bold">Agents</h1>
          <p className="text-muted-foreground">
            Create and manage your AI agents
          </p>
        </div>
        <Button onClick={handleCreateAgent}>
          <Plus className="mr-2 h-4 w-4" />
          Create Agent
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4">
            <div className="flex gap-4 flex-wrap">
              <div className="relative flex-1 min-w-[300px]">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search agents by name or description..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                  <SelectItem value="template">From Template</SelectItem>
                </SelectContent>
              </Select>

              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="updated_desc">Recently Updated</SelectItem>
                  <SelectItem value="updated_asc">Least Recently Updated</SelectItem>
                  <SelectItem value="created_desc">Newest First</SelectItem>
                  <SelectItem value="created_asc">Oldest First</SelectItem>
                  <SelectItem value="name_asc">Name (A-Z)</SelectItem>
                  <SelectItem value="name_desc">Name (Z-A)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Active Filters */}
            {(filterType !== 'all' || filterStatus !== 'all' || searchQuery) && (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-muted-foreground">Active filters:</span>
                {searchQuery && (
                  <Badge variant="secondary" className="gap-1">
                    Search: {searchQuery}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() => setSearchQuery('')}
                    />
                  </Badge>
                )}
                {filterType !== 'all' && (
                  <Badge variant="secondary" className="gap-1">
                    Type: {filterType}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() => setFilterType('all')}
                    />
                  </Badge>
                )}
                {filterStatus !== 'all' && (
                  <Badge variant="secondary" className="gap-1">
                    Status: {filterStatus}
                    <X
                      className="h-3 w-3 cursor-pointer"
                      onClick={() => setFilterStatus('all')}
                    />
                  </Badge>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSearchQuery('');
                    setFilterType('all');
                    setFilterStatus('all');
                  }}
                >
                  Clear all
                </Button>
              </div>
            )}

            {/* Results count */}
            <div className="text-sm text-muted-foreground">
              Showing {agents.length} {agents.length === 1 ? 'agent' : 'agents'}
            </div>
          </div>
        </CardContent>
      </Card>

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
          <div className="rounded-full bg-muted p-3 mb-4">
            <Inbox className="h-6 w-6 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold mb-2">No agents yet</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Get started by creating your first agent
          </p>
          <Button onClick={handleCreateAgent}>
            <Plus className="mr-2 h-4 w-4" />
            Create Agent
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.map((agent: Agent) => (
            <Card key={agent.id} className="hover:shadow-lg transition-all hover:scale-[1.02] group">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <Avatar className="h-12 w-12 border-2 border-primary/20">
                      <AvatarFallback className="bg-gradient-to-br from-primary/20 to-primary/10 text-primary font-semibold">
                        {agent.name.substring(0, 2).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-base truncate">{agent.name}</CardTitle>
                        <Badge variant="outline" className="text-xs">
                          {agent.agent_type}
                        </Badge>
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
                      <Badge key={tool.id || tool.tool_id || index} variant="secondary" className="text-xs">
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

                {/* Stats - Placeholder for now */}
                <div className="grid grid-cols-3 gap-2 pt-2 border-t">
                  <div className="text-center">
                    <div className="text-lg font-semibold text-primary">0</div>
                    <div className="text-xs text-muted-foreground">Runs</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-green-600">0%</div>
                    <div className="text-xs text-muted-foreground">Success</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-semibold text-blue-600">0s</div>
                    <div className="text-xs text-muted-foreground">Avg Time</div>
                  </div>
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
          ))}
        </div>
      )}
    </div>
  );
}
