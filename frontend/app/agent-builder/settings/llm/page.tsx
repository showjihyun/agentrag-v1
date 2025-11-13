'use client';

import { useState, useEffect } from 'react';
import { Cpu, Save, TestTube, CheckCircle, XCircle, Loader2, Eye, EyeOff } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface LLMProvider {
  id: string;
  name: string;
  description: string;
  requiresApiKey: boolean;
  models: string[];
  icon: string;
}

const LLM_PROVIDERS: LLMProvider[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    description: 'GPT-4, GPT-3.5 Turbo',
    requiresApiKey: true,
    models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'],
    icon: '🤖',
  },
  {
    id: 'anthropic',
    name: 'Anthropic Claude',
    description: 'Claude 3 Opus, Sonnet, Haiku',
    requiresApiKey: true,
    models: ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
    icon: '🧠',
  },
  {
    id: 'google',
    name: 'Google Gemini',
    description: 'Gemini Pro, Gemini Ultra',
    requiresApiKey: true,
    models: ['gemini-pro', 'gemini-pro-vision', 'gemini-ultra'],
    icon: '✨',
  },
  {
    id: 'ollama',
    name: 'Ollama (Local)',
    description: 'Run models locally',
    requiresApiKey: false,
    models: ['llama3.1:8b', 'llama3.1:70b', 'mistral', 'mixtral', 'codellama'],
    icon: '🦙',
  },
  {
    id: 'groq',
    name: 'Groq',
    description: 'Ultra-fast inference',
    requiresApiKey: true,
    models: ['llama3-70b-8192', 'llama3-8b-8192', 'mixtral-8x7b-32768'],
    icon: '⚡',
  },
];

