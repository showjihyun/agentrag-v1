'use client';

/**
 * Version Control Panel
 * 
 * Git-like version control for workflows:
 * - Branch management
 * - Commit history
 * - Visual diff
 * - Environment deployment
 */

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  GitBranch,
  GitCommit,
  GitMerge,
  GitPullRequest,
  Plus,
  Minus,
  Edit3,
  Clock,
  User,
  ChevronRight,
  ChevronDown,
  Check,
  X,
  Upload,
  Download,
  RotateCcw,
  Eye,
  Copy,
  MoreHorizontal,
  Rocket,
  Shield,
  AlertTriangle,
} from 'lucide-react';

// Types
export interface Branch {
  id: string;
  name: string;
  isDefault: boolean;
  isCurrent: boolean;
  lastCommit?: Commit;
  aheadBehind?: { ahead: number; behind: number };
}

export interface Commit {
  id: string;
  hash: string;
  message: string;
  author: string;
  timestamp: Date;
  changes: Change[];
}

export interface Change {
  type: 'added' | 'modified' | 'removed';
  nodeId: string;
  nodeName: string;
  details?: string;
}

export interface Environment {
  id: string;
  name: string;
  status: 'deployed' | 'pending' | 'failed';
  currentVersion?: string;
  lastDeployed?: Date;
}

interface VersionControlPanelProps {
  workflowId: string;
  branches: Branch[];
  commits: Commit[];
  environments: Environment[];
  currentBranch: string;
  hasUncommittedChanges: boolean;
  onCreateBranch: (name: string) => void;
  onSwitchBranch: (branchId: string) => void;
  onCommit: (message: string) => void;
  onMerge: (sourceBranch: string, targetBranch: string) => void;
  onDeploy: (environmentId: string) => void;
  onRevert: (commitId: string) => void;
  className?: string;
}

// Change type badge
const ChangeTypeBadge: React.FC<{ type: Change['type'] }> = ({ type }) => {
  const config = {
    added: { icon: Plus, color: 'bg-green-100 text-green-700', label: '추가' },
    modified: { icon: Edit3, color: 'bg-blue-100 text-blue-700', label: '수정' },
    removed: { icon: Minus, color: 'bg-red-100 text-red-700', label: '삭제' },
  };

  const { icon: Icon, color, label } = config[type];

  return (
    <Badge className={cn('text-xs gap-1', color)}>
      <Icon className="w-3 h-3" />
      {label}
    </Badge>
  );
};

// Environment status badge
const EnvironmentStatusBadge: React.FC<{ status: Environment['status'] }> = ({ status }) => {
  const config = {
    deployed: { color: 'bg-green-100 text-green-700', label: '배포됨' },
    pending: { color: 'bg-yellow-100 text-yellow-700', label: '대기중' },
    failed: { color: 'bg-red-100 text-red-700', label: '실패' },
  };

  return (
    <Badge className={cn('text-xs', config[status].color)}>
      {config[status].label}
    </Badge>
  );
};

