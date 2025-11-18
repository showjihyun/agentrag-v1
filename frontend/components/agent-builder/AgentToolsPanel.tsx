'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Calculator,
  Code,
  Globe,
  Search,
  Workflow,
  FileJson,
  Split,
  Plus,
  Check,
  Info,
  X
} from 'lucide-react';
import {
  BUILTIN_AGENT_TOOLS,
  AgentTool,
  getAllCategories,
  getToolsByCategory,
  searchTools,
  ToolCategory
} from '@/lib/agent-tools';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface AgentToolsPanelProps {
  agentId: string;
  selectedTools: string[];
  onToolsChange: (tools: string[]) => void;
}

const ICON_MAP: Record<string, any> = {
  Calculator,
  Code,
  Globe,
  Search,
  Workflow,
  FileJson,
  Split,
};

export function AgentToolsPanel({ agentId, selectedTools, onToolsChange }: AgentToolsPanelProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<ToolCategory | 'all'>('all');
  const [detailTool, setDetailTool] = useState<AgentTool | null>(null);
  
  const categories = getAllCategories();
  
  // Filter tools
  const filteredTools = searchQuery
    ? searchTools(searchQuery)
    : selectedCategory === 'all'
    ? BUILTIN_AGENT_TOOLS
    : getToolsByCategory(selectedCategory);
  
  const toggleTool = (toolId: string) => {
    if (selectedTools.includes(toolId)) {
      onToolsChange(selectedTools.filter(id => id !== toolId));
    } else {
      onToolsChange([...selectedTools, toolId]);
    }
  };
  
  const getIcon = (iconName: string) => {
    const Icon = ICON_MAP[iconName] || Plus;
    return <Icon className="h-4 w-4" />;
  };
  
  const getCategoryColor = (category: ToolCategory) => {
    const colors: Record<ToolCategory, string> = {
      search: 'bg-blue-100 text-blue-800',
      data: 'bg-green-100 text-green-800',
      code: 'bg-purple-100 text-purple-800',
      api: 'bg-orange-100 text-orange-800',
      custom: 'bg-gray-100 text-gray-800',
      workflow: 'bg-pink-100 text-pink-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };
  
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Workflow className="h-5 w-5" />
            Agent Tools
          </CardTitle>
          <CardDescription>
            Select tools that this agent can use to accomplish tasks. Tools enable your agent to perform actions like calculations, API calls, and data processing.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search tools..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          {/* Category Tabs */}
          <Tabs value={selectedCategory} onValueChange={(v) => setSelectedCategory(v as any)}>
            <TabsList className="w-full justify-start overflow-x-auto">
              <TabsTrigger value="all">
                All ({BUILTIN_AGENT_TOOLS.length})
              </TabsTrigger>
              {categories.map((cat) => (
                <TabsTrigger key={cat.category} value={cat.category}>
                  {cat.label} ({cat.count})
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          
          {/* Tools Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[500px] overflow-y-auto">
            {filteredTools.map((tool) => {
              const isSelected = selectedTools.includes(tool.id);
              
              return (
                <div
                  key={tool.id}
                  className={`
                    relative p-4 border rounded-lg cursor-pointer transition-all
                    ${isSelected
                      ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                    }
                  `}
                  onClick={() => toggleTool(tool.id)}
                >
                  {/* Selection Indicator */}
                  {isSelected && (
                    <div className="absolute top-2 right-2">
                      <div className="bg-primary text-primary-foreground rounded-full p-1">
                        <Check className="h-3 w-3" />
                      </div>
                    </div>
                  )}
                  
                  {/* Tool Header */}
                  <div className="flex items-start gap-3 mb-2">
                    <div className={`p-2 rounded-lg ${isSelected ? 'bg-primary/10' : 'bg-gray-100'}`}>
                      {getIcon(tool.icon)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm truncate">{tool.name}</h4>
                      <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                        {tool.description}
                      </p>
                    </div>
                  </div>
                  
                  {/* Tool Footer */}
                  <div className="flex items-center justify-between mt-3">
                    <Badge variant="outline" className={`text-xs ${getCategoryColor(tool.category)}`}>
                      {tool.category}
                    </Badge>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2"
                      onClick={(e) => {
                        e.stopPropagation();
                        setDetailTool(tool);
                      }}
                    >
                      <Info className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
          
          {/* Empty State */}
          {filteredTools.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No tools found matching your search.</p>
            </div>
          )}
          
          {/* Selected Tools Summary */}
          {selectedTools.length > 0 && (
            <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  Selected Tools ({selectedTools.length})
                </p>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onToolsChange([])}
                  className="h-6 text-xs text-blue-700 hover:text-blue-900"
                >
                  Clear All
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedTools.map((toolId) => {
                  const tool = BUILTIN_AGENT_TOOLS.find(t => t.id === toolId);
                  return tool ? (
                    <Badge key={toolId} variant="secondary" className="gap-1">
                      {tool.name}
                      <X
                        className="h-3 w-3 cursor-pointer hover:text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleTool(toolId);
                        }}
                      />
                    </Badge>
                  ) : null;
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Tool Detail Dialog */}
      <Dialog open={!!detailTool} onOpenChange={() => setDetailTool(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          {detailTool && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-3 rounded-lg bg-primary/10">
                    {getIcon(detailTool.icon)}
                  </div>
                  <div>
                    <DialogTitle>{detailTool.name}</DialogTitle>
                    <DialogDescription>{detailTool.description}</DialogDescription>
                  </div>
                </div>
              </DialogHeader>
              
              <div className="space-y-4">
                {/* Metadata */}
                <div className="flex gap-2">
                  <Badge variant="outline" className={getCategoryColor(detailTool.category)}>
                    {detailTool.category}
                  </Badge>
                  <Badge variant="outline">v{detailTool.version}</Badge>
                  {detailTool.requiresAuth && (
                    <Badge variant="outline" className="bg-yellow-100 text-yellow-800">
                      Requires Auth
                    </Badge>
                  )}
                </div>
                
                {/* Parameters */}
                <div>
                  <h4 className="font-semibold mb-2">Parameters</h4>
                  <div className="space-y-2">
                    {detailTool.parameters.map((param) => (
                      <div key={param.name} className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                        <div className="flex items-center gap-2 mb-1">
                          <code className="text-sm font-mono">{param.name}</code>
                          <Badge variant="outline" className="text-xs">{param.type}</Badge>
                          {param.required && (
                            <Badge variant="destructive" className="text-xs">Required</Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground">{param.description}</p>
                        {param.default !== undefined && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Default: <code>{JSON.stringify(param.default)}</code>
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Usage Instructions */}
                <div>
                  <h4 className="font-semibold mb-2">Usage Instructions</h4>
                  <p className="text-sm text-muted-foreground">
                    {detailTool.agentIntegration.usageInstructions}
                  </p>
                </div>
                
                {/* Examples */}
                <div>
                  <h4 className="font-semibold mb-2">Examples</h4>
                  <ul className="space-y-1">
                    {detailTool.agentIntegration.examples.map((example, idx) => (
                      <li key={idx} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="text-primary">•</span>
                        <span>{example}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                {/* Input/Output Format */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-semibold mb-2 text-sm">Input Format</h4>
                    <pre className="text-xs bg-gray-50 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                      {detailTool.agentIntegration.inputFormat}
                    </pre>
                  </div>
                  <div>
                    <h4 className="font-semibold mb-2 text-sm">Output Format</h4>
                    <pre className="text-xs bg-gray-50 dark:bg-gray-900 p-2 rounded overflow-x-auto">
                      {detailTool.agentIntegration.outputFormat}
                    </pre>
                  </div>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
