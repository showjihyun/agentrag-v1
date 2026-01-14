'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  ArrowLeft,
  Save,
  Play,
  MessageSquare,
  Settings,
  Sparkles,
  Database,
  Brain,
  Wrench,
  Code,
  Globe,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';

const TEMPLATES = [
  {
    id: 'rag-chatbot',
    name: 'RAG Chatbot',
    description: 'Document-based Q&A chatbot (Knowledge base integration)',
    features: ['RAG', 'Memory'],
    icon: '📚',
    config: {
      rag_enabled: true,
      memory_type: 'vector',
      tools: ['vector_search', 'web_search'],
    },
  },
  {
    id: 'customer-support',
    name: 'Customer Support Chatbot',
    description: 'Support bot with FAQ and ticket creation features',
    features: ['Tools', 'Memory'],
    icon: '🎧',
    config: {
      rag_enabled: false,
      memory_type: 'buffer',
      tools: ['slack', 'email', 'database'],
    },
  },
  {
    id: 'code-assistant',
    name: 'Code Assistant',
    description: 'AI that helps with code writing, review, and debugging',
    features: ['Tools', 'Code'],
    icon: '💻',
    config: {
      rag_enabled: false,
      memory_type: 'summary',
      tools: ['code_execution', 'github', 'documentation'],
    },
  },
  {
    id: 'research-assistant',
    name: 'Research Assistant',
    description: 'Research support through web search and document analysis',
    features: ['RAG', 'Web Search'],
    icon: '🔬',
    config: {
      rag_enabled: true,
      memory_type: 'hybrid',
      tools: ['web_search', 'vector_search', 'document_analysis'],
    },
  },
];

const MEMORY_TYPES = [
  {
    id: 'buffer',
    name: 'Buffer Memory',
    description: 'Stores recent conversation content as-is',
    icon: Brain,
  },
  {
    id: 'summary',
    name: 'Summary Memory',
    description: 'Stores conversation content as summaries',
    icon: Brain,
  },
  {
    id: 'vector',
    name: 'Vector Memory',
    description: 'Semantic-based storage using embeddings',
    icon: Database,
  },
  {
    id: 'hybrid',
    name: 'Hybrid Memory',
    description: 'Combines multiple memory methods',
    icon: Sparkles,
  },
];

