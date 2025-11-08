'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { Save, RefreshCw } from 'lucide-react';

interface MemorySettingsProps {
  agentId: string;
  onUpdate?: () => void;
}

interface Settings {
  short_term_retention_hours: number;
  auto_consolidation_enabled: boolean;
  consolidation_threshold: number;
  compression_enabled: boolean;
  max_memory_size_mb: number;
  importance_threshold: number;
  auto_cleanup_enabled: boolean;
}

export function MemorySettings({ agentId, onUpdate }: MemorySettingsProps) {
  const { toast } = useToast();
  const [settings, setSettings] = useState<Settings>({
    short_term_retention_hours: 24,
    auto_consolidation_enabled: true,
    consolidation_threshold: 10,
    compression_enabled: true,
    max_memory_size_mb: 100,
    importance_threshold: 0.5,
    auto_cleanup_enabled: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadSettings();
  }, [agentId]);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getMemorySettings(agentId);
      setSettings(data);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await agentBuilderAPI.updateMemorySettings(agentId, settings);
      toast({
        title: 'Settings Saved',
        description: 'Memory settings have been updated',
      });
      if (onUpdate) onUpdate();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save settings',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleConsolidate = async () => {
    try {
      await agentBuilderAPI.consolidateMemories(agentId);
      toast({
        title: 'Consolidation Started',
        description: 'Memory consolidation is in progress',
      });
      if (onUpdate) onUpdate();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to consolidate memories',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Retention Policy</CardTitle>
          <CardDescription>
            Configure how long memories are retained
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="retention">Short-term Memory Retention (hours)</Label>
            <Input
              id="retention"
              type="number"
              value={settings.short_term_retention_hours}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  short_term_retention_hours: parseInt(e.target.value) || 24,
                })
              }
              min={1}
              max={168}
            />
            <p className="text-xs text-muted-foreground">
              Memories older than this will be consolidated or deleted
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto Cleanup</Label>
              <p className="text-xs text-muted-foreground">
                Automatically remove low-importance memories
              </p>
            </div>
            <Switch
              checked={settings.auto_cleanup_enabled}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, auto_cleanup_enabled: checked })
              }
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Consolidation</CardTitle>
          <CardDescription>
            Merge short-term memories into long-term storage
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Auto Consolidation</Label>
              <p className="text-xs text-muted-foreground">
                Automatically consolidate memories
              </p>
            </div>
            <Switch
              checked={settings.auto_consolidation_enabled}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, auto_consolidation_enabled: checked })
              }
            />
          </div>

          <div className="space-y-2">
            <Label>Consolidation Threshold</Label>
            <Slider
              value={[settings.consolidation_threshold]}
              onValueChange={([value]) =>
                setSettings({ ...settings, consolidation_threshold: value })
              }
              min={5}
              max={50}
              step={5}
            />
            <p className="text-xs text-muted-foreground">
              Consolidate when {settings.consolidation_threshold} or more related memories exist
            </p>
          </div>

          <Button onClick={handleConsolidate} variant="outline" className="w-full">
            <RefreshCw className="mr-2 h-4 w-4" />
            Consolidate Now
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Storage & Compression</CardTitle>
          <CardDescription>
            Optimize memory storage
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Compression</Label>
              <p className="text-xs text-muted-foreground">
                Compress memories to save space
              </p>
            </div>
            <Switch
              checked={settings.compression_enabled}
              onCheckedChange={(checked) =>
                setSettings({ ...settings, compression_enabled: checked })
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="max-size">Max Memory Size (MB)</Label>
            <Input
              id="max-size"
              type="number"
              value={settings.max_memory_size_mb}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  max_memory_size_mb: parseInt(e.target.value) || 100,
                })
              }
              min={10}
              max={1000}
            />
          </div>

          <div className="space-y-2">
            <Label>Importance Threshold</Label>
            <Slider
              value={[settings.importance_threshold * 100]}
              onValueChange={([value]) =>
                setSettings({ ...settings, importance_threshold: value / 100 })
              }
              min={0}
              max={100}
              step={5}
            />
            <p className="text-xs text-muted-foreground">
              Only keep memories with importance ≥ {(settings.importance_threshold * 100).toFixed(0)}%
            </p>
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave} disabled={saving} className="w-full">
        <Save className="mr-2 h-4 w-4" />
        {saving ? 'Saving...' : 'Save Settings'}
      </Button>
    </div>
  );
}
