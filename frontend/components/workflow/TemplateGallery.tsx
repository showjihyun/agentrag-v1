'use client';

/**
 * Workflow Template Gallery
 * 
 * Pre-built template selection UI with:
 * - Category filtering
 * - Search
 * - Preview
 * - Quick start
 */

import React, { useState, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Search,
  Zap,
  Mail,
  Database,
  Globe,
  Bot,
  GitBranch,
  Clock,
  FileText,
  MessageSquare,
  Sparkles,
  ArrowRight,
  Eye,
  Plus,
  Star,
  Users,
  TrendingUp,
} from 'lucide-react';

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: React.ReactNode;
  color: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: string;
  nodeCount: number;
  tags: string[];
  popular?: boolean;
  new?: boolean;
  preview?: {
    nodes: Array<{ type: string; name: string }>;
    description: string;
  };
}

const TEMPLATES: WorkflowTemplate[] = [
  {
    id: 'email-automation',
    name: 'Email Automation',
    description: 'Automatically process and respond to incoming emails with AI',
    category: 'communication',
    icon: <Mail className="h-5 w-5" />,
    color: '#3b82f6',
    difficulty: 'beginner',
    estimatedTime: '5 min',
    nodeCount: 4,
    tags: ['email', 'ai', 'automation'],
    popular: true,
    preview: {
      nodes: [
        { type: 'trigger', name: 'Email Trigger' },
        { type: 'ai', name: 'AI Classifier' },
        { type: 'condition', name: 'Route by Type' },
        { type: 'email', name: 'Send Response' },
      ],
      description: 'Receives emails, classifies them using AI, and sends appropriate responses.',
    },
  },
  {
    id: 'data-pipeline',
    name: 'Data Pipeline',
    description: 'ETL workflow for processing and transforming data',
    category: 'data',
    icon: <Database className="h-5 w-5" />,
    color: '#10b981',
    difficulty: 'intermediate',
    estimatedTime: '15 min',
    nodeCount: 6,
    tags: ['etl', 'database', 'transform'],
    preview: {
      nodes: [
        { type: 'trigger', name: 'Schedule Trigger' },
        { type: 'database', name: 'Fetch Data' },
        { type: 'transform', name: 'Transform' },
        { type: 'filter', name: 'Filter' },
        { type: 'database', name: 'Save Results' },
        { type: 'slack', name: 'Notify' },
      ],
      description: 'Scheduled data extraction, transformation, and loading with notifications.',
    },
  },
  {
    id: 'ai-chatbot',
    name: 'AI Chatbot',
    description: 'Conversational AI agent with memory and tool access',
    category: 'ai',
    icon: <Bot className="h-5 w-5" />,
    color: '#8b5cf6',
    difficulty: 'intermediate',
    estimatedTime: '10 min',
    nodeCount: 5,
    tags: ['chatbot', 'ai', 'conversation'],
    popular: true,
    new: true,
    preview: {
      nodes: [
        { type: 'trigger', name: 'Webhook Trigger' },
        { type: 'ai_agent', name: 'AI Agent' },
        { type: 'memory', name: 'Memory Store' },
        { type: 'tool', name: 'Web Search' },
        { type: 'webhook_response', name: 'Response' },
      ],
      description: 'AI chatbot with conversation memory and web search capabilities.',
    },
  },
  {
    id: 'webhook-api',
    name: 'Webhook API',
    description: 'Create a custom API endpoint with data processing',
    category: 'api',
    icon: <Globe className="h-5 w-5" />,
    color: '#f59e0b',
    difficulty: 'beginner',
    estimatedTime: '5 min',
    nodeCount: 3,
    tags: ['api', 'webhook', 'rest'],
    preview: {
      nodes: [
        { type: 'trigger', name: 'Webhook Trigger' },
        { type: 'code', name: 'Process Data' },
        { type: 'webhook_response', name: 'Response' },
      ],
      description: 'Simple webhook endpoint that processes incoming data and returns a response.',
    },
  },
  {
    id: 'scheduled-report',
    name: 'Scheduled Report',
    description: 'Generate and send reports on a schedule',
    category: 'automation',
    icon: <Clock className="h-5 w-5" />,
    color: '#ec4899',
    difficulty: 'beginner',
    estimatedTime: '10 min',
    nodeCount: 5,
    tags: ['report', 'schedule', 'email'],
    preview: {
      nodes: [
        { type: 'trigger', name: 'Schedule (Daily)' },
        { type: 'database', name: 'Fetch Metrics' },
        { type: 'transform', name: 'Format Report' },
        { type: 'ai', name: 'Generate Summary' },
        { type: 'email', name: 'Send Report' },
      ],
      description: 'Daily report generation with AI-powered summaries sent via email.',
    },
  },
  {
    id: 'content-moderation',
    name: 'Content Moderation',
    description: 'AI-powered content review and moderation',
    category: 'ai',
    icon: <FileText className="h-5 w-5" />,
    color: '#ef4444',
    difficulty: 'intermediate',
    estimatedTime: '15 min',
    nodeCount: 7,
    tags: ['moderation', 'ai', 'content'],
    new: true,
    preview: {
      nodes: [
        { type: 'trigger', name: 'Webhook Trigger' },
        { type: 'ai', name: 'Content Analyzer' },
        { type: 'condition', name: 'Check Score' },
        { type: 'human_approval', name: 'Manual Review' },
        { type: 'database', name: 'Update Status' },
      ],
      description: 'Automated content moderation with human-in-the-loop for edge cases.',
    },
  },
  {
    id: 'slack-bot',
    name: 'Slack Bot',
    description: 'Interactive Slack bot with AI responses',
    category: 'communication',
    icon: <MessageSquare className="h-5 w-5" />,
    color: '#4a154b',
    difficulty: 'intermediate',
    estimatedTime: '10 min',
    nodeCount: 4,
    tags: ['slack', 'bot', 'ai'],
    popular: true,
    preview: {
      nodes: [
        { type: 'trigger', name: 'Slack Event' },
        { type: 'ai_agent', name: 'AI Agent' },
        { type: 'slack', name: 'Send Reply' },
      ],
      description: 'Slack bot that responds to messages using AI.',
    },
  },
  {
    id: 'parallel-processing',
    name: 'Parallel Processing',
    description: 'Process multiple items in parallel for speed',
    category: 'advanced',
    icon: <GitBranch className="h-5 w-5" />,
    color: '#06b6d4',
    difficulty: 'advanced',
    estimatedTime: '20 min',
    nodeCount: 8,
    tags: ['parallel', 'performance', 'batch'],
    preview: {
      nodes: [
        { type: 'trigger', name: 'Webhook Trigger' },
        { type: 'loop', name: 'Split Items' },
        { type: 'parallel', name: 'Parallel Process' },
        { type: 'merge', name: 'Merge Results' },
        { type: 'webhook_response', name: 'Response' },
      ],
      description: 'Advanced workflow with parallel processing for batch operations.',
    },
  },
];

