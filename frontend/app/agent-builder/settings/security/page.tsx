'use client';

import React, { useState, useEffect } from 'react';
import { Shield, Key, Lock, Eye, EyeOff, Save, AlertTriangle, CheckCircle, Clock, LogOut, Smartphone } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';

interface SecuritySettings {
  // Password settings
  requireStrongPassword: boolean;
  passwordMinLength: number;
  passwordExpiryDays: number;
  
  // Session settings
  sessionTimeout: number; // minutes
  rememberMe: boolean;
  singleSession: boolean;
  
  // Two-factor authentication
  twoFactorEnabled: boolean;
  twoFactorMethod: 'app' | 'sms' | 'email';
  
  // API security
  apiRateLimitEnabled: boolean;
  apiRateLimitRequests: number;
  apiRateLimitWindow: number; // seconds
  
  // Audit logging
  auditLoggingEnabled: boolean;
  logApiCalls: boolean;
  logWorkflowExecutions: boolean;
  logLoginAttempts: boolean;
}

interface ActiveSession {
  id: string;
  device: string;
  browser: string;
  location: string;
  lastActive: string;
  current: boolean;
}

const defaultSettings: SecuritySettings = {
  requireStrongPassword: true,
  passwordMinLength: 8,
  passwordExpiryDays: 90,
  
  sessionTimeout: 30,
  rememberMe: true,
  singleSession: false,
  
  twoFactorEnabled: false,
  twoFactorMethod: 'app',
  
  apiRateLimitEnabled: true,
  apiRateLimitRequests: 100,
  apiRateLimitWindow: 60,
  
  auditLoggingEnabled: true,
  logApiCalls: true,
  logWorkflowExecutions: true,
  logLoginAttempts: true,
};

