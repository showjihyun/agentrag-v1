'use client';

import React from 'react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { CollaborationUser } from '@/lib/websocket/collaboration-client';

interface UserPresenceProps {
  users: CollaborationUser[];
  currentUserId: string;
  maxVisible?: number;
}

export function UserPresence({ users, currentUserId, maxVisible = 5 }: UserPresenceProps) {
  const visibleUsers = users.slice(0, maxVisible);
  const hiddenCount = Math.max(0, users.length - maxVisible);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <TooltipProvider>
      <div className="flex items-center gap-2">
        <div className="flex -space-x-2">
          {visibleUsers.map((user) => (
            <Tooltip key={user.id}>
              <TooltipTrigger asChild>
                <Avatar
                  className="border-2 border-background cursor-pointer hover:z-10 transition-transform hover:scale-110"
                  style={{ borderColor: user.color }}
                >
                  <AvatarFallback
                    style={{
                      backgroundColor: user.color + '20',
                      color: user.color,
                    }}
                  >
                    {getInitials(user.name)}
                  </AvatarFallback>
                </Avatar>
              </TooltipTrigger>
              <TooltipContent>
                <div className="space-y-1">
                  <p className="font-semibold">{user.name}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                  {user.id === currentUserId && (
                    <Badge variant="outline" className="text-xs">
                      You
                    </Badge>
                  )}
                </div>
              </TooltipContent>
            </Tooltip>
          ))}
          {hiddenCount > 0 && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Avatar className="border-2 border-background cursor-pointer">
                  <AvatarFallback className="bg-muted text-muted-foreground">
                    +{hiddenCount}
                  </AvatarFallback>
                </Avatar>
              </TooltipTrigger>
              <TooltipContent>
                <p>{hiddenCount} more {hiddenCount === 1 ? 'user' : 'users'}</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}
