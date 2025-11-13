'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface Agent {
  id: string;
  name: string;
  weight: number;
}

interface ConsensusNodeConfigProps {
  data: {
    consensusType?: 'majority' | 'unanimous' | 'weighted' | 'best';
    agents?: Agent[];
    threshold?: number;
    evaluationCriteria?: string;
  };
  onChange: (data: any) => void;
}

export default function ConsensusNodeConfig({ data, onChange }: ConsensusNodeConfigProps) {
  const [consensusType, setConsensusType] = useState<'majority' | 'unanimous' | 'weighted' | 'best'>(
    data.consensusType || 'majority'
  );
  const [agents, setAgents] = useState<Agent[]>(
    data.agents || [
      { id: '1', name: 'Agent 1', weight: 1 },
      { id: '2', name: 'Agent 2', weight: 1 },
      { id: '3', name: 'Agent 3', weight: 1 },
    ]
  );
  const [threshold, setThreshold] = useState(data.threshold || 0.5);
  const [evaluationCriteria, setEvaluationCriteria] = useState(data.evaluationCriteria || '');

  const handleConsensusTypeChange = (value: 'majority' | 'unanimous' | 'weighted' | 'best') => {
    setConsensusType(value);
    onChange({ ...data, consensusType: value });
  };

  const handleThresholdChange = (value: string) => {
    const num = parseFloat(value) || 0.5;
    setThreshold(num);
    onChange({ ...data, threshold: num });
  };

  const handleEvaluationCriteriaChange = (value: string) => {
    setEvaluationCriteria(value);
    onChange({ ...data, evaluationCriteria: value });
  };

  const updateAgentWeight = (id: string, weight: number) => {
    const newAgents = agents.map((agent) =>
      agent.id === id ? { ...agent, weight } : agent
    );
    setAgents(newAgents);
    onChange({ ...data, agents: newAgents });
  };

  return (
    <div className="space-y-4">
      <div className="bg-teal-50 border border-teal-200 rounded-lg p-3">
        <p className="text-xs text-teal-800 mb-2">
          <strong>Consensus Pattern:</strong>
        </p>
        <p className="text-xs text-teal-700">
          Multiple agents work on the same task independently, then their results are combined using a consensus mechanism.
        </p>
      </div>

      <div>
        <Label>Consensus Type</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          <button
            onClick={() => handleConsensusTypeChange('majority')}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              consensusType === 'majority'
                ? 'bg-teal-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <div className="font-semibold">Majority</div>
            <div className="text-xs opacity-80">Most common result</div>
          </button>
          <button
            onClick={() => handleConsensusTypeChange('unanimous')}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              consensusType === 'unanimous'
                ? 'bg-teal-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <div className="font-semibold">Unanimous</div>
            <div className="text-xs opacity-80">All must agree</div>
          </button>
          <button
            onClick={() => handleConsensusTypeChange('weighted')}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              consensusType === 'weighted'
                ? 'bg-teal-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <div className="font-semibold">Weighted</div>
            <div className="text-xs opacity-80">By agent weight</div>
          </button>
          <button
            onClick={() => handleConsensusTypeChange('best')}
            className={`px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
              consensusType === 'best'
                ? 'bg-teal-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            <div className="font-semibold">Best Result</div>
            <div className="text-xs opacity-80">Highest quality</div>
          </button>
        </div>
      </div>

      {consensusType === 'majority' && (
        <div>
          <Label>Threshold</Label>
          <div className="flex gap-2 items-center">
            <Input
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={threshold}
              onChange={(e) => handleThresholdChange(e.target.value)}
              className="w-24"
            />
            <span className="text-sm text-gray-600">
              ({Math.round(threshold * 100)}%)
            </span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Minimum agreement ratio required (0.5 = 50%)
          </p>
        </div>
      )}

      {consensusType === 'weighted' && (
        <div>
          <Label>Agent Weights</Label>
          <div className="space-y-2 mt-2">
            {agents.map((agent) => (
              <div key={agent.id} className="flex items-center gap-2">
                <span className="text-sm text-gray-700 w-20">{agent.name}</span>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  step="0.1"
                  value={agent.weight}
                  onChange={(e) =>
                    updateAgentWeight(agent.id, parseFloat(e.target.value) || 1)
                  }
                  className="w-24"
                />
                <span className="text-xs text-gray-500">weight</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {consensusType === 'best' && (
        <div>
          <Label>Evaluation Criteria</Label>
          <textarea
            value={evaluationCriteria}
            onChange={(e) => handleEvaluationCriteriaChange(e.target.value)}
            className="w-full h-24 p-3 border rounded-lg text-sm resize-none"
            placeholder="Describe how to evaluate which result is best..."
          />
          <p className="text-xs text-gray-500 mt-1">
            e.g., "Most detailed answer", "Highest confidence score", "Best matches criteria X"
          </p>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800 font-medium mb-2">
          How it works:
        </p>
        <ul className="text-xs text-blue-700 space-y-1 ml-4 list-disc">
          <li>All agents receive the same input</li>
          <li>Agents work independently in parallel</li>
          <li>Results are collected and compared</li>
          <li>Consensus mechanism selects final output</li>
          <li>Disagreements are logged for review</li>
        </ul>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <p className="text-xs text-green-800 font-medium mb-2">
          Use Cases:
        </p>
        <ul className="text-xs text-green-700 space-y-1 ml-4 list-disc">
          <li>Critical decisions requiring validation</li>
          <li>Quality assurance and fact-checking</li>
          <li>Reducing hallucinations in LLM outputs</li>
          <li>Combining diverse perspectives</li>
        </ul>
      </div>
    </div>
  );
}
