'use client';

/**
 * Improved Block Palette
 * 
 * Enhanced with:
 * - Loading states and feedback
 * - Keyboard navigation
 * - Drag and drop support
 * - Empty state illustrations
 * - Accessibility improvements
 */

import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import {
  Search,
  Wrench,
  Zap,
  Database,
  Code,
  Globe,
  Mail,
  MessageSquare,
  Bot,
  FileText,
  Calculator,
  GitBranch,
  Clock,
  Filter,
  ChevronRight,
  Star,
  TrendingUp,
  Sparkles,
  Loader2,
  Plus,
  X,
  Keyboard,
  Eye,
  Mic,
  Volume2,
  Users,
  Wand2,
  Route
} from 'lucide-react';

interface BlockPaletteProps {
  onAddNode: (type: string, toolId?: string, toolName?: string) => void;
  executionLogs?: ExecutionLog[];
}

interface ExecutionLog {
  id: string;
  timestamp: Date;
  nodeId: string;
  nodeName: string;
  type: 'info' | 'success' | 'error' | 'warning';
  message: string;
  duration?: number;
  data?: any;
}

interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: any;
  popular?: boolean;
  new?: boolean;
}

const TOOLS: Tool[] = [
  // AI & Agents (Priority)
  { id: 'ai_agent', name: 'AI Agent', description: 'Autonomous agent with reasoning and tool use', category: 'ai', icon: Bot, popular: true },
  { id: 'openai_chat', name: 'OpenAI Chat', description: 'GPT-4 and GPT-3.5 models', category: 'ai', icon: Sparkles, popular: true },
  { id: 'anthropic_claude', name: 'Claude', description: 'Anthropic Claude AI', category: 'ai', icon: Bot },
  { id: 'google_gemini', name: 'Gemini', description: 'Google Gemini AI', category: 'ai', icon: Sparkles },
  
  // 🌟 Gemini 3.0 MultiModal (NEW - Priority)
  { id: 'gemini_vision', name: 'Gemini Vision', description: 'Advanced image analysis with Gemini 3.0', category: 'multimodal', icon: Eye, popular: true, new: true },
  { id: 'gemini_audio', name: 'Gemini Audio', description: 'Audio processing and transcription with Gemini 3.0', category: 'multimodal', icon: Mic, popular: true, new: true },
  { id: 'gemini_video', name: 'Gemini Video', description: 'Advanced video analysis and content extraction', category: 'multimodal', icon: Volume2, popular: true, new: true },
  { id: 'gemini_batch', name: 'Gemini Batch', description: 'Batch processing for multiple videos simultaneously', category: 'multimodal', icon: Users, popular: true, new: true },
  { id: 'gemini_fusion', name: 'Gemini Fusion', description: 'Advanced multimodal fusion processing', category: 'multimodal', icon: Sparkles, popular: true, new: true },
  { id: 'gemini_auto_optimizer', name: 'Gemini Auto-optimizer', description: 'AI-powered automatic optimization and strategy selection', category: 'multimodal', icon: Wand2, popular: true, new: true },
  { id: 'predictive_routing', name: 'Predictive Routing', description: 'AI-powered predictive routing and intelligent strategy selection', category: 'ai', icon: Route, popular: true, new: true },
  { id: 'gemini_document', name: 'Gemini Document', description: 'Document structure analysis and data extraction', category: 'multimodal', icon: FileText, new: true },
  
  // Communication (Priority)
  { id: 'slack', name: 'Slack', description: 'Send messages, manage channels', category: 'communication', icon: MessageSquare, popular: true, new: true },
  { id: 'gmail', name: 'Gmail', description: 'Send and manage emails', category: 'communication', icon: Mail, popular: true, new: true },
  { id: 'discord', name: 'Discord', description: 'Discord webhooks', category: 'communication', icon: MessageSquare },
  { id: 'telegram', name: 'Telegram', description: 'Telegram bot', category: 'communication', icon: MessageSquare },
  
  // API & Integration
  { id: 'http_request', name: 'HTTP Request', description: 'Make HTTP/REST API calls', category: 'api', icon: Globe, popular: true },
  { id: 'webhook', name: 'Webhook', description: 'Receive webhooks', category: 'api', icon: Zap },
  { id: 'graphql', name: 'GraphQL', description: 'Execute GraphQL queries', category: 'api', icon: Code },
  
  // Data & Database
  { id: 'vector_search', name: 'Vector Search', description: 'Semantic search in Milvus', category: 'data', icon: Database, popular: true },
  { id: 'postgres', name: 'PostgreSQL', description: 'Query PostgreSQL', category: 'data', icon: Database },
  { id: 'csv_parser', name: 'CSV Parser', description: 'Parse CSV files', category: 'data', icon: FileText },
  { id: 'json_transform', name: 'JSON Transform', description: 'Transform JSON data', category: 'data', icon: Code },
  
  // Code Execution
  { id: 'python_code', name: 'Python Code', description: 'Execute Python code', category: 'code', icon: Code },
  { id: 'javascript_code', name: 'JavaScript', description: 'Execute JavaScript', category: 'code', icon: Code },
  { id: 'calculator', name: 'Calculator', description: 'Mathematical calculations', category: 'code', icon: Calculator },
];