// Commit item
const CommitItem: React.FC<{
  commit: Commit;
  onRevert: () => void;
  onViewDetails: () => void;
}> = ({ commit, onRevert, onViewDetails }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border rounded-lg p-3">
      <div className="flex items-start gap-3">
        <div className="p-1.5 bg-muted rounded-full mt-0.5">
          <GitCommit className="w-4 h-4 text-muted-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm truncate">{commit.message}</span>
          </div>
          <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <User className="w-3 h-3" />
              {commit.author}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {commit.timestamp.toLocaleDateString()}
            </span>
            <code className="px-1.5 py-0.5 bg-muted rounded text-xs">
              {commit.hash.slice(0, 7)}
            </code>
          </div>
          
          {/* Changes summary */}
          <button
            className="flex items-center gap-1 mt-2 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
            {commit.changes.length}개 변경사항
          </button>
          
          {expanded && (
            <div className="mt-2 space-y-1">
              {commit.changes.map((change, index) => (
                <div key={index} className="flex items-center gap-2 text-xs">
                  <ChangeTypeBadge type={change.type} />
                  <span>{change.nodeName}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-1">
          <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={onViewDetails}>
            <Eye className="w-4 h-4" />
          </Button>
          <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={onRevert}>
            <RotateCcw className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

// Branch item
const BranchItem: React.FC<{
  branch: Branch;
  onSwitch: () => void;
  onMerge: () => void;
}> = ({ branch, onSwitch, onMerge }) => {
  return (
    <div className={cn(
      'flex items-center gap-3 p-3 rounded-lg border',
      branch.isCurrent && 'bg-primary/5 border-primary/30'
    )}>
      <GitBranch className={cn(
        'w-5 h-5',
        branch.isCurrent ? 'text-primary' : 'text-muted-foreground'
      )} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{branch.name}</span>
          {branch.isDefault && (
            <Badge variant="outline" className="text-xs">기본</Badge>
          )}
          {branch.isCurrent && (
            <Badge className="text-xs bg-primary">현재</Badge>
          )}
        </div>
        {branch.aheadBehind && (
          <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
            {branch.aheadBehind.ahead > 0 && (
              <span className="text-green-600">↑ {branch.aheadBehind.ahead}</span>
            )}
            {branch.aheadBehind.behind > 0 && (
              <span className="text-orange-600">↓ {branch.aheadBehind.behind}</span>
            )}
          </div>
        )}
      </div>
      
      {!branch.isCurrent && (
        <div className="flex items-center gap-1">
          <Button size="sm" variant="outline" className="h-7" onClick={onSwitch}>
            전환
          </Button>
          <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={onMerge}>
            <GitMerge className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
};

// Main component
export function VersionControlPanel({
  workflowId,
  branches,
  commits,
  environments,
  currentBranch,
  hasUncommittedChanges,
  onCreateBranch,
  onSwitchBranch,
  onCommit,
  onMerge,
  onDeploy,
  onRevert,
  className,
}: VersionControlPanelProps) {
  const [commitMessage, setCommitMessage] = useState('');
  const [newBranchName, setNewBranchName] = useState('');
  const [showNewBranch, setShowNewBranch] = useState(false);

  const handleCommit = () => {
    if (commitMessage.trim()) {
      onCommit(commitMessage.trim());
      setCommitMessage('');
    }
  };

  const handleCreateBranch = () => {
    if (newBranchName.trim()) {
      onCreateBranch(newBranchName.trim());
      setNewBranchName('');
      setShowNewBranch(false);
    }
  };

  return (
    <div className={cn('flex flex-col h-full bg-background', className)}>
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-primary" />
            <span className="font-semibold">버전 관리</span>
          </div>
          <Badge variant="outline" className="text-xs">
            {currentBranch}
          </Badge>
        </div>

        {/* Uncommitted changes warning */}
        {hasUncommittedChanges && (
          <div className="flex items-center gap-2 p-2 bg-yellow-50 border border-yellow-200 rounded-lg mb-3">
            <AlertTriangle className="w-4 h-4 text-yellow-600" />
            <span className="text-xs text-yellow-700">저장되지 않은 변경사항이 있습니다</span>
          </div>
        )}

        {/* Quick commit */}
        <div className="flex gap-2">
          <input
            type="text"
            value={commitMessage}
            onChange={(e) => setCommitMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCommit()}
            placeholder="커밋 메시지..."
            className="flex-1 px-3 py-2 text-sm border rounded-md"
          />
          <Button onClick={handleCommit} disabled={!commitMessage.trim()}>
            <GitCommit className="w-4 h-4 mr-1" />
            커밋
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="commits" className="flex-1 flex flex-col">
        <TabsList className="mx-4 mt-2">
          <TabsTrigger value="commits" className="gap-1 text-xs">
            <GitCommit className="w-3 h-3" />
            커밋
          </TabsTrigger>
          <TabsTrigger value="branches" className="gap-1 text-xs">
            <GitBranch className="w-3 h-3" />
            브랜치
          </TabsTrigger>
          <TabsTrigger value="deploy" className="gap-1 text-xs">
            <Rocket className="w-3 h-3" />
            배포
          </TabsTrigger>
        </TabsList>

        {/* Commits tab */}
        <TabsContent value="commits" className="flex-1 m-0 overflow-hidden">
          <ScrollArea className="h-full p-4">
            <div className="space-y-3">
              {commits.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <GitCommit className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">아직 커밋이 없습니다</p>
                </div>
              ) : (
                commits.map(commit => (
                  <CommitItem
                    key={commit.id}
                    commit={commit}
                    onRevert={() => onRevert(commit.id)}
                    onViewDetails={() => {}}
                  />
                ))
              )}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Branches tab */}
        <TabsContent value="branches" className="flex-1 m-0 overflow-hidden">
          <ScrollArea className="h-full p-4">
            <div className="space-y-3">
              {/* New branch button */}
              {showNewBranch ? (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newBranchName}
                    onChange={(e) => setNewBranchName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleCreateBranch()}
                    placeholder="브랜치 이름..."
                    className="flex-1 px-3 py-2 text-sm border rounded-md"
                    autoFocus
                  />
                  <Button size="sm" onClick={handleCreateBranch}>
                    생성
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setShowNewBranch(false)}>
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ) : (
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setShowNewBranch(true)}
                >
                  <Plus className="w-4 h-4 mr-1" />
                  새 브랜치
                </Button>
              )}

              {branches.map(branch => (
                <BranchItem
                  key={branch.id}
                  branch={branch}
                  onSwitch={() => onSwitchBranch(branch.id)}
                  onMerge={() => onMerge(branch.name, currentBranch)}
                />
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        {/* Deploy tab */}
        <TabsContent value="deploy" className="flex-1 m-0 overflow-hidden">
          <ScrollArea className="h-full p-4">
            <div className="space-y-3">
              {environments.map(env => (
                <div
                  key={env.id}
                  className="flex items-center gap-3 p-4 rounded-lg border"
                >
                  <div className={cn(
                    'p-2 rounded-lg',
                    env.name === 'production' ? 'bg-red-100' : 
                    env.name === 'staging' ? 'bg-yellow-100' : 'bg-blue-100'
                  )}>
                    {env.name === 'production' ? (
                      <Shield className="w-5 h-5 text-red-600" />
                    ) : (
                      <Rocket className="w-5 h-5 text-blue-600" />
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium capitalize">{env.name}</span>
                      <EnvironmentStatusBadge status={env.status} />
                    </div>
                    {env.currentVersion && (
                      <p className="text-xs text-muted-foreground mt-0.5">
                        버전: {env.currentVersion}
                      </p>
                    )}
                    {env.lastDeployed && (
                      <p className="text-xs text-muted-foreground">
                        마지막 배포: {env.lastDeployed.toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant={env.name === 'production' ? 'destructive' : 'default'}
                    onClick={() => onDeploy(env.id)}
                  >
                    <Upload className="w-4 h-4 mr-1" />
                    배포
                  </Button>
                </div>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default VersionControlPanel;
