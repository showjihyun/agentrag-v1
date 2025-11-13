'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { Plus, Search, Zap, Clock, Webhook, Mail, Calendar, Database, Play, Pause, Trash2, Power, PowerOff } from 'lucide-react';

interface Trigger {
  id: string;
  name: string;
  description: string;
  type: 'manual' | 'schedule' | 'webhook' | 'email' | 'event' | 'database' | 'file' | 'api' | 'chat' | 'form';
  workflowId: string;
  workflowName: string;
  isActive: boolean;
  config: Record<string, any>;
  lastRun?: string;
  nextRun?: string;
  runCount: number;
}

const triggerIcons = {
  manual: Zap,
  schedule: Clock,
  webhook: Webhook,
  email: Mail,
  event: Calendar,
  database: Database,
  file: Mail,
  api: Zap,
  chat: Mail,
  form: Mail,
};

const triggerColors = {
  manual: 'bg-yellow-100 text-yellow-700',
  schedule: 'bg-blue-100 text-blue-700',
  webhook: 'bg-purple-100 text-purple-700',
  email: 'bg-green-100 text-green-700',
  event: 'bg-red-100 text-red-700',
  database: 'bg-indigo-100 text-indigo-700',
  file: 'bg-orange-100 text-orange-700',
  api: 'bg-violet-100 text-violet-700',
  chat: 'bg-cyan-100 text-cyan-700',
  form: 'bg-emerald-100 text-emerald-700',
};

