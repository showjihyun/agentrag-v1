'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Edit, Play } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { CacheWarmingSection } from '@/components/agent/CacheWarmingSection';

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (agentId) {
      loadAgent();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId]);

  const loadAgent = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getAgent(agentId);
      setAgent(data);
    } catch (error: any) {
      console.error('Failed to load agent:', error);
      
      // Check for permission error
      const errorData = error.response?.data || error;
      const isPermissionError = errorData.error === 'AGENT_PERMISSION_DENIED' || 
                                error.message?.includes('Permission denied');
      
      toast({
        title: isPermissionError ? 'Access Denied' : 'Error',
        description: isPermissionError 
          ? 'You do not have permission to view this agent'
          : error.message || 'Failed to load agent',
      });
      
      // Set agent to null to show "not found" message
      setAgent(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-12 w-64" />
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-12 text-center space-y-4">
            <div className="text-6xl">🔒</div>
            <div>
              <h3 className="text-lg font-semibold mb-2">Access Denied</h3>
              <p className="text-muted-foreground">
                You do not have permission to view this agent, or it does not exist.
              </p>
            </div>
            <Button
              onClick={() => router.push('/agent-builder/agents')}
            >
              Back to Agents
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/agent-builder/agents')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{agent.name}</h1>
            {agent.description && (
              <p className="text-muted-foreground mt-1">{agent.description}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/agent-builder/agents/${agentId}/test`)}
          >
            <Play className="mr-2 h-4 w-4" />
            Test
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push(`/agent-builder/agents/${agentId}/edit`)}
          >
            <Edit className="mr-2 h-4 w-4" />
            Edit
          </Button>
        </div>
      </div>

      {/* Agent Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Agent settings and parameters</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-sm font-medium text-muted-foreground">Type</div>
              <Badge variant="outline" className="mt-1">
                {agent.agent_type}
              </Badge>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">LLM Provider</div>
              <div className="mt-1">{agent.llm_provider}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Model</div>
              <div className="mt-1">{agent.llm_model}</div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Status</div>
              <Badge variant={agent.is_public ? 'default' : 'secondary'} className="mt-1">
                {agent.is_public ? 'Public' : 'Private'}
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Tools</CardTitle>
                <CardDescription>Available tools for this agent</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push(`/agent-builder/agents/${agentId}/tools`)}
              >
                <Edit className="mr-2 h-4 w-4" />
                Configure
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {agent.tools && agent.tools.length > 0 ? (
              <div className="space-y-2">
                {agent.tools.map((tool: any, index: number) => (
                  <div key={tool.tool_id || index} className="flex items-center gap-2 p-2 border rounded">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{tool.tool_id}</div>
                      {tool.configuration && Object.keys(tool.configuration).length > 0 && (
                        <div className="text-xs text-muted-foreground">
                          {Object.keys(tool.configuration).length} parameters configured
                        </div>
                      )}
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Order: {tool.order}
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <p className="text-sm text-muted-foreground mb-3">No tools configured</p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => router.push(`/agent-builder/agents/${agentId}/tools`)}
                >
                  Add Tools
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Cache Warming */}
      {agent.knowledgebases && agent.knowledgebases.length > 0 && (
        <CacheWarmingSection agentId={agentId} />
      )}

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-muted-foreground">Created</div>
              <div>{new Date(agent.created_at).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-muted-foreground">Last Updated</div>
              <div>{new Date(agent.updated_at).toLocaleString()}</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
