'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ExternalLink } from 'lucide-react';

interface GoogleDriveNodeConfigProps {
  data: {
    action?: 'upload' | 'download' | 'list' | 'delete' | 'share';
    folderId?: string;
    fileName?: string;
    fileContent?: string;
    mimeType?: string;
    shareWith?: string;
    shareRole?: 'reader' | 'writer' | 'commenter';
  };
  onChange: (data: any) => void;
}

export default function GoogleDriveNodeConfig({ data, onChange }: GoogleDriveNodeConfigProps) {
  const [action, setAction] = useState<'upload' | 'download' | 'list' | 'delete' | 'share'>(
    data.action || 'upload'
  );
  const [folderId, setFolderId] = useState(data.folderId || '');
  const [fileName, setFileName] = useState(data.fileName || '');
  const [fileContent, setFileContent] = useState(data.fileContent || '');
  const [mimeType, setMimeType] = useState(data.mimeType || 'text/plain');
  const [shareWith, setShareWith] = useState(data.shareWith || '');
  const [shareRole, setShareRole] = useState<'reader' | 'writer' | 'commenter'>(
    data.shareRole || 'reader'
  );

  const handleActionChange = (value: 'upload' | 'download' | 'list' | 'delete' | 'share') => {
    setAction(value);
    onChange({ ...data, action: value });
  };

  const handleFolderIdChange = (value: string) => {
    setFolderId(value);
    onChange({ ...data, folderId: value });
  };

  const handleFileNameChange = (value: string) => {
    setFileName(value);
    onChange({ ...data, fileName: value });
  };

  const handleFileContentChange = (value: string) => {
    setFileContent(value);
    onChange({ ...data, fileContent: value });
  };

  const handleMimeTypeChange = (value: string) => {
    setMimeType(value);
    onChange({ ...data, mimeType: value });
  };

  const handleShareWithChange = (value: string) => {
    setShareWith(value);
    onChange({ ...data, shareWith: value });
  };

  const handleShareRoleChange = (value: 'reader' | 'writer' | 'commenter') => {
    setShareRole(value);
    onChange({ ...data, shareRole: value });
  };

  const MIME_TYPES = [
    { label: 'Plain Text', value: 'text/plain' },
    { label: 'JSON', value: 'application/json' },
    { label: 'CSV', value: 'text/csv' },
    { label: 'PDF', value: 'application/pdf' },
    { label: 'Google Docs', value: 'application/vnd.google-apps.document' },
    { label: 'Google Sheets', value: 'application/vnd.google-apps.spreadsheet' },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-red-50 border border-red-200 rounded-lg p-3">
        <p className="text-xs text-red-800 mb-2">
          <strong>Setup Required:</strong>
        </p>
        <ol className="text-xs text-red-700 space-y-1 ml-4 list-decimal">
          <li>Create a Google Cloud Project</li>
          <li>Enable Google Drive API</li>
          <li>Create OAuth 2.0 credentials</li>
          <li>Add credentials to API Keys settings</li>
          <li>Authorize the application</li>
        </ol>
        <Button
          variant="link"
          size="sm"
          className="text-red-600 p-0 h-auto mt-2"
          onClick={() => window.open('https://console.cloud.google.com', '_blank')}
        >
          <ExternalLink className="w-3 h-3 mr-1" />
          Google Cloud Console
        </Button>
      </div>

      <div>
        <Label>Action</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {(['upload', 'download', 'list', 'delete', 'share'] as const).map((act) => (
            <button
              key={act}
              onClick={() => handleActionChange(act)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
                action === act
                  ? 'bg-red-500 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {act}
            </button>
          ))}
        </div>
      </div>

      {(action === 'upload' || action === 'list') && (
        <div>
          <Label>Folder ID (optional)</Label>
          <Input
            value={folderId}
            onChange={(e) => handleFolderIdChange(e.target.value)}
            placeholder="root"
            className="font-mono"
          />
          <p className="text-xs text-gray-500 mt-1">
            Leave empty for root folder. Get ID from folder URL.
          </p>
        </div>
      )}

      {action === 'upload' && (
        <>
          <div>
            <Label>File Name</Label>
            <Input
              value={fileName}
              onChange={(e) => handleFileNameChange(e.target.value)}
              placeholder="document.txt"
            />
            <p className="text-xs text-gray-500 mt-1">
              Use {'{{$json.filename}}'} for dynamic names
            </p>
          </div>

          <div>
            <Label>MIME Type</Label>
            <select
              value={mimeType}
              onChange={(e) => handleMimeTypeChange(e.target.value)}
              className="w-full p-2 border rounded-lg text-sm"
            >
              {MIME_TYPES.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <Label>File Content</Label>
            <textarea
              value={fileContent}
              onChange={(e) => handleFileContentChange(e.target.value)}
              className="w-full h-32 p-3 border rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              placeholder="File content or {{$json.content}}"
            />
          </div>
        </>
      )}

      {(action === 'download' || action === 'delete') && (
        <div>
          <Label>File ID</Label>
          <Input
            value={fileName}
            onChange={(e) => handleFileNameChange(e.target.value)}
            placeholder="File ID from Google Drive"
            className="font-mono"
          />
          <p className="text-xs text-gray-500 mt-1">
            Get file ID from the file URL or list action
          </p>
        </div>
      )}

      {action === 'share' && (
        <>
          <div>
            <Label>File ID</Label>
            <Input
              value={fileName}
              onChange={(e) => handleFileNameChange(e.target.value)}
              placeholder="File ID to share"
              className="font-mono"
            />
          </div>

          <div>
            <Label>Share With (Email)</Label>
            <Input
              value={shareWith}
              onChange={(e) => handleShareWithChange(e.target.value)}
              placeholder="user@example.com"
            />
          </div>

          <div>
            <Label>Permission Role</Label>
            <div className="flex gap-2 mt-2">
              {(['reader', 'writer', 'commenter'] as const).map((role) => (
                <button
                  key={role}
                  onClick={() => handleShareRoleChange(role)}
                  className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
                    shareRole === role
                      ? 'bg-red-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {role}
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <p className="text-xs text-green-800 font-medium mb-2">
          Output Variables:
        </p>
        <div className="text-xs text-green-700 space-y-1 font-mono">
          {action === 'upload' && <div>fileId - Uploaded file ID</div>}
          {action === 'download' && <div>content - File content</div>}
          {action === 'list' && <div>files[] - Array of files</div>}
          {action === 'delete' && <div>success - Deletion status</div>}
          {action === 'share' && <div>permissionId - Share permission ID</div>}
        </div>
      </div>
    </div>
  );
}
