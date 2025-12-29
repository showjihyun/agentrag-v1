'use client';

import React, { useEffect, useState } from 'react';
import { Plus, Key, Trash, Edit, TestTube, ExternalLink, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiKeysAPI, APIKey, SUPPORTED_SERVICES, getServiceInfo } from '@/lib/api/api-keys';

export default function APIKeysPage() {
  const { toast } = useToast();
  const [apiKeys, setApiKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedKey, setSelectedKey] = useState<APIKey | null>(null);
  const [testing, setTesting] = useState<string | null>(null);

  // Form state
  const [serviceName, setServiceName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadAPIKeys();
  }, []);

  const loadAPIKeys = async () => {
    try {
      setLoading(true);
      const response = await apiKeysAPI.listAPIKeys();
      setApiKeys(response.api_keys || []);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to load API keys',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!serviceName || !apiKey) {
      toast({
        title: 'Validation Error',
        description: 'Please select a service and enter an API key',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSubmitting(true);
      const serviceInfo = getServiceInfo(serviceName);
      
      await apiKeysAPI.createAPIKey({
        service_name: serviceName,
        service_display_name: serviceInfo?.displayName || serviceName,
        api_key: apiKey,
        ...(description && { description }),
      });

      toast({
        title: 'Success',
        description: 'API key added successfully',
      });

      setAddDialogOpen(false);
      resetForm();
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to add API key',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = async () => {
    if (!selectedKey) return;

    try {
      setSubmitting(true);
      await apiKeysAPI.updateAPIKey(selectedKey.id, {
        ...(apiKey && { api_key: apiKey }),
        ...(description && { description }),
      });

      toast({
        title: 'Success',
        description: 'API key updated successfully',
      });

      setEditDialogOpen(false);
      resetForm();
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to update API key',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedKey) return;

    try {
      await apiKeysAPI.deleteAPIKey(selectedKey.id);

      toast({
        title: 'Success',
        description: 'API key deleted successfully',
      });

      setDeleteDialogOpen(false);
      setSelectedKey(null);
      loadAPIKeys();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete API key',
        variant: 'destructive',
      });
    }
  };

  const handleTest = async (key: APIKey) => {
    try {
      setTesting(key.id);
      const result = await apiKeysAPI.testAPIKey(key.service_name);

      if (result.success) {
        toast({
          title: 'Test Successful',
          description: result.message,
        });
      } else {
        toast({
          title: 'Test Failed',
          description: result.message,
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      toast({
        title: 'Test Failed',
        description: error.message || 'Failed to test API key',
        variant: 'destructive',
      });
    } finally {
      setTesting(null);
    }
  };

  const resetForm = () => {
    setServiceName('');
    setApiKey('');
    setDescription('');
    setSelectedKey(null);
  };

  const openEditDialog = (key: APIKey) => {
    setSelectedKey(key);
    setDescription(key.description || '');
    setApiKey('');
    setEditDialogOpen(true);
  };

  const openDeleteDialog = (key: APIKey) => {
    setSelectedKey(key);
    setDeleteDialogOpen(true);
  };

  // Get services that don't have keys yet
  const availableServices = SUPPORTED_SERVICES.filter(
    service => !apiKeys.some(key => key.service_name === service.name)
  );

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Key className="h-8 w-8" />
            API Keys
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your API keys for external services
          </p>
        </div>
        <Button onClick={() => setAddDialogOpen(true)} disabled={availableServices.length === 0}>
          <Plus className="mr-2 h-4 w-4" />
          Add API Key
        </Button>
      </div>

      {/* Info Card */}
      <Card className="mb-6 border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm text-blue-900 font-medium">Secure Storage</p>
              <p className="text-sm text-blue-700 mt-1">
                Your API keys are encrypted and stored securely. They are only used when you execute workflows or agents that require them.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : apiKeys.length === 0 ? (
        <Card className="p-12">
          <div className="text-center">
            <Key className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No API Keys Yet</h3>
            <p className="text-muted-foreground mb-4">
              Add your first API key to start using external services in your workflows
            </p>
            <Button onClick={() => setAddDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add API Key
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {apiKeys.map((key) => {
            const serviceInfo = getServiceInfo(key.service_name);
            return (
              <Card key={key.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
                        style={{ backgroundColor: `${serviceInfo?.color}20` }}
                      >
                        {serviceInfo?.icon || '🔑'}
                      </div>
                      <div>
                        <CardTitle className="text-lg">{key.service_display_name}</CardTitle>
                        <CardDescription className="mt-1">
                          {key.description || serviceInfo?.description}
                        </CardDescription>
                      </div>
                    </div>
                    <Badge variant={key.is_active ? 'default' : 'secondary'}>
                      {key.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        <span>
                          {key.last_used_at
                            ? `Used ${new Date(key.last_used_at).toLocaleDateString()}`
                            : 'Never used'}
                        </span>
                      </div>
                      <div>
                        <span className="font-medium">{key.usage_count}</span> uses
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTest(key)}
                        disabled={testing === key.id}
                      >
                        <TestTube className="mr-2 h-4 w-4" />
                        {testing === key.id ? 'Testing...' : 'Test'}
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openEditDialog(key)}
                      >
                        <Edit className="mr-2 h-4 w-4" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openDeleteDialog(key)}
                      >
                        <Trash className="mr-2 h-4 w-4" />
                        Delete
                      </Button>
                      {serviceInfo?.docsUrl && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(serviceInfo.docsUrl, '_blank')}
                        >
                          <ExternalLink className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add API Key Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add API Key</DialogTitle>
            <DialogDescription>
              Add a new API key for an external service
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="service">Service</Label>
              <Select value={serviceName} onValueChange={setServiceName}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a service" />
                </SelectTrigger>
                <SelectContent>
                  {availableServices.map((service) => (
                    <SelectItem key={service.name} value={service.name}>
                      <div className="flex items-center gap-2">
                        <span>{service.icon}</span>
                        <span>{service.displayName}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {serviceName && getServiceInfo(serviceName)?.getKeyUrl && (
                <p className="text-xs text-muted-foreground mt-1">
                  <a
                    href={getServiceInfo(serviceName)!.getKeyUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline inline-flex items-center gap-1"
                  >
                    Get API key here
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </p>
              )}
            </div>
            <div>
              <Label htmlFor="apiKey">API Key</Label>
              <Input
                id="apiKey"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
              />
            </div>
            <div>
              <Label htmlFor="description">Description (Optional)</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add a note about this API key"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAdd} disabled={submitting}>
              {submitting ? 'Adding...' : 'Add API Key'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit API Key Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Edit API Key</DialogTitle>
            <DialogDescription>
              Update your API key for {selectedKey?.service_display_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="editApiKey">New API Key (Optional)</Label>
              <Input
                id="editApiKey"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Leave empty to keep current key"
              />
            </div>
            <div>
              <Label htmlFor="editDescription">Description</Label>
              <Textarea
                id="editDescription"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add a note about this API key"
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleEdit} disabled={submitting}>
              {submitting ? 'Updating...' : 'Update'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete API Key</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the API key for{' '}
              <strong>{selectedKey?.service_display_name}</strong>?
              <br />
              <br />
              Workflows and agents using this service will fall back to environment variables if available.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
