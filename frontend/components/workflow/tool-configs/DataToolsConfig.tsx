'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Database, TestTube, Key, Cloud, Server, HardDrive } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

interface DataToolConfig {
  toolType: string;
  // Connection
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  ssl: boolean;
  // Query/Operation
  operation: string;
  query: string;
  collection: string;
  index: string;
  // Data
  data: string;
  // Cloud specific
  region: string;
  bucket: string;
  apiKey: string;
  projectId: string;
  // Vector DB specific
  namespace: string;
  vectorField: string;
  topK: number;
}

const DATA_TOOLS = [
  { id: 'mongodb_insert', name: 'MongoDB', icon: Database, color: 'bg-green-100 text-green-600', type: 'nosql' },
  { id: 'redis_set', name: 'Redis', icon: Server, color: 'bg-red-100 text-red-600', type: 'cache' },
  { id: 'elasticsearch_index', name: 'Elasticsearch', icon: Database, color: 'bg-yellow-100 text-yellow-600', type: 'search' },
  { id: 'supabase_query', name: 'Supabase', icon: Cloud, color: 'bg-emerald-100 text-emerald-600', type: 'cloud' },
  { id: 'bigquery_query', name: 'BigQuery', icon: Cloud, color: 'bg-blue-100 text-blue-600', type: 'cloud' },
  { id: 'pinecone_upsert', name: 'Pinecone', icon: HardDrive, color: 'bg-purple-100 text-purple-600', type: 'vector' },
  { id: 'qdrant_insert', name: 'Qdrant', icon: HardDrive, color: 'bg-pink-100 text-pink-600', type: 'vector' },
];

const OPERATIONS = {
  nosql: ['find', 'insert', 'update', 'delete', 'aggregate'],
  cache: ['get', 'set', 'delete', 'exists', 'expire', 'hget', 'hset'],
  search: ['search', 'index', 'delete', 'update'],
  cloud: ['query', 'insert', 'update', 'delete'],
  vector: ['upsert', 'query', 'delete', 'fetch'],
};

