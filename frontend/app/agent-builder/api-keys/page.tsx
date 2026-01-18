'use client';

import { useState, useEffect } from 'react';
import {
  Key,
  Plus,
  Copy,
  Trash,
  Eye,
  EyeOff,
  RefreshCw,
  Shield,
  Clock,
  Activity,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';

interface APIKey {
  id: string;
  name: string;
  key: string;
  prefix: string;
  permissions: string[];
  rate_limit: number;
  expires_at?: string;
  last_used_at?: string;
  usage_count: number;
  is_active: boolean;
  created_at: string;
}

const PERMISSIONS = [
  { id: 'agentflows:read', label: 'Read Agentflows', description: 'View agentflow list and details' },
  { id: 'agentflows:write', label: 'Write Agentflows', description: 'Create, update, delete agentflows' },
  { id: 'agentflows:execute', label: 'Execute Agentflows', description: 'Execute agentflows' },
  { id: 'chatflows:read', label: 'Read Chatflows', description: 'View chatflow list and details' },
  { id: 'chatflows:write', label: 'Write Chatflows', description: 'Create, update, delete chatflows' },
  { id: 'chatflows:execute', label: 'Execute Chatflows', description: 'Execute chatflow conversations' },
  { id: 'workflows:read', label: 'Read Workflows', description: 'View workflow list and details' },
  { id: 'workflows:write', label: 'Write Workflows', description: 'Create, update, delete workflows' },
  { id: 'workflows:execute', label: 'Execute Workflows', description: 'Execute workflows' },
  { id: 'knowledgebases:read', label: 'Read Knowledgebases', description: 'View and search knowledgebases' },
  { id: 'knowledgebases:write', label: 'Write Knowledgebases', description: 'Create knowledgebases, upload documents' },
];

export default function APIKeysPage() {
  const { toast } = useToast();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState<string | null>(null);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [newKeyVisible, setNewKeyVisible] = useState(false);
  const [newKey, setNewKey] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    permissions: [] as string[],
    rate_limit: 1000,
    expires_in: 'never',
  });

  useEffect(() => {
    loadAPIKeys();
  }, []);

  const loadAPIKeys = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockKeys: APIKey[] = [
        {
          id: '1',
          name: 'Production API Key',
          key: 'ak_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxx',
          prefix: 'ak_live_',
          permissions: ['agentflows:execute', 'chatflows:execute', 'workflows:execute'],
          rate_limit: 1000,
          last_used_at: new Date().toISOString(),
          usage_count: 15234,
          is_active: true,
          created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '2',
          name: 'Development API Key',
          key: 'ak_test_yyyyyyyyyyyyyyyyyyyyyyyyyyyy',
          prefix: 'ak_test_',
          permissions: ['agentflows:read', 'agentflows:write', 'chatflows:read', 'chatflows:write'],
          rate_limit: 100,
          expires_at: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
          last_used_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
          usage_count: 523,
          is_active: true,
          created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        },
      ];
      setApiKeys(mockKeys);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load API keys',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async () => {
    try {
      // Mock API call - replace with actual implementation
      const generatedKey = `ak_${formData.expires_in === 'never' ? 'live' : 'test'}_${Math.random().toString(36).substring(2, 34)}`;
      setNewKey(generatedKey);
      setNewKeyVisible(true);
      
      toast({
        title: 'API Key Created',
        description: 'New API key has been created. Please save it in a secure location.',
      });
      
      loadAPIKeys();
      setCreateDialogOpen(false);
      setFormData({
        name: '',
        permissions: [],
        rate_limit: 1000,
        expires_in: 'never',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create API key',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteKey = async () => {
    if (!keyToDelete) return;

    try {
      // Mock API call
      setApiKeys(apiKeys.filter((k) => k.id !== keyToDelete));
      toast({
        title: 'Deleted',
        description: 'API key has been deleted',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete API key',
        variant: 'destructive',
      });
    } finally {
      setDeleteDialogOpen(false);
      setKeyToDelete(null);
    }
  };

  const toggleKeyVisibility = (keyId: string) => {
    const newVisible = new Set(visibleKeys);
    if (newVisible.has(keyId)) {
      newVisible.delete(keyId);
    } else {
      newVisible.add(keyId);
    }
    setVisibleKeys(newVisible);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: 'API key has been copied to clipboard',
    });
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Key className="h-8 w-8 text-yellow-500" />
            API Keys
          </h1>
          <p className="text-muted-foreground mt-1">
            Create and manage API keys to access from external applications
          </p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New API Key
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                Create a new API key. The key will only be shown once after creation.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Key Name</Label>
                <Input
                  id="name"
                  placeholder="e.g., Production API Key"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>

              <div className="space-y-2">
                <Label>Permissions</Label>
                <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto border rounded-md p-3">
                  {PERMISSIONS.map((permission) => (
                    <div key={permission.id} className="flex items-start space-x-2">
                      <Checkbox
                        id={permission.id}
                        checked={formData.permissions.includes(permission.id)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setFormData({
                              ...formData,
                              permissions: [...formData.permissions, permission.id],
                            });
                          } else {
                            setFormData({
                              ...formData,
                              permissions: formData.permissions.filter((p) => p !== permission.id),
                            });
                          }
                        }}
                      />
                      <div className="grid gap-0.5 leading-none">
                        <label
                          htmlFor={permission.id}
                          className="text-sm font-medium cursor-pointer"
                        >
                          {permission.label}
                        </label>
                        <p className="text-xs text-muted-foreground">{permission.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="rate_limit">Rate Limit (requests/min)</Label>
                <Input
                  id="rate_limit"
                  type="number"
                  value={formData.rate_limit}
                  onChange={(e) =>
                    setFormData({ ...formData, rate_limit: parseInt(e.target.value) || 0 })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="expires">Expiration Period</Label>
                <Select
                  value={formData.expires_in}
                  onValueChange={(v) => setFormData({ ...formData, expires_in: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="never">Never Expires</SelectItem>
                    <SelectItem value="30d">30 Days</SelectItem>
                    <SelectItem value="90d">90 Days</SelectItem>
                    <SelectItem value="1y">1 Year</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateKey} disabled={!formData.name || formData.permissions.length === 0}>
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* New Key Alert */}
      {newKey && newKeyVisible && (
        <Card className="mb-6 border-green-500 bg-green-50 dark:bg-green-950">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-green-700 dark:text-green-300 flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                New API Key Created
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setNewKeyVisible(false)}>
                Close
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2 p-3 bg-white dark:bg-gray-900 rounded-md font-mono text-sm">
              <code className="flex-1 break-all">{newKey}</code>
              <Button variant="ghost" size="icon" onClick={() => copyToClipboard(newKey)}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-sm text-yellow-600 dark:text-yellow-400 mt-2 flex items-center gap-1">
              <AlertTriangle className="h-4 w-4" />
              This key will not be shown again. Please save it in a secure location.
            </p>
          </CardContent>
        </Card>
      )}

      {/* API Keys List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-32 mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-10 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : apiKeys.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Key className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No API Keys</h3>
            <p className="text-muted-foreground mb-4">
              Create your first API key to access from external applications
            </p>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create New API Key
            </Button>
          </div>
        </Card>
      ) : (
        <div className="space-y-4">
          {apiKeys.map((apiKey) => (
            <Card key={apiKey.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      {apiKey.name}
                      {apiKey.is_active ? (
                        <Badge variant="default">Active</Badge>
                      ) : (
                        <Badge variant="secondary">Inactive</Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      Created: {new Date(apiKey.created_at).toLocaleDateString()}
                      {apiKey.expires_at && (
                        <> · Expires: {new Date(apiKey.expires_at).toLocaleDateString()}</>
                      )}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        setKeyToDelete(apiKey.id);
                        setDeleteDialogOpen(true);
                      }}
                    >
                      <Trash className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* API Key Display */}
                <div className="flex items-center gap-2 p-3 bg-muted rounded-md font-mono text-sm">
                  <code className="flex-1">
                    {visibleKeys.has(apiKey.id)
                      ? apiKey.key
                      : `${apiKey.prefix}${'•'.repeat(24)}`}
                  </code>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => toggleKeyVisibility(apiKey.id)}
                  >
                    {visibleKeys.has(apiKey.id) ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => copyToClipboard(apiKey.key)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Usage:</span>
                    <span className="font-medium">{apiKey.usage_count.toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Last used:</span>
                    <span className="font-medium">
                      {apiKey.last_used_at ? formatTimeAgo(apiKey.last_used_at) : 'Never'}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Rate Limit:</span>
                    <span className="font-medium">{apiKey.rate_limit}/min</span>
                  </div>
                </div>

                {/* Permissions */}
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Permissions:</p>
                  <div className="flex flex-wrap gap-1">
                    {apiKey.permissions.map((perm) => (
                      <Badge key={perm} variant="outline" className="text-xs">
                        {perm}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete API Key</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this API key? All applications using this key will stop working.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteKey}
              className="bg-destructive text-destructive-foreground"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
