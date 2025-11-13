'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Plus, Trash2 } from 'lucide-react';

interface SubAgent {
  id: string;
  name: string;
  role: string;
  priority: number;
}

interface ManagerAgentConfigProps {
  data: {
    role?: string;
    goal?: string;
    delegationStrategy?: 'sequential' | 'parallel' | 'priority';
    subAgents?: SubAgent[];
    maxConcurrent?: number;
  };
  onChange: (data: any) => void;
}

export default function ManagerAgentConfig({ data, onChange }: ManagerAgentConfigProps) {
  const [role, setRole] = useState(data.role || 'Project Manager');
  const [goal, setGoal] = useState(data.goal || '');
  const [delegationStrategy, setDelegationStrategy] = useState<'sequential' | 'parallel' | 'priority'>(
    data.delegationStrategy || 'sequential'
  );
  const [subAgents, setSubAgents] = useState<SubAgent[]>(data.subAgents || []);
  const [maxConcurrent, setMaxConcurrent] = useState(data.maxConcurrent || 3);

  const handleRoleChange = (value: string) => {
    setRole(value);
    onChange({ ...data, role: value });
  };

  const handleGoalChange = (value: string) => {
    setGoal(value);
    onChange({ ...data, goal: value });
  };

  const handleStrategyChange = (value: 'sequential' | 'parallel' | 'priority') => {
    setDelegationStrategy(value);
    onChange({ ...data, delegationStrategy: value });
  };

  const handleMaxConcurrentChange = (value: string) => {
    const num = parseInt(value) || 1;
    setMaxConcurrent(num);
    onChange({ ...data, maxConcurrent: num });
  };

  const addSubAgent = () => {
    const newAgent: SubAgent = {
      id: `agent-${Date.now()}`,
      name: '',
      role: '',
      priority: subAgents.length + 1,
    };
    const newSubAgents = [...subAgents, newAgent];
    setSubAgents(newSubAgents);
    onChange({ ...data, subAgents: newSubAgents });
  };

  const updateSubAgent = (id: string, field: keyof SubAgent, value: any) => {
    const newSubAgents = subAgents.map((agent) =>
      agent.id === id ? { ...agent, [field]: value } : agent
    );
    setSubAgents(newSubAgents);
    onChange({ ...data, subAgents: newSubAgents });
  };

  const removeSubAgent = (id: string) => {
    const newSubAgents = subAgents.filter((agent) => agent.id !== id);
    setSubAgents(newSubAgents);
    onChange({ ...data, subAgents: newSubAgents });
  };

  const ROLE_TEMPLATES = [
    'Project Manager',
    'Team Lead',
    'Coordinator',
    'Orchestrator',
    'Supervisor',
  ];

  return (
    <div className="space-y-4">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-xs text-yellow-800 mb-2">
          <strong>Hierarchical Pattern:</strong>
        </p>
        <p className="text-xs text-yellow-700">
          Manager agent coordinates and delegates tasks to sub-agents based on their roles and capabilities.
        </p>
      </div>

      <div>
        <Label>Manager Role</Label>
        <Input
          value={role}
          onChange={(e) => handleRoleChange(e.target.value)}
          placeholder="Project Manager"
        />
        <div className="flex gap-1 mt-2 flex-wrap">
          {ROLE_TEMPLATES.map((template) => (
            <button
              key={template}
              onClick={() => handleRoleChange(template)}
              className="px-2 py-1 text-xs rounded border hover:bg-gray-50"
            >
              {template}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Goal</Label>
        <textarea
          value={goal}
          onChange={(e) => handleGoalChange(e.target.value)}
          className="w-full h-24 p-3 border rounded-lg text-sm resize-none"
          placeholder="Describe the overall goal this manager should achieve..."
        />
      </div>

      <div>
        <Label>Delegation Strategy</Label>
        <div className="grid grid-cols-3 gap-2 mt-2">
          <button
            onClick={() => handleStrategyChange('sequential')}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              delegationStrategy === 'sequential'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <div className="font-semibold">Sequential</div>
            <div className="text-xs opacity-80">One by one</div>
          </button>
          <button
            onClick={() => handleStrategyChange('parallel')}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              delegationStrategy === 'parallel'
                ? 'bg-green-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <div className="font-semibold">Parallel</div>
            <div className="text-xs opacity-80">All at once</div>
          </button>
          <button
            onClick={() => handleStrategyChange('priority')}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              delegationStrategy === 'priority'
                ? 'bg-purple-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <div className="font-semibold">Priority</div>
            <div className="text-xs opacity-80">By priority</div>
          </button>
        </div>
      </div>

      {delegationStrategy === 'parallel' && (
        <div>
          <Label>Max Concurrent Agents</Label>
          <Input
            type="number"
            min="1"
            max="10"
            value={maxConcurrent}
            onChange={(e) => handleMaxConcurrentChange(e.target.value)}
            className="w-24"
          />
          <p className="text-xs text-gray-500 mt-1">
            Maximum number of agents to run simultaneously
          </p>
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label>Sub-Agents</Label>
          <Button onClick={addSubAgent} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            Add Agent
          </Button>
        </div>

        <div className="space-y-3">
          {subAgents.length === 0 ? (
            <div className="text-sm text-gray-500 text-center py-4 border rounded-lg">
              No sub-agents defined. Click "Add Agent" to create one.
            </div>
          ) : (
            subAgents.map((agent, idx) => (
              <div key={agent.id} className="border rounded-lg p-3 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">
                    Agent {idx + 1}
                  </span>
                  <Button
                    onClick={() => removeSubAgent(agent.id)}
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0"
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>

                <div>
                  <Label className="text-xs">Name</Label>
                  <Input
                    value={agent.name}
                    onChange={(e) => updateSubAgent(agent.id, 'name', e.target.value)}
                    placeholder="Agent name"
                    className="text-sm"
                  />
                </div>

                <div>
                  <Label className="text-xs">Role/Specialty</Label>
                  <Input
                    value={agent.role}
                    onChange={(e) => updateSubAgent(agent.id, 'role', e.target.value)}
                    placeholder="e.g., Data Analyst, Researcher"
                    className="text-sm"
                  />
                </div>

                {delegationStrategy === 'priority' && (
                  <div>
                    <Label className="text-xs">Priority (1-10)</Label>
                    <Input
                      type="number"
                      min="1"
                      max="10"
                      value={agent.priority}
                      onChange={(e) =>
                        updateSubAgent(agent.id, 'priority', parseInt(e.target.value) || 1)
                      }
                      className="w-20 text-sm"
                    />
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800 font-medium mb-2">
          How it works:
        </p>
        <ul className="text-xs text-blue-700 space-y-1 ml-4 list-disc">
          <li>Manager analyzes the task and breaks it down</li>
          <li>Delegates sub-tasks to appropriate agents</li>
          <li>Monitors progress and handles failures</li>
          <li>Aggregates results from all agents</li>
          <li>Returns final consolidated output</li>
        </ul>
      </div>
    </div>
  );
}
