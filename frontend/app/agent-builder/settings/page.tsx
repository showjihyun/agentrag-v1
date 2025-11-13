'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Settings, Key, Cpu, Database, Bell, Shield, Palette } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function SettingsPage() {
  const router = useRouter();

  const settingsCategories = [
    {
      id: 'llm',
      title: 'LLM Configuration',
      description: 'Configure AI model providers and API keys',
      icon: Cpu,
      href: '/agent-builder/settings/llm',
      color: 'from-purple-500 to-pink-500',
    },
    {
      id: 'api-keys',
      title: 'API Keys',
      description: 'Manage API keys for integrations',
      icon: Key,
      href: '/agent-builder/settings/api-keys',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      id: 'environment',
      title: 'Environment Variables',
      description: 'Configure environment variables',
      icon: Database,
      href: '/agent-builder/settings/environment',
      color: 'from-green-500 to-emerald-500',
    },
    {
      id: 'notifications',
      title: 'Notifications',
      description: 'Configure notification preferences',
      icon: Bell,
      href: '/agent-builder/settings/notifications',
      color: 'from-yellow-500 to-orange-500',
    },
    {
      id: 'security',
      title: 'Security',
      description: 'Security and privacy settings',
      icon: Shield,
      href: '/agent-builder/settings/security',
      color: 'from-red-500 to-pink-500',
    },
    {
      id: 'appearance',
      title: 'Appearance',
      description: 'Customize theme and display',
      icon: Palette,
      href: '/agent-builder/settings/appearance',
      color: 'from-indigo-500 to-purple-500',
    },
  ];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Settings className="h-8 w-8" />
          Settings
        </h1>
        <p className="text-muted-foreground mt-1">
          Configure your Agent Builder preferences and integrations
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {settingsCategories.map((category) => {
          const Icon = category.icon;
          return (
            <Card
              key={category.id}
              className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] group"
              onClick={() => router.push(category.href)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div
                    className={`p-3 rounded-lg bg-gradient-to-br ${category.color} group-hover:scale-110 transition-transform`}
                  >
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                </div>
                <CardTitle className="mt-4">{category.title}</CardTitle>
                <CardDescription>{category.description}</CardDescription>
              </CardHeader>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
