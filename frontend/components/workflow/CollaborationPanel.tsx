'use client';

/**
 * Real-time Collaboration Panel
 * 
 * Features:
 * - Live presence indicators
 * - Cursor sharing
 * - Inline comments
 * - Activity feed
 */

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Users,
  MessageSquare,
  Activity,
  Eye,
  Edit3,
  Clock,
  Send,
  AtSign,
  Hash,
  MoreHorizontal,
  Check,
  X,
  Bell,
  Settings,
  UserPlus,
  Link2,
  Copy,
} from 'lucide-react';

// Types
export interface Collaborator {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  color: string;
  status: 'online' | 'away' | 'offline';
  currentNodeId?: string;
  isEditing?: boolean;
  lastSeen?: Date;
}

export interface Comment {
  id: string;
  nodeId?: string;
  author: Collaborator;
  content: string;
  timestamp: Date;
  resolved?: boolean;
  replies?: Comment[];
}

export interface ActivityItem {
  id: string;
  type: 'edit' | 'comment' | 'join' | 'leave' | 'execute' | 'save';
  user: Collaborator;
  description: string;
  timestamp: Date;
  nodeId?: string;
  nodeName?: string;
}

interface CollaborationPanelProps {
  workflowId: string;
  currentUser: Collaborator;
  collaborators: Collaborator[];
  comments: Comment[];
  activities: ActivityItem[];
  onAddComment: (content: string, nodeId?: string) => void;
  onResolveComment: (commentId: string) => void;
  onInvite: (email: string) => void;
  onFollowUser: (userId: string) => void;
  className?: string;
}

// Presence indicator colors
const PRESENCE_COLORS = [
  '#3B82F6', // blue
  '#10B981', // green
  '#F59E0B', // amber
  '#EF4444', // red
  '#8B5CF6', // purple
  '#EC4899', // pink
  '#06B6D4', // cyan
  '#F97316', // orange
];

// Status badge
const StatusBadge: React.FC<{ status: Collaborator['status'] }> = ({ status }) => {
  const config = {
    online: { color: 'bg-green-500', label: '온라인' },
    away: { color: 'bg-yellow-500', label: '자리비움' },
    offline: { color: 'bg-gray-400', label: '오프라인' },
  };

  return (
    <span className={cn('w-2.5 h-2.5 rounded-full', config[status].color)} />
  );
};

// Collaborator avatar with presence
const CollaboratorAvatar: React.FC<{
  collaborator: Collaborator;
  size?: 'sm' | 'md' | 'lg';
  showStatus?: boolean;
}> = ({ collaborator, size = 'md', showStatus = true }) => {
  const sizeClasses = {
    sm: 'w-6 h-6 text-xs',
    md: 'w-8 h-8 text-sm',
    lg: 'w-10 h-10 text-base',
  };

  return (
    <div className="relative">
      <Avatar className={sizeClasses[size]}>
        {collaborator.avatar ? (
          <AvatarImage src={collaborator.avatar} alt={collaborator.name} />
        ) : null}
        <AvatarFallback
          style={{ backgroundColor: collaborator.color }}
          className="text-white font-medium"
        >
          {collaborator.name.slice(0, 2).toUpperCase()}
        </AvatarFallback>
      </Avatar>
      {showStatus && (
        <span
          className={cn(
            'absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2 border-background',
            collaborator.status === 'online' && 'bg-green-500',
            collaborator.status === 'away' && 'bg-yellow-500',
            collaborator.status === 'offline' && 'bg-gray-400'
          )}
        />
      )}
    </div>
  );
};

