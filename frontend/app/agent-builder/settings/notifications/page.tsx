'use client';

import React, { useState, useEffect } from 'react';
import { Bell, Mail, MessageSquare, Smartphone, Save, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface NotificationSettings {
  // Email notifications
  emailEnabled: boolean;
  emailAddress: string;
  emailOnWorkflowComplete: boolean;
  emailOnWorkflowError: boolean;
  emailOnAgentAlert: boolean;
  emailDigestFrequency: 'realtime' | 'hourly' | 'daily' | 'weekly' | 'never';
  
  // In-app notifications
  inAppEnabled: boolean;
  inAppOnWorkflowComplete: boolean;
  inAppOnWorkflowError: boolean;
  inAppOnAgentAlert: boolean;
  inAppOnSystemUpdate: boolean;
  
  // Slack notifications
  slackEnabled: boolean;
  slackWebhookUrl: string;
  slackOnWorkflowComplete: boolean;
  slackOnWorkflowError: boolean;
  
  // Browser notifications
  browserEnabled: boolean;
  browserOnWorkflowComplete: boolean;
  browserOnWorkflowError: boolean;
}

const defaultSettings: NotificationSettings = {
  emailEnabled: true,
  emailAddress: '',
  emailOnWorkflowComplete: false,
  emailOnWorkflowError: true,
  emailOnAgentAlert: true,
  emailDigestFrequency: 'daily',
  
  inAppEnabled: true,
  inAppOnWorkflowComplete: true,
  inAppOnWorkflowError: true,
  inAppOnAgentAlert: true,
  inAppOnSystemUpdate: true,
  
  slackEnabled: false,
  slackWebhookUrl: '',
  slackOnWorkflowComplete: false,
  slackOnWorkflowError: true,
  
  browserEnabled: false,
  browserOnWorkflowComplete: false,
  browserOnWorkflowError: true,
};

export default function NotificationsPage() {
  const { toast } = useToast();
  const [settings, setSettings] = useState<NotificationSettings>(defaultSettings);
  const [saving, setSaving] = useState(false);
  const [browserPermission, setBrowserPermission] = useState<NotificationPermission>('default');

  useEffect(() => {
    // Load saved settings
    const saved = localStorage.getItem('notification_settings');
    if (saved) {
      try {
        setSettings({ ...defaultSettings, ...JSON.parse(saved) });
      } catch {
        // Invalid JSON in localStorage, use default settings
        console.warn('Failed to parse notification settings from localStorage, using defaults');
      }
    }
    
    // Check browser notification permission
    if ('Notification' in window) {
      setBrowserPermission(Notification.permission);
    }
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      // Save to localStorage as backup
      localStorage.setItem('notification_settings', JSON.stringify(settings));
      
      // Save to backend API
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/agent-builder/user-settings/notifications`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          email_enabled: settings.emailEnabled,
          email_address: settings.emailAddress,
          email_on_workflow_complete: settings.emailOnWorkflowComplete,
          email_on_workflow_error: settings.emailOnWorkflowError,
          email_on_agent_alert: settings.emailOnAgentAlert,
          email_digest_frequency: settings.emailDigestFrequency,
          in_app_enabled: settings.inAppEnabled,
          in_app_on_workflow_complete: settings.inAppOnWorkflowComplete,
          in_app_on_workflow_error: settings.inAppOnWorkflowError,
          in_app_on_agent_alert: settings.inAppOnAgentAlert,
          in_app_on_system_update: settings.inAppOnSystemUpdate,
          slack_enabled: settings.slackEnabled,
          slack_webhook_url: settings.slackWebhookUrl,
          slack_on_workflow_complete: settings.slackOnWorkflowComplete,
          slack_on_workflow_error: settings.slackOnWorkflowError,
          browser_enabled: settings.browserEnabled,
          browser_on_workflow_complete: settings.browserOnWorkflowComplete,
          browser_on_workflow_error: settings.browserOnWorkflowError,
        }),
      });
      
      if (response.ok) {
        toast({
          title: '✅ Settings Saved',
          description: 'Your notification preferences have been updated.',
        });
      } else {
        throw new Error('Failed to save');
      }
    } catch (error) {
      // Still saved to localStorage
      toast({
        title: '✅ Settings Saved Locally',
        description: 'Settings saved to local storage.',
      });
    } finally {
      setSaving(false);
    }
  };

  const requestBrowserPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setBrowserPermission(permission);
      if (permission === 'granted') {
        setSettings({ ...settings, browserEnabled: true });
        toast({
          title: '✅ Permission Granted',
          description: 'Browser notifications are now enabled.',
        });
      }
    }
  };

  const updateSetting = <K extends keyof NotificationSettings>(
    key: K,
    value: NotificationSettings[K]
  ) => {
    setSettings({ ...settings, [key]: value });
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Bell className="h-8 w-8" />
          Notifications
        </h1>
        <p className="text-muted-foreground mt-1">
          Configure how and when you receive notifications
        </p>
      </div>

      <div className="space-y-6">
        {/* Email Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <Mail className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <CardTitle>Email Notifications</CardTitle>
                  <CardDescription>Receive notifications via email</CardDescription>
                </div>
              </div>
              <Switch
                checked={settings.emailEnabled}
                onCheckedChange={(checked) => updateSetting('emailEnabled', checked)}
              />
            </div>
          </CardHeader>
          {settings.emailEnabled && (
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="your@email.com"
                  value={settings.emailAddress}
                  onChange={(e) => updateSetting('emailAddress', e.target.value)}
                />
              </div>
              
              <Separator />
              
              <div className="space-y-3">
                <Label className="text-sm font-medium">Notify me when:</Label>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-complete" className="font-normal">Workflow completes successfully</Label>
                    <Switch
                      id="email-complete"
                      checked={settings.emailOnWorkflowComplete}
                      onCheckedChange={(checked) => updateSetting('emailOnWorkflowComplete', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-error" className="font-normal">Workflow fails or errors</Label>
                    <Switch
                      id="email-error"
                      checked={settings.emailOnWorkflowError}
                      onCheckedChange={(checked) => updateSetting('emailOnWorkflowError', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="email-alert" className="font-normal">Agent requires attention</Label>
                    <Switch
                      id="email-alert"
                      checked={settings.emailOnAgentAlert}
                      onCheckedChange={(checked) => updateSetting('emailOnAgentAlert', checked)}
                    />
                  </div>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <Label>Email Digest Frequency</Label>
                <Select
                  value={settings.emailDigestFrequency}
                  onValueChange={(value: any) => updateSetting('emailDigestFrequency', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="realtime">Real-time (immediate)</SelectItem>
                    <SelectItem value="hourly">Hourly digest</SelectItem>
                    <SelectItem value="daily">Daily digest</SelectItem>
                    <SelectItem value="weekly">Weekly digest</SelectItem>
                    <SelectItem value="never">Never</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          )}
        </Card>

        {/* In-App Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                  <Bell className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle>In-App Notifications</CardTitle>
                  <CardDescription>Show notifications within the application</CardDescription>
                </div>
              </div>
              <Switch
                checked={settings.inAppEnabled}
                onCheckedChange={(checked) => updateSetting('inAppEnabled', checked)}
              />
            </div>
          </CardHeader>
          {settings.inAppEnabled && (
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="inapp-complete" className="font-normal">Workflow completes</Label>
                <Switch
                  id="inapp-complete"
                  checked={settings.inAppOnWorkflowComplete}
                  onCheckedChange={(checked) => updateSetting('inAppOnWorkflowComplete', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="inapp-error" className="font-normal">Workflow errors</Label>
                <Switch
                  id="inapp-error"
                  checked={settings.inAppOnWorkflowError}
                  onCheckedChange={(checked) => updateSetting('inAppOnWorkflowError', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="inapp-alert" className="font-normal">Agent alerts</Label>
                <Switch
                  id="inapp-alert"
                  checked={settings.inAppOnAgentAlert}
                  onCheckedChange={(checked) => updateSetting('inAppOnAgentAlert', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="inapp-system" className="font-normal">System updates</Label>
                <Switch
                  id="inapp-system"
                  checked={settings.inAppOnSystemUpdate}
                  onCheckedChange={(checked) => updateSetting('inAppOnSystemUpdate', checked)}
                />
              </div>
            </CardContent>
          )}
        </Card>

        {/* Slack Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900">
                  <MessageSquare className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <CardTitle>Slack Notifications</CardTitle>
                  <CardDescription>Send notifications to a Slack channel</CardDescription>
                </div>
              </div>
              <Switch
                checked={settings.slackEnabled}
                onCheckedChange={(checked) => updateSetting('slackEnabled', checked)}
              />
            </div>
          </CardHeader>
          {settings.slackEnabled && (
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="slack-webhook">Slack Webhook URL</Label>
                <Input
                  id="slack-webhook"
                  type="password"
                  placeholder="https://hooks.slack.com/services/..."
                  value={settings.slackWebhookUrl}
                  onChange={(e) => updateSetting('slackWebhookUrl', e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  <a
                    href="https://api.slack.com/messaging/webhooks"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline"
                  >
                    Learn how to create a Slack webhook
                  </a>
                </p>
              </div>
              
              <Separator />
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="slack-complete" className="font-normal">Workflow completes</Label>
                  <Switch
                    id="slack-complete"
                    checked={settings.slackOnWorkflowComplete}
                    onCheckedChange={(checked) => updateSetting('slackOnWorkflowComplete', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="slack-error" className="font-normal">Workflow errors</Label>
                  <Switch
                    id="slack-error"
                    checked={settings.slackOnWorkflowError}
                    onCheckedChange={(checked) => updateSetting('slackOnWorkflowError', checked)}
                  />
                </div>
              </div>
            </CardContent>
          )}
        </Card>

        {/* Browser Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-900">
                  <Smartphone className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                </div>
                <div>
                  <CardTitle>Browser Notifications</CardTitle>
                  <CardDescription>Show desktop notifications in your browser</CardDescription>
                </div>
              </div>
              <Switch
                checked={settings.browserEnabled}
                onCheckedChange={(checked) => updateSetting('browserEnabled', checked)}
                disabled={browserPermission !== 'granted'}
              />
            </div>
          </CardHeader>
          <CardContent>
            {browserPermission === 'denied' ? (
              <div className="flex items-center gap-2 text-sm text-destructive">
                <AlertCircle className="h-4 w-4" />
                <span>Browser notifications are blocked. Please enable them in your browser settings.</span>
              </div>
            ) : browserPermission === 'granted' ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  <span>Browser notifications are enabled</span>
                </div>
                {settings.browserEnabled && (
                  <>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <Label htmlFor="browser-complete" className="font-normal">Workflow completes</Label>
                      <Switch
                        id="browser-complete"
                        checked={settings.browserOnWorkflowComplete}
                        onCheckedChange={(checked) => updateSetting('browserOnWorkflowComplete', checked)}
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label htmlFor="browser-error" className="font-normal">Workflow errors</Label>
                      <Switch
                        id="browser-error"
                        checked={settings.browserOnWorkflowError}
                        onCheckedChange={(checked) => updateSetting('browserOnWorkflowError', checked)}
                      />
                    </div>
                  </>
                )}
              </div>
            ) : (
              <Button variant="outline" onClick={requestBrowserPermission}>
                Enable Browser Notifications
              </Button>
            )}
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={saving} size="lg">
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : 'Save Preferences'}
          </Button>
        </div>
      </div>
    </div>
  );
}
