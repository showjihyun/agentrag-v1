'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { Save, Key, Cpu, TestTube, CheckCircle, XCircle, Loader2, RefreshCw, Server, Eye, EyeOff } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface LLMConfig {
  apiKeys: {
    openai: string;
    anthropic: string;
    gemini: string;
  };
  ollama: {
    enabled: boolean;
    baseUrl: string;
    defaultModel: string;
  };
  defaultProvider: 'openai' | 'anthropic' | 'gemini' | 'ollama';
  defaultModel: string;
}

interface TestResult {
  provider: string;
  success: boolean;
  message: string;
  latency?: number;
}

const defaultConfig: LLMConfig = {
  apiKeys: {
    openai: '',
    anthropic: '',
    gemini: '',
  },
  ollama: {
    enabled: false,
    baseUrl: 'http://localhost:11434',
    defaultModel: 'llama3.1',
  },
  defaultProvider: 'openai',
  defaultModel: 'gpt-4o-mini',
};

const providerModels: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
  gemini: ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
  ollama: ['llama3.3:70b', 'llama3.1:70b', 'llama3.1:8b', 'gps-oss:20b', 'llama3.2', 'mistral', 'codellama', 'phi3', 'qwen2.5'],
};

export default function LLMSettingsPage() {
  const { toast } = useToast();
  const [config, setConfig] = useState<LLMConfig>(defaultConfig);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [ollamaModels, setOllamaModels] = useState<string[]>([]);
  const [loadingOllamaModels, setLoadingOllamaModels] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem('llm_config');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setConfig({ ...defaultConfig, ...parsed });
      } catch {
        // Invalid JSON in localStorage, use default config
        console.warn('Failed to parse LLM config from localStorage, using defaults');
      }
    }
  }, []);

  useEffect(() => {
    if (config.ollama.enabled) {
      fetchOllamaModels();
    }
  }, [config.ollama.enabled, config.ollama.baseUrl]);

  const fetchOllamaModels = async () => {
    setLoadingOllamaModels(true);
    try {
      const response = await fetch(`${config.ollama.baseUrl}/api/tags`);
      if (response.ok) {
        const data = await response.json();
        const models = data.models?.map((m: any) => m.name) || [];
        setOllamaModels(models);
        
        // Save to localStorage for use in other components
        localStorage.setItem('ollama_models', JSON.stringify(models));
      }
    } catch (error) {
      console.error('Failed to fetch Ollama models:', error);
    } finally {
      setLoadingOllamaModels(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      localStorage.setItem('llm_config', JSON.stringify(config));
      toast({
        title: '✅ Saved',
        description: 'LLM configuration saved successfully',
      });
    } catch {
      toast({
        title: '❌ Error',
        description: 'Failed to save configuration',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const testProvider = async (provider: string) => {
    setTesting(provider);
    const startTime = Date.now();
    
    try {
      let success = false;
      let message = '';

      if (provider === 'ollama') {
        const response = await fetch(`${config.ollama.baseUrl}/api/tags`);
        success = response.ok;
        message = success ? 'Ollama is running and accessible' : 'Failed to connect to Ollama';
      } else {
        const apiKey = config.apiKeys[provider as keyof typeof config.apiKeys];
        if (!apiKey) {
          throw new Error('API key not configured');
        }

        // Simple validation test
        if (provider === 'openai') {
          const response = await fetch('https://api.openai.com/v1/models', {
            headers: { Authorization: `Bearer ${apiKey}` },
          });
          success = response.ok;
          message = success ? 'OpenAI API key is valid' : 'Invalid API key';
        } else if (provider === 'anthropic') {
          // Anthropic doesn't have a simple validation endpoint, so we just check format
          success = apiKey.startsWith('sk-ant-');
          message = success ? 'API key format is valid' : 'Invalid API key format';
        } else if (provider === 'gemini') {
          success = apiKey.startsWith('AIza');
          message = success ? 'API key format is valid' : 'Invalid API key format';
        }
      }

      const latency = Date.now() - startTime;
      setTestResults({
        ...testResults,
        [provider]: { provider, success, message, latency },
      });

      toast({
        title: success ? '✅ Test Passed' : '❌ Test Failed',
        description: message,
        variant: success ? 'success' : 'destructive',
      });
    } catch (error: any) {
      setTestResults({
        ...testResults,
        [provider]: { provider, success: false, message: error.message },
      });
      toast({
        title: '❌ Test Failed',
        description: error.message,
        variant: 'destructive',
      });
    } finally {
      setTesting(null);
    }
  };

  const toggleShowKey = (provider: string) => {
    setShowKeys({ ...showKeys, [provider]: !showKeys[provider] });
  };

  const updateApiKey = (provider: string, value: string) => {
    setConfig({
      ...config,
      apiKeys: { ...config.apiKeys, [provider]: value },
    });
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Cpu className="h-8 w-8" />
          LLM Configuration
        </h1>
        <p className="text-muted-foreground mt-2">
          Configure AI model providers and API keys for your workflows
        </p>
      </div>

      <div className="space-y-4">
        {/* Default Provider Selection */}
        <Card>
          <CardHeader>
            <CardTitle>Default Provider</CardTitle>
            <CardDescription>
              Select the default LLM provider for new AI Agent nodes
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Provider</Label>
                <Select
                  value={config.defaultProvider}
                  onValueChange={(value: any) => setConfig({ ...config, defaultProvider: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="anthropic">Anthropic (Claude)</SelectItem>
                    <SelectItem value="gemini">Google Gemini</SelectItem>
                    {config.ollama.enabled && (
                      <SelectItem value="ollama">Ollama (Local)</SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Model</Label>
                <Select
                  value={config.defaultModel}
                  onValueChange={(value) => setConfig({ ...config, defaultModel: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(config.defaultProvider === 'ollama' ? ollamaModels : providerModels[config.defaultProvider])?.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* OpenAI */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-100 dark:bg-green-900">
                  <span className="text-xl">🤖</span>
                </div>
                <div>
                  <CardTitle>OpenAI</CardTitle>
                  <CardDescription>GPT-4o, GPT-4, GPT-3.5 Turbo</CardDescription>
                </div>
              </div>
              {testResults.openai && (
                <Badge variant={testResults.openai.success ? 'default' : 'destructive'}>
                  {testResults.openai.success ? <CheckCircle className="h-3 w-3 mr-1" /> : <XCircle className="h-3 w-3 mr-1" />}
                  {testResults.openai.success ? 'Connected' : 'Failed'}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="openai-key">API Key</Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    id="openai-key"
                    type={showKeys.openai ? 'text' : 'password'}
                    placeholder="sk-..."
                    value={config.apiKeys.openai}
                    onChange={(e) => updateApiKey('openai', e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                    onClick={() => toggleShowKey('openai')}
                  >
                    {showKeys.openai ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                <Button
                  variant="outline"
                  onClick={() => testProvider('openai')}
                  disabled={testing === 'openai' || !config.apiKeys.openai}
                >
                  {testing === 'openai' ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTube className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Get your API key from{' '}
                <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  platform.openai.com
                </a>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Anthropic */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-900">
                  <span className="text-xl">🧠</span>
                </div>
                <div>
                  <CardTitle>Anthropic (Claude)</CardTitle>
                  <CardDescription>Claude 3.5 Sonnet, Claude 3 Opus</CardDescription>
                </div>
              </div>
              {testResults.anthropic && (
                <Badge variant={testResults.anthropic.success ? 'default' : 'destructive'}>
                  {testResults.anthropic.success ? <CheckCircle className="h-3 w-3 mr-1" /> : <XCircle className="h-3 w-3 mr-1" />}
                  {testResults.anthropic.success ? 'Valid' : 'Invalid'}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="anthropic-key">API Key</Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    id="anthropic-key"
                    type={showKeys.anthropic ? 'text' : 'password'}
                    placeholder="sk-ant-..."
                    value={config.apiKeys.anthropic}
                    onChange={(e) => updateApiKey('anthropic', e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                    onClick={() => toggleShowKey('anthropic')}
                  >
                    {showKeys.anthropic ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                <Button
                  variant="outline"
                  onClick={() => testProvider('anthropic')}
                  disabled={testing === 'anthropic' || !config.apiKeys.anthropic}
                >
                  {testing === 'anthropic' ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTube className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Get your API key from{' '}
                <a href="https://console.anthropic.com/settings/keys" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  console.anthropic.com
                </a>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Gemini */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
                  <span className="text-xl">💎</span>
                </div>
                <div>
                  <CardTitle>Google Gemini</CardTitle>
                  <CardDescription>Gemini 2.0, Gemini 1.5 Pro</CardDescription>
                </div>
              </div>
              {testResults.gemini && (
                <Badge variant={testResults.gemini.success ? 'default' : 'destructive'}>
                  {testResults.gemini.success ? <CheckCircle className="h-3 w-3 mr-1" /> : <XCircle className="h-3 w-3 mr-1" />}
                  {testResults.gemini.success ? 'Valid' : 'Invalid'}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="gemini-key">API Key</Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    id="gemini-key"
                    type={showKeys.gemini ? 'text' : 'password'}
                    placeholder="AIza..."
                    value={config.apiKeys.gemini}
                    onChange={(e) => updateApiKey('gemini', e.target.value)}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                    onClick={() => toggleShowKey('gemini')}
                  >
                    {showKeys.gemini ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
                <Button
                  variant="outline"
                  onClick={() => testProvider('gemini')}
                  disabled={testing === 'gemini' || !config.apiKeys.gemini}
                >
                  {testing === 'gemini' ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTube className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Get your API key from{' '}
                <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  aistudio.google.com
                </a>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Ollama (Local) */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
                  <Server className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <CardTitle>Ollama (Local)</CardTitle>
                  <CardDescription>Run models locally with Ollama</CardDescription>
                </div>
              </div>
              <Switch
                checked={config.ollama.enabled}
                onCheckedChange={(checked) => setConfig({ ...config, ollama: { ...config.ollama, enabled: checked } })}
              />
            </div>
          </CardHeader>
          {config.ollama.enabled && (
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="ollama-url">Ollama Base URL</Label>
                <div className="flex gap-2">
                  <Input
                    id="ollama-url"
                    placeholder="http://localhost:11434"
                    value={config.ollama.baseUrl}
                    onChange={(e) => setConfig({ ...config, ollama: { ...config.ollama, baseUrl: e.target.value } })}
                  />
                  <Button
                    variant="outline"
                    onClick={() => testProvider('ollama')}
                    disabled={testing === 'ollama'}
                  >
                    {testing === 'ollama' ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTube className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
              
              <Separator />
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Available Models</Label>
                  <Button variant="ghost" size="sm" onClick={fetchOllamaModels} disabled={loadingOllamaModels}>
                    <RefreshCw className={`h-4 w-4 mr-1 ${loadingOllamaModels ? 'animate-spin' : ''}`} />
                    Refresh
                  </Button>
                </div>
                {ollamaModels.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {ollamaModels.map((model) => (
                      <Badge
                        key={model}
                        variant={config.ollama.defaultModel === model ? 'default' : 'outline'}
                        className="cursor-pointer"
                        onClick={() => setConfig({ ...config, ollama: { ...config.ollama, defaultModel: model } })}
                      >
                        {model}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    {loadingOllamaModels ? 'Loading models...' : 'No models found. Make sure Ollama is running.'}
                  </p>
                )}
              </div>
              
              {testResults.ollama && (
                <div className={`flex items-center gap-2 text-sm ${testResults.ollama.success ? 'text-green-600' : 'text-destructive'}`}>
                  {testResults.ollama.success ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                  {testResults.ollama.message}
                  {testResults.ollama.latency && ` (${testResults.ollama.latency}ms)`}
                </div>
              )}
            </CardContent>
          )}
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} size="lg" disabled={saving}>
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </div>
      </div>

      {/* Info */}
      <Card className="mt-6 border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/20">
        <CardContent className="pt-6">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Note:</strong> API keys are stored locally in your browser and are only sent to the respective LLM providers when making API calls. For production use, consider storing keys securely on the server.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
