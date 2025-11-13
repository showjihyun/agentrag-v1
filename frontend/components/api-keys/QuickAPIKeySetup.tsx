'use client';

import React, { useState, useEffect } from 'react';
import { Key, ExternalLink, CheckCircle, AlertCircle, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { apiKeysAPI, getServiceInfo } from '@/lib/api/api-keys';
import Link from 'next/link';

interface QuickAPIKeySetupProps {
  serviceName: string;
  onKeyAdded?: () => void;
  compact?: boolean;
}

export function QuickAPIKeySetup({ serviceName, onKeyAdded, compact = false }: QuickAPIKeySetupProps) {
  const { toast } = useToast();
  const [hasKey, setHasKey] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const serviceInfo = getServiceInfo(serviceName);

  useEffect(() => {
    checkAPIKey();
  }, [serviceName]);

  const checkAPIKey = async () => {
    try {
      setLoading(true);
      const response = await apiKeysAPI.listAPIKeys();
      const exists = response.api_keys.some(
        (key) => key.service_name === serviceName && key.is_active
      );
      setHasKey(exists);
    } catch (error) {
      console.error('Failed to check API key:', error);
      setHasKey(false);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!apiKey.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Please enter an API key',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSubmitting(true);
      await apiKeysAPI.createAPIKey({
        service_name: serviceName,
        service_display_name: serviceInfo?.displayName || serviceName,
        api_key: apiKey,
      });

      toast({
        title: 'Success',
        description: `${serviceInfo?.displayName || serviceName} API key added successfully`,
      });

      setDialogOpen(false);
      setApiKey('');
      setHasKey(true);
      
      if (onKeyAdded) {
        onKeyAdded();
      }
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

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
        <span>Checking API key...</span>
      </div>
    );
  }

  if (compact) {
    return (
      <>
        {hasKey ? (
          <Badge variant="default" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            API Key Configured
          </Badge>
        ) : (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDialogOpen(true)}
            className="gap-2"
          >
            <Key className="h-3 w-3" />
            Add API Key
          </Button>
        )}

        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                {serviceInfo?.icon && <span className="text-2xl">{serviceInfo.icon}</span>}
                Add {serviceInfo?.displayName || serviceName} API Key
              </DialogTitle>
              <DialogDescription>
                {serviceInfo?.description || 'Enter your API key to use this service'}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="quickApiKey">API Key</Label>
                <Input
                  id="quickApiKey"
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleAdd();
                    }
                  }}
                />
                {serviceInfo?.getKeyUrl && (
                  <p className="text-xs text-muted-foreground mt-2">
                    <a
                      href={serviceInfo.getKeyUrl}
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
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAdd} disabled={submitting}>
                {submitting ? 'Adding...' : 'Add API Key'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </>
    );
  }

  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {serviceInfo?.icon && (
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center text-xl"
              style={{ backgroundColor: `${serviceInfo.color}20` }}
            >
              {serviceInfo.icon}
            </div>
          )}
          <div>
            <h4 className="font-medium">{serviceInfo?.displayName || serviceName}</h4>
            <p className="text-sm text-muted-foreground">
              {serviceInfo?.description || 'API key required'}
            </p>
          </div>
        </div>
        {hasKey ? (
          <Badge variant="default" className="gap-1">
            <CheckCircle className="h-3 w-3" />
            Configured
          </Badge>
        ) : (
          <Badge variant="secondary" className="gap-1">
            <AlertCircle className="h-3 w-3" />
            Not Configured
          </Badge>
        )}
      </div>

      {!hasKey && (
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setDialogOpen(true)}
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            Add API Key
          </Button>
          <Link href="/agent-builder/settings/api-keys">
            <Button variant="ghost" size="sm">
              Manage All Keys
            </Button>
          </Link>
        </div>
      )}

      {hasKey && (
        <div className="flex gap-2">
          <Link href="/agent-builder/settings/api-keys">
            <Button variant="outline" size="sm">
              Manage API Keys
            </Button>
          </Link>
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {serviceInfo?.icon && <span className="text-2xl">{serviceInfo.icon}</span>}
              Add {serviceInfo?.displayName || serviceName} API Key
            </DialogTitle>
            <DialogDescription>
              {serviceInfo?.description || 'Enter your API key to use this service'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="apiKey">API Key</Label>
              <Input
                id="apiKey"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleAdd();
                  }
                }}
              />
              {serviceInfo?.getKeyUrl && (
                <p className="text-xs text-muted-foreground mt-2">
                  <a
                    href={serviceInfo.getKeyUrl}
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
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAdd} disabled={submitting}>
              {submitting ? 'Adding...' : 'Add API Key'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