const CONTROL_TOOLS = [
  // Basic Control
  { id: 'start', name: 'Start', description: 'Workflow entry point', icon: Zap, category: 'control', popular: true },
  { id: 'end', name: 'End', description: 'Workflow exit point', icon: Zap, category: 'control', popular: true },
  { id: 'condition', name: 'Condition', description: 'If/else branching logic', icon: GitBranch, category: 'control', popular: true },
  
  // Loops & Iteration
  { id: 'loop', name: 'Loop', description: 'Iterate over items', icon: GitBranch, category: 'control' },
  { id: 'parallel', name: 'Parallel', description: 'Execute branches in parallel', icon: Zap, category: 'control' },
  
  // Flow Control
  { id: 'delay', name: 'Delay', description: 'Wait for duration', icon: Clock, category: 'control' },
  { id: 'switch', name: 'Switch', description: 'Multi-way branching', icon: GitBranch, category: 'control' },
  { id: 'merge', name: 'Merge', description: 'Merge multiple branches', icon: GitBranch, category: 'control' },
  
  // Data Processing
  { id: 'filter', name: 'Filter', description: 'Filter data items', icon: Filter, category: 'control' },
  { id: 'transform', name: 'Transform', description: 'Transform data', icon: Code, category: 'control' },
  
  // Error Handling
  { id: 'try_catch', name: 'Try/Catch', description: 'Error handling', icon: Zap, category: 'control' },
  
  // Human Interaction
  { id: 'human_approval', name: 'Human Approval', description: 'Wait for human approval', icon: Zap, category: 'control', new: true },
];

const TRIGGERS: Tool[] = [
  { id: 'webhook_trigger', name: 'Webhook', description: 'Trigger workflow via HTTP webhook', icon: Globe, category: 'trigger', popular: true },
  { id: 'schedule_trigger', name: 'Schedule', description: 'Run workflow on schedule (cron)', icon: Clock, category: 'trigger', popular: true },
  { id: 'manual_trigger', name: 'Manual', description: 'Manually trigger workflow', icon: Zap, category: 'trigger', popular: true },
  { id: 'email_trigger', name: 'Email', description: 'Trigger on email received', icon: Mail, category: 'trigger' },
  { id: 'file_trigger', name: 'File Upload', description: 'Trigger on file upload', icon: FileText, category: 'trigger' },
  { id: 'slack_trigger', name: 'Slack Event', description: 'Trigger on Slack message/event', icon: MessageSquare, category: 'trigger', new: true },
];

const BLOCKS: Tool[] = [
  { id: 'text_block', name: 'Text', description: 'Static text or template', icon: FileText, category: 'block' },
  { id: 'code_block', name: 'Code', description: 'Custom code execution', icon: Code, category: 'block', popular: true },
  { id: 'http_block', name: 'HTTP Request', description: 'Make HTTP API calls', icon: Globe, category: 'block', popular: true },
  { id: 'database_block', name: 'Database Query', description: 'Query database', icon: Database, category: 'block' },
  { id: 'transform_block', name: 'Transform', description: 'Transform data structure', icon: Code, category: 'block' },
  { id: 'ai_block', name: 'AI Processing', description: 'AI/LLM processing', icon: Bot, category: 'block', popular: true },
];

