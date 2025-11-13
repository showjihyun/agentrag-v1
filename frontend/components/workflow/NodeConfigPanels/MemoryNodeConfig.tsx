'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface MemoryNodeConfigProps {
  data: {
    memoryType?: 'short_term' | 'long_term' | 'entity' | 'contextual';
    operation?: 'store' | 'retrieve' | 'update' | 'clear';
    key?: string;
    value?: string;
    ttl?: number;
    namespace?: string;
  };
  onChange: (data: any) => void;
}

export default function MemoryNodeConfig({ data, onChange }: MemoryNodeConfigProps) {
  const [memoryType, setMemoryType] = useState<'short_term' | 'long_term' | 'entity' | 'contextual'>(
    data.memoryType || 'short_term'
  );
  const [operation, setOperation] = useState<'store' | 'retrieve' | 'update' | 'clear'>(
    data.operation || 'store'
  );
  const [key, setKey] = useState(data.key || '');
  const [value, setValue] = useState(data.value || '');
  const [ttl, setTtl] = useState(data.ttl || 3600);
  const [namespace, setNamespace] = useState(data.namespace || 'default');

  const handleMemoryTypeChange = (value: 'short_term' | 'long_term' | 'entity' | 'contextual') => {
    setMemoryType(value);
    onChange({ ...data, memoryType: value });
  };

  const handleOperationChange = (value: 'store' | 'retrieve' | 'update' | 'clear') => {
    setOperation(value);
    onChange({ ...data, operation: value });
  };

  const handleKeyChange = (value: string) => {
    setKey(value);
    onChange({ ...data, key: value });
  };

  const handleValueChange = (value: string) => {
    setValue(value);
    onChange({ ...data, value: value });
  };

  const handleTtlChange = (value: string) => {
    const num = parseInt(value) || 3600;
    setTtl(num);
    onChange({ ...data, ttl: num });
  };

  const handleNamespaceChange = (value: string) => {
    setNamespace(value);
    onChange({ ...data, namespace: value });
  };

  return (
    <div className="space-y-4">
      <div className="bg-pink-50 border border-pink-200 rounded-lg p-3">
        <p className="text-xs text-pink-800 mb-2">
          <strong>Memory System:</strong>
        </p>
        <ul className="text-xs text-pink-700 space-y-1 ml-4 list-disc">
          <li><strong>STM:</strong> Temporary data for current execution</li>
          <li><strong>LTM:</strong> Persistent data across executions</li>
          <li><strong>Entity:</strong> Information about specific entities</li>
          <li><strong>Context:</strong> Conversation/workflow context</li>
        </ul>
      </div>

      <div>
        <Label>Memory Type</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {(['short_term', 'long_term', 'entity', 'contextual'] as const).map((type) => (
            <button
              key={type}
              onClick={() => handleMemoryTypeChange(type)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                memoryType === type
                  ? 'bg-pink-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {type === 'short_term' && 'Short Term'}
              {type === 'long_term' && 'Long Term'}
              {type === 'entity' && 'Entity'}
              {type === 'contextual' && 'Contextual'}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Operation</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {(['store', 'retrieve', 'update', 'clear'] as const).map((op) => (
            <button
              key={op}
              onClick={() => handleOperationChange(op)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                operation === op
                  ? 'bg-pink-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {op}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Namespace</Label>
        <Input
          value={namespace}
          onChange={(e) => handleNamespaceChange(e.target.value)}
          placeholder="default"
        />
        <p className="text-xs text-gray-500 mt-1">
          Organize memories by namespace (e.g., user_123, session_abc)
        </p>
      </div>

      {(operation === 'store' || operation === 'retrieve' || operation === 'update') && (
        <div>
          <Label>Key</Label>
          <Input
            value={key}
            onChange={(e) => handleKeyChange(e.target.value)}
            placeholder="memory_key"
            className="font-mono"
          />
          <p className="text-xs text-gray-500 mt-1">
            Use {'{{$json.field}}'} for dynamic keys
          </p>
        </div>
      )}

      {(operation === 'store' || operation === 'update') && (
        <div>
          <Label>Value</Label>
          <textarea
            value={value}
            onChange={(e) => handleValueChange(e.target.value)}
            className="w-full h-24 p-3 border rounded-lg text-sm resize-none font-mono"
            placeholder="{{$json}} or custom value"
          />
        </div>
      )}

      {memoryType === 'short_term' && (operation === 'store' || operation === 'update') && (
        <div>
          <Label>TTL (Time To Live)</Label>
          <div className="flex gap-2 items-center">
            <Input
              type="number"
              min="60"
              value={ttl}
              onChange={(e) => handleTtlChange(e.target.value)}
              className="w-32"
            />
            <span className="text-sm text-gray-600">seconds</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            How long to keep this memory (default: 1 hour)
          </p>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800 font-medium mb-2">
          Use Cases:
        </p>
        <ul className="text-xs text-blue-700 space-y-1 ml-4 list-disc">
          <li><strong>STM:</strong> Cache API responses, temporary calculations</li>
          <li><strong>LTM:</strong> User preferences, learned patterns</li>
          <li><strong>Entity:</strong> Customer info, product details</li>
          <li><strong>Context:</strong> Conversation history, workflow state</li>
        </ul>
      </div>
    </div>
  );
}
