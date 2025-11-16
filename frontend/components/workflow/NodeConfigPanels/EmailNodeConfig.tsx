'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Plus, Trash2 } from 'lucide-react';
import { ExpressionEditor } from '../ExpressionEditor';

interface EmailNodeConfigProps {
  data: {
    to?: string[];
    cc?: string[];
    bcc?: string[];
    subject?: string;
    body?: string;
    bodyType?: 'text' | 'html';
    attachments?: boolean;
  };
  onChange: (data: any) => void;
}

export default function EmailNodeConfig({ data, onChange }: EmailNodeConfigProps) {
  const [to, setTo] = useState<string[]>(data.to || ['']);
  const [cc, setCc] = useState<string[]>(data.cc || []);
  const [bcc, setBcc] = useState<string[]>(data.bcc || []);
  const [subject, setSubject] = useState(data.subject || '');
  const [body, setBody] = useState(data.body || '');
  const [bodyType, setBodyType] = useState<'text' | 'html'>(data.bodyType || 'text');
  const [attachments, setAttachments] = useState(data.attachments !== false);

  const handleToChange = (index: number, value: string) => {
    const newTo = [...to];
    newTo[index] = value;
    setTo(newTo);
    onChange({ ...data, to: newTo.filter(email => email.trim()) });
  };

  const addToRecipient = () => {
    const newTo = [...to, ''];
    setTo(newTo);
  };

  const removeToRecipient = (index: number) => {
    const newTo = to.filter((_, i) => i !== index);
    setTo(newTo);
    onChange({ ...data, to: newTo.filter(email => email.trim()) });
  };

  const handleCcChange = (index: number, value: string) => {
    const newCc = [...cc];
    newCc[index] = value;
    setCc(newCc);
    onChange({ ...data, cc: newCc.filter(email => email.trim()) });
  };

  const addCcRecipient = () => {
    const newCc = [...cc, ''];
    setCc(newCc);
  };

  const removeCcRecipient = (index: number) => {
    const newCc = cc.filter((_, i) => i !== index);
    setCc(newCc);
    onChange({ ...data, cc: newCc.filter(email => email.trim()) });
  };

  const handleSubjectChange = (value: string) => {
    setSubject(value);
    onChange({ ...data, subject: value });
  };

  const handleBodyChange = (value: string) => {
    setBody(value);
    onChange({ ...data, body: value });
  };

  const handleBodyTypeChange = (value: 'text' | 'html') => {
    setBodyType(value);
    onChange({ ...data, bodyType: value });
  };

  const SUBJECT_TEMPLATES = [
    'Workflow Completed: {{$workflow.name}}',
    'Alert: {{$json.status}}',
    'Daily Report - {{$json.date}}',
    'Error Notification: {{$json.error}}',
  ];

  const BODY_TEMPLATES = {
    text: [
      'Workflow {{$workflow.name}} completed successfully.\n\nResult: {{$json.result}}\nStatus: {{$json.status}}',
      'Hello,\n\nYour workflow has finished processing.\n\nDetails:\n- Duration: {{$json.duration}}s\n- Items processed: {{$json.count}}\n\nBest regards',
    ],
    html: [
      '<h2>Workflow Completed</h2><p>Status: <strong>{{$json.status}}</strong></p><p>Result: {{$json.result}}</p>',
      '<div style="font-family: Arial, sans-serif;"><h1>Workflow Report</h1><table><tr><td>Status:</td><td>{{$json.status}}</td></tr><tr><td>Duration:</td><td>{{$json.duration}}s</td></tr></table></div>',
    ],
  };

  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800 mb-2">
          <strong>Setup Required:</strong>
        </p>
        <ol className="text-xs text-blue-700 space-y-1 ml-4 list-decimal">
          <li>Configure SMTP settings in API Keys</li>
          <li>Add credentials: Gmail, SendGrid, or custom SMTP</li>
          <li>For Gmail: Enable "Less secure app access" or use App Password</li>
        </ol>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label>To (Recipients)</Label>
          <Button onClick={addToRecipient} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            Add
          </Button>
        </div>
        <div className="space-y-2">
          {to.map((email, index) => (
            <div key={index} className="flex gap-2">
              <Input
                value={email}
                onChange={(e) => handleToChange(index, e.target.value)}
                placeholder="recipient@example.com"
                className="flex-1"
              />
              {to.length > 1 && (
                <Button
                  onClick={() => removeToRecipient(index)}
                  size="sm"
                  variant="ghost"
                  className="px-2"
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label>CC (optional)</Label>
          <Button onClick={addCcRecipient} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            Add CC
          </Button>
        </div>
        {cc.length > 0 && (
          <div className="space-y-2">
            {cc.map((email, index) => (
              <div key={index} className="flex gap-2">
                <Input
                  value={email}
                  onChange={(e) => handleCcChange(index, e.target.value)}
                  placeholder="cc@example.com"
                  className="flex-1"
                />
                <Button
                  onClick={() => removeCcRecipient(index)}
                  size="sm"
                  variant="ghost"
                  className="px-2"
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <Label>Subject</Label>
        <Input
          value={subject}
          onChange={(e) => handleSubjectChange(e.target.value)}
          placeholder="Email subject"
        />
        <div className="flex gap-1 mt-2 flex-wrap">
          {SUBJECT_TEMPLATES.map((template, idx) => (
            <button
              key={idx}
              onClick={() => handleSubjectChange(template)}
              className="px-2 py-1 text-xs rounded border hover:bg-gray-50"
            >
              Template {idx + 1}
            </button>
          ))}
        </div>
      </div>

      <div>
        <Label>Body Type</Label>
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => handleBodyTypeChange('text')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              bodyType === 'text'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Plain Text
          </button>
          <button
            onClick={() => handleBodyTypeChange('html')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              bodyType === 'html'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            HTML
          </button>
        </div>
      </div>

      <div>
        <Label>Email Body</Label>
        <ExpressionEditor
          value={body}
          onChange={handleBodyChange}
          placeholder={bodyType === 'html' ? '<p>HTML content...</p>' : 'Plain text content...'}
          multiline={true}
          availableVariables={{
            user_name: 'John Doe',
            user_email: 'john@example.com',
            status: 'completed',
            result: 'Success',
          }}
        />
        <div className="flex gap-1 mt-2 flex-wrap">
          {BODY_TEMPLATES[bodyType].map((template, idx) => (
            <button
              key={idx}
              onClick={() => handleBodyChange(template)}
              className="px-2 py-1 text-xs rounded border hover:bg-gray-50"
            >
              Template {idx + 1}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="attachments"
          checked={attachments}
          onChange={(e) => setAttachments(e.target.checked)}
          className="rounded"
        />
        <Label htmlFor="attachments" className="cursor-pointer">
          Include workflow data as attachment
        </Label>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <p className="text-xs text-green-800 font-medium mb-2">
          Template Variables:
        </p>
        <div className="text-xs text-green-700 space-y-1 font-mono">
          <div>{'{{$json.field}}'} - Data from previous node</div>
          <div>{'{{$workflow.name}}'} - Workflow name</div>
          <div>{'{{$workflow.id}}'} - Workflow ID</div>
          <div>{'{{$execution.timestamp}}'} - Execution time</div>
        </div>
      </div>
    </div>
  );
}
