'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface DatabaseNodeConfigProps {
  data: {
    dbType?: 'postgresql' | 'mysql' | 'mongodb' | 'redis';
    operation?: 'query' | 'insert' | 'update' | 'delete';
    query?: string;
    collection?: string;
    document?: string;
  };
  onChange: (data: any) => void;
}

export default function DatabaseNodeConfig({ data, onChange }: DatabaseNodeConfigProps) {
  const [dbType, setDbType] = useState<'postgresql' | 'mysql' | 'mongodb' | 'redis'>(
    data.dbType || 'postgresql'
  );
  const [operation, setOperation] = useState<'query' | 'insert' | 'update' | 'delete'>(
    data.operation || 'query'
  );
  const [query, setQuery] = useState(data.query || '');
  const [collection, setCollection] = useState(data.collection || '');
  const [document, setDocument] = useState(data.document || '');

  const handleDbTypeChange = (value: 'postgresql' | 'mysql' | 'mongodb' | 'redis') => {
    setDbType(value);
    onChange({ ...data, dbType: value });
  };

  const handleOperationChange = (value: 'query' | 'insert' | 'update' | 'delete') => {
    setOperation(value);
    onChange({ ...data, operation: value });
  };

  const handleQueryChange = (value: string) => {
    setQuery(value);
    onChange({ ...data, query: value });
  };

  const handleCollectionChange = (value: string) => {
    setCollection(value);
    onChange({ ...data, collection: value });
  };

  const handleDocumentChange = (value: string) => {
    setDocument(value);
    onChange({ ...data, document: value });
  };

  const QUERY_TEMPLATES = {
    postgresql: {
      query: 'SELECT * FROM users WHERE id = {{$json.userId}}',
      insert: 'INSERT INTO users (name, email) VALUES ({{$json.name}}, {{$json.email}})',
      update: 'UPDATE users SET status = {{$json.status}} WHERE id = {{$json.userId}}',
      delete: 'DELETE FROM users WHERE id = {{$json.userId}}',
    },
    mysql: {
      query: 'SELECT * FROM users WHERE id = {{$json.userId}}',
      insert: 'INSERT INTO users (name, email) VALUES ({{$json.name}}, {{$json.email}})',
      update: 'UPDATE users SET status = {{$json.status}} WHERE id = {{$json.userId}}',
      delete: 'DELETE FROM users WHERE id = {{$json.userId}}',
    },
    mongodb: {
      query: '{"userId": "{{$json.userId}}"}',
      insert: '{"name": "{{$json.name}}", "email": "{{$json.email}}"}',
      update: '{"$set": {"status": "{{$json.status}}"}}',
      delete: '{"userId": "{{$json.userId}}"}',
    },
    redis: {
      query: 'GET {{$json.key}}',
      insert: 'SET {{$json.key}} {{$json.value}}',
      update: 'SET {{$json.key}} {{$json.value}}',
      delete: 'DEL {{$json.key}}',
    },
  };

  return (
    <div className="space-y-4">
      <div className="bg-cyan-50 border border-cyan-200 rounded-lg p-3">
        <p className="text-xs text-cyan-800">
          <strong>Setup:</strong> Add database credentials to API Keys
        </p>
      </div>

      <div>
        <Label>Database Type</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {(['postgresql', 'mysql', 'mongodb', 'redis'] as const).map((type) => (
            <button
              key={type}
              onClick={() => handleDbTypeChange(type)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize ${
                dbType === type ? 'bg-cyan-500 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Operation</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {(['query', 'insert', 'update', 'delete'] as const).map((op) => (
            <button
              key={op}
              onClick={() => handleOperationChange(op)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize ${
                operation === op ? 'bg-cyan-500 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              {op}
            </button>
          ))}
        </div>
      </div>

      {dbType === 'mongodb' && (
        <div>
          <Label>Collection</Label>
          <Input
            value={collection}
            onChange={(e) => handleCollectionChange(e.target.value)}
            placeholder="users"
          />
        </div>
      )}

      <div>
        <Label>{dbType === 'mongodb' ? 'Query/Document' : 'SQL Query'}</Label>
        <textarea
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          className="w-full h-32 p-3 border rounded-lg text-sm resize-none font-mono"
          placeholder={QUERY_TEMPLATES[dbType][operation]}
        />
        <button
          onClick={() => handleQueryChange(QUERY_TEMPLATES[dbType][operation])}
          className="text-xs text-blue-600 hover:text-blue-700 mt-1"
        >
          Load Template
        </button>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-xs text-yellow-800">
          <strong>Security:</strong> Use parameterized queries to prevent SQL injection
        </p>
      </div>
    </div>
  );
}