export default function DataToolsConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState<DataToolConfig>({
    toolType: data.toolType || data.tool_id || 'mongodb_insert',
    host: data.host || 'localhost',
    port: data.port || 27017,
    database: data.database || '',
    username: data.username || '',
    password: data.password || '',
    ssl: data.ssl ?? false,
    operation: data.operation || 'find',
    query: data.query || '',
    collection: data.collection || '',
    index: data.index || '',
    data: data.data || '{}',
    region: data.region || 'us-east-1',
    bucket: data.bucket || '',
    apiKey: data.apiKey || data.api_key || '',
    projectId: data.projectId || data.project_id || '',
    namespace: data.namespace || 'default',
    vectorField: data.vectorField || data.vector_field || 'embedding',
    topK: data.topK || data.top_k || 10,
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: keyof DataToolConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const currentTool = DATA_TOOLS.find(t => t.id === config.toolType) || DATA_TOOLS[0];
  const IconComponent = currentTool.icon;
  const operations = OPERATIONS[currentTool.type as keyof typeof OPERATIONS] || OPERATIONS.nosql;

  const isCloudTool = ['supabase_query', 'bigquery_query'].includes(config.toolType);
  const isVectorTool = ['pinecone_upsert', 'qdrant_insert'].includes(config.toolType);
  const isCacheTool = config.toolType === 'redis_set';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className={`p-2 rounded-lg ${currentTool.color}`}>
          <IconComponent className="h-5 w-5" />
        </div>
        <div>
          <h3 className="font-semibold">{currentTool.name}</h3>
          <p className="text-sm text-muted-foreground">
            {isVectorTool ? 'Vector database operations' : 
             isCacheTool ? 'Cache operations' : 
             'Database operations'}
          </p>
        </div>
        <Badge variant="secondary" className="ml-auto">{currentTool.type}</Badge>
      </div>

      {/* Tool Selection */}
      <div className="space-y-2">
        <Label>Data Store</Label>
        <Select value={config.toolType} onValueChange={(v) => updateConfig('toolType', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {DATA_TOOLS.map(tool => (
              <SelectItem key={tool.id} value={tool.id}>
                <div className="flex items-center gap-2">
                  <tool.icon className="h-4 w-4" />
                  {tool.name}
                  <Badge variant="outline" className="ml-2 text-xs">{tool.type}</Badge>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="connection" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="connection">Connection</TabsTrigger>
          <TabsTrigger value="operation">Operation</TabsTrigger>
          <TabsTrigger value="data">Data</TabsTrigger>
        </TabsList>

        {/* Connection Tab */}
        <TabsContent value="connection" className="space-y-4">
          {isCloudTool ? (
            <>
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  API Key / Service Account
                </Label>
                <Input
                  type="password"
                  placeholder="Enter API key"
                  value={config.apiKey}
                  onChange={(e) => updateConfig('apiKey', e.target.value)}
                />
              </div>

              {config.toolType === 'bigquery_query' && (
                <div className="space-y-2">
                  <Label>Project ID</Label>
                  <Input
                    placeholder="my-gcp-project"
                    value={config.projectId}
                    onChange={(e) => updateConfig('projectId', e.target.value)}
                  />
                </div>
              )}

              {config.toolType === 'supabase_query' && (
                <div className="space-y-2">
                  <Label>Supabase URL</Label>
                  <Input
                    placeholder="https://xxx.supabase.co"
                    value={config.host}
                    onChange={(e) => updateConfig('host', e.target.value)}
                  />
                </div>
              )}

              <div className="space-y-2">
                <Label>Region</Label>
                <Select value={config.region} onValueChange={(v) => updateConfig('region', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="us-east-1">US East (N. Virginia)</SelectItem>
                    <SelectItem value="us-west-2">US West (Oregon)</SelectItem>
                    <SelectItem value="eu-west-1">EU (Ireland)</SelectItem>
                    <SelectItem value="ap-northeast-1">Asia Pacific (Tokyo)</SelectItem>
                    <SelectItem value="ap-northeast-2">Asia Pacific (Seoul)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </>
          ) : isVectorTool ? (
            <>
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  API Key
                </Label>
                <Input
                  type="password"
                  placeholder="Enter API key"
                  value={config.apiKey}
                  onChange={(e) => updateConfig('apiKey', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Host / Environment</Label>
                <Input
                  placeholder={config.toolType === 'pinecone_upsert' ? 'xxx-xxx.svc.pinecone.io' : 'localhost:6333'}
                  value={config.host}
                  onChange={(e) => updateConfig('host', e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label>Namespace / Collection</Label>
                <Input
                  placeholder="default"
                  value={config.namespace}
                  onChange={(e) => updateConfig('namespace', e.target.value)}
                />
              </div>
            </>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Host</Label>
                  <Input
                    placeholder="localhost"
                    value={config.host}
                    onChange={(e) => updateConfig('host', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Port</Label>
                  <Input
                    type="number"
                    placeholder={isCacheTool ? '6379' : '27017'}
                    value={config.port}
                    onChange={(e) => updateConfig('port', parseInt(e.target.value) || 0)}
                  />
                </div>
              </div>

              {!isCacheTool && (
                <div className="space-y-2">
                  <Label>Database</Label>
                  <Input
                    placeholder="mydb"
                    value={config.database}
                    onChange={(e) => updateConfig('database', e.target.value)}
                  />
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Username</Label>
                  <Input
                    placeholder="username"
                    value={config.username}
                    onChange={(e) => updateConfig('username', e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Password</Label>
                  <Input
                    type="password"
                    placeholder="password"
                    value={config.password}
                    onChange={(e) => updateConfig('password', e.target.value)}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <Label>Use SSL/TLS</Label>
                <Switch
                  checked={config.ssl}
                  onCheckedChange={(v) => updateConfig('ssl', v)}
                />
              </div>
            </>
          )}
        </TabsContent>

        {/* Operation Tab */}
        <TabsContent value="operation" className="space-y-4">
          <div className="space-y-2">
            <Label>Operation</Label>
            <Select value={config.operation} onValueChange={(v) => updateConfig('operation', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {operations.map(op => (
                  <SelectItem key={op} value={op}>
                    {op.charAt(0).toUpperCase() + op.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {!isCacheTool && !isVectorTool && (
            <div className="space-y-2">
              <Label>Collection / Table</Label>
              <Input
                placeholder="users"
                value={config.collection}
                onChange={(e) => updateConfig('collection', e.target.value)}
              />
            </div>
          )}

          {config.toolType === 'elasticsearch_index' && (
            <div className="space-y-2">
              <Label>Index</Label>
              <Input
                placeholder="my-index"
                value={config.index}
                onChange={(e) => updateConfig('index', e.target.value)}
              />
            </div>
          )}

          {isVectorTool && (
            <>
              <div className="space-y-2">
                <Label>Vector Field</Label>
                <Input
                  placeholder="embedding"
                  value={config.vectorField}
                  onChange={(e) => updateConfig('vectorField', e.target.value)}
                />
              </div>

              {config.operation === 'query' && (
                <div className="space-y-2">
                  <Label>Top K Results: {config.topK}</Label>
                  <Input
                    type="number"
                    min={1}
                    max={100}
                    value={config.topK}
                    onChange={(e) => updateConfig('topK', parseInt(e.target.value) || 10)}
                  />
                </div>
              )}
            </>
          )}

          {isCacheTool && config.operation === 'expire' && (
            <div className="space-y-2">
              <Label>TTL (seconds)</Label>
              <Input
                type="number"
                placeholder="3600"
                value={config.port}
                onChange={(e) => updateConfig('port', parseInt(e.target.value) || 3600)}
              />
            </div>
          )}
        </TabsContent>

        {/* Data Tab */}
        <TabsContent value="data" className="space-y-4">
          {isCacheTool ? (
            <>
              <div className="space-y-2">
                <Label>Key</Label>
                <Input
                  placeholder="my-key or {{variable}}"
                  value={config.query}
                  onChange={(e) => updateConfig('query', e.target.value)}
                />
              </div>
              {['set', 'hset'].includes(config.operation) && (
                <div className="space-y-2">
                  <Label>Value</Label>
                  <Textarea
                    placeholder="Value to store"
                    value={config.data}
                    onChange={(e) => updateConfig('data', e.target.value)}
                    rows={4}
                  />
                </div>
              )}
            </>
          ) : isVectorTool ? (
            <>
              {config.operation === 'query' && (
                <div className="space-y-2">
                  <Label>Query Vector (JSON array)</Label>
                  <Textarea
                    placeholder="[0.1, 0.2, 0.3, ...] or {{embedding}}"
                    value={config.query}
                    onChange={(e) => updateConfig('query', e.target.value)}
                    rows={4}
                    className="font-mono text-sm"
                  />
                </div>
              )}
              {config.operation === 'upsert' && (
                <div className="space-y-2">
                  <Label>Vectors (JSON)</Label>
                  <Textarea
                    placeholder={'[\n  {"id": "1", "values": [0.1, ...], "metadata": {}}\n]'}
                    value={config.data}
                    onChange={(e) => updateConfig('data', e.target.value)}
                    rows={8}
                    className="font-mono text-sm"
                  />
                </div>
              )}
            </>
          ) : (
            <>
              <div className="space-y-2">
                <Label>Query / Filter</Label>
                <Textarea
                  placeholder={config.toolType === 'bigquery_query' 
                    ? 'SELECT * FROM dataset.table WHERE ...'
                    : '{"field": "value"}'}
                  value={config.query}
                  onChange={(e) => updateConfig('query', e.target.value)}
                  rows={4}
                  className="font-mono text-sm"
                />
              </div>

              {['insert', 'update', 'index'].includes(config.operation) && (
                <div className="space-y-2">
                  <Label>Data (JSON)</Label>
                  <Textarea
                    placeholder={'{\n  "field": "value"\n}'}
                    value={config.data}
                    onChange={(e) => updateConfig('data', e.target.value)}
                    rows={6}
                    className="font-mono text-sm"
                  />
                </div>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* Test Button */}
      {onTest && (
        <Button 
          onClick={onTest} 
          variant="outline" 
          className="w-full"
        >
          <TestTube className="h-4 w-4 mr-2" />
          Test Connection
        </Button>
      )}
    </div>
  );
}