const CATEGORIES = [
  { id: 'all', name: 'All Templates', icon: Sparkles },
  { id: 'popular', name: 'Popular', icon: Star },
  { id: 'ai', name: 'AI & Agents', icon: Bot },
  { id: 'communication', name: 'Communication', icon: MessageSquare },
  { id: 'data', name: 'Data', icon: Database },
  { id: 'api', name: 'API', icon: Globe },
  { id: 'automation', name: 'Automation', icon: Zap },
  { id: 'advanced', name: 'Advanced', icon: GitBranch },
];

interface TemplateGalleryProps {
  onSelect: (template: WorkflowTemplate) => void;
  onClose?: () => void;
}

export function TemplateGallery({ onSelect, onClose }: TemplateGalleryProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [previewTemplate, setPreviewTemplate] = useState<WorkflowTemplate | null>(null);

  const filteredTemplates = useMemo(() => {
    let templates = TEMPLATES;

    if (selectedCategory === 'popular') {
      templates = templates.filter(t => t.popular);
    } else if (selectedCategory !== 'all') {
      templates = templates.filter(t => t.category === selectedCategory);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      templates = templates.filter(t =>
        t.name.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query) ||
        t.tags.some(tag => tag.includes(query))
      );
    }

    return templates;
  }, [searchQuery, selectedCategory]);

  const difficultyColors = {
    beginner: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    intermediate: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    advanced: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-xl font-semibold">Template Gallery</h2>
            <p className="text-sm text-muted-foreground">
              Start with a pre-built workflow template
            </p>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <TrendingUp className="h-4 w-4" />
            <span>{TEMPLATES.length} templates</span>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search templates..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Categories */}
      <div className="px-6 py-3 border-b">
        <ScrollArea className="w-full">
          <div className="flex gap-2">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <Button
                  key={cat.id}
                  variant={selectedCategory === cat.id ? 'default' : 'outline'}
                  size="sm"
                  className="gap-2 whitespace-nowrap"
                  onClick={() => setSelectedCategory(cat.id)}
                >
                  <Icon className="h-4 w-4" />
                  {cat.name}
                </Button>
              );
            })}
          </div>
        </ScrollArea>
      </div>

      {/* Templates Grid */}
      <ScrollArea className="flex-1 p-6">
        {filteredTemplates.length === 0 ? (
          <div className="text-center py-12">
            <Search className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
            <p className="font-medium">No templates found</p>
            <p className="text-sm text-muted-foreground mt-1">
              Try a different search term or category
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTemplates.map((template) => (
              <Card
                key={template.id}
                className="group cursor-pointer hover:shadow-md transition-all hover:border-primary/50"
                onClick={() => setPreviewTemplate(template)}
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${template.color}20` }}
                    >
                      <div style={{ color: template.color }}>{template.icon}</div>
                    </div>
                    <div className="flex gap-1">
                      {template.popular && (
                        <Badge variant="secondary" className="text-xs gap-1">
                          <Star className="h-3 w-3 fill-current" />
                          Popular
                        </Badge>
                      )}
                      {template.new && (
                        <Badge className="text-xs gap-1">
                          <Sparkles className="h-3 w-3" />
                          New
                        </Badge>
                      )}
                    </div>
                  </div>
                  <CardTitle className="text-base mt-3">{template.name}</CardTitle>
                  <CardDescription className="line-clamp-2">
                    {template.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant="outline" className={cn('text-xs', difficultyColors[template.difficulty])}>
                      {template.difficulty}
                    </Badge>
                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {template.estimatedTime}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {template.nodeCount} nodes
                    </span>
                  </div>
                  <div className="flex gap-1 mt-3 flex-wrap">
                    {template.tags.slice(0, 3).map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Preview Dialog */}
      <Dialog open={!!previewTemplate} onOpenChange={() => setPreviewTemplate(null)}>
        <DialogContent className="max-w-2xl">
          {previewTemplate && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <div
                    className="p-3 rounded-lg"
                    style={{ backgroundColor: `${previewTemplate.color}20` }}
                  >
                    <div style={{ color: previewTemplate.color }}>{previewTemplate.icon}</div>
                  </div>
                  <div>
                    <DialogTitle>{previewTemplate.name}</DialogTitle>
                    <DialogDescription>{previewTemplate.description}</DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {/* Workflow preview */}
                {previewTemplate.preview && (
                  <div className="p-4 rounded-lg bg-muted/50 border">
                    <h4 className="font-medium text-sm mb-3">Workflow Structure</h4>
                    <div className="flex items-center gap-2 flex-wrap">
                      {previewTemplate.preview.nodes.map((node, i) => (
                        <React.Fragment key={i}>
                          <div className="px-3 py-1.5 rounded-lg bg-background border text-sm">
                            {node.name}
                          </div>
                          {i < previewTemplate.preview!.nodes.length - 1 && (
                            <ArrowRight className="h-4 w-4 text-muted-foreground" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                    <p className="text-sm text-muted-foreground mt-3">
                      {previewTemplate.preview.description}
                    </p>
                  </div>
                )}

                {/* Details */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold">{previewTemplate.nodeCount}</div>
                    <div className="text-xs text-muted-foreground">Nodes</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold">{previewTemplate.estimatedTime}</div>
                    <div className="text-xs text-muted-foreground">Setup Time</div>
                  </div>
                  <div className="text-center p-3 rounded-lg bg-muted/50">
                    <div className="text-2xl font-bold capitalize">{previewTemplate.difficulty}</div>
                    <div className="text-xs text-muted-foreground">Difficulty</div>
                  </div>
                </div>

                {/* Tags */}
                <div className="flex gap-2 flex-wrap">
                  {previewTemplate.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setPreviewTemplate(null)}>
                  Cancel
                </Button>
                <Button
                  className="gap-2"
                  onClick={() => {
                    onSelect(previewTemplate);
                    setPreviewTemplate(null);
                    onClose?.();
                  }}
                >
                  <Plus className="h-4 w-4" />
                  Use Template
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export type { WorkflowTemplate };
