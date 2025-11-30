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
import { Cloud, TestTube, Key, Upload, Download, Trash, FolderOpen } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

interface S3Config {
  operation: string;
  bucket: string;
  key: string;
  region: string;
  accessKeyId: string;
  secretAccessKey: string;
  // Upload options
  contentType: string;
  acl: string;
  metadata: string;
  // Download options
  outputFormat: string;
  // List options
  prefix: string;
  maxKeys: number;
  // Advanced
  endpoint: string;
  usePathStyle: boolean;
}

const OPERATIONS = [
  { value: 'upload', label: 'Upload File', icon: Upload },
  { value: 'download', label: 'Download File', icon: Download },
  { value: 'delete', label: 'Delete File', icon: Trash },
  { value: 'list', label: 'List Files', icon: FolderOpen },
  { value: 'getSignedUrl', label: 'Get Signed URL', icon: Key },
];

const REGIONS = [
  { value: 'us-east-1', label: 'US East (N. Virginia)' },
  { value: 'us-east-2', label: 'US East (Ohio)' },
  { value: 'us-west-1', label: 'US West (N. California)' },
  { value: 'us-west-2', label: 'US West (Oregon)' },
  { value: 'eu-west-1', label: 'EU (Ireland)' },
  { value: 'eu-central-1', label: 'EU (Frankfurt)' },
  { value: 'ap-northeast-1', label: 'Asia Pacific (Tokyo)' },
  { value: 'ap-northeast-2', label: 'Asia Pacific (Seoul)' },
  { value: 'ap-southeast-1', label: 'Asia Pacific (Singapore)' },
];

const ACL_OPTIONS = [
  { value: 'private', label: 'Private' },
  { value: 'public-read', label: 'Public Read' },
  { value: 'public-read-write', label: 'Public Read/Write' },
  { value: 'authenticated-read', label: 'Authenticated Read' },
];

const CONTENT_TYPES = [
  'application/octet-stream',
  'application/json',
  'application/pdf',
  'text/plain',
  'text/csv',
  'image/png',
  'image/jpeg',
  'video/mp4',
];

