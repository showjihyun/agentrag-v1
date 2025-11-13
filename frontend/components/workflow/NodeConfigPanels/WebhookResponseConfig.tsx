'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface WebhookResponseConfigProps {
  data: {
    statusCode?: number;
    headers?: Record<string, string>;
    responseBody?: string;
  };
  onChange: (data: any) => void;
}

export default function WebhookResponseConfig({ data, onChange }: WebhookResponseConfigProps) {
  const [statusCode, setStatusCode] = useState(data.statusCode || 200);
  const [headers, setHeaders] = useState(
    data.headers || { 'Content-Type': 'application/json' }
  );
  const [responseBody, setResponseBody] = useState(
    data.responseBody || '{"success": true, "data": {{$json}}}'
  );

  const handleStatusCodeChange = (value: string) => {
    const code = parseInt(value) || 200;
    setStatusCode(code);
    onChange({ ...data, statusCode: code });
  };

  const handleHeaderChange = (key: string, value: string) => {
    const newHeaders = { ...headers, [key]: value };
    setHeaders(newHeaders);
    onChange({ ...data, headers: newHeaders });
  };

  const handleResponseBodyChange = (value: string) => {
    setResponseBody(value);
    onChange({ ...data, responseBody: value });
  };

  const addHeader = () => {
    const newHeaders = { ...headers, 'New-Header': 'value' };
    setHeaders(newHeaders);
    onChange({ ...data, headers: newHeaders });
  };

  const removeHeader = (key: string) => {
    const newHeaders = { ...headers };
    delete newHeaders[key];
    setHeaders(newHeaders);
    onChange({ ...data, headers: newHeaders });
  };

  const STATUS_PRESETS = [
    { code: 200, label: '200 OK' },
    { code: 201, label: '201 Created' },
    { code: 204, label: '204 No Content' },
    { code: 400, label: '400 Bad Request' },
    { code: 401, label: '401 Unauthorized' },
    { code: 404, label: '404 Not Found' },
    { code: 500, label: '500 Internal Error' },
  ];

  return (
    <div className="space-y-4">
      <div>
        <Label>Status Code</Label>
        <div className="flex gap-2 mt-2">
          <Input
            type="number"
            value={statusCode}
            onChange={(e) => handleStatusCodeChange(e.target.value)}
            className="w-24"
          />
          <select
            value={statusCode}
            onChange={(e) => handleStatusCodeChange(e.target.value)}
            className="flex-1 p-2 border rounded-lg text-sm"
          >
            {STATUS_PRESETS.map((preset) => (
              <option key={preset.code} value={preset.code}>
                {preset.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label>Response Headers</Label>
          <button
            onClick={addHeader}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            + Add Header
          </button>
        </div>
        <div className="space-y-2">
          {Object.entries(headers).map(([key, value]) => (
            <div key={key} className="flex gap-2">
              <Input
                value={key}
                onChange={(e) => {
                  const newHeaders = { ...headers };
                  delete newHeaders[key];
                  newHeaders[e.target.value] = value;
                  setHeaders(newHeaders);
                  onChange({ ...data, headers: newHeaders });
                }}
                placeholder="Header name"
                className="flex-1 text-sm"
              />
              <Input
                value={value}
                onChange={(e) => handleHeaderChange(key, e.target.value)}
                placeholder="Header value"
                className="flex-1 text-sm"
              />
              <button
                onClick={() => removeHeader(key)}
                className="px-3 py-2 text-red-600 hover:bg-red-50 rounded"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </div>

      <div>
        <Label>Response Body</Label>
        <textarea
          value={responseBody}
          onChange={(e) => handleResponseBodyChange(e.target.value)}
          className="w-full h-32 p-3 border rounded-lg font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 mt-2"
          placeholder="Response body template"
        />
        <p className="text-xs text-gray-500 mt-1">
          Use {'{{$json}}'} to reference data from previous nodes
        </p>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
        <p className="text-xs text-purple-800 font-medium mb-2">
          Template Variables:
        </p>
        <ul className="text-xs text-purple-700 space-y-1 ml-4 list-disc">
          <li>
            <code className="bg-purple-100 px-1 rounded">{'{{$json}}'}</code>
            : Previous node output
          </li>
          <li>
            <code className="bg-purple-100 px-1 rounded">
              {'{{$json.field}}'}
            </code>
            : Specific field
          </li>
          <li>
            <code className="bg-purple-100 px-1 rounded">
              {'{{$workflow.id}}'}
            </code>
            : Workflow ID
          </li>
        </ul>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <p className="text-xs text-green-800">
          <strong>Example Response:</strong>
        </p>
        <pre className="text-xs text-green-700 font-mono bg-green-100 p-2 rounded mt-2 overflow-x-auto">
          {`{
  "success": true,
  "message": "Workflow executed",
  "data": {
    "workflowId": "wf_123",
    "result": "..."
  }
}`}
        </pre>
      </div>
    </div>
  );
}
