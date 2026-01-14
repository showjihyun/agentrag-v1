'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search, Bot, Zap, Settings, Plus, Check } from 'lucide-react';
import { agentBuilderAPI, Agent } from '@/lib/api/agent-builder';

interface AgentSelectorProps {
  onSelect: (agent: Agent) => void;
  selectedAgentIds?: string[];
  trigger?: React.ReactNode;
  orchestrationType?: string;
  preferredRoles?: string[];
}

export function AgentSelector({ 
  onSelect, 
  selectedAgentIds = [], 
  trigger, 
  orchestrationType,
  preferredRoles = []
}: AgentSelectorProps) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [agentType, setAgentType] = useState<string>('');
  const [page, setPage] = useState(1);

  const { data: agentsData, isLoading } = useQuery({
    queryKey: ['available-agents', search, agentType, page],
    queryFn: () => agentBuilderAPI.getAgents({
      ...(search && { search }),
      ...(agentType && { agent_type: agentType }),
      page,
      page_size: 20,
    }),
    enabled: open,
  });

  const handleSelectAgent = (agent: Agent) => {
    onSelect(agent);
    setOpen(false);
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'ollama':
        return '🦙';
      case 'openai':
        return '🤖';
      case 'anthropic':
        return '🧠';
      default:
        return '⚡';
    }
  };

  const getAgentTypeColor = (type: string) => {
    switch (type) {
      case 'custom':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'template_based':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Select Agent from Building Blocks
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Select Agent
            {orchestrationType && (
              <Badge variant="outline" className="ml-2">
                {orchestrationType} Optimized
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            {orchestrationType 
              ? `Select an agent suitable for ${orchestrationType} orchestration to add to your Agentflow team`
              : 'Select an agent created in Building Blocks to add to your AgentFlow team'
            }
          </DialogDescription>
        </DialogHeader>

        {/* Filters */}
        <div className="flex gap-4 mb-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by agent name..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <Select value={agentType} onValueChange={setAgentType}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Type Filter" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Types</SelectItem>
              <SelectItem value="custom">Custom</SelectItem>
              <SelectItem value="template_based">Template Based</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Agent List */}
        <ScrollArea className="h-[400px]">
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(6)].map((_, i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : agentsData?.agents?.length === 0 ? (
            <div className="text-center py-12">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-full blur-3xl opacity-60" />
                <div className="relative inline-flex items-center justify-center w-20 h-20 rounded-full bg-white dark:bg-gray-900 shadow-lg mb-6">
                  <Bot className="h-10 w-10 text-blue-500" />
                </div>
              </div>
              <h3 className="text-xl font-semibold mb-3">No Available Agents</h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                There are no agents available to add to Agentflow.<br />
                First create an agent in Building Blocks or try using a template.
              </p>
              <div className="flex gap-3 justify-center">
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setOpen(false);
                    window.open('/agent-builder/agents', '_blank');
                  }}
                  className="shadow-md hover:shadow-lg transition-all"
                >
                  <Bot className="h-4 w-4 mr-2" />
                  Go to Building Blocks
                </Button>
                <Button 
                  onClick={() => {
                    setOpen(false);
                    window.open('/agent-builder/agents/new', '_blank');
                  }}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 shadow-md hover:shadow-lg transition-all"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Create New Agent
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {/* Recommended agents section */}
              {orchestrationType && preferredRoles.length > 0 && (
                <div className="mb-4 p-3 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/20 dark:to-purple-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <h4 className="font-medium text-sm text-blue-700 dark:text-blue-300 mb-2">
                    🎯 Recommended Roles for {orchestrationType}
                  </h4>
                  <div className="flex flex-wrap gap-1">
                    {preferredRoles.map((role, index) => (
                      <Badge key={index} variant="outline" className="text-xs bg-white dark:bg-gray-900">
                        {role}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {agentsData?.agents
                ?.sort((a, b) => {
                  // Show agents matching recommended roles at the top
                  if (preferredRoles.length > 0) {
                    const aMatches = preferredRoles.some(role => 
                      a.name.toLowerCase().includes(role.toLowerCase()) ||
                      a.description?.toLowerCase().includes(role.toLowerCase())
                    );
                    const bMatches = preferredRoles.some(role => 
                      b.name.toLowerCase().includes(role.toLowerCase()) ||
                      b.description?.toLowerCase().includes(role.toLowerCase())
                    );
                    
                    if (aMatches && !bMatches) return -1;
                    if (!aMatches && bMatches) return 1;
                  }
                  
                  // Otherwise sort by creation date
                  return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
                })
                ?.map((agent) => {
                const isSelected = selectedAgentIds.includes(agent.id);
                const isRecommended = preferredRoles.length > 0 && preferredRoles.some(role => 
                  agent.name.toLowerCase().includes(role.toLowerCase()) ||
                  agent.description?.toLowerCase().includes(role.toLowerCase())
                );
                
                return (
                  <Card
                    key={agent.id}
                    className={`cursor-pointer transition-all duration-200 hover:shadow-md ${
                      isSelected
                        ? 'border-green-500 bg-green-50 dark:bg-green-950/20'
                        : isRecommended
                        ? 'border-blue-400 bg-blue-50 dark:bg-blue-950/20 hover:border-blue-500'
                        : 'hover:border-purple-300'
                    }`}
                    onClick={() => !isSelected && handleSelectAgent(agent)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-lg">
                                {getProviderIcon(agent.llm_provider)}
                              </span>
                              <h3 className="font-semibold">{agent.name}</h3>
                            </div>
                            <div className="flex gap-1">
                              <Badge className={getAgentTypeColor(agent.agent_type)}>
                                {agent.agent_type === 'custom' ? 'Custom' : 'Template Based'}
                              </Badge>
                              {isRecommended && (
                                <Badge className="bg-blue-500 hover:bg-blue-600 text-white">
                                  ⭐ Recommended
                                </Badge>
                              )}
                              {isSelected && (
                                <Badge className="bg-green-500 hover:bg-green-600">
                                  <Check className="h-3 w-3 mr-1" />
                                  Selected
                                </Badge>
                              )}
                            </div>
                          </div>
                          
                          {agent.description && (
                            <p className="text-sm text-muted-foreground mb-3">
                              {agent.description}
                            </p>
                          )}

                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Settings className="h-3 w-3" />
                              {agent.llm_provider} / {agent.llm_model}
                            </div>
                            <div className="flex items-center gap-1">
                              <Zap className="h-3 w-3" />
                              {agent.tools?.length || 0} tools
                            </div>
                          </div>

                          {/* Tools */}
                          {agent.tools && agent.tools.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-3">
                              {agent.tools.slice(0, 3).map((tool, index) => (
                                <Badge key={index} variant="outline" className="text-xs">
                                  {tool.name}
                                </Badge>
                              ))}
                              {agent.tools.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{agent.tools.length - 3} more
                                </Badge>
                              )}
                            </div>
                          )}

                          {/* Tools */}
                          {agent.tools && agent.tools.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {agent.tools.slice(0, 3).map((tool, index) => (
                                <Badge key={index} variant="secondary" className="text-xs">
                                  {tool.name || tool.id}
                                </Badge>
                              ))}
                              {agent.tools.length > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{agent.tools.length - 3} tools
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>

                        {!isSelected && (
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleSelectAgent(agent);
                            }}
                          >
                            Select
                          </Button>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </ScrollArea>

        {/* Pagination */}
        {agentsData && agentsData.total > 20 && (
          <div className="flex items-center justify-between pt-4 border-t">
            <p className="text-sm text-muted-foreground">
              Showing {((page - 1) * 20) + 1}-
              {Math.min(page * 20, agentsData.total)} of {agentsData.total}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page * 20 >= agentsData.total}
                onClick={() => setPage(page + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}