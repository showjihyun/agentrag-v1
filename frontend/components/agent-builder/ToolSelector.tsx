"use client";

import React, { useState, useEffect } from "react";
import { Search, Plus, Settings, X, ExternalLink } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ToolConfigPanel } from "./ToolConfigPanel";

interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  params: Record<string, any>;
  outputs: Record<string, any>;
  icon?: string;
  bg_color?: string;
  docs_link?: string;
}

interface SelectedTool {
  tool_id: string;
  tool: Tool;
  configuration: Record<string, any>;
  order: number;
}

interface ToolSelectorProps {
  agentId?: string;
  selectedTools: SelectedTool[];
  onToolsChange: (tools: SelectedTool[]) => void;
}

export function ToolSelector({
  agentId,
  selectedTools,
  onToolsChange,
}: ToolSelectorProps) {
  const [tools, setTools] = useState<Tool[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [configuringTool, setConfiguringTool] = useState<Tool | null>(null);
  const [editingToolIndex, setEditingToolIndex] = useState<number | null>(null);

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      const response = await fetch("/api/agent-builder/tools");
      const data = await response.json();
      console.log('Fetched tools from API:', data.tools?.length, 'tools');
      console.log('Tool IDs:', data.tools?.map((t: any) => t.id));
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

  const handleAddTool = (tool: Tool) => {
    console.log('handleAddTool called for tool:', tool.name);
    // Check if already added
    if (selectedTools.some((t) => t.tool_id === tool.id)) {
      // Open config for existing tool
      console.log('Tool already added, opening config');
      const index = selectedTools.findIndex((t) => t.tool_id === tool.id);
      setEditingToolIndex(index);
      setConfiguringTool(tool);
      return;
    }

    // Open config panel for new tool
    console.log('Adding new tool, opening config panel');
    setConfiguringTool(tool);
    setEditingToolIndex(null);
  };

  const handleSaveConfig = (config: Record<string, any>) => {
    if (!configuringTool) return;

    if (editingToolIndex !== null) {
      // Update existing tool
      const updated = [...selectedTools];
      updated[editingToolIndex] = {
        ...updated[editingToolIndex],
        configuration: config,
      };
      onToolsChange(updated);
    } else {
      // Add new tool
      const newTool: SelectedTool = {
        tool_id: configuringTool.id,
        tool: configuringTool,
        configuration: config,
        order: selectedTools.length,
      };
      onToolsChange([...selectedTools, newTool]);
    }

    setConfiguringTool(null);
    setEditingToolIndex(null);
  };

  const handleRemoveTool = (index: number) => {
    const updated = selectedTools.filter((_, i) => i !== index);
    // Reorder
    updated.forEach((tool, i) => {
      tool.order = i;
    });
    onToolsChange(updated);
  };

  const handleEditTool = (index: number) => {
    console.log('handleEditTool called for index:', index);
    const selectedTool = selectedTools[index];
    console.log('Selected tool:', selectedTool);
    console.log('Available tools:', tools.length);
    console.log('Looking for tool_id:', selectedTool.tool_id);
    let tool = tools.find((t) => t.id === selectedTool.tool_id);
    
    if (!tool) {
      console.warn('Tool not found in API, using placeholder:', selectedTool.tool_id);
      // Create a placeholder tool if not found (backend might not be restarted)
      tool = {
        id: selectedTool.tool_id,
        name: selectedTool.tool_id.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        description: `Configuration for ${selectedTool.tool_id}`,
        category: 'custom',
        params: {},
        outputs: {},
      };
      console.log('Created placeholder tool:', tool);
    }
    
    console.log('Opening config panel for tool:', tool.name);
    setConfiguringTool(tool);
    setEditingToolIndex(index);
  };

  const handleReorder = (index: number, direction: "up" | "down") => {
    const newIndex = direction === "up" ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= selectedTools.length) return;

    const updated = [...selectedTools];
    [updated[index], updated[newIndex]] = [updated[newIndex], updated[index]];
    updated.forEach((tool, i) => {
      tool.order = i;
    });
    onToolsChange(updated);
  };

  return (
    <div className="space-y-6">
      {/* Selected Tools */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">Selected Tools</h3>
          <Badge variant="secondary">{selectedTools.length} tools</Badge>
        </div>

        {selectedTools.length === 0 ? (
          <div className="border-2 border-dashed rounded-lg p-8 text-center">
            <p className="text-sm text-muted-foreground">
              No tools selected. Add tools from the catalog below.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {selectedTools.map((selectedTool, index) => (
              <div
                key={selectedTool.tool_id}
                className="flex items-center gap-3 p-3 border rounded-lg bg-card hover:bg-accent/50 transition-colors"
              >
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold"
                  style={{ backgroundColor: selectedTool.tool.bg_color || "#6B7280" }}
                >
                  {selectedTool.tool.name.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium truncate">
                      {selectedTool.tool.name}
                    </p>
                    <Badge variant="outline" className="text-xs">
                      {selectedTool.tool.category}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {Object.keys(selectedTool.configuration).length} parameters configured
                  </p>
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleReorder(index, "up");
                    }}
                    disabled={index === 0}
                  >
                    ↑
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleReorder(index, "down");
                    }}
                    disabled={index === selectedTools.length - 1}
                  >
                    ↓
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditTool(index);
                    }}
                  >
                    <Settings className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveTool(index);
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tool Catalog */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium">Tool Catalog</h3>

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
                    const isSelected = selectedTools.some((t) => t.tool_id === tool.id);
                    return (
                      <div
                        key={tool.id}
                        className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                          isSelected ? "border-primary bg-primary/5" : "hover:border-primary/50"
                        }`}
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleAddTool(tool);
                        }}
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
                                <Badge variant="default" className="text-xs">
                                  Added
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground line-clamp-2">
                              {tool.description}
                            </p>
                            <div className="flex items-center gap-2 mt-2">
                              <Badge variant="outline" className="text-xs">
                                {tool.category}
                              </Badge>
                              {tool.docs_link && (
                                <a
                                  href={tool.docs_link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  onClick={(e) => e.stopPropagation()}
                                  className="text-xs text-primary hover:underline flex items-center gap-1"
                                >
                                  Docs
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              )}
                            </div>
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

      {/* Config Panel */}
      {configuringTool && (
        <>
          {console.log('Rendering ToolConfigPanel for:', configuringTool.name)}
          <ToolConfigPanel
            tool={configuringTool}
            initialConfig={
              editingToolIndex !== null
                ? selectedTools[editingToolIndex].configuration
                : {}
            }
            onSave={handleSaveConfig}
            onClose={() => {
              console.log('Closing ToolConfigPanel');
              setConfiguringTool(null);
              setEditingToolIndex(null);
            }}
          />
        </>
      )}
    </div>
  );
}
