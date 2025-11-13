'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface S3NodeConfigProps {
  data: {
    action?: 'upload' | 'download' | 'list' | 'delete';
    bucket?: string;
    key?: string;
    content?: string;
    region?: string;
  };
  onChange: (data: any) => void;
}

export default function S3NodeConfig({ data, onChange }: S3NodeConfigProps) {
  const [action, setAction] = useState<'upload' | 'download' | 'list' | 'delete'>(
    data.action || 'upload'
  );
  const [bucket, setBucket] = useState(data.bucket || '');
  const [key, setKey] = useState(data.key || '');
  const [content, setContent] = useState(data.content || '');
  const [region, setRegion] = useState(data.region || 'us-east-1');

  const handleActionChange = (value: 'upload' | 'download' | 'list' | 'delete') => {
    setAction(value);
    onChange({ ...data, action: value });
  };

  const handleBucketChange = (value: string) => {
    setBucket(value);
    onChange({ ...data, bucket: value });
  };

  const handleKeyChange = (value: string) => {
    setKey(value);
    onChange({ ...data, key: value });
  };

  const handleContentChange = (value: string) => {
    setContent(value);
    onChange({ ...data, content: value });
  };

  const handleRegionChange = (value: string) => {
    setRegion(value);
    onChange({ ...data, region: value });
  };

  const AWS_REGIONS = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1',
  ];

  return (
    <div className="space-y-4">
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
        <p className="text-xs text-orange-800 mb-1">
          <strong>Setup:</strong> Add AWS credentials to API Keys
        </p>
      </div>

      <div>
        <Label>Action</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {(['upload', 'download', 'list', 'delete'] as const).map((act) => (
            <button
              key={act}
              onClick={() => handleActionChange(act)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize ${
                action === act ? 'bg-orange-500 text-white' : 'bg-gray-100 text-gray-700'
              }`}
            >
              {act}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Bucket Name</Label>
        <Input
          value={bucket}
          onChange={(e) => handleBucketChange(e.target.value)}
          placeholder="my-bucket"
        />
      </div>

      <div>
        <Label>Region</Label>
        <select
          value={region}
          onChange={(e) => handleRegionChange(e.target.value)}
          className="w-full p-2 border rounded-lg text-sm"
        >
          {AWS_REGIONS.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      {(action === 'upload' || action === 'download' || action === 'delete') && (
        <div>
          <Label>Object Key</Label>
          <Input
            value={key}
            onChange={(e) => handleKeyChange(e.target.value)}
            placeholder="path/to/file.txt"
          />
        </div>
      )}

      {action === 'upload' && (
        <div>
          <Label>Content</Label>
          <textarea
            value={content}
            onChange={(e) => handleContentChange(e.target.value)}
            className="w-full h-32 p-3 border rounded-lg text-sm resize-none"
            placeholder="{{$json.content}}"
          />
        </div>
      )}
    </div>
  );
}