export default function LLMSettingsPage() {
  const { toast } = useToast();
  const [selectedProvider, setSelectedProvider] = useState<string>('openai');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [apiKey, setApiKey] = useState<string>('');
  const [showApiKey, setShowApiKey] = useState<boolean>(false);
  const [ollamaUrl, setOllamaUrl] = useState<string>('http://localhost:11434');
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [isTesting, setIsTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);

  const currentProvider = LLM_PROVIDERS.find((p) => p.id === selectedProvider);

  useEffect(() => {
    // Load saved settings
    loadSettings();
  }, []);

  useEffect(() => {
    // Set default model when provider changes
    if (currentProvider && currentProvider.models.length > 0) {
      setSelectedModel(currentProvider.models[0]);
    }
  }, [selectedProvider, currentProvider]);

  const loadSettings = async () => {
    try {
      // Load from localStorage for now
      const saved = localStorage.getItem('llm_settings');
      if (saved) {
        const settings = JSON.parse(saved);
        setSelectedProvider(settings.provider || 'openai');
        setSelectedModel(settings.model || '');
        setApiKey(settings.apiKey || '');
        setOllamaUrl(settings.ollamaUrl || 'http://localhost:11434');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const settings = {
        provider: selectedProvider,
        model: selectedModel,
        apiKey: apiKey,
        ollamaUrl: ollamaUrl,
      };

      // Save to localStorage
      localStorage.setItem('llm_settings', JSON.stringify(settings));

      // TODO: Save to backend API
      // await fetch('/api/settings/llm', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(settings),
      // });

      toast({
        title: '✅ Settings Saved',
        description: 'LLM configuration has been saved successfully',
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: '❌ Save Failed',
        description: 'Failed to save LLM settings',
        variant: 'error',
        duration: 3000,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      // Test the LLM connection
      const response = await fetch('/api/llm/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider: selectedProvider,
          model: selectedModel,
          apiKey: apiKey,
          ollamaUrl: ollamaUrl,
        }),
      });

      if (response.ok) {
        setTestResult('success');
        toast({
          title: '✅ Connection Successful',
          description: 'LLM provider is working correctly',
          duration: 3000,
        });
      } else {
        setTestResult('error');
        const error = await response.json();
        toast({
          title: '❌ Connection Failed',
          description: error.message || 'Failed to connect to LLM provider',
          variant: 'error',
          duration: 3000,
        });
      }
    } catch (error) {
      setTestResult('error');
      toast({
        title: '❌ Test Failed',
        description: 'Failed to test LLM connection',
        variant: 'error',
        duration: 3000,
      });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Cpu className="h-8 w-8" />
          LLM Configuration
        </h1>
        <p className="text-muted-foreground mt-1">
          Configure AI model providers for workflow generation and agent execution
        </p>
      </div>

      {/* Provider Selection */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Select Provider</CardTitle>
          <CardDescription>Choose your preferred LLM provider</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {LLM_PROVIDERS.map((provider) => (
              <button
                key={provider.id}
                onClick={() => setSelectedProvider(provider.id)}
                className={`p-4 border-2 rounded-lg text-left transition-all hover:shadow-md ${
                  selectedProvider === provider.id
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="text-3xl mb-2">{provider.icon}</div>
                <div className="font-semibold">{provider.name}</div>
                <div className="text-sm text-muted-foreground">{provider.description}</div>
                {selectedProvider === provider.id && (
                  <div className="mt-2">
                    <CheckCircle className="h-5 w-5 text-blue-500" />
                  </div>
                )}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Configuration */}
      {currentProvider && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Configure {currentProvider.name} settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Model Selection */}
            <div>
              <Label htmlFor="model">Model</Label>
              <Select value={selectedModel} onValueChange={setSelectedModel}>
                <SelectTrigger id="model">
                  <SelectValue placeholder="Select a model" />
                </SelectTrigger>
                <SelectContent>
                  {currentProvider.models.map((model) => (
                    <SelectItem key={model} value={model}>
                      {model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* API Key (if required) */}
            {currentProvider.requiresApiKey && (
              <div>
                <Label htmlFor="apiKey">API Key</Label>
                <div className="relative">
                  <Input
                    id="apiKey"
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Get your API key from{' '}
                  {currentProvider.id === 'openai' && (
                    <a
                      href="https://platform.openai.com/api-keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                      OpenAI Platform
                    </a>
                  )}
                  {currentProvider.id === 'anthropic' && (
                    <a
                      href="https://console.anthropic.com/settings/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                      Anthropic Console
                    </a>
                  )}
                  {currentProvider.id === 'google' && (
                    <a
                      href="https://makersuite.google.com/app/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                      Google AI Studio
                    </a>
                  )}
                  {currentProvider.id === 'groq' && (
                    <a
                      href="https://console.groq.com/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                      Groq Console
                    </a>
                  )}
                </p>
              </div>
            )}

            {/* Ollama URL */}
            {currentProvider.id === 'ollama' && (
              <div>
                <Label htmlFor="ollamaUrl">Ollama URL</Label>
                <Input
                  id="ollamaUrl"
                  type="text"
                  value={ollamaUrl}
                  onChange={(e) => setOllamaUrl(e.target.value)}
                  placeholder="http://localhost:11434"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Make sure Ollama is running locally. Install from{' '}
                  <a
                    href="https://ollama.ai"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:underline"
                  >
                    ollama.ai
                  </a>
                </p>
              </div>
            )}

            {/* Test Result */}
            {testResult && (
              <div
                className={`p-3 rounded-lg flex items-center gap-2 ${
                  testResult === 'success'
                    ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                    : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                }`}
              >
                {testResult === 'success' ? (
                  <>
                    <CheckCircle className="h-5 w-5" />
                    <span>Connection successful!</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-5 w-5" />
                    <span>Connection failed. Please check your settings.</span>
                  </>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-4">
              <Button onClick={handleTest} variant="outline" disabled={isTesting}>
                {isTesting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <TestTube className="mr-2 h-4 w-4" />
                    Test Connection
                  </>
                )}
              </Button>
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Save Settings
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>About LLM Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            • <strong>OpenAI</strong>: Best for general-purpose tasks, excellent reasoning
          </p>
          <p>
            • <strong>Anthropic Claude</strong>: Great for long context, safety-focused
          </p>
          <p>
            • <strong>Google Gemini</strong>: Multimodal capabilities, fast inference
          </p>
          <p>
            • <strong>Ollama</strong>: Run models locally, no API costs, privacy-first
          </p>
          <p>
            • <strong>Groq</strong>: Ultra-fast inference, cost-effective
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