// Comment item
const CommentItem: React.FC<{
  comment: Comment;
  onResolve: () => void;
}> = ({ comment, onResolve }) => {
  const [showReplies, setShowReplies] = useState(false);

  return (
    <div className={cn(
      'p-3 rounded-lg border',
      comment.resolved && 'opacity-60 bg-muted/30'
    )}>
      <div className="flex items-start gap-2">
        <CollaboratorAvatar collaborator={comment.author} size="sm" showStatus={false} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{comment.author.name}</span>
            <span className="text-xs text-muted-foreground">
              {comment.timestamp.toLocaleTimeString()}
            </span>
            {comment.resolved && (
              <Badge variant="outline" className="text-xs text-green-600">
                <Check className="w-3 h-3 mr-1" />
                해결됨
              </Badge>
            )}
          </div>
          <p className="text-sm mt-1">{comment.content}</p>
          
          {comment.nodeId && (
            <Badge variant="secondary" className="text-xs mt-2">
              <Hash className="w-3 h-3 mr-1" />
              {comment.nodeId}
            </Badge>
          )}
          
          <div className="flex items-center gap-2 mt-2">
            {!comment.resolved && (
              <Button size="sm" variant="ghost" className="h-6 text-xs" onClick={onResolve}>
                <Check className="w-3 h-3 mr-1" />
                해결
              </Button>
            )}
            {comment.replies && comment.replies.length > 0 && (
              <Button
                size="sm"
                variant="ghost"
                className="h-6 text-xs"
                onClick={() => setShowReplies(!showReplies)}
              >
                <MessageSquare className="w-3 h-3 mr-1" />
                {comment.replies.length}개 답글
              </Button>
            )}
          </div>
        </div>
      </div>
      
      {showReplies && comment.replies && (
        <div className="ml-8 mt-2 space-y-2 border-l-2 pl-3">
          {comment.replies.map(reply => (
            <div key={reply.id} className="text-sm">
              <span className="font-medium">{reply.author.name}</span>
              <span className="text-muted-foreground ml-2">{reply.content}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Activity item
const ActivityItemComponent: React.FC<{ activity: ActivityItem }> = ({ activity }) => {
  const getIcon = () => {
    switch (activity.type) {
      case 'edit': return <Edit3 className="w-4 h-4 text-blue-500" />;
      case 'comment': return <MessageSquare className="w-4 h-4 text-green-500" />;
      case 'join': return <UserPlus className="w-4 h-4 text-purple-500" />;
      case 'leave': return <X className="w-4 h-4 text-gray-500" />;
      case 'execute': return <Activity className="w-4 h-4 text-orange-500" />;
      case 'save': return <Check className="w-4 h-4 text-green-500" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  return (
    <div className="flex items-start gap-3 py-2">
      <div className="mt-0.5">{getIcon()}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm">
          <span className="font-medium">{activity.user.name}</span>
          <span className="text-muted-foreground ml-1">{activity.description}</span>
        </p>
        {activity.nodeName && (
          <Badge variant="outline" className="text-xs mt-1">
            {activity.nodeName}
          </Badge>
        )}
        <p className="text-xs text-muted-foreground mt-0.5">
          {activity.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </div>
  );
};

// Main component
export function CollaborationPanel({
  workflowId,
  currentUser,
  collaborators,
  comments,
  activities,
  onAddComment,
  onResolveComment,
  onInvite,
  onFollowUser,
  className,
}: CollaborationPanelProps) {
  const [newComment, setNewComment] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [showInvite, setShowInvite] = useState(false);
  const [copied, setCopied] = useState(false);

  const onlineCollaborators = collaborators.filter(c => c.status === 'online');
  const unresolvedComments = comments.filter(c => !c.resolved);

  const handleAddComment = () => {
    if (newComment.trim()) {
      onAddComment(newComment.trim());
      setNewComment('');
    }
  };

  const handleInvite = () => {
    if (inviteEmail.trim()) {
      onInvite(inviteEmail.trim());
      setInviteEmail('');
      setShowInvite(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(`${window.location.origin}/workflow/${workflowId}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn('flex flex-col h-full bg-background border-l', className)}>
      {/* Header */}
      <div className="p-3 border-b">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-primary" />
            <span className="font-semibold">협업</span>
            <Badge variant="secondary" className="text-xs">
              {onlineCollaborators.length} 온라인
            </Badge>
          </div>
          <div className="flex items-center gap-1">
            <Button size="sm" variant="ghost" onClick={() => setShowInvite(!showInvite)}>
              <UserPlus className="w-4 h-4" />
            </Button>
            <Button size="sm" variant="ghost" onClick={handleCopyLink}>
              {copied ? <Check className="w-4 h-4 text-green-500" /> : <Link2 className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Invite form */}
        {showInvite && (
          <div className="flex gap-2 mb-3">
            <input
              type="email"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="이메일 주소"
              className="flex-1 px-3 py-1.5 text-sm border rounded-md"
            />
            <Button size="sm" onClick={handleInvite}>
              초대
            </Button>
          </div>
        )}

        {/* Online collaborators */}
        <div className="flex items-center gap-1">
          {onlineCollaborators.slice(0, 5).map(collaborator => (
            <button
              key={collaborator.id}
              onClick={() => onFollowUser(collaborator.id)}
              className="relative group"
              title={`${collaborator.name} 따라가기`}
            >
              <CollaboratorAvatar collaborator={collaborator} size="sm" />
              {collaborator.isEditing && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-blue-500 rounded-full flex items-center justify-center">
                  <Edit3 className="w-2 h-2 text-white" />
                </span>
              )}
            </button>
          ))}
          {onlineCollaborators.length > 5 && (
            <Badge variant="outline" className="text-xs">
              +{onlineCollaborators.length - 5}
            </Badge>
          )}
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="comments" className="flex-1 flex flex-col">
        <TabsList className="mx-3 mt-2">
          <TabsTrigger value="comments" className="gap-1 text-xs">
            <MessageSquare className="w-3 h-3" />
            댓글
            {unresolvedComments.length > 0 && (
              <Badge variant="destructive" className="ml-1 h-4 w-4 p-0 text-xs">
                {unresolvedComments.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="activity" className="gap-1 text-xs">
            <Activity className="w-3 h-3" />
            활동
          </TabsTrigger>
          <TabsTrigger value="members" className="gap-1 text-xs">
            <Users className="w-3 h-3" />
            멤버
          </TabsTrigger>
        </TabsList>

        {/* Comments tab */}
        <TabsContent value="comments" className="flex-1 flex flex-col m-0 overflow-hidden">
          <ScrollArea className="flex-1 p-3">
            <div className="space-y-3">
              {comments.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">아직 댓글이 없습니다</p>
                </div>
              ) : (
                comments.map(comment => (
                  <CommentItem
                    key={comment.id}
                    comment={comment}
                    onResolve={() => onResolveComment(comment.id)}
                  />
                ))
              )}
            </div>
          </ScrollArea>
          
          {/* Comment input */}
          <div className="p-3 border-t">
            <div className="flex gap-2">
              <input
                type="text"
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                placeholder="댓글 작성..."
                className="flex-1 px-3 py-2 text-sm border rounded-md"
              />
              <Button size="sm" onClick={handleAddComment} disabled={!newComment.trim()}>
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </TabsContent>

        {/* Activity tab */}
        <TabsContent value="activity" className="flex-1 m-0 overflow-hidden">
          <ScrollArea className="h-full p-3">
            <div className="space-y-1">
              {activities.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">아직 활동이 없습니다</p>
                </div>
              ) : (
                activities.map(activity => (
                  <ActivityItemComponent key={activity.id} activity={activity} />
                ))
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Members tab */}
        <TabsContent value="members" className="flex-1 m-0 overflow-hidden">
          <ScrollArea className="h-full p-3">
            <div className="space-y-2">
              {collaborators.map(collaborator => (
                <div
                  key={collaborator.id}
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted/50"
                >
                  <CollaboratorAvatar collaborator={collaborator} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-sm truncate">
                        {collaborator.name}
                      </span>
                      {collaborator.id === currentUser.id && (
                        <Badge variant="outline" className="text-xs">나</Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">
                      {collaborator.email}
                    </p>
                  </div>
                  {collaborator.currentNodeId && (
                    <Badge variant="secondary" className="text-xs">
                      <Eye className="w-3 h-3 mr-1" />
                      {collaborator.currentNodeId}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default CollaborationPanel;