export default function S3Config({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState<S3Config>({
    operation: data.operation || 'upload',
    bucket: data.bucket || '',
    key: data.key || '',
    region: data.region || 'us-east-1',
    accessKeyId: data.accessKeyId || data.access_key_id || '',
    secretAccessKey: data.secretAccessKey || data.secret_access_key || '',
    contentType: data.contentType || data.content_type || 'application/octet-stream',
    acl: data.acl || 'private',
    metadata: data.metadata || '{}',
    outputFormat: data.outputFormat || data.output_format || 'buffer',
    prefix: data.prefix || '',
    maxKeys: data.maxKeys || data.max_keys || 1000,
    endpoint: data.endpoint || '',
    usePathStyle: data.usePathStyle ?? data.use_path_style ?? false,
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: keyof S3Config, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const currentOp = OPERATIONS.find(op => op.value === config.operation) || OPERATIONS[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-950">
          <Cloud className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        </div>
        <div>
          <h3 className="font-semibold">Amazon S3</h3>
          <p className="text-sm text-muted-foreground">Cloud object storage operations</p>
        </div>
        <Badge variant="secondary" className="ml-auto">AWS</Badge>
      </div>

      {/* Operation Selection */}
      <div className="space-y-2">
        <Label>Operation</Label>
        <Select value={config.operation} onValueChange={(v) => updateConfig('operation', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {OPERATIONS.map(op => (
              <SelectItem key={op.value} value={op.value}>
                <div className="flex items-center gap-2">
                  <op.icon className="h-4 w-4" />
                  {op.label}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="bucket" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="bucket">Bucket</TabsTrigger>
          <TabsTrigger value="credentials">Credentials</TabsTrigger>
          <TabsTrigger value="options">Options</TabsTrigger>
        </TabsList>

        {/* Bucket Tab */}
        <TabsContent value="bucket" className="space-y-4">
          <div className="space-y-2">
            <Label>Bucket Name</Label>
            <Input
              placeholder="my-bucket"
              value={config.bucket}
              onChange={(e) => updateConfig('bucket', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Region</Label>
            <Select value={config.region} onValueChange={(v) => updateConfig('region', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {REGIONS.map(region => (
                  <SelectItem key={region.value} value={region.value}>
                    {region.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {config.operation !== 'list' && (
            <div className="space-y-2">
              <Label>Object Key (Path)</Label>
              <Input
                placeholder="folder/file.txt or {{variable}}"
                value={config.key}
                onChange={(e) => updateConfig('key', e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                The path to the object within the bucket
              </p>
            </div>
          )}

          {config.operation === 'list' && (
            <>
              <div className="space-y-2">
                <Label>Prefix (optional)</Label>
                <Input
                  placeholder="folder/"
                  value={config.prefix}
                  onChange={(e) => updateConfig('prefix', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Max Keys</Label>
                <Input
                  type="number"
                  min={1}
                  max={1000}
                  value={config.maxKeys}
                  onChange={(e) => updateConfig('maxKeys', parseInt(e.target.value) || 1000)}
                />
              </div>
            </>
          )}
        </TabsContent>

        {/* Credentials Tab */}
        <TabsContent value="credentials" className="space-y-4">
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Key className="h-4 w-4" />
              Access Key ID
            </Label>
            <Input
              placeholder="AKIAIOSFODNN7EXAMPLE"
              value={config.accessKeyId}
              onChange={(e) => updateConfig('accessKeyId', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Secret Access Key</Label>
            <Input
              type="password"
              placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
              value={config.secretAccessKey}
              onChange={(e) => updateConfig('secretAccessKey', e.target.value)}
            />
          </div>

          <p className="text-xs text-muted-foreground">
            Or use environment variables: {'{{env.AWS_ACCESS_KEY_ID}}'}, {'{{env.AWS_SECRET_ACCESS_KEY}}'}
          </p>

          <div className="space-y-2">
            <Label>Custom Endpoint (optional)</Label>
            <Input
              placeholder="https://s3.custom-endpoint.com"
              value={config.endpoint}
              onChange={(e) => updateConfig('endpoint', e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              For S3-compatible services (MinIO, DigitalOcean Spaces, etc.)
            </p>
          </div>

          {config.endpoint && (
            <div className="flex items-center justify-between">
              <Label>Use Path Style</Label>
              <Switch
                checked={config.usePathStyle}
                onCheckedChange={(v) => updateConfig('usePathStyle', v)}
              />
            </div>
          )}
        </TabsContent>

        {/* Options Tab */}
        <TabsContent value="options" className="space-y-4">
          {config.operation === 'upload' && (
            <>
              <div className="space-y-2">
                <Label>Content Type</Label>
                <Select value={config.contentType} onValueChange={(v) => updateConfig('contentType', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CONTENT_TYPES.map(type => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>ACL (Access Control)</Label>
                <Select value={config.acl} onValueChange={(v) => updateConfig('acl', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {ACL_OPTIONS.map(acl => (
                      <SelectItem key={acl.value} value={acl.value}>
                        {acl.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Metadata (JSON)</Label>
                <Textarea
                  placeholder={'{\n  "custom-key": "value"\n}'}
                  value={config.metadata}
                  onChange={(e) => updateConfig('metadata', e.target.value)}
                  rows={4}
                  className="font-mono text-sm"
                />
              </div>
            </>
          )}

          {config.operation === 'download' && (
            <div className="space-y-2">
              <Label>Output Format</Label>
              <Select value={config.outputFormat} onValueChange={(v) => updateConfig('outputFormat', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="buffer">Buffer (Binary)</SelectItem>
                  <SelectItem value="string">String (Text)</SelectItem>
                  <SelectItem value="base64">Base64</SelectItem>
                  <SelectItem value="stream">Stream</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {config.operation === 'getSignedUrl' && (
            <div className="space-y-2">
              <Label>URL Expiration (seconds)</Label>
              <Input
                type="number"
                min={60}
                max={604800}
                placeholder="3600"
                value={config.maxKeys}
                onChange={(e) => updateConfig('maxKeys', parseInt(e.target.value) || 3600)}
              />
              <p className="text-xs text-muted-foreground">
                URL will expire after this many seconds (max 7 days)
              </p>
            </div>
          )}

          {(config.operation === 'delete' || config.operation === 'list') && (
            <p className="text-sm text-muted-foreground text-center py-4">
              No additional options for this operation
            </p>
          )}
        </TabsContent>
      </Tabs>

      {/* Test Button */}
      {onTest && (
        <Button 
          onClick={onTest} 
          variant="outline" 
          className="w-full"
          disabled={!config.bucket}
        >
          <TestTube className="h-4 w-4 mr-2" />
          Test Connection
        </Button>
      )}
    </div>
  );
}
