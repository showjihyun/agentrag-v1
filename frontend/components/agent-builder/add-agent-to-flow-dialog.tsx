'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2, Search, Bot } from 'lucide-react';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface AddAgentToFlowDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  agentflowId: string;
  onAgentAdded: () => void;
}

const AGENT_ROLES = [
  { value: 'manager', label: 'Manager', description: 'Coordinates other agents' },
  { value: 'worker', label: 'Worker', description: 'Executes specific tasks' },
  { value: 'researcher', label: 'Researcher', description: 'Gathers information' },
  { value: 'analyst', label: 'Analyst', description: 'Analyzes data' },
  { value: 'writer', label: 'Writer', description: 'Creates content' },
  { value: 'reviewer', label: 'Reviewer', description: 'Reviews and validates' },
  { value: 'critic', label: 'Critic', description: 'Provides feedback' },
  { value: 'synthesizer', label: 'Synthesizer', description: 'Combines results' },
];

export function AddAgentToFlowDialog({
  open,
  onOpenChange,
  agentflowId,
  onAgentAdded,
}: AddAgentToFlowDialogProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [role, setRole] = useState('worker');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState(1);
  const [maxRetries, setMaxRetries] = useState(3);
  const [timeoutSeconds, setTimeoutSeconds] = useState(60);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch available agents
  const { data: agentsData, isLoading } = useQuery({
    queryKey: ['agents', searchQuery],
    queryFn: () => agentBuilderAPI.getAgents({ search: searchQuery, page_size: 50 }),
    enabled: open,
  });

  const agents = agentsData?.agents || [];
  const selectedAgent = agents.find((a) => a.id === selectedAgentId);

  const handleSubmit = async () => {
    if (!selectedAgentId || !role) return;

    setIsSubmitting(true);
    try {
      const { FlowsAPI } = await import('@/lib/api/flows');
      const api = new FlowsAPI();

      await api.addAgentToAgentflow(agentflowId, {
        agent_id: selectedAgentId,
        role,
        name: name || selectedAgent?.name || '',
        description: description || selectedAgent?.description || '',
        priority,
        max_retries: maxRetries,
        timeout_seconds: timeoutSeconds,
        capabilities: selectedAgent?.tools?.map((t) => t.name).filter((name): name is string => name != null) || [],
      });

      onAgentAdded();
      onOpenChange(false);
      
      // Reset form
      setSelectedAgentId('');
      setRole('worker');
      setName('');
      setDescription('');
      setPriority(1);
      setMaxRetries(3);
      setTimeoutSeconds(60);
    } catch (error) {
      console.error('Failed to add agent:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Add Agent to Agentflow</DialogTitle>
          <DialogDescription>
            Select an agent and configure its role in the agentflow
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="space-y-6">
            {/* Agent Selection */}
            <div className="space-y-2">
              <Label>Select Agent</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search agents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>

              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-2 mt-2">
                  {agents.map((agent) => (
                    <div
                      key={agent.id}
                      onClick={() => {
                        setSelectedAgentId(agent.id);
                        setName(agent.name);
                        setDescription(agent.description || '');
                      }}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedAgentId === agent.id
                          ? 'border-primary bg-primary/5'
                          : 'hover:border-primary/50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                          <Bot className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium">{agent.name}</div>
                          <div className="text-sm text-muted-foreground line-clamp-1">
                            {agent.description || 'No description'}
                          </div>
                          <div className="flex gap-1 mt-1 flex-wrap">
                            <Badge variant="secondary" className="text-xs">
                              {agent.llm_provider}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {agent.llm_model}
                            </Badge>
                            {agent.tools && agent.tools.length > 0 && (
                              <Badge variant="outline" className="text-xs">
                                {agent.tools.length} tools
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {selectedAgentId && (
              <>
                {/* Role Selection */}
                <div className="space-y-2">
                  <Label>Role in Agentflow</Label>
                  <Select value={role} onValueChange={setRole}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {AGENT_ROLES.map((r) => (
                        <SelectItem key={r.value} value={r.value}>
                          <div>
                            <div className="font-medium">{r.label}</div>
                            <div className="text-xs text-muted-foreground">{r.description}</div>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Name Override */}
                <div className="space-y-2">
                  <Label>Display Name (optional)</Label>
                  <Input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Override agent name in this flow"
                  />
                </div>

                {/* Description Override */}
                <div className="space-y-2">
                  <Label>Description (optional)</Label>
                  <Textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Describe this agent's role in the flow"
                    rows={2}
                  />
                </div>

                {/* Advanced Settings */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label>Priority</Label>
                    <Input
                      type="number"
                      value={priority}
                      onChange={(e) => setPriority(parseInt(e.target.value))}
                      min={1}
                    />
                    <p className="text-xs text-muted-foreground">Lower = earlier execution</p>
                  </div>

                  <div className="space-y-2">
                    <Label>Max Retries</Label>
                    <Input
                      type="number"
                      value={maxRetries}
                      onChange={(e) => setMaxRetries(parseInt(e.target.value))}
                      min={0}
                      max={10}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Timeout (seconds)</Label>
                    <Input
                      type="number"
                      value={timeoutSeconds}
                      onChange={(e) => setTimeoutSeconds(parseInt(e.target.value))}
                      min={10}
                      max={600}
                    />
                  </div>
                </div>
              </>
            )}
          </div>
        </ScrollArea>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!selectedAgentId || !role || isSubmitting}
          >
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Add Agent
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
