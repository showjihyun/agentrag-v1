'use client';

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { agentBuilderAPI, type Tool } from '@/lib/api/agent-builder';
import { Search } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ToolSelectorProps {
  selectedTools: string[];
  onSelectionChange: (toolIds: string[]) => void;
}

export function ToolSelector({ selectedTools, onSelectionChange }: ToolSelectorProps) {
  const [searchQuery, setSearchQuery] = React.useState('');
  const [categoryFilter, setCategoryFilter] = React.useState('all');
  const [showCustomTools, setShowCustomTools] = React.useState(false);

  const { data: tools, isLoading } = useQuery({
    queryKey: ['tools'],
    queryFn: () => agentBuilderAPI.getTools(),
  });

  const { data: customToolsData, isLoading: customToolsLoading } = useQuery({
    queryKey: ['custom-tools'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/agent-builder/custom-tools');
        if (!response.ok) {
          console.warn('Custom tools API not available:', response.status);
          return { tools: [] };
        }
        return response.json();
      } catch (error) {
        console.warn('Failed to load custom tools:', error);
        return { tools: [] };
      }
    },
    retry: false,
    staleTime: 30000,
  });

  const allTools = React.useMemo(() => {
    const builtInTools = tools || [];
    const customTools = customToolsData?.tools || [];
    
    // Combine built-in and custom tools
    return [...builtInTools, ...customTools.map((ct: any) => ({
      id: ct.id,
      name: ct.name,
      description: ct.description,
      category: ct.category,
      icon: ct.icon,
      requires_auth: ct.requires_auth,
      is_custom: true,
    }))];
  }, [tools, customToolsData]);

  const filteredTools = React.useMemo(() => {
    if (!allTools || !Array.isArray(allTools)) return [];
    
    let filtered = allTools;
    
    // Filter by custom/built-in
    if (showCustomTools) {
      filtered = filtered.filter((tool: any) => tool.is_custom);
    }
    
    // Filter by search and category
    return filtered.filter((tool) => {
      const matchesSearch = tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tool.description?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesCategory = categoryFilter === 'all' || tool.category === categoryFilter;
      return matchesSearch && matchesCategory;
    });
  }, [allTools, searchQuery, categoryFilter, showCustomTools]);

  const categories = React.useMemo(() => {
    if (!allTools || !Array.isArray(allTools)) return [];
    return Array.from(new Set(allTools.map((t) => t.category)));
  }, [allTools]);

  const toggleTool = (toolId: string) => {
    if (selectedTools.includes(toolId)) {
      onSelectionChange(selectedTools.filter((id) => id !== toolId));
    } else {
      onSelectionChange([...selectedTools, toolId]);
    }
  };

  if (isLoading || customToolsLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-3/4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-12 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Selected Tools Summary */}
      {selectedTools.length > 0 && (
        <div className="flex items-center justify-between p-3 bg-primary/10 border border-primary/20 rounded-lg">
          <div className="flex items-center gap-2">
            <Badge variant="default" className="font-semibold">
              {selectedTools.length}
            </Badge>
            <span className="text-sm font-medium">
              {selectedTools.length === 1 ? 'tool selected' : 'tools selected'}
            </span>
          </div>
          <button
            onClick={() => onSelectionChange([])}
            className="text-xs text-muted-foreground hover:text-foreground underline"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Search and Filter */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map((category) => (
              <SelectItem key={category} value={category}>
                {category}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <button
          onClick={() => setShowCustomTools(!showCustomTools)}
          className={cn(
            "px-4 py-2 rounded-md text-sm font-medium transition-colors",
            showCustomTools
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
          )}
        >
          {showCustomTools ? "Show All" : "Custom Only"}
        </button>
      </div>

      {/* Tool Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredTools.map((tool: Tool) => {
          const isSelected = selectedTools.includes(tool.id);
          
          return (
            <Card
              key={tool.id}
              className={cn(
                "cursor-pointer transition-all hover:shadow-md",
                isSelected 
                  ? "ring-2 ring-primary bg-primary/5 border-primary" 
                  : "hover:border-gray-400 dark:hover:border-gray-500"
              )}
              onClick={() => toggleTool(tool.id)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-sm font-semibold">{tool.name}</CardTitle>
                    {isSelected && (
                      <Badge variant="default" className="text-xs px-1.5 py-0">
                        ✓
                      </Badge>
                    )}
                  </div>
                  <Switch
                    checked={isSelected}
                    onCheckedChange={() => toggleTool(tool.id)}
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  {tool.description || 'No description'}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {tool.category}
                  </Badge>
                  {(tool as any).is_custom && (
                    <Badge variant="default" className="text-xs">
                      Custom
                    </Badge>
                  )}
                  {tool.requires_auth && (
                    <Badge variant="secondary" className="text-xs">
                      Auth Required
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredTools.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No tools found matching your criteria
        </div>
      )}
    </div>
  );
}