export function ImprovedBlockPalette({ onAddNode, executionLogs = [] }: BlockPaletteProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('tools');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [recentlyUsed, setRecentlyUsed] = useState<string[]>([]);
  const [isAdding, setIsAdding] = useState<string | null>(null);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();
  
  // Load recently used tools from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('workflow_recently_used_tools');
    if (saved) {
      try {
        setRecentlyUsed(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load recently used tools:', e);
      }
    }
  }, []);
  
  // Keyboard shortcut for search (Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);
  
  // Track tool usage
  const trackToolUsage = useCallback((toolId: string) => {
    setRecentlyUsed(prev => {
      const updated = [toolId, ...prev.filter(id => id !== toolId)].slice(0, 5);
      localStorage.setItem('workflow_recently_used_tools', JSON.stringify(updated));
      return updated;
    });
  }, []);
  
  // Handle add node with tracking and feedback
  const handleAddNode = useCallback(async (type: string, toolId?: string, toolName?: string) => {
    const id = toolId || type;
    setIsAdding(id);
    
    try {
      if (toolId) {
        trackToolUsage(toolId);
      }
      
      // Small delay for visual feedback
      await new Promise(resolve => setTimeout(resolve, 150));
      
      onAddNode(type, toolId, toolName);
      
      toast({
        title: '✓ Node Added',
        description: `${toolName || type} has been added to the canvas`,
        duration: 2000,
      });
    } finally {
      setIsAdding(null);
    }
  }, [onAddNode, trackToolUsage, toast]);
  
  // Keyboard navigation for tool list
  const handleKeyDown = useCallback((e: React.KeyboardEvent, tools: Tool[]) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => Math.min(prev + 1, tools.length - 1));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => Math.max(prev - 1, 0));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < tools.length) {
          const tool = tools[highlightedIndex];
          handleAddNode('tool', tool.id, tool.name);
        }
        break;
      case 'Escape':
        setSearchQuery('');
        setHighlightedIndex(-1);
        searchInputRef.current?.blur();
        break;
    }
  }, [highlightedIndex, handleAddNode]);
  
  // Reset highlighted index when search changes
  useEffect(() => {
    setHighlightedIndex(-1);
  }, [searchQuery, selectedCategory]);
  
  // Filter tools
  const filteredTools = useMemo(() => {
    let tools = TOOLS;
    
    if (selectedCategory !== 'all') {
      tools = tools.filter(t => t.category === selectedCategory);
    }
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      tools = tools.filter(t =>
        t.name.toLowerCase().includes(query) ||
        t.description.toLowerCase().includes(query)
      );
    }
    
    // Sort: popular first, then alphabetically
    return tools.sort((a, b) => {
      if (a.popular && !b.popular) return -1;
      if (!a.popular && b.popular) return 1;
      return a.name.localeCompare(b.name);
    });
  }, [searchQuery, selectedCategory]);
  
  const categories = useMemo(() => {
    const cats = new Map<string, number>();
    TOOLS.forEach(tool => {
      cats.set(tool.category, (cats.get(tool.category) || 0) + 1);
    });
    return Array.from(cats.entries()).map(([name, count]) => ({ name, count }));
  }, []);
  
  const getLogIcon = (type: ExecutionLog['type']) => {
    switch (type) {
      case 'success': return '✓';
      case 'error': return '✗';
      case 'warning': return '⚠';
      default: return 'ℹ';
    }
  };
  
  const getLogColor = (type: ExecutionLog['type']) => {
    switch (type) {
      case 'success': return 'text-green-600';
      case 'error': return 'text-red-600';
      case 'warning': return 'text-yellow-600';
      default: return 'text-blue-600';
    }
  };
  
  return (
    <div className="flex flex-col h-full">
      {/* Main Content Area - 70% */}
      <div className="flex-1 flex flex-col min-h-0">
        <Card className="flex-1 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b">
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              <Wrench className="h-5 w-5" />
              Block Palette
            </h3>
            
            {/* Search with keyboard shortcut hint */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
              <Input
                ref={searchInputRef}
                type="text"
                placeholder="Search blocks and tools..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-20"
                aria-label="Search blocks and tools"
                role="combobox"
                aria-expanded={searchQuery.length > 0}
                aria-controls="tool-results"
              />
              <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
                {searchQuery ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSearchQuery('')}
                    className="h-6 px-2 text-xs"
                    aria-label="Clear search"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                ) : (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <kbd className="hidden sm:inline-flex h-5 items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
                          <Keyboard className="h-3 w-3" />
                          K
                        </kbd>
                      </TooltipTrigger>
                      <TooltipContent>Press Ctrl+K to search</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </div>
            </div>
            
            {/* Recently Used - Quick Access */}
            {recentlyUsed.length > 0 && !searchQuery && (
              <div className="mt-3">
                <p className="text-xs text-muted-foreground mb-2">Recently Used</p>
                <div className="flex flex-wrap gap-1">
                  {recentlyUsed.map(toolId => {
                    const tool = [...TOOLS, ...CONTROL_TOOLS, ...TRIGGERS, ...BLOCKS].find(t => t.id === toolId);
                    if (!tool) return null;
                    return (
                      <Button
                        key={toolId}
                        variant="outline"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={() => handleAddNode('tool', tool.id, tool.name)}
                      >
                        {tool.name}
                      </Button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
          
          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
            <div className="px-4 pt-2 border-b">
              <TabsList className="w-full grid grid-cols-4">
                <TabsTrigger value="tools">
                  <Wrench className="h-4 w-4 mr-1" />
                  Tools
                </TabsTrigger>
                <TabsTrigger value="control">
                  <GitBranch className="h-4 w-4 mr-1" />
                  Control
                </TabsTrigger>
                <TabsTrigger value="triggers">
                  <Zap className="h-4 w-4 mr-1" />
                  Triggers
                </TabsTrigger>
                <TabsTrigger value="blocks">
                  <Code className="h-4 w-4 mr-1" />
                  Blocks
                </TabsTrigger>
              </TabsList>
            </div>
            
            <TabsContent value="tools" className="flex-1 flex flex-col min-h-0 m-0">
              {/* Category Filter */}
              <div className="px-4 py-2 border-b">
                <ScrollArea className="w-full">
                  <div className="flex gap-2">
                    <Button
                      variant={selectedCategory === 'all' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedCategory('all')}
                    >
                      All
                    </Button>
                    {categories.map(cat => (
                      <Button
                        key={cat.name}
                        variant={selectedCategory === cat.name ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setSelectedCategory(cat.name)}
                      >
                        {cat.name} ({cat.count})
                      </Button>
                    ))}
                  </div>
                </ScrollArea>
              </div>
              
              {/* Tools List */}
              <ScrollArea className="flex-1">
                <div 
                  id="tool-results"
                  className="p-4 space-y-2"
                  role="listbox"
                  aria-label="Available tools"
                  onKeyDown={(e) => handleKeyDown(e, filteredTools)}
                >
                  {filteredTools.map((tool, index) => {
                    const Icon = tool.icon;
                    const isHighlighted = index === highlightedIndex;
                    const isLoading = isAdding === tool.id;
                    
                    return (
                      <div
                        key={tool.id}
                        role="option"
                        aria-selected={isHighlighted}
                        tabIndex={0}
                        className={cn(
                          "group relative p-3 border rounded-lg transition-all cursor-pointer",
                          "bg-background hover:border-primary hover:shadow-md",
                          "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                          isHighlighted && "border-primary bg-primary/5",
                          isLoading && "opacity-70 pointer-events-none"
                        )}
                        onClick={() => handleAddNode('tool', tool.id, tool.name)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddNode('tool', tool.id, tool.name)}
                        onMouseEnter={() => setHighlightedIndex(index)}
                        aria-label={`Add ${tool.name} node`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={cn(
                            "p-2 rounded-lg transition-colors",
                            "bg-primary/10 group-hover:bg-primary/20",
                            isHighlighted && "bg-primary/20"
                          )}>
                            {isLoading ? (
                              <Loader2 className="h-5 w-5 text-primary animate-spin" />
                            ) : (
                              <Icon className="h-5 w-5 text-primary" />
                            )}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-medium text-sm">{tool.name}</h4>
                              {tool.popular && (
                                <Badge variant="secondary" className="text-xs gap-1">
                                  <Star className="h-3 w-3 fill-current" />
                                  Popular
                                </Badge>
                              )}
                              {tool.new && (
                                <Badge variant="default" className="text-xs gap-1">
                                  <Sparkles className="h-3 w-3" />
                                  New
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {tool.description}
                            </p>
                            <Badge variant="outline" className="text-xs mt-2">
                              {tool.category}
                            </Badge>
                          </div>
                          
                          <div className={cn(
                            "flex items-center gap-1 transition-opacity",
                            "opacity-0 group-hover:opacity-100",
                            isHighlighted && "opacity-100"
                          )}>
                            <Plus className="h-4 w-4 text-primary" />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  
                  {filteredTools.length === 0 && (
                    <div 
                      className="text-center py-12 text-muted-foreground" 
                      role="status" 
                      aria-live="polite"
                    >
                      {/* Empty state illustration */}
                      <div className="relative mx-auto w-24 h-24 mb-4">
                        <div className="absolute inset-0 bg-muted/50 rounded-full" />
                        <Search className="absolute inset-0 m-auto h-10 w-10 opacity-30" aria-hidden="true" />
                      </div>
                      <p className="font-medium">No tools found</p>
                      <p className="text-xs mt-2 max-w-[200px] mx-auto">
                        Try a different search term or browse other categories
                      </p>
                      {searchQuery && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="mt-4 gap-2"
                          onClick={() => setSearchQuery('')}
                        >
                          <X className="h-3 w-3" />
                          Clear search
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
            
            <TabsContent value="control" className="flex-1 min-h-0 m-0">
              <ScrollArea className="h-full">
                <div className="p-4 space-y-2">
                  {CONTROL_TOOLS.map((control) => {
                    const Icon = control.icon;
                    return (
                      <div
                        key={control.id}
                        className="group relative p-3 border rounded-lg hover:border-primary hover:shadow-md transition-all cursor-pointer bg-white dark:bg-gray-950"
                        onClick={() => onAddNode(control.id, undefined, control.name)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950 group-hover:bg-blue-200 dark:group-hover:bg-blue-900 transition-colors">
                            <Icon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-medium text-sm">{control.name}</h4>
                              {control.popular && (
                                <Badge variant="secondary" className="text-xs gap-1">
                                  <Star className="h-3 w-3 fill-current" />
                                  Popular
                                </Badge>
                              )}
                              {control.new && (
                                <Badge variant="default" className="text-xs gap-1">
                                  <Sparkles className="h-3 w-3" />
                                  New
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {control.description}
                            </p>
                          </div>
                          
                          <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-primary transition-colors" />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </TabsContent>
            
            <TabsContent value="triggers" className="flex-1 min-h-0 m-0">
              <ScrollArea className="h-full">
                <div className="p-4 space-y-2">
                  {TRIGGERS.map((trigger) => {
                    const Icon = trigger.icon;
                    return (
                      <div
                        key={trigger.id}
                        className="group relative p-3 border rounded-lg hover:border-primary hover:shadow-md transition-all cursor-pointer bg-white dark:bg-gray-950"
                        onClick={() => onAddNode(trigger.id, undefined, trigger.name)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-2 rounded-lg bg-green-100 dark:bg-green-950 group-hover:bg-green-200 dark:group-hover:bg-green-900 transition-colors">
                            <Icon className="h-5 w-5 text-green-600 dark:text-green-400" />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-medium text-sm">{trigger.name}</h4>
                              {trigger.popular && (
                                <Badge variant="secondary" className="text-xs gap-1">
                                  <Star className="h-3 w-3 fill-current" />
                                  Popular
                                </Badge>
                              )}
                              {trigger.new && (
                                <Badge variant="default" className="text-xs gap-1">
                                  <Sparkles className="h-3 w-3" />
                                  New
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {trigger.description}
                            </p>
                          </div>
                          
                          <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-primary transition-colors" />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </TabsContent>
            
            <TabsContent value="blocks" className="flex-1 min-h-0 m-0">
              <ScrollArea className="h-full">
                <div className="p-4 space-y-2">
                  {BLOCKS.map((block) => {
                    const Icon = block.icon;
                    return (
                      <div
                        key={block.id}
                        className="group relative p-3 border rounded-lg hover:border-primary hover:shadow-md transition-all cursor-pointer bg-white dark:bg-gray-950"
                        onClick={() => onAddNode('block', block.id, block.name)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-950 group-hover:bg-purple-200 dark:group-hover:bg-purple-900 transition-colors">
                            <Icon className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <h4 className="font-medium text-sm">{block.name}</h4>
                              {block.popular && (
                                <Badge variant="secondary" className="text-xs gap-1">
                                  <Star className="h-3 w-3 fill-current" />
                                  Popular
                                </Badge>
                              )}
                              {block.new && (
                                <Badge variant="default" className="text-xs gap-1">
                                  <Sparkles className="h-3 w-3" />
                                  New
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {block.description}
                            </p>
                          </div>
                          
                          <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-primary transition-colors" />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </Card>
      </div>
      
      {/* Execution Logs Panel - 30% */}
      <div className="h-[30%] min-h-[200px] border-t">
        <Card className="h-full flex flex-col">
          <div className="p-3 border-b bg-gray-50 dark:bg-gray-900">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Execution Logs
              </h4>
              <Badge variant="outline" className="text-xs">
                {executionLogs.length} events
              </Badge>
            </div>
          </div>
          
          <ScrollArea className="flex-1">
            <div className="p-3 space-y-1">
              {executionLogs.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No execution logs yet</p>
                  <p className="text-xs mt-1">Logs will appear here when you run workflows</p>
                </div>
              ) : (
                executionLogs.map((log) => (
                  <div
                    key={log.id}
                    className="p-2 rounded border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
                  >
                    <div className="flex items-start gap-2">
                      <span className={`text-sm font-mono ${getLogColor(log.type)}`}>
                        {getLogIcon(log.type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-medium truncate">
                            {log.nodeName}
                          </span>
                          {log.duration && (
                            <Badge variant="outline" className="text-xs">
                              {log.duration}ms
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {log.message}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {log.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </ScrollArea>
        </Card>
      </div>
    </div>
  );
}
