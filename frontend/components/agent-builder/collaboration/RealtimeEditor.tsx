'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Textarea } from '@/components/ui/textarea';
import { useCollaboration, CollaborationChange } from '@/lib/websocket/collaboration-client';
import { Users, Wifi, WifiOff } from 'lucide-react';
import { UserPresence } from './UserPresence';
import { CursorOverlay } from './CursorOverlay';

interface RealtimeEditorProps {
  resourceType: 'agent' | 'workflow' | 'block';
  resourceId: string;
  userId: string;
  userName: string;
  initialContent: string;
  onContentChange: (content: string) => void;
  readOnly?: boolean;
}

export function RealtimeEditor({
  resourceType,
  resourceId,
  userId,
  userName,
  initialContent,
  onContentChange,
  readOnly = false,
}: RealtimeEditorProps) {
  const { client, users, connected } = useCollaboration(resourceType, resourceId, userId);
  const [content, setContent] = useState(initialContent);
  const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const contentRef = useRef(content);

  // Keep content ref in sync
  useEffect(() => {
    contentRef.current = content;
  }, [content]);

  // Handle incoming changes
  useEffect(() => {
    const handleChange = (change: CollaborationChange) => {
      if (change.userId === userId) return; // Ignore own changes

      switch (change.type) {
        case 'insert':
          const newContent = contentRef.current.slice(0, change.data.position) +
            change.data.text +
            contentRef.current.slice(change.data.position);
          setContent(newContent);
          onContentChange(newContent);
          break;
        case 'delete':
          const deletedContent = contentRef.current.slice(0, change.data.start) +
            contentRef.current.slice(change.data.end);
          setContent(deletedContent);
          onContentChange(deletedContent);
          break;
        case 'update':
          setContent(change.data.content);
          onContentChange(change.data.content);
          break;
      }
    };

    client.on('change', handleChange);
    return () => {
      client.off('change', handleChange);
    };
  }, [client, userId, onContentChange]);

  // Handle local changes
  const handleContentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newContent = e.target.value;
    const oldContent = content;

    setContent(newContent);
    onContentChange(newContent);

    // Calculate diff and send change
    if (newContent.length > oldContent.length) {
      // Insert
      const position = findDiffPosition(oldContent, newContent);
      const text = newContent.slice(position, position + (newContent.length - oldContent.length));
      client.sendChange({
        type: 'insert',
        data: { position, text },
      });
    } else if (newContent.length < oldContent.length) {
      // Delete
      const start = findDiffPosition(oldContent, newContent);
      const end = start + (oldContent.length - newContent.length);
      client.sendChange({
        type: 'delete',
        data: { start, end },
      });
    } else {
      // Update (same length but different content)
      client.sendChange({
        type: 'update',
        data: { content: newContent },
      });
    }
  };

  // Handle cursor movement
  const handleMouseMove = (e: React.MouseEvent<HTMLTextAreaElement>) => {
    if (readOnly) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    setCursorPosition({ x, y });
    client.sendCursor({ x, y });
  };

  // Handle selection
  const handleSelect = (e: React.SyntheticEvent<HTMLTextAreaElement>) => {
    if (readOnly) return;

    const target = e.target as HTMLTextAreaElement;
    const start = target.selectionStart;
    const end = target.selectionEnd;

    if (start !== end) {
      client.sendSelection({ start, end });
    }
  };

  const findDiffPosition = (oldStr: string, newStr: string): number => {
    for (let i = 0; i < Math.min(oldStr.length, newStr.length); i++) {
      if (oldStr[i] !== newStr[i]) {
        return i;
      }
    }
    return Math.min(oldStr.length, newStr.length);
  };

  const otherUsers = users.filter((u) => u.id !== userId);

  return (
    <div className="space-y-4">
      {/* Connection Status & Users */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg">Collaborative Editing</CardTitle>
              {connected ? (
                <Badge variant="default" className="gap-1">
                  <Wifi className="h-3 w-3" />
                  Connected
                </Badge>
              ) : (
                <Badge variant="destructive" className="gap-1">
                  <WifiOff className="h-3 w-3" />
                  Disconnected
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">
                {users.length} {users.length === 1 ? 'user' : 'users'}
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <UserPresence users={users} currentUserId={userId} />
        </CardContent>
      </Card>

      {/* Editor with Cursor Overlay */}
      <Card>
        <CardContent className="p-0 relative">
          <CursorOverlay users={otherUsers} />
          <Textarea
            ref={textareaRef}
            value={content}
            onChange={handleContentChange}
            onMouseMove={handleMouseMove}
            onSelect={handleSelect}
            readOnly={readOnly}
            className="min-h-[400px] font-mono text-sm border-0 focus-visible:ring-0"
            placeholder="Start typing... (changes are synced in real-time)"
          />
        </CardContent>
      </Card>

      {/* Activity Indicator */}
      {otherUsers.length > 0 && (
        <div className="text-xs text-muted-foreground">
          {otherUsers.map((user) => (
            <div key={user.id} className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: user.color }}
              />
              <span>{user.name} is editing</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
