'use client';

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/Toast';
import { Copy, Check, Mail, Link as LinkIcon, Users } from 'lucide-react';

interface ShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  resourceType: 'agent' | 'workflow' | 'block';
  resourceId: string;
  resourceName: string;
}

export function ShareDialog({
  open,
  onOpenChange,
  resourceType,
  resourceId,
  resourceName,
}: ShareDialogProps) {
  const { toast } = useToast();
  const [shareLink, setShareLink] = React.useState('');
  const [copied, setCopied] = React.useState(false);
  const [permission, setPermission] = React.useState<'view' | 'edit' | 'execute'>('view');
  const [email, setEmail] = React.useState('');
  const [sharedWith, setSharedWith] = React.useState<Array<{
    email: string;
    permission: string;
  }>>([]);

  React.useEffect(() => {
    if (open) {
      // Generate share link
      const link = `${window.location.origin}/agent-builder/${resourceType}s/${resourceId}/shared`;
      setShareLink(link);
    }
  }, [open, resourceType, resourceId]);

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(shareLink);
      setCopied(true);
      toast({
        title: 'Link copied',
        description: 'Share link copied to clipboard',
      });
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to copy',
        description: 'Could not copy link to clipboard',
      });
    }
  };

  const handleInviteByEmail = async () => {
    if (!email) return;

    try {
      // TODO: API call to invite user
      setSharedWith([...sharedWith, { email, permission }]);
      setEmail('');
      toast({
        title: 'Invitation sent',
        description: `Invited ${email} with ${permission} permission`,
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Failed to invite',
        description: 'Could not send invitation',
      });
    }
  };

  const handleRemoveAccess = (email: string) => {
    setSharedWith(sharedWith.filter((s) => s.email !== email));
    toast({
      title: 'Access removed',
      description: `Removed access for ${email}`,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Share {resourceType}</DialogTitle>
          <DialogDescription>
            Share "{resourceName}" with others
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Share Link */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <LinkIcon className="h-4 w-4" />
              Share Link
            </Label>
            <div className="flex gap-2">
              <Input value={shareLink} readOnly className="flex-1" />
              <Button
                variant="outline"
                size="icon"
                onClick={handleCopyLink}
              >
                {copied ? (
                  <Check className="h-4 w-4 text-green-500" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Anyone with this link can {permission} this {resourceType}
            </p>
          </div>

          {/* Invite by Email */}
          <div className="space-y-2">
            <Label className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Invite by Email
            </Label>
            <div className="flex gap-2">
              <Input
                type="email"
                placeholder="email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleInviteByEmail();
                  }
                }}
                className="flex-1"
              />
              <Select value={permission} onValueChange={(v: any) => setPermission(v)}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="view">View</SelectItem>
                  <SelectItem value="edit">Edit</SelectItem>
                  <SelectItem value="execute">Execute</SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={handleInviteByEmail} disabled={!email}>
                Invite
              </Button>
            </div>
          </div>

          {/* Shared With */}
          {sharedWith.length > 0 && (
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Users className="h-4 w-4" />
                Shared With
              </Label>
              <div className="space-y-2 max-h-[200px] overflow-y-auto">
                {sharedWith.map((share) => (
                  <div
                    key={share.email}
                    className="flex items-center justify-between p-2 border rounded-md"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{share.email}</span>
                      <Badge variant="outline" className="text-xs">
                        {share.permission}
                      </Badge>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveAccess(share.email)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Done
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
