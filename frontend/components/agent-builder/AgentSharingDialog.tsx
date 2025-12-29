'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  Share,
  Users,
  Link,
  Copy,
  Mail,
  Eye,
  Edit,
  Trash,
  Crown,
  Shield,
  UserPlus,
  Check,
  X,
  Globe,
  Lock,
} from 'lucide-react';

interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
}

interface SharePermission {
  id: string;
  user_id: string;
  user: User;
  permission: 'read' | 'write' | 'admin';
  granted_at: string;
  granted_by: string;
}

interface AgentSharingDialogProps {
  agentId: string;
  agentName: string;
  isPublic: boolean;
  trigger?: React.ReactNode;
  onVisibilityChange?: (isPublic: boolean) => void;
}

const PERMISSION_LEVELS = [
  {
    value: 'read',
    label: '보기',
    description: '에이전트 보기 및 실행',
    icon: Eye,
    color: 'text-blue-600',
  },
  {
    value: 'write',
    label: '편집',
    description: '에이전트 수정 및 실행',
    icon: Edit,
    color: 'text-green-600',
  },
  {
    value: 'admin',
    label: '관리자',
    description: '모든 권한 (삭제, 공유 관리)',
    icon: Crown,
    color: 'text-purple-600',
  },
];

export function AgentSharingDialog({
  agentId,
  agentName,
  isPublic,
  trigger,
  onVisibilityChange,
}: AgentSharingDialogProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [shareEmail, setShareEmail] = useState('');
  const [sharePermission, setSharePermission] = useState<'read' | 'write' | 'admin'>('read');
  const [shareMessage, setShareMessage] = useState('');
  const [showUserSearch, setShowUserSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch current sharing settings
  const { data: sharingData, isLoading } = useQuery({
    queryKey: ['agent-sharing', agentId],
    queryFn: () => agentBuilderAPI.getAgentSharing(agentId),
    enabled: open,
  });

  // Fetch users for search
  const { data: usersData } = useQuery({
    queryKey: ['users-search', searchQuery],
    queryFn: () => agentBuilderAPI.searchUsers(searchQuery),
    enabled: searchQuery.length > 2,
  });

  // Share agent mutation
  const shareAgentMutation = useMutation({
    mutationFn: (data: { email: string; permission: string; message?: string }) =>
      agentBuilderAPI.shareAgent(agentId, data),
    onSuccess: () => {
      toast({
        title: '공유 완료',
        description: '에이전트가 성공적으로 공유되었습니다',
      });
      queryClient.invalidateQueries({ queryKey: ['agent-sharing', agentId] });
      setShareEmail('');
      setShareMessage('');
    },
    onError: (error: any) => {
      toast({
        title: '공유 실패',
        description: error.message || '에이전트 공유에 실패했습니다',
        variant: 'destructive',
      });
    },
  });

  // Update permission mutation
  const updatePermissionMutation = useMutation({
    mutationFn: (data: { userId: string; permission: string }) =>
      agentBuilderAPI.updateAgentPermission(agentId, data.userId, data.permission),
    onSuccess: () => {
      toast({
        title: '권한 업데이트',
        description: '사용자 권한이 업데이트되었습니다',
      });
      queryClient.invalidateQueries({ queryKey: ['agent-sharing', agentId] });
    },
  });

  // Remove permission mutation
  const removePermissionMutation = useMutation({
    mutationFn: (userId: string) =>
      agentBuilderAPI.removeAgentPermission(agentId, userId),
    onSuccess: () => {
      toast({
        title: '권한 제거',
        description: '사용자 권한이 제거되었습니다',
      });
      queryClient.invalidateQueries({ queryKey: ['agent-sharing', agentId] });
    },
  });

  // Toggle public visibility
  const togglePublicMutation = useMutation({
    mutationFn: (isPublic: boolean) =>
      agentBuilderAPI.updateAgent(agentId, { is_public: isPublic }),
    onSuccess: (_, isPublic) => {
      toast({
        title: isPublic ? '공개 설정' : '비공개 설정',
        description: `에이전트가 ${isPublic ? '공개' : '비공개'}로 설정되었습니다`,
      });
      onVisibilityChange?.(isPublic);
    },
  });

  const handleShare = () => {
    if (!shareEmail) {
      toast({
        title: '오류',
        description: '이메일을 입력해주세요',
        variant: 'destructive',
      });
      return;
    }

    shareAgentMutation.mutate({
      email: shareEmail,
      permission: sharePermission,
      message: shareMessage,
    });
  };

  const handleUserSelect = (user: User) => {
    setShareEmail(user.email);
    setShowUserSearch(false);
    setSearchQuery('');
  };

  const copyShareLink = async () => {
    const shareLink = `${window.location.origin}/agent-builder/agents/${agentId}`;
    try {
      await navigator.clipboard.writeText(shareLink);
      toast({
        title: '링크 복사됨',
        description: '공유 링크가 클립보드에 복사되었습니다',
      });
    } catch (error) {
      toast({
        title: '복사 실패',
        description: '링크 복사에 실패했습니다',
        variant: 'destructive',
      });
    }
  };

  const getPermissionIcon = (permission: string) => {
    const perm = PERMISSION_LEVELS.find(p => p.value === permission);
    return perm ? perm.icon : Eye;
  };

  const getPermissionColor = (permission: string) => {
    const perm = PERMISSION_LEVELS.find(p => p.value === permission);
    return perm ? perm.color : 'text-gray-600';
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline" className="gap-2">
            <Share className="h-4 w-4" />
            공유
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Share className="h-5 w-5" />
            {agentName} 공유
          </DialogTitle>
          <DialogDescription>
            에이전트를 다른 사용자와 공유하고 권한을 관리하세요
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Public Visibility */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label className="text-base font-medium">공개 설정</Label>
                <p className="text-sm text-muted-foreground">
                  모든 사용자가 이 에이전트를 검색하고 사용할 수 있습니다
                </p>
              </div>
              <Switch
                checked={isPublic}
                onCheckedChange={(checked) => togglePublicMutation.mutate(checked)}
                disabled={togglePublicMutation.isPending}
              />
            </div>

            {isPublic && (
              <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                    공개 에이전트
                  </span>
                </div>
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  이 에이전트는 모든 사용자에게 공개되어 있습니다
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={copyShareLink}
                  className="mt-2 gap-2"
                >
                  <Link className="h-3 w-3" />
                  공유 링크 복사
                </Button>
              </div>
            )}
          </div>

          <Separator />

          {/* Direct Sharing */}
          <div className="space-y-4">
            <div>
              <Label className="text-base font-medium">사용자 초대</Label>
              <p className="text-sm text-muted-foreground">
                특정 사용자에게 에이전트 접근 권한을 부여하세요
              </p>
            </div>

            <div className="space-y-3">
              <div className="space-y-2">
                <Label>사용자 이메일</Label>
                <div className="relative">
                  <Input
                    placeholder="user@example.com"
                    value={shareEmail}
                    onChange={(e) => setShareEmail(e.target.value)}
                    onFocus={() => setShowUserSearch(true)}
                  />
                  {showUserSearch && (
                    <div className="absolute top-full left-0 right-0 z-10 mt-1">
                      <Command className="border rounded-md shadow-md bg-background">
                        <CommandInput
                          placeholder="사용자 검색..."
                          value={searchQuery}
                          onValueChange={setSearchQuery}
                        />
                        <CommandEmpty>사용자를 찾을 수 없습니다</CommandEmpty>
                        <CommandGroup>
                          {usersData?.users?.map((user: User) => (
                            <CommandItem
                              key={user.id}
                              onSelect={() => handleUserSelect(user)}
                              className="flex items-center gap-2"
                            >
                              <Avatar className="h-6 w-6">
                                <AvatarImage src={user.avatar} />
                                <AvatarFallback className="text-xs">
                                  {user.name.substring(0, 2).toUpperCase()}
                                </AvatarFallback>
                              </Avatar>
                              <div>
                                <p className="text-sm font-medium">{user.name}</p>
                                <p className="text-xs text-muted-foreground">{user.email}</p>
                              </div>
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </Command>
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <Label>권한 수준</Label>
                <Select value={sharePermission} onValueChange={(value: any) => setSharePermission(value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PERMISSION_LEVELS.map((level) => {
                      const Icon = level.icon;
                      return (
                        <SelectItem key={level.value} value={level.value}>
                          <div className="flex items-center gap-2">
                            <Icon className={`h-4 w-4 ${level.color}`} />
                            <div>
                              <p className="font-medium">{level.label}</p>
                              <p className="text-xs text-muted-foreground">{level.description}</p>
                            </div>
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>메시지 (선택사항)</Label>
                <Textarea
                  placeholder="공유와 함께 보낼 메시지를 입력하세요..."
                  value={shareMessage}
                  onChange={(e) => setShareMessage(e.target.value)}
                  rows={3}
                />
              </div>

              <Button
                onClick={handleShare}
                disabled={shareAgentMutation.isPending || !shareEmail}
                className="w-full gap-2"
              >
                <UserPlus className="h-4 w-4" />
                {shareAgentMutation.isPending ? '공유 중...' : '사용자 초대'}
              </Button>
            </div>
          </div>

          <Separator />

          {/* Current Permissions */}
          <div className="space-y-4">
            <div>
              <Label className="text-base font-medium">현재 공유 상태</Label>
              <p className="text-sm text-muted-foreground">
                이 에이전트에 접근 권한이 있는 사용자들
              </p>
            </div>

            {isLoading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 border rounded-lg">
                    <div className="h-8 w-8 bg-muted rounded-full animate-pulse" />
                    <div className="flex-1 space-y-1">
                      <div className="h-4 bg-muted rounded animate-pulse" />
                      <div className="h-3 bg-muted rounded w-2/3 animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : sharingData?.permissions?.length > 0 ? (
              <div className="space-y-2">
                {sharingData.permissions.map((permission: SharePermission) => {
                  const PermissionIcon = getPermissionIcon(permission.permission);
                  return (
                    <div key={permission.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={permission.user.avatar} />
                          <AvatarFallback>
                            {permission.user.name.substring(0, 2).toUpperCase()}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{permission.user.name}</p>
                          <p className="text-sm text-muted-foreground">{permission.user.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="gap-1">
                          <PermissionIcon className={`h-3 w-3 ${getPermissionColor(permission.permission)}`} />
                          {PERMISSION_LEVELS.find(p => p.value === permission.permission)?.label}
                        </Badge>
                        <Select
                          value={permission.permission}
                          onValueChange={(value) => updatePermissionMutation.mutate({
                            userId: permission.user_id,
                            permission: value
                          })}
                        >
                          <SelectTrigger className="w-24 h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {PERMISSION_LEVELS.map((level) => (
                              <SelectItem key={level.value} value={level.value}>
                                {level.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removePermissionMutation.mutate(permission.user_id)}
                          className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                <Lock className="h-8 w-8 mx-auto mb-2" />
                <p>아직 공유된 사용자가 없습니다</p>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}