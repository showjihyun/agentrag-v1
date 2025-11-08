"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Plus,
  Search,
  Edit,
  Trash2,
  Copy,
  ExternalLink,
  Star,
} from "lucide-react";
import { CustomToolBuilder } from "./CustomToolBuilder";

interface CustomTool {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  usage_count: number;
  is_public: boolean;
  is_marketplace: boolean;
  is_owner: boolean;
  created_at: string;
}

export function CustomToolManager() {
  const [tools, setTools] = useState<CustomTool[]>([]);
  const [filteredTools, setFilteredTools] = useState<CustomTool[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [showBuilder, setShowBuilder] = useState(false);
  const [editingTool, setEditingTool] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTools();
  }, []);

  useEffect(() => {
    filterTools();
  }, [searchQuery, selectedCategory, tools]);

  const loadTools = async () => {
    try {
      const response = await fetch("/api/agent-builder/custom-tools");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setTools(data.tools || []);
    } catch (error) {
      console.error("Failed to load tools:", error);
      // Show user-friendly error
      alert("Failed to load custom tools. Please make sure the backend server is running.");
    } finally {
      setLoading(false);
    }
  };

  const filterTools = () => {
    let filtered = tools;

    if (searchQuery) {
      filtered = filtered.filter(
        (tool) =>
          tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          tool.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (selectedCategory !== "all") {
      filtered = filtered.filter((tool) => tool.category === selectedCategory);
    }

    setFilteredTools(filtered);
  };

  const handleSaveTool = async (toolData: any) => {
    try {
      const url = editingTool
        ? `/api/agent-builder/custom-tools/${editingTool.id}`
        : "/api/agent-builder/custom-tools";

      const response = await fetch(url, {
        method: editingTool ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(toolData),
      });

      if (response.ok) {
        await loadTools();
        setShowBuilder(false);
        setEditingTool(null);
      }
    } catch (error) {
      console.error("Failed to save tool:", error);
    }
  };

  const handleDeleteTool = async (toolId: string) => {
    if (!confirm("Are you sure you want to delete this tool?")) return;

    try {
      const response = await fetch(
        `/api/agent-builder/custom-tools/${toolId}`,
        {
          method: "DELETE",
        }
      );

      if (response.ok) {
        await loadTools();
      }
    } catch (error) {
      console.error("Failed to delete tool:", error);
    }
  };

  const handleCloneTool = async (toolId: string) => {
    try {
      const response = await fetch(
        `/api/agent-builder/custom-tools/${toolId}/clone`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        await loadTools();
      }
    } catch (error) {
      console.error("Failed to clone tool:", error);
    }
  };

  const handleEditTool = async (toolId: string) => {
    try {
      const response = await fetch(
        `/api/agent-builder/custom-tools/${toolId}`
      );
      const tool = await response.json();
      setEditingTool(tool);
      setShowBuilder(true);
    } catch (error) {
      console.error("Failed to load tool:", error);
    }
  };

  const categories = [
    { value: "all", label: "All Categories" },
    { value: "custom", label: "Custom" },
    { value: "api", label: "API" },
    { value: "data", label: "Data" },
    { value: "communication", label: "Communication" },
    { value: "productivity", label: "Productivity" },
  ];

  if (showBuilder) {
    return (
      <div className="p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-bold">
            {editingTool ? "Edit Tool" : "Create Custom Tool"}
          </h2>
        </div>
        <CustomToolBuilder
          onSave={handleSaveTool}
          onCancel={() => {
            setShowBuilder(false);
            setEditingTool(null);
          }}
          initialData={editingTool}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Custom Tools</h2>
          <p className="text-muted-foreground">
            Create and manage your custom tools
          </p>
        </div>
        <Button onClick={() => setShowBuilder(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Tool
        </Button>
      </div>

      <div className="flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tools..."
            className="pl-10"
          />
        </div>

        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="px-4 py-2 border rounded-md"
        >
          {categories.map((cat) => (
            <option key={cat.value} value={cat.value}>
              {cat.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading tools...</p>
        </div>
      ) : filteredTools.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground mb-4">
              {searchQuery || selectedCategory !== "all"
                ? "No tools found matching your criteria"
                : "No custom tools yet"}
            </p>
            {!searchQuery && selectedCategory === "all" && (
              <Button onClick={() => setShowBuilder(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Create Your First Tool
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTools.map((tool) => (
            <Card key={tool.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">{tool.icon}</span>
                    <div>
                      <CardTitle className="text-lg">{tool.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">
                        {tool.category}
                      </p>
                    </div>
                  </div>
                  {tool.is_marketplace && (
                    <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {tool.description || "No description"}
                </p>

                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{tool.usage_count} uses</span>
                  <span>
                    {new Date(tool.created_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="flex gap-2">
                  {tool.is_owner ? (
                    <>
                      <Button
                        onClick={() => handleEditTool(tool.id)}
                        size="sm"
                        variant="outline"
                        className="flex-1"
                      >
                        <Edit className="h-3 w-3 mr-1" />
                        Edit
                      </Button>
                      <Button
                        onClick={() => handleDeleteTool(tool.id)}
                        size="sm"
                        variant="outline"
                        className="text-destructive"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </>
                  ) : (
                    <Button
                      onClick={() => handleCloneTool(tool.id)}
                      size="sm"
                      variant="outline"
                      className="flex-1"
                    >
                      <Copy className="h-3 w-3 mr-1" />
                      Clone
                    </Button>
                  )}
                  <Button size="sm" variant="outline">
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
