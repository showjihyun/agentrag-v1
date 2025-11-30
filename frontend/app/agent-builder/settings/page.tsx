'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Settings, Key, Cpu, Database, Bell, Shield, Palette, ChevronRight, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface SettingsStatus {
  llm: { configured: boolean; providers: number };
  apiKeys: { configured: boolean; count: number };
  environment: { configured: boolean; count: number };
  notifications: { configured: boolean };
  security: { configured: boolean; twoFactor: boolean };
  appearance: { configured: boolean };
}

export default function SettingsPage() {
  const router = useRouter();
  const [status, setStatus] = useState<SettingsStatus>({
    llm: { configured: false, providers: 0 },
    apiKeys: { configured: false, count: 0 },
    environment: { configured: false, count: 0 },
    notifications: { configured: false },
    security: { configured: false, twoFactor: false },
    appearance: { configured: true },
  });

  useEffect(() => {
    // Check configuration status from localStorage
    const llmConfig = localStorage.getItem('llm_config');
    const envVars = localStorage.getItem('environment_variables');
    const notificationSettings = localStorage.getItem('notification_settings');
    const securitySettings = localStorage.getItem('security_settings');
    const appearanceSettings = localStorage.getItem('appearance_settings');

    let llmProviders = 0;
    if (llmConfig) {
      try {
        const config = JSON.parse(llmConfig);
        if (config.apiKeys?.openai) llmProviders++;
        if (config.apiKeys?.anthropic) llmProviders++;
        if (config.apiKeys?.gemini) llmProviders++;
        if (config.ollama?.enabled) llmProviders++;
      } catch {
        // Invalid JSON in localStorage, ignore
      }
    }

    let envCount = 0;
    if (envVars) {
      try {
        const vars = JSON.parse(envVars);
        envCount = Array.isArray(vars) ? vars.length : 0;
      } catch {
        // Invalid JSON in localStorage, ignore
      }
    }

    let twoFactor = false;
    if (securitySettings) {
      try {
        const settings = JSON.parse(securitySettings);
        twoFactor = settings.twoFactorEnabled || false;
      } catch {
        // Invalid JSON in localStorage, ignore
      }
    }

    setStatus({
      llm: { configured: llmProviders > 0, providers: llmProviders },
      apiKeys: { configured: false, count: 0 }, // Will be loaded from API
      environment: { configured: envCount > 0, count: envCount },
      notifications: { configured: !!notificationSettings },
      security: { configured: !!securitySettings, twoFactor },
      appearance: { configured: !!appearanceSettings },
    });
  }, []);

  const settingsCategories = [
    {
      id: 'llm',
      title: 'LLM Configuration',
      description: 'Configure AI model providers and API keys',
      icon: Cpu,
      href: '/agent-builder/settings/llm',
      color: 'from-purple-500 to-pink-500',
      status: status.llm.configured 
        ? `${status.llm.providers} provider${status.llm.providers > 1 ? 's' : ''} configured`
        : 'Not configured',
      isConfigured: status.llm.configured,
    },
    {
      id: 'api-keys',
      title: 'API Keys',
      description: 'Manage API keys for external integrations',
      icon: Key,
      href: '/agent-builder/settings/api-keys',
      color: 'from-blue-500 to-cyan-500',
      status: status.apiKeys.configured 
        ? `${status.apiKeys.count} key${status.apiKeys.count > 1 ? 's' : ''} stored`
        : 'No keys stored',
      isConfigured: status.apiKeys.configured,
    },
    {
      id: 'environment',
      title: 'Environment Variables',
      description: 'Configure variables for workflows',
      icon: Database,
      href: '/agent-builder/settings/environment',
      color: 'from-green-500 to-emerald-500',
      status: status.environment.configured 
        ? `${status.environment.count} variable${status.environment.count > 1 ? 's' : ''} defined`
        : 'No variables defined',
      isConfigured: status.environment.configured,
    },
    {
      id: 'notifications',
      title: 'Notifications',
      description: 'Configure notification preferences',
      icon: Bell,
      href: '/agent-builder/settings/notifications',
      color: 'from-yellow-500 to-orange-500',
      status: status.notifications.configured ? 'Configured' : 'Using defaults',
      isConfigured: status.notifications.configured,
    },
    {
      id: 'security',
      title: 'Security',
      description: 'Security and privacy settings',
      icon: Shield,
      href: '/agent-builder/settings/security',
      color: 'from-red-500 to-pink-500',
      status: status.security.twoFactor ? '2FA enabled' : status.security.configured ? 'Configured' : 'Review recommended',
      isConfigured: status.security.configured,
      highlight: !status.security.configured,
    },
    {
      id: 'appearance',
      title: 'Appearance',
      description: 'Customize theme and display',
      icon: Palette,
      href: '/agent-builder/settings/appearance',
      color: 'from-indigo-500 to-purple-500',
      status: status.appearance.configured ? 'Customized' : 'Using defaults',
      isConfigured: status.appearance.configured,
    },
  ];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Settings className="h-8 w-8" />
          Settings
        </h1>
        <p className="text-muted-foreground mt-1">
          Configure your Agent Builder preferences and integrations
        </p>
      </div>

      {/* Quick Status */}
      <div className="mb-6 p-4 rounded-lg bg-muted/50 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span className="text-sm">
              {settingsCategories.filter(c => c.isConfigured).length} of {settingsCategories.length} configured
            </span>
          </div>
          {!status.security.configured && (
            <Badge variant="outline" className="text-orange-600 border-orange-300">
              <AlertCircle className="h-3 w-3 mr-1" />
              Security review recommended
            </Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {settingsCategories.map((category) => {
          const Icon = category.icon;
          return (
            <Card
              key={category.id}
              className={`cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] group ${
                category.highlight ? 'ring-2 ring-orange-300' : ''
              }`}
              onClick={() => router.push(category.href)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div
                    className={`p-3 rounded-lg bg-gradient-to-br ${category.color} group-hover:scale-110 transition-transform`}
                  >
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                </div>
                <CardTitle className="mt-4">{category.title}</CardTitle>
                <CardDescription>{category.description}</CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex items-center gap-2 text-sm">
                  {category.isConfigured ? (
                    <CheckCircle className="h-4 w-4 text-green-500" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-muted-foreground" />
                  )}
                  <span className={category.isConfigured ? 'text-green-600' : 'text-muted-foreground'}>
                    {category.status}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Help Section */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle className="text-lg">Need Help?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-medium mb-1">Getting Started</h4>
              <p className="text-muted-foreground">
                Start by configuring your LLM providers to enable AI-powered workflows.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">Security Best Practices</h4>
              <p className="text-muted-foreground">
                Enable two-factor authentication and review your security settings regularly.
              </p>
            </div>
            <div>
              <h4 className="font-medium mb-1">Environment Variables</h4>
              <p className="text-muted-foreground">
                Use environment variables to store sensitive data and configuration values.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