export default function SecurityPage() {
  const { toast } = useToast();
  const [settings, setSettings] = useState<SecuritySettings>(defaultSettings);
  const [saving, setSaving] = useState(false);
  const [showPasswordChange, setShowPasswordChange] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);
  
  // Mock active sessions
  const [activeSessions] = useState<ActiveSession[]>([
    {
      id: '1',
      device: 'Windows PC',
      browser: 'Chrome 120',
      location: 'Seoul, South Korea',
      lastActive: 'Now',
      current: true,
    },
    {
      id: '2',
      device: 'MacBook Pro',
      browser: 'Safari 17',
      location: 'Seoul, South Korea',
      lastActive: '2 hours ago',
      current: false,
    },
  ]);

  useEffect(() => {
    const saved = localStorage.getItem('security_settings');
    if (saved) {
      try {
        setSettings({ ...defaultSettings, ...JSON.parse(saved) });
      } catch {
        // Invalid JSON in localStorage, use default settings
        console.warn('Failed to parse security settings from localStorage, using defaults');
      }
    }
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      localStorage.setItem('security_settings', JSON.stringify(settings));
      toast({
        title: '✅ Settings Saved',
        description: 'Your security settings have been updated.',
      });
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to save security settings.',
        variant: 'error',
      });
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    if (newPassword !== confirmPassword) {
      toast({
        title: '❌ Error',
        description: 'New passwords do not match.',
        variant: 'error',
      });
      return;
    }
    
    if (newPassword.length < settings.passwordMinLength) {
      toast({
        title: '❌ Error',
        description: `Password must be at least ${settings.passwordMinLength} characters.`,
        variant: 'error',
      });
      return;
    }
    
    // Call backend API to change password
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v2/auth/change-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        toast({
          title: '✅ Password Changed',
          description: 'Your password has been updated successfully.',
        });
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setShowPasswordChange(false);
      } else {
        toast({
          title: '❌ Error',
          description: data.error?.message || 'Failed to change password.',
          variant: 'error',
        });
      }
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to change password. Please try again.',
        variant: 'error',
      });
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });
      
      toast({
        title: '✅ Session Revoked',
        description: 'The session has been terminated.',
      });
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to revoke session.',
        variant: 'error',
      });
    }
  };

  const handleRevokeAllSessions = async () => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/sessions`, {
        method: 'DELETE',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });
      
      toast({
        title: '✅ All Sessions Revoked',
        description: 'All other sessions have been terminated.',
      });
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to revoke sessions.',
        variant: 'error',
      });
    }
  };

  const updateSetting = <K extends keyof SecuritySettings>(
    key: K,
    value: SecuritySettings[K]
  ) => {
    setSettings({ ...settings, [key]: value });
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Shield className="h-8 w-8" />
          Security
        </h1>
        <p className="text-muted-foreground mt-1">
          Manage your account security and privacy settings
        </p>
      </div>

      <div className="space-y-6">
        {/* Password Settings */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                <Key className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <CardTitle>Password</CardTitle>
                <CardDescription>Manage your password and password policies</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {!showPasswordChange ? (
              <Button variant="outline" onClick={() => setShowPasswordChange(true)}>
                <Lock className="mr-2 h-4 w-4" />
                Change Password
              </Button>
            ) : (
              <div className="space-y-4 p-4 border rounded-lg">
                <div className="space-y-2">
                  <Label htmlFor="current-password">Current Password</Label>
                  <div className="relative">
                    <Input
                      id="current-password"
                      type={showPasswords ? 'text' : 'password'}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new-password">New Password</Label>
                  <Input
                    id="new-password"
                    type={showPasswords ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm-password">Confirm New Password</Label>
                  <Input
                    id="confirm-password"
                    type={showPasswords ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    id="show-passwords"
                    checked={showPasswords}
                    onCheckedChange={setShowPasswords}
                  />
                  <Label htmlFor="show-passwords" className="font-normal">Show passwords</Label>
                </div>
                <div className="flex gap-2">
                  <Button onClick={handlePasswordChange}>Save Password</Button>
                  <Button variant="outline" onClick={() => setShowPasswordChange(false)}>Cancel</Button>
                </div>
              </div>
            )}
            
            <Separator />
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="strong-password">Require strong password</Label>
                  <p className="text-xs text-muted-foreground">Must include uppercase, lowercase, number, and symbol</p>
                </div>
                <Switch
                  id="strong-password"
                  checked={settings.requireStrongPassword}
                  onCheckedChange={(checked) => updateSetting('requireStrongPassword', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label>Minimum password length</Label>
                <Select
                  value={settings.passwordMinLength.toString()}
                  onValueChange={(value) => updateSetting('passwordMinLength', parseInt(value))}
                >
                  <SelectTrigger className="w-24">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="6">6</SelectItem>
                    <SelectItem value="8">8</SelectItem>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="12">12</SelectItem>
                    <SelectItem value="16">16</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Two-Factor Authentication */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900">
                  <Smartphone className="h-5 w-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <CardTitle>Two-Factor Authentication</CardTitle>
                  <CardDescription>Add an extra layer of security to your account</CardDescription>
                </div>
              </div>
              <Switch
                checked={settings.twoFactorEnabled}
                onCheckedChange={(checked) => updateSetting('twoFactorEnabled', checked)}
              />
            </div>
          </CardHeader>
          {settings.twoFactorEnabled && (
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2 text-sm text-green-600">
                <CheckCircle className="h-4 w-4" />
                <span>Two-factor authentication is enabled</span>
              </div>
              
              <div className="space-y-2">
                <Label>Authentication Method</Label>
                <Select
                  value={settings.twoFactorMethod}
                  onValueChange={(value: any) => updateSetting('twoFactorMethod', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="app">Authenticator App (Recommended)</SelectItem>
                    <SelectItem value="sms">SMS</SelectItem>
                    <SelectItem value="email">Email</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <Button variant="outline" size="sm">
                Regenerate Recovery Codes
              </Button>
            </CardContent>
          )}
        </Card>

        {/* Session Management */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                <Clock className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <CardTitle>Session Management</CardTitle>
                <CardDescription>Control your active sessions and timeout settings</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Session Timeout</Label>
                <p className="text-xs text-muted-foreground">Auto-logout after inactivity</p>
              </div>
              <Select
                value={settings.sessionTimeout.toString()}
                onValueChange={(value) => updateSetting('sessionTimeout', parseInt(value))}
              >
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15">15 minutes</SelectItem>
                  <SelectItem value="30">30 minutes</SelectItem>
                  <SelectItem value="60">1 hour</SelectItem>
                  <SelectItem value="120">2 hours</SelectItem>
                  <SelectItem value="480">8 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="single-session">Single session only</Label>
                <p className="text-xs text-muted-foreground">Only allow one active session at a time</p>
              </div>
              <Switch
                id="single-session"
                checked={settings.singleSession}
                onCheckedChange={(checked) => updateSetting('singleSession', checked)}
              />
            </div>
            
            <Separator />
            
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label>Active Sessions</Label>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="outline" size="sm">
                      <LogOut className="mr-2 h-4 w-4" />
                      Revoke All Other Sessions
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Revoke All Sessions?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will log you out from all other devices. You will remain logged in on this device.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={handleRevokeAllSessions}>
                        Revoke All
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
              
              <div className="space-y-2">
                {activeSessions.map((session) => (
                  <div
                    key={session.id}
                    className="flex items-center justify-between p-3 border rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">
                        {session.device.includes('Windows') ? '💻' : session.device.includes('Mac') ? '🖥️' : '📱'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{session.device}</span>
                          {session.current && (
                            <Badge variant="secondary" className="text-xs">Current</Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {session.browser} • {session.location} • {session.lastActive}
                        </p>
                      </div>
                    </div>
                    {!session.current && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRevokeSession(session.id)}
                      >
                        Revoke
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API Security */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-900">
                  <Lock className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                </div>
                <div>
                  <CardTitle>API Rate Limiting</CardTitle>
                  <CardDescription>Protect your account from excessive API usage</CardDescription>
                </div>
              </div>
              <Switch
                checked={settings.apiRateLimitEnabled}
                onCheckedChange={(checked) => updateSetting('apiRateLimitEnabled', checked)}
              />
            </div>
          </CardHeader>
          {settings.apiRateLimitEnabled && (
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Max Requests</Label>
                  <Input
                    type="number"
                    value={settings.apiRateLimitRequests}
                    onChange={(e) => updateSetting('apiRateLimitRequests', parseInt(e.target.value) || 100)}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Time Window (seconds)</Label>
                  <Input
                    type="number"
                    value={settings.apiRateLimitWindow}
                    onChange={(e) => updateSetting('apiRateLimitWindow', parseInt(e.target.value) || 60)}
                  />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Limit: {settings.apiRateLimitRequests} requests per {settings.apiRateLimitWindow} seconds
              </p>
            </CardContent>
          )}
        </Card>

        {/* Audit Logging */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900">
                  <Eye className="h-5 w-5 text-red-600 dark:text-red-400" />
                </div>
                <div>
                  <CardTitle>Audit Logging</CardTitle>
                  <CardDescription>Track and log security-related activities</CardDescription>
                </div>
              </div>
              <Switch
                checked={settings.auditLoggingEnabled}
                onCheckedChange={(checked) => updateSetting('auditLoggingEnabled', checked)}
              />
            </div>
          </CardHeader>
          {settings.auditLoggingEnabled && (
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="log-api" className="font-normal">Log API calls</Label>
                <Switch
                  id="log-api"
                  checked={settings.logApiCalls}
                  onCheckedChange={(checked) => updateSetting('logApiCalls', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="log-workflow" className="font-normal">Log workflow executions</Label>
                <Switch
                  id="log-workflow"
                  checked={settings.logWorkflowExecutions}
                  onCheckedChange={(checked) => updateSetting('logWorkflowExecutions', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="log-login" className="font-normal">Log login attempts</Label>
                <Switch
                  id="log-login"
                  checked={settings.logLoginAttempts}
                  onCheckedChange={(checked) => updateSetting('logLoginAttempts', checked)}
                />
              </div>
              
              <Separator />
              
              <Button variant="outline" size="sm">
                View Audit Logs
              </Button>
            </CardContent>
          )}
        </Card>

        {/* Danger Zone */}
        <Card className="border-destructive">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <CardTitle className="text-destructive">Danger Zone</CardTitle>
                <CardDescription>Irreversible and destructive actions</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Delete all API keys</p>
                <p className="text-xs text-muted-foreground">Remove all stored API keys from your account</p>
              </div>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm">Delete All Keys</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete All API Keys?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. All your stored API keys will be permanently deleted.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction className="bg-destructive text-destructive-foreground">
                      Delete All
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
            
            <Separator />
            
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Delete Account</p>
                <p className="text-xs text-muted-foreground">Permanently delete your account and all data</p>
              </div>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm">Delete Account</Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Account?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. Your account and all associated data will be permanently deleted.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction className="bg-destructive text-destructive-foreground">
                      Delete Account
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} disabled={saving} size="lg">
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </div>
    </div>
  );
}
