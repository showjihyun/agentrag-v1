'use client';

import { useState, useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
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
  Sparkles
} from 'lucide-react';

interface BlockPaletteProps {
  onAddNode: (type: string, toolId?: string) => void;
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

const BLOCK_TYPES = [
  { id: 'trigger', name: 'Trigger', description: 'Start workflow', icon: Zap, category: 'control' },
  { id: 'condition', name: 'Condition', description: 'If/else logic', icon: GitBranch, category: 'control' },
  { id: 'loop', name: 'Loop', description: 'Iterate over items', icon: GitBranch, category: 'control' },
  { id: 'delay', name: 'Delay', description: 'Wait for duration', icon: Clock, category: 'control' },
  { id: 'filter', name: 'Filter', description: 'Filter data', icon: Filter, category: 'control' },
];

export function ImprovedBlockPalette({ onAddNode, executionLogs = [] }: BlockPaletteProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('tools');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
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
            
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search blocks and tools..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          
          {/* Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
            <div className="px-4 pt-2 border-b">
              <TabsList className="w-full">
                <TabsTrigger value="tools" className="flex-1">
                  <Wrench className="h-4 w-4 mr-2" />
                  Tools ({TOOLS.length})
                </TabsTrigger>
                <TabsTrigger value="blocks" className="flex-1">
                  <GitBranch className="h-4 w-4 mr-2" />
                  Blocks ({BLOCK_TYPES.length})
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
                <div className="p-4 space-y-2">
                  {filteredTools.map((tool) => {
                    const Icon = tool.icon;
                    return (
                      <div
                        key={tool.id}
                        className="group relative p-3 border rounded-lg hover:border-primary hover:shadow-md transition-all cursor-pointer bg-white dark:bg-gray-950"
                        onClick={() => onAddNode('tool', tool.id)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                            <Icon className="h-5 w-5 text-primary" />
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
                          
                          <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-primary transition-colors" />
                        </div>
                      </div>
                    );
                  })}
                  
                  {filteredTools.length === 0 && (
                    <div className="text-center py-12 text-muted-foreground">
                      <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>No tools found</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
            
            <TabsContent value="blocks" className="flex-1 min-h-0 m-0">
              <ScrollArea className="h-full">
                <div className="p-4 space-y-2">
                  {BLOCK_TYPES.map((block) => {
                    const Icon = block.icon;
                    return (
                      <div
                        key={block.id}
                        className="group p-3 border rounded-lg hover:border-primary hover:shadow-md transition-all cursor-pointer"
                        onClick={() => onAddNode(block.id)}
                      >
                        <div className="flex items-start gap-3">
                          <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                            <Icon className="h-5 w-5 text-primary" />
                          </div>
                          
                          <div className="flex-1">
                            <h4 className="font-medium text-sm mb-1">{block.name}</h4>
                            <p className="text-xs text-muted-foreground">
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