export default function NewChatflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    chat_config: {
      llm_provider: 'ollama',
      llm_model: 'llama3.1:8b',
      system_prompt: 'You are a helpful AI assistant. Please answer user questions accurately and kindly.',
      temperature: 0.7,
      max_tokens: 2000,
      streaming: true,
      welcome_message: 'Hello! How can I help you?',
      suggested_questions: [
        'How do I use this system?',
        'I need help',
        'Please analyze this document',
      ],
    },
    memory_config: {
      type: 'buffer',
      max_messages: 20,
      summary_threshold: null,
      vector_store_id: null,
    },
    rag_config: {
      enabled: false,
      knowledgebase_ids: [],
      retrieval_strategy: 'hybrid',
      top_k: 5,
      score_threshold: 0.7,
      reranking_enabled: true,
      reranking_model: null,
    },
    graph_definition: {},
    tags: [] as string[],
  });
  
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Load template if specified in URL
  useEffect(() => {
    const templateId = searchParams.get('template');
    if (templateId) {
      const template = TEMPLATES.find(t => t.id === templateId);
      if (template) {
        setSelectedTemplate(templateId);
        setFormData(prev => ({
          ...prev,
          name: template.name,
          description: template.description,
          memory_config: {
            ...prev.memory_config,
            type: template.config.memory_type,
          },
          rag_config: {
            ...prev.rag_config,
            enabled: template.config.rag_enabled,
          },
          tags: template.features.map(f => f.toLowerCase()),
        }));
      }
    }
  }, [searchParams]);

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a Chatflow name',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      const chatflow = await flowsAPI.createChatflow(formData as any);
      
      toast({
        title: 'Created Successfully',
        description: `"${formData.name}" Chatflow has been created`,
      });
      
      router.push(`/agent-builder/chatflows/${chatflow.id}`);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create Chatflow',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleTemplateSelect = (template: typeof TEMPLATES[0]) => {
    setSelectedTemplate(template.id);
    setFormData(prev => ({
      ...prev,
      name: template.name,
      description: template.description,
      memory_config: {
        ...prev.memory_config,
        type: template.config.memory_type,
      },
      rag_config: {
        ...prev.rag_config,
        enabled: template.config.rag_enabled,
      },
      tags: template.features.map(f => f.toLowerCase()),
    }));
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900">
              <MessageSquare className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            Create New Chatflow
          </h1>
          <p className="text-muted-foreground mt-1">
            Build RAG-based chatbots and AI assistants
          </p>
        </div>
      </div>

      <Tabs defaultValue="basic" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="basic">Basic Information</TabsTrigger>
          <TabsTrigger value="chat">Chat Settings</TabsTrigger>
          <TabsTrigger value="memory">Memory & RAG</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        {/* Basic Information */}
        <TabsContent value="basic" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>
                Enter the name and description for your Chatflow
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g., Customer Support Chatbot"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe what this Chatflow will do..."
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label>Tags</Label>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                  {formData.tags.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      Tags will be automatically added when you select a template
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Chat Configuration */}
        <TabsContent value="chat" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>LLM Settings</CardTitle>
              <CardDescription>
                Configure the language model for chat
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>LLM Provider</Label>
                  <Select
                    value={formData.chat_config.llm_provider}
                    onValueChange={(value) => setFormData(prev => ({
                      ...prev,
                      chat_config: { ...prev.chat_config, llm_provider: value }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ollama">Ollama (Local)</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="anthropic">Anthropic</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Model</Label>
                  <Input
                    value={formData.chat_config.llm_model}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      chat_config: { ...prev.chat_config, llm_model: e.target.value }
                    }))}
                    placeholder="llama3.1:8b"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>System Prompt</Label>
                <Textarea
                  value={formData.chat_config.system_prompt}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, system_prompt: e.target.value }
                  }))}
                  rows={4}
                  placeholder="Define the AI's role and behavior..."
                />
              </div>

              <div className="space-y-2">
                <Label>Temperature: {formData.chat_config.temperature}</Label>
                <Slider
                  value={[formData.chat_config.temperature]}
                  onValueChange={([value]) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, temperature: value ?? 0.7 }
                  }))}
                  max={2}
                  min={0}
                  step={0.1}
                  className="w-full"
                />
                <p className="text-xs text-muted-foreground">
                  Lower values produce consistent responses, higher values produce creative responses
                </p>
              </div>

              <div className="space-y-2">
                <Label>Max Tokens</Label>
                <Input
                  type="number"
                  min="100"
                  max="8000"
                  value={formData.chat_config.max_tokens}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, max_tokens: parseInt(e.target.value) || 2000 }
                  }))}
                />
              </div>

              <div className="flex items-center space-x-2">
                <Switch
                  id="streaming"
                  checked={formData.chat_config.streaming}
                  onCheckedChange={(checked) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, streaming: checked }
                  }))}
                />
                <Label htmlFor="streaming">Streaming Response</Label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>User Experience</CardTitle>
              <CardDescription>
                Configure the first interaction with users
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Welcome Message</Label>
                <Input
                  value={formData.chat_config.welcome_message}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    chat_config: { ...prev.chat_config, welcome_message: e.target.value }
                  }))}
                  placeholder="Hello! How can I help you?"
                />
              </div>

              <div className="space-y-2">
                <Label>Suggested Questions</Label>
                {formData.chat_config.suggested_questions.map((question, index) => (
                  <Input
                    key={index}
                    value={question}
                    onChange={(e) => {
                      const newQuestions = [...formData.chat_config.suggested_questions];
                      newQuestions[index] = e.target.value;
                      setFormData(prev => ({
                        ...prev,
                        chat_config: { ...prev.chat_config, suggested_questions: newQuestions }
                      }));
                    }}
                    placeholder={`Suggested question ${index + 1}`}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Memory & RAG */}
        <TabsContent value="memory" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Memory Settings</CardTitle>
              <CardDescription>
                Configure how conversation history is stored and utilized
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {MEMORY_TYPES.map((type) => {
                  const Icon = type.icon;
                  const isSelected = formData.memory_config.type === type.id;
                  
                  return (
                    <Card
                      key={type.id}
                      className={`cursor-pointer transition-all border-2 ${
                        isSelected 
                          ? 'border-primary shadow-lg' 
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => setFormData(prev => ({ 
                        ...prev, 
                        memory_config: { ...prev.memory_config, type: type.id }
                      }))}
                    >
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-3">
                          <Icon className="h-5 w-5 text-blue-500" />
                          <div>
                            <CardTitle className="text-base">{type.name}</CardTitle>
                            <CardDescription className="text-sm">
                              {type.description}
                            </CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                    </Card>
                  );
                })}
              </div>

              <div className="mt-4 space-y-4">
                <div className="space-y-2">
                  <Label>Max Messages</Label>
                  <Input
                    type="number"
                    min="5"
                    max="100"
                    value={formData.memory_config.max_messages}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      memory_config: { ...prev.memory_config, max_messages: parseInt(e.target.value) || 20 }
                    }))}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5 text-purple-500" />
                RAG Settings
              </CardTitle>
              <CardDescription>
                Connect with knowledge bases to provide accurate information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch
                  id="rag-enabled"
                  checked={formData.rag_config.enabled}
                  onCheckedChange={(checked) => setFormData(prev => ({
                    ...prev,
                    rag_config: { ...prev.rag_config, enabled: checked }
                  }))}
                />
                <Label htmlFor="rag-enabled">Enable RAG</Label>
              </div>

              {formData.rag_config.enabled && (
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="space-y-2">
                    <Label>Retrieval Strategy</Label>
                    <Select
                      value={formData.rag_config.retrieval_strategy}
                      onValueChange={(value) => setFormData(prev => ({
                        ...prev,
                        rag_config: { ...prev.rag_config, retrieval_strategy: value }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="similarity">Similarity Search</SelectItem>
                        <SelectItem value="mmr">MMR (Diversity Considered)</SelectItem>
                        <SelectItem value="hybrid">Hybrid Search</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Top K</Label>
                      <Input
                        type="number"
                        min="1"
                        max="20"
                        value={formData.rag_config.top_k}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          rag_config: { ...prev.rag_config, top_k: parseInt(e.target.value) || 5 }
                        }))}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Score Threshold</Label>
                      <Input
                        type="number"
                        min="0"
                        max="1"
                        step="0.1"
                        value={formData.rag_config.score_threshold}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          rag_config: { ...prev.rag_config, score_threshold: parseFloat(e.target.value) || 0.7 }
                        }))}
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Switch
                      id="reranking"
                      checked={formData.rag_config.reranking_enabled}
                      onCheckedChange={(checked) => setFormData(prev => ({
                        ...prev,
                        rag_config: { ...prev.rag_config, reranking_enabled: checked }
                      }))}
                    />
                    <Label htmlFor="reranking">Enable Reranking</Label>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates */}
        <TabsContent value="templates" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-blue-500" />
                Chatflow Templates
              </CardTitle>
              <CardDescription>
                Get started quickly with pre-configured chatbot templates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {TEMPLATES.map((template) => {
                  const isSelected = selectedTemplate === template.id;
                  
                  return (
                    <Card
                      key={template.id}
                      className={`cursor-pointer transition-all border-2 ${
                        isSelected 
                          ? 'border-primary shadow-lg' 
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => handleTemplateSelect(template)}
                    >
                      <CardHeader>
                        <div className="text-3xl mb-2">{template.icon}</div>
                        <CardTitle className="text-base">{template.name}</CardTitle>
                        <CardDescription className="text-sm">
                          {template.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-2 flex-wrap">
                          {template.features.map((feature) => (
                            <Badge key={feature} variant="secondary" className="text-xs">
                              {feature === 'RAG' && <Database className="h-3 w-3 mr-1" />}
                              {feature === 'Tools' && <Wrench className="h-3 w-3 mr-1" />}
                              {feature === 'Memory' && <Brain className="h-3 w-3 mr-1" />}
                              {feature === 'Code' && <Code className="h-3 w-3 mr-1" />}
                              {feature === 'Web Search' && <Globe className="h-3 w-3 mr-1" />}
                              {feature}
                            </Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Actions */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
        <div className="flex gap-3">
          <Button variant="outline" disabled={saving}>
            <Play className="h-4 w-4 mr-2" />
            Preview
          </Button>
          <Button onClick={handleSave} disabled={saving || !formData.name.trim()}>
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Creating...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Create
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}