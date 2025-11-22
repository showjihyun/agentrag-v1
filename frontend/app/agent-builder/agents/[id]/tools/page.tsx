"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Save, Loader2, ChevronDown, ChevronRight, Plus, X, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";

interface SelectedTool {
  tool_id: string;
  tool: any;
  configuration: Record<string, any>;
  order: number;
}

export default function AgentToolsPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<any>(null);
  const [selectedTools, setSelectedTools] = useState<SelectedTool[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (agentId) {
      fetchAgent();
    }
  }, [agentId]);

  const fetchAgent = async () => {
    try {
      const response = await fetch(`/api/agent-builder/agents/${agentId}`);
      if (!response.ok) throw new Error("Failed to fetch agent");
      
      const data = await response.json();
      setAgent(data);

      console.log('Agent data:', data);
      console.log('Agent tools:', data.tools);

      // Convert agent tools to SelectedTool format
      if (data.tools && Array.isArray(data.tools)) {
        const toolsWithConfig = data.tools.map((tool: any, index: number) => ({
          tool_id: tool.tool_id,
          tool: { 
            id: tool.tool_id, 
            name: tool.tool_id.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
          },
          configuration: tool.configuration || {},
          order: tool.order !== undefined ? tool.order : index,
        }));
        console.log('Converted tools:', toolsWithConfig);
        setSelectedTools(toolsWithConfig);
      }
    } catch (error) {
      console.error("Failed to fetch agent:", error);
      toast({
        title: "Error",
        description: "Failed to load agent data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Save tools configuration
      const response = await fetch(`/api/agent-builder/agents/${agentId}/tools`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tools: selectedTools.map((t) => ({
            tool_id: t.tool_id,
            configuration: t.configuration,
            order: t.order,
          })),
        }),
      });

      if (!response.ok) throw new Error("Failed to save tools");

      toast({
        title: "Success",
        description: "Tools configuration saved successfully",
      });

      router.push(`/agent-builder/agents/${agentId}`);
    } catch (error) {
      console.error("Failed to save tools:", error);
      toast({
        title: "Error",
        description: "Failed to save tools configuration",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/agent-builder/agents/${agentId}`)}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Configure Tools</h1>
            <p className="text-muted-foreground mt-1">
              {agent?.name} - Select and configure tools for your agent
            </p>
          </div>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Tools
            </>
          )}
        </Button>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Add/Remove Tools */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Manage Tools</h3>
          <ToolManagementPanel
            selectedTools={selectedTools}
            onToolsChange={setSelectedTools}
          />
        </div>

        {/* Right: Selected Tools Configuration */}
        <div className="bg-card border rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">Tool Configuration</h3>
          {selectedTools.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <p>No tools selected</p>
              <p className="text-sm mt-2">Add tools from the left panel to configure them</p>
            </div>
          ) : (
            <div className="space-y-3">
              {selectedTools.map((tool, index) => (
                <ToolConfigCard
                  key={tool.tool_id}
                  tool={tool}
                  index={index}
                  onUpdate={(updatedTool) => {
                    const updated = [...selectedTools];
                    updated[index] = updatedTool;
                    setSelectedTools(updated);
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Tool Management Panel Component
function ToolManagementPanel({
  selectedTools,
  onToolsChange,
}: {
  selectedTools: SelectedTool[];
  onToolsChange: (tools: SelectedTool[]) => void;
}) {
  const [availableTools, setAvailableTools] = useState<any[]>([]);
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
      setAvailableTools(data.tools || []);
      setCategories(["all", ...(data.categories || [])]);
    } catch (error) {
      console.error("Failed to fetch tools:", error);
    } finally {
      setLoading(false);
    }
  };

  const filteredTools = availableTools.filter((tool) => {
    const matchesSearch =
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === "all" || tool.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const addTool = (tool: any) => {
    if (selectedTools.some((t) => t.tool_id === tool.id)) return;

    const newTool: SelectedTool = {
      tool_id: tool.id,
      tool: tool,
      configuration: {},
      order: selectedTools.length,
    };
    onToolsChange([...selectedTools, newTool]);
  };

  const removeTool = (toolId: string) => {
    const updated = selectedTools.filter((t) => t.tool_id !== toolId);
    // Reorder
    updated.forEach((tool, i) => {
      tool.order = i;
    });
    onToolsChange(updated);
  };

  return (
    <div className="space-y-4">
      {/* Selected Tools */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium">Selected Tools ({selectedTools.length})</h4>
        {selectedTools.length === 0 ? (
          <div className="border-2 border-dashed rounded-lg p-6 text-center text-sm text-muted-foreground">
            No tools added yet
          </div>
        ) : (
          <div className="space-y-2">
            {selectedTools.map((tool) => (
              <div
                key={tool.tool_id}
                className="flex items-center justify-between p-3 border rounded-lg bg-card"
              >
                <div className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-semibold"
                    style={{ backgroundColor: tool.tool?.bg_color || "#6B7280" }}
                  >
                    {tool.tool?.name?.charAt(0) || tool.tool_id.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{tool.tool?.name || tool.tool_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {Object.keys(tool.configuration).length} params
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeTool(tool.tool_id)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

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
            <div className="space-y-2">
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                </div>
              ) : filteredTools.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No tools found
                </div>
              ) : (
                filteredTools.map((tool) => {
                  const isSelected = selectedTools.some((t) => t.tool_id === tool.id);
                  return (
                    <div
                      key={tool.id}
                      className={`flex items-center justify-between p-3 border rounded-lg transition-colors ${
                        isSelected
                          ? "border-primary bg-primary/5"
                          : "hover:border-primary/50 cursor-pointer"
                      }`}
                      onClick={() => !isSelected && addTool(tool)}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm font-semibold"
                          style={{ backgroundColor: tool.bg_color || "#6B7280" }}
                        >
                          {tool.name.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{tool.name}</p>
                          <p className="text-xs text-muted-foreground truncate">
                            {tool.description}
                          </p>
                        </div>
                      </div>
                      {isSelected ? (
                        <Badge variant="default" className="text-xs">
                          Added
                        </Badge>
                      ) : (
                        <Button variant="ghost" size="icon" onClick={(e) => {
                          e.stopPropagation();
                          addTool(tool);
                        }}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      )}
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

// Tool Configuration Card Component
function ToolConfigCard({
  tool,
  index,
  onUpdate,
}: {
  tool: SelectedTool;
  index: number;
  onUpdate: (tool: SelectedTool) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [toolDetails, setToolDetails] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (expanded && !toolDetails) {
      fetchToolDetails();
    }
  }, [expanded]);

  const fetchToolDetails = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/agent-builder/tools/${tool.tool_id}`);
      if (response.ok) {
        const data = await response.json();
        setToolDetails(data);
      } else if (response.status === 404) {
        // Tool not found in catalog, create a basic schema
        console.warn(`Tool ${tool.tool_id} not found in catalog, using basic schema`);
        setToolDetails({
          id: tool.tool_id,
          name: tool.tool_id.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
          description: `Configuration for ${tool.tool_id}`,
          params: {
            url: {
              type: "string",
              description: "Request URL",
              required: true,
            },
            method: {
              type: "string",
              description: "HTTP method",
              enum: ["GET", "POST", "PUT", "PATCH", "DELETE"],
              default: "GET",
            },
            headers: {
              type: "object",
              description: "Request headers",
              default: {},
            },
            body: {
              type: "object",
              description: "Request body",
              default: {},
            },
          },
        });
      }
    } catch (error) {
      console.error('Failed to fetch tool details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfigChange = (key: string, value: any) => {
    onUpdate({
      ...tool,
      configuration: {
        ...tool.configuration,
        [key]: value,
      },
    });
  };

  return (
    <div className="border rounded-lg">
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-accent/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-semibold"
            style={{ backgroundColor: tool.tool?.bg_color || "#6B7280" }}
          >
            {tool.tool?.name?.charAt(0) || tool.tool_id.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-medium">{tool.tool?.name || tool.tool_id}</p>
            <p className="text-xs text-muted-foreground">
              {Object.keys(tool.configuration).length} parameters configured
            </p>
          </div>
        </div>
        <Button variant="ghost" size="icon" onClick={(e) => e.stopPropagation()}>
          {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        </Button>
      </div>

      {/* Configuration Panel */}
      {expanded && (
        <div className="border-t p-4 space-y-4">
          {loading ? (
            <div className="text-center py-4">
              <Loader2 className="h-6 w-6 animate-spin mx-auto text-muted-foreground" />
              <p className="text-xs text-muted-foreground mt-2">Loading tool configuration...</p>
            </div>
          ) : toolDetails?.params ? (
            <>
              {!toolDetails.id && (
                <div className="p-3 bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-lg mb-4">
                  <p className="text-xs text-yellow-900 dark:text-yellow-100">
                    ℹ️ Using basic configuration. Restart backend to load full tool schema.
                  </p>
                </div>
              )}
              {Object.entries(toolDetails.params).map(([key, param]: [string, any]) => (
                <div key={key} className="space-y-2">
                  <Label htmlFor={`${tool.tool_id}-${key}`}>
                    {key}
                    {param.required && <span className="text-destructive ml-1">*</span>}
                  </Label>
                  {param.description && (
                    <p className="text-xs text-muted-foreground">{param.description}</p>
                  )}
                  {renderInput(key, param, tool.configuration[key], handleConfigChange)}
                </div>
              ))}
            </>
          ) : (
            <div className="text-center py-8">
              <p className="text-sm text-muted-foreground mb-2">No configuration available</p>
              <p className="text-xs text-muted-foreground">
                This tool may not have configurable parameters
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Helper function to render input based on parameter type
function renderInput(
  key: string,
  param: any,
  value: any,
  onChange: (key: string, value: any) => void
) {
  switch (param.type) {
    case "string":
      if (param.enum) {
        return (
          <Select value={value || ""} onValueChange={(val) => onChange(key, val)}>
            <SelectTrigger>
              <SelectValue placeholder="Select an option" />
            </SelectTrigger>
            <SelectContent>
              {param.enum.map((option: string) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );
      }
      return (
        <Input
          id={key}
          value={value || ""}
          onChange={(e) => onChange(key, e.target.value)}
          placeholder={param.default || ""}
        />
      );

    case "number":
      return (
        <Input
          id={key}
          type="number"
          value={value ?? ""}
          onChange={(e) => onChange(key, e.target.value ? Number(e.target.value) : undefined)}
          min={param.min}
          max={param.max}
          placeholder={param.default?.toString() || ""}
        />
      );

    case "object":
    case "array":
      return (
        <Textarea
          id={key}
          value={typeof value === "object" ? JSON.stringify(value, null, 2) : value || ""}
          onChange={(e) => {
            try {
              const parsed = JSON.parse(e.target.value);
              onChange(key, parsed);
            } catch {
              // Invalid JSON, ignore
            }
          }}
          rows={4}
          className="font-mono text-sm"
          placeholder={param.type === "array" ? '["item1", "item2"]' : '{"key": "value"}'}
        />
      );

    default:
      return (
        <Input
          id={key}
          value={value || ""}
          onChange={(e) => onChange(key, e.target.value)}
        />
      );
  }
}
