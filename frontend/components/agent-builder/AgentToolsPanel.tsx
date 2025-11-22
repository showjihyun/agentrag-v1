'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Workflow, Search, Check, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface AgentToolsPanelProps {
  agentId: string;
  selectedTools: string[];
  onToolsChange: (tools: string[]) => void;
  onToolsWithConfigChange?: (tools: SelectedTool[]) => void;
}

interface SelectedTool {
  tool_id: string;
  tool: any;
  configuration: Record<string, any>;
  order: number;
}

interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  icon?: string;
  bg_color?: string;
}

function SimpleToolSelector({
  selectedTools,
  onToolsChange,
}: {
  selectedTools: string[];
  onToolsChange: (tools: string[]) => void;
}) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      const response = await fetch("/api/agent-builder/tools");
      const data = await response.json();
      setTools(data.tools || []);
      setCategories(["all", ...(data.categories || [])]);
    } catch (error) {
      console.error("Failed to fetch tools:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTools = tools.filter((tool) => {
    const matchesSearch =
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === "all" || tool.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const toggleTool = (toolId: string) => {
    if (selectedTools.includes(toolId)) {
      onToolsChange(selectedTools.filter((id) => id !== toolId));
    } else {
      onToolsChange([...selectedTools, toolId]);
    }
  };

  return (
    <div className="space-y-4">
      {/* Selected Tools Summary */}
      {selectedTools.length > 0 && (
        <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium">
              Selected Tools ({selectedTools.length})
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToolsChange([])}
              className="h-6 text-xs"
            >
              Clear All
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedTools.map((toolId) => {
              const tool = tools.find((t) => t.id === toolId);
              return (
                <Badge key={toolId} variant="secondary" className="gap-1">
                  {tool?.name || toolId}
                  <X
                    className="h-3 w-3 cursor-pointer hover:text-destructive"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleTool(toolId);
                    }}
                  />
                </Badge>
              );
            })}
          </div>
        </div>
      )}

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search tools..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Category Tabs */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="w-full justify-start overflow-x-auto">
          {categories.map((category) => (
            <TabsTrigger key={category} value={category} className="capitalize">
              {category}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value={selectedCategory} className="mt-4">
          <ScrollArea className="h-[400px] pr-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {loading ? (
                <div className="col-span-2 text-center py-8 text-muted-foreground">
                  Loading tools...
                </div>
              ) : filteredTools.length === 0 ? (
                <div className="col-span-2 text-center py-8 text-muted-foreground">
                  No tools found
                </div>
              ) : (
                filteredTools.map((tool) => {
                  const isSelected = selectedTools.includes(tool.id);
                  return (
                    <div
                      key={tool.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                        isSelected ? "border-primary bg-primary/5" : "hover:border-primary/50"
                      }`}
                      onClick={() => toggleTool(tool.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold flex-shrink-0"
                          style={{ backgroundColor: tool.bg_color || "#6B7280" }}
                        >
                          {tool.name.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-sm font-medium truncate">{tool.name}</h4>
                            {isSelected && (
                              <Check className="h-4 w-4 text-primary" />
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {tool.description}
                          </p>
                          <Badge variant="outline" className="text-xs mt-2">
                            {tool.category}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  );
}

export function AgentToolsPanel({ 
  agentId, 
  selectedTools, 
  onToolsChange,
  onToolsWithConfigChange 
}: AgentToolsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Workflow className="h-5 w-5" />
          Agent Tools
        </CardTitle>
        <CardDescription>
          Select tools for your agent. You can configure tool parameters after creating the agent.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <SimpleToolSelector
          selectedTools={selectedTools}
          onToolsChange={onToolsChange}
        />
      </CardContent>
    </Card>
  );
}