export default function TriggersPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadTriggers();
  }, []);

  const loadTriggers = async () => {
    try {
      setLoading(true);
      
      // Load workflows and extract triggers from them
      const workflowsData = await agentBuilderAPI.getWorkflows();
      const workflows = workflowsData.workflows || [];
      
      // Extract triggers from workflows
      const extractedTriggers: Trigger[] = [];
      
      workflows.forEach((workflow: any) => {
        const nodes = workflow.graph_definition?.nodes || [];
        const triggerNodes = nodes.filter((node: any) => 
          node.node_type === 'trigger' || 
          node.configuration?.type === 'trigger' ||
          node.type === 'trigger'
        );
        
        triggerNodes.forEach((node: any) => {
          const config = node.configuration || node.data || {};
          extractedTriggers.push({
            id: node.id,
            name: config.name || 'Unnamed Trigger',
            description: config.description || '',
            type: config.triggerType || 'manual',
            workflowId: workflow.id,
            workflowName: workflow.name,
            isActive: workflow.is_active || false,
            config: config.config || {},
            runCount: 0, // TODO: Get from execution history
          });
        });
      });
      
      setTriggers(extractedTriggers);
    } catch (error: any) {
      console.error('Failed to load triggers:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load triggers',
      });
    } finally {
      setLoading(false);
    }
  };

  const toggleTrigger = async (triggerId: string) => {
    try {
      // TODO: API 호출
      setTriggers(triggers.map(t => 
        t.id === triggerId ? { ...t, isActive: !t.isActive } : t
      ));
      
      const trigger = triggers.find(t => t.id === triggerId);
      toast({
        title: 'Success',
        description: `Trigger ${trigger?.isActive ? 'deactivated' : 'activated'}`,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update trigger',
      });
    }
  };

  const runTrigger = async (triggerId: string) => {
    const trigger = triggers.find(t => t.id === triggerId);
    if (!trigger) return;

    try {
      toast({
        title: '⚡ Trigger Executing',
        description: `Running workflow: ${trigger.workflowName}`,
      });

      // Execute the workflow
      const result = await agentBuilderAPI.executeWorkflow(trigger.workflowId, {
        trigger_id: triggerId,
        trigger_type: trigger.type,
      });

      // Update trigger stats
      setTriggers(triggers.map(t => 
        t.id === triggerId ? { 
          ...t, 
          runCount: t.runCount + 1,
          lastRun: new Date().toISOString()
        } : t
      ));

      toast({
        title: '✅ Execution Started',
        description: `Workflow "${trigger.workflowName}" is now running`,
      });

      // Optionally navigate to execution details
      if (result.execution_id) {
        setTimeout(() => {
          router.push(`/agent-builder/workflows/${trigger.workflowId}?tab=executions`);
        }, 1000);
      }

    } catch (error: any) {
      console.error('Failed to execute trigger:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to execute trigger',
      });
    }
  };

  const deleteTrigger = async (triggerId: string) => {
    if (!confirm('Are you sure you want to delete this trigger?')) return;
    
    try {
      // TODO: API 호출
      setTriggers(triggers.filter(t => t.id !== triggerId));
      
      toast({
        title: 'Success',
        description: 'Trigger deleted',
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete trigger',
      });
    }
  };

  const filteredTriggers = triggers.filter(trigger =>
    trigger.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    trigger.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Triggers</h1>
          <p className="text-muted-foreground mt-1">
            Manage workflow triggers and automation
          </p>
        </div>
        <Button onClick={() => router.push('/agent-builder/workflows/new')}>
          <Plus className="mr-2 h-4 w-4" />
          Create Workflow with Trigger
        </Button>
      </div>

      {/* Search */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search triggers..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Triggers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{triggers.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Active</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {triggers.filter(t => t.isActive).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Inactive</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">
              {triggers.filter(t => !t.isActive).length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Runs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {triggers.reduce((sum, t) => sum + t.runCount, 0)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Triggers List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading triggers...</p>
        </div>
      ) : filteredTriggers.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Zap className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No triggers found</h3>
            <p className="text-muted-foreground mb-4">
              {searchQuery ? 'Try a different search term' : 'Create a workflow with triggers to get started'}
            </p>
            <Button onClick={() => router.push('/agent-builder/workflows/new')}>
              <Plus className="mr-2 h-4 w-4" />
              Create Workflow
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredTriggers.map((trigger) => {
            const Icon = triggerIcons[trigger.type];
            const colorClass = triggerColors[trigger.type];
            
            return (
              <Card key={trigger.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <div className={`p-2 rounded-lg ${colorClass}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <CardTitle className="text-lg">{trigger.name}</CardTitle>
                          <Badge variant={trigger.isActive ? 'default' : 'secondary'}>
                            {trigger.isActive ? 'Active' : 'Inactive'}
                          </Badge>
                          <Badge variant="outline" className="capitalize">
                            {trigger.type}
                          </Badge>
                        </div>
                        <CardDescription className="mt-1">
                          {trigger.description}
                        </CardDescription>
                        <div className="mt-2 text-sm text-muted-foreground">
                          Workflow: <span className="font-medium">{trigger.workflowName}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Run Trigger Button (Manual execution) */}
                      <Button
                        variant="default"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          runTrigger(trigger.id);
                        }}
                        title="Run workflow now"
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <Play className="h-4 w-4 mr-1" />
                        Run
                      </Button>
                      
                      {/* Toggle Active/Inactive */}
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleTrigger(trigger.id);
                        }}
                        title={trigger.isActive ? 'Deactivate' : 'Activate'}
                      >
                        {trigger.isActive ? (
                          <Power className="h-4 w-4 text-green-600" />
                        ) : (
                          <PowerOff className="h-4 w-4 text-gray-400" />
                        )}
                      </Button>
                      
                      {/* Delete Button */}
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteTrigger(trigger.id);
                        }}
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Run Count</div>
                      <div className="font-medium">{trigger.runCount}</div>
                    </div>
                    {trigger.lastRun && (
                      <div>
                        <div className="text-muted-foreground">Last Run</div>
                        <div className="font-medium">
                          {new Date(trigger.lastRun).toLocaleString()}
                        </div>
                      </div>
                    )}
                    {trigger.nextRun && (
                      <div>
                        <div className="text-muted-foreground">Next Run</div>
                        <div className="font-medium">
                          {new Date(trigger.nextRun).toLocaleString()}
                        </div>
                      </div>
                    )}
                    {trigger.type === 'schedule' && trigger.config.cronExpression && (
                      <div>
                        <div className="text-muted-foreground">Schedule</div>
                        <div className="font-mono text-xs">{trigger.config.cronExpression}</div>
                      </div>
                    )}
                    {trigger.type === 'webhook' && trigger.config.webhookUrl && (
                      <div className="col-span-2">
                        <div className="text-muted-foreground">Webhook URL</div>
                        <div className="font-mono text-xs truncate">{trigger.config.webhookUrl}</div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
