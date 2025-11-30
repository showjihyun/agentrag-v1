'use client';

import React, { useState, useEffect } from 'react';
import { Palette, Sun, Moon, Monitor, Type, Layout, Eye, Save, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { useTheme } from 'next-themes';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface AppearanceSettings {
  // Theme
  theme: 'light' | 'dark' | 'system';
  accentColor: string;
  
  // Typography
  fontSize: number;
  fontFamily: 'system' | 'inter' | 'roboto' | 'mono';
  
  // Layout
  sidebarCollapsed: boolean;
  compactMode: boolean;
  showBreadcrumbs: boolean;
  
  // Editor
  editorFontSize: number;
  editorLineNumbers: boolean;
  editorWordWrap: boolean;
  editorMinimap: boolean;
  
  // Accessibility
  reduceMotion: boolean;
  highContrast: boolean;
}

const defaultSettings: AppearanceSettings = {
  theme: 'system',
  accentColor: '#3b82f6',
  
  fontSize: 14,
  fontFamily: 'system',
  
  sidebarCollapsed: false,
  compactMode: false,
  showBreadcrumbs: true,
  
  editorFontSize: 14,
  editorLineNumbers: true,
  editorWordWrap: true,
  editorMinimap: true,
  
  reduceMotion: false,
  highContrast: false,
};

const accentColors = [
  { name: 'Blue', value: '#3b82f6' },
  { name: 'Purple', value: '#8b5cf6' },
  { name: 'Pink', value: '#ec4899' },
  { name: 'Red', value: '#ef4444' },
  { name: 'Orange', value: '#f97316' },
  { name: 'Green', value: '#22c55e' },
  { name: 'Teal', value: '#14b8a6' },
  { name: 'Cyan', value: '#06b6d4' },
];

export default function AppearancePage() {
  const { toast } = useToast();
  const { theme, setTheme } = useTheme();
  const [settings, setSettings] = useState<AppearanceSettings>(defaultSettings);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('appearance_settings');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSettings({ ...defaultSettings, ...parsed });
      } catch {
        // Invalid JSON in localStorage, use default settings
        console.warn('Failed to parse appearance settings from localStorage, using defaults');
      }
    }
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      localStorage.setItem('appearance_settings', JSON.stringify(settings));
      
      // Apply theme
      setTheme(settings.theme);
      
      // Apply font size to document
      document.documentElement.style.fontSize = `${settings.fontSize}px`;
      
      toast({
        title: '✅ Settings Saved',
        description: 'Your appearance preferences have been updated.',
      });
    } catch (error) {
      toast({
        title: '❌ Error',
        description: 'Failed to save appearance settings.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = <K extends keyof AppearanceSettings>(
    key: K,
    value: AppearanceSettings[K]
  ) => {
    setSettings({ ...settings, [key]: value });
  };

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    updateSetting('theme', newTheme);
    setTheme(newTheme);
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Palette className="h-8 w-8" />
          Appearance
        </h1>
        <p className="text-muted-foreground mt-1">
          Customize the look and feel of your workspace
        </p>
      </div>

      <div className="space-y-6">
        {/* Theme */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                <Sun className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <CardTitle>Theme</CardTitle>
                <CardDescription>Choose your preferred color scheme</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              {[
                { value: 'light', label: 'Light', icon: Sun },
                { value: 'dark', label: 'Dark', icon: Moon },
                { value: 'system', label: 'System', icon: Monitor },
              ].map(({ value, label, icon: Icon }) => (
                <button
                  key={value}
                  onClick={() => handleThemeChange(value as any)}
                  className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-all ${
                    settings.theme === value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  }`}
                >
                  <Icon className="h-6 w-6" />
                  <span className="text-sm font-medium">{label}</span>
                  {settings.theme === value && (
                    <Check className="h-4 w-4 text-primary" />
                  )}
                </button>
              ))}
            </div>
            
            <Separator />
            
            <div className="space-y-2">
              <Label>Accent Color</Label>
              <div className="flex flex-wrap gap-2">
                {accentColors.map((color) => (
                  <button
                    key={color.value}
                    onClick={() => updateSetting('accentColor', color.value)}
                    className={`w-8 h-8 rounded-full border-2 transition-all ${
                      settings.accentColor === color.value
                        ? 'border-foreground scale-110'
                        : 'border-transparent hover:scale-105'
                    }`}
                    style={{ backgroundColor: color.value }}
                    title={color.name}
                  />
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Typography */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                <Type className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <CardTitle>Typography</CardTitle>
                <CardDescription>Adjust font settings for better readability</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Font Size: {settings.fontSize}px</Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => updateSetting('fontSize', 14)}
                >
                  Reset
                </Button>
              </div>
              <Slider
                value={[settings.fontSize]}
                onValueChange={([value]) => updateSetting('fontSize', value)}
                min={12}
                max={20}
                step={1}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Small</span>
                <span>Large</span>
              </div>
            </div>
            
            <Separator />
            
            <div className="space-y-2">
              <Label>Font Family</Label>
              <Select
                value={settings.fontFamily}
                onValueChange={(value: any) => updateSetting('fontFamily', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="system">System Default</SelectItem>
                  <SelectItem value="inter">Inter</SelectItem>
                  <SelectItem value="roboto">Roboto</SelectItem>
                  <SelectItem value="mono">Monospace</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Layout */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900">
                <Layout className="h-5 w-5 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <CardTitle>Layout</CardTitle>
                <CardDescription>Configure the workspace layout</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="sidebar-collapsed">Collapse sidebar by default</Label>
                <p className="text-xs text-muted-foreground">Start with a minimized sidebar</p>
              </div>
              <Switch
                id="sidebar-collapsed"
                checked={settings.sidebarCollapsed}
                onCheckedChange={(checked) => updateSetting('sidebarCollapsed', checked)}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="compact-mode">Compact mode</Label>
                <p className="text-xs text-muted-foreground">Reduce spacing and padding</p>
              </div>
              <Switch
                id="compact-mode"
                checked={settings.compactMode}
                onCheckedChange={(checked) => updateSetting('compactMode', checked)}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="breadcrumbs">Show breadcrumbs</Label>
                <p className="text-xs text-muted-foreground">Display navigation breadcrumbs</p>
              </div>
              <Switch
                id="breadcrumbs"
                checked={settings.showBreadcrumbs}
                onCheckedChange={(checked) => updateSetting('showBreadcrumbs', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Code Editor */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-900">
                <Type className="h-5 w-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <CardTitle>Code Editor</CardTitle>
                <CardDescription>Customize the code editor appearance</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Editor Font Size: {settings.editorFontSize}px</Label>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => updateSetting('editorFontSize', 14)}
                >
                  Reset
                </Button>
              </div>
              <Slider
                value={[settings.editorFontSize]}
                onValueChange={([value]) => updateSetting('editorFontSize', value)}
                min={10}
                max={24}
                step={1}
              />
            </div>
            
            <Separator />
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label htmlFor="line-numbers" className="font-normal">Show line numbers</Label>
                <Switch
                  id="line-numbers"
                  checked={settings.editorLineNumbers}
                  onCheckedChange={(checked) => updateSetting('editorLineNumbers', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="word-wrap" className="font-normal">Word wrap</Label>
                <Switch
                  id="word-wrap"
                  checked={settings.editorWordWrap}
                  onCheckedChange={(checked) => updateSetting('editorWordWrap', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <Label htmlFor="minimap" className="font-normal">Show minimap</Label>
                <Switch
                  id="minimap"
                  checked={settings.editorMinimap}
                  onCheckedChange={(checked) => updateSetting('editorMinimap', checked)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Accessibility */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100 dark:bg-red-900">
                <Eye className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <CardTitle>Accessibility</CardTitle>
                <CardDescription>Settings for improved accessibility</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="reduce-motion">Reduce motion</Label>
                <p className="text-xs text-muted-foreground">Minimize animations and transitions</p>
              </div>
              <Switch
                id="reduce-motion"
                checked={settings.reduceMotion}
                onCheckedChange={(checked) => updateSetting('reduceMotion', checked)}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="high-contrast">High contrast</Label>
                <p className="text-xs text-muted-foreground">Increase color contrast for better visibility</p>
              </div>
              <Switch
                id="high-contrast"
                checked={settings.highContrast}
                onCheckedChange={(checked) => updateSetting('highContrast', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Preview */}
        <Card>
          <CardHeader>
            <CardTitle>Preview</CardTitle>
            <CardDescription>See how your settings look</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              className="p-4 rounded-lg border"
              style={{ fontSize: `${settings.fontSize}px` }}
            >
              <h3 className="font-semibold mb-2">Sample Content</h3>
              <p className="text-muted-foreground mb-4">
                This is how your content will appear with the current settings.
                Adjust the options above to customize your experience.
              </p>
              <div className="flex gap-2">
                <Button size="sm" style={{ backgroundColor: settings.accentColor }}>
                  Primary Button
                </Button>
                <Button size="sm" variant="outline">
                  Secondary Button
                </Button>
              </div>
            </div>
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
