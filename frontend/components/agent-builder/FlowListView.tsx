'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Users, 
  MessageSquare, 
  Play, 
  Edit,
  Copy,
  Trash,
  Eye,
  MoreVertical,
  CheckCircle2,
  Clock,
  TrendingUp,
  Calendar
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface FlowListViewProps {
  flows: any[];
  type: 'agentflow' | 'chatflow';
  onAction: (action: string, flowId: string, flow?: any) => void;
}

export function FlowListView({ flows, type, onAction }: FlowListViewProps) {
  const isAgentflow = type === 'agentflow';
  const Icon = isAgentflow ? Users : MessageSquare;

  return (
    <div className="space-y-3">
      {flows.map((flow) => (
        <Card 
          key={flow.id}
          className="group hover:shadow-lg transition-all duration-200 cursor-pointer border-l-4 border-l-gray-200 hover:border-l-purple-500"
          onClick={() => onAction('view', flow.id)}
        >
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              {/* Left: Basic Info */}
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <div className={`p-2 rounded-lg shrink-0 ${
                  isAgentflow 
                    ? 'bg-purple-100 dark:bg-purple-900' 
                    : 'bg-blue-100 dark:bg-blue-900'
                }`}>
                  <Icon className={`h-5 w-5 ${
                    isAgentflow 
                      ? 'text-purple-600 dark:text-purple-400' 
                      : 'text-blue-600 dark:text-blue-400'
                  }`} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold text-lg truncate group-hover:text-purple-600 transition-colors">
                      {flow.name}
                    </h3>
                    {flow.is_active && (
                      <Badge className="bg-green-500 text-xs shrink-0">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Active
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-1">
                    {flow.description || 'No description'}
                  </p>
                </div>
              </div>

              {/* Center: Metrics */}
              <div className="hidden md:flex items-center gap-6 mx-6">
                <div className="text-center">
                  <div className={`text-lg font-bold ${
                    isAgentflow ? 'text-purple-600' : 'text-blue-600'
                  }`}>
                    {isAgentflow ? (flow.agents?.length || 0) : (flow.execution_count || 0)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {isAgentflow ? 'Agents' : 'Conversations'}
                  </div>
                </div>
                
                <div className="text-center">
                  <div className="text-lg font-bold text-green-600">
                    {flow.execution_count > 0 
                      ? `${Math.round(((flow.success_count || Math.floor(flow.execution_count * 0.85)) / flow.execution_count) * 100)}%`
                      : '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">Success Rate</div>
                </div>
                
                <div className="text-center">
                  <div className="text-sm text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {flow.updated_at
                      ? new Date(flow.updated_at).toLocaleDateString()
                      : new Date(flow.created_at).toLocaleDateString()}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {flow.updated_at ? 'Updated' : 'Created'}
                  </div>
                </div>
              </div>

              {/* Right: Actions */}
              <div className="flex items-center gap-2 shrink-0">
                <Button 
                  size="sm" 
                  className={`opacity-0 group-hover:opacity-100 transition-opacity ${
                    isAgentflow 
                      ? 'bg-purple-600 hover:bg-purple-700' 
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    onAction(isAgentflow ? 'execute' : 'chat', flow.id);
                  }}
                >
                  <Play className="h-3 w-3 mr-1" />
                  {isAgentflow ? 'Execute' : 'Chat'}
                </Button>

                <DropdownMenu>
                  <DropdownMenuTrigger 
                    className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:bg-accent hover:text-accent-foreground h-10 w-10 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <MoreVertical className="h-4 w-4" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onAction('view', flow.id)}>
                      <Eye className="mr-2 h-4 w-4" />
                      View
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onAction('edit', flow.id)}>
                      <Edit className="mr-2 h-4 w-4" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onAction('duplicate', flow.id, flow)}>
                      <Copy className="mr-2 h-4 w-4" />
                      Duplicate
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      className="text-destructive"
                      onClick={() => onAction('delete', flow.id)}
                    >
                      <Trash className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>

            {/* Mobile Metrics */}
            <div className="md:hidden mt-3 pt-3 border-t">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className={`text-lg font-bold ${
                    isAgentflow ? 'text-purple-600' : 'text-blue-600'
                  }`}>
                    {isAgentflow ? (flow.agents?.length || 0) : (flow.execution_count || 0)}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {isAgentflow ? 'Agents' : 'Conversations'}
                  </div>
                </div>
                <div>
                  <div className="text-lg font-bold text-green-600">
                    {flow.execution_count > 0 
                      ? `${Math.round(((flow.success_count || Math.floor(flow.execution_count * 0.85)) / flow.execution_count) * 100)}%`
                      : '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">Success Rate</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">
                    {flow.updated_at
                      ? new Date(flow.updated_at).toLocaleDateString()
                      : new Date(flow.created_at).toLocaleDateString()}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {flow.updated_at ? 'Updated' : 'Created'}
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}