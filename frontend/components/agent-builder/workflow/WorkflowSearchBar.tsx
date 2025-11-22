'use client';

import { useState, useMemo } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Search, Filter, X, Save, Bookmark } from 'lucide-react';
import { Node } from 'reactflow';

interface WorkflowSearchBarProps {
  nodes: Node[];
  onFilteredNodesChange: (nodes: Node[]) => void;
  onSearchChange?: (query: string) => void;
}

interface FilterState {
  nodeTypes: Set<string>;
  statuses: Set<string>;
  tags: Set<string>;
}

export function WorkflowSearchBar({
  nodes,
  onFilteredNodesChange,
  onSearchChange,
}: WorkflowSearchBarProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterState>({
    nodeTypes: new Set(),
    statuses: new Set(),
    tags: new Set(),
  });
  const [savedSearches, setSavedSearches] = useState<Array<{ name: string; query: string; filters: FilterState }>>([]);

  // Extract unique values for filters
  const availableNodeTypes = useMemo(() => {
    const types = new Set<string>();
    nodes.forEach((node) => {
      if (node.type) types.add(node.type);
    });
    return Array.from(types);
  }, [nodes]);

  const availableStatuses = useMemo(() => {
    const statuses = new Set<string>();
    nodes.forEach((node) => {
      if (node.data.status) statuses.add(node.data.status);
    });
    return Array.from(statuses);
  }, [nodes]);

  const availableTags = useMemo(() => {
    const tags = new Set<string>();
    nodes.forEach((node) => {
      if (node.data.tags && Array.isArray(node.data.tags)) {
        node.data.tags.forEach((tag: string) => tags.add(tag));
      }
    });
    return Array.from(tags);
  }, [nodes]);

  // Apply filters
  const filteredNodes = useMemo(() => {
    let result = nodes;

    // Search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (node) =>
          node.data.label?.toLowerCase().includes(query) ||
          node.data.description?.toLowerCase().includes(query) ||
          node.id.toLowerCase().includes(query)
      );
    }

    // Node type filter
    if (filters.nodeTypes.size > 0) {
      result = result.filter((node) => node.type && filters.nodeTypes.has(node.type));
    }

    // Status filter
    if (filters.statuses.size > 0) {
      result = result.filter((node) => node.data.status && filters.statuses.has(node.data.status));
    }

    // Tags filter
    if (filters.tags.size > 0) {
      result = result.filter((node) => {
        if (!node.data.tags || !Array.isArray(node.data.tags)) return false;
        return node.data.tags.some((tag: string) => filters.tags.has(tag));
      });
    }

    return result;
  }, [nodes, searchQuery, filters]);

  // Notify parent of filtered nodes
  useMemo(() => {
    onFilteredNodesChange(filteredNodes);
  }, [filteredNodes, onFilteredNodesChange]);

  const handleSearchChange = (value: string) => {
    setSearchQuery(value);
    onSearchChange?.(value);
  };

  const toggleFilter = (category: keyof FilterState, value: string) => {
    setFilters((prev) => {
      const newSet = new Set(prev[category]);
      if (newSet.has(value)) {
        newSet.delete(value);
      } else {
        newSet.add(value);
      }
      return { ...prev, [category]: newSet };
    });
  };

  const clearFilters = () => {
    setSearchQuery('');
    setFilters({
      nodeTypes: new Set(),
      statuses: new Set(),
      tags: new Set(),
    });
  };

  const saveSearch = () => {
    const name = prompt('Enter a name for this search:');
    if (name) {
      setSavedSearches((prev) => [
        ...prev,
        {
          name,
          query: searchQuery,
          filters: {
            nodeTypes: new Set(filters.nodeTypes),
            statuses: new Set(filters.statuses),
            tags: new Set(filters.tags),
          },
        },
      ]);
    }
  };

  const loadSearch = (search: { name: string; query: string; filters: FilterState }) => {
    setSearchQuery(search.query);
    setFilters(search.filters);
  };

  const activeFilterCount =
    filters.nodeTypes.size + filters.statuses.size + filters.tags.size;

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Search nodes by name, description, or ID..."
            className="pl-9 pr-9"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              onClick={() => handleSearchChange('')}
            >
              <X className="h-3 w-3" />
            </Button>
          )}
        </div>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" className="relative">
              <Filter className="h-4 w-4 mr-2" />
              Filters
              {activeFilterCount > 0 && (
                <Badge
                  variant="secondary"
                  className="ml-2 h-5 w-5 rounded-full p-0 flex items-center justify-center"
                >
                  {activeFilterCount}
                </Badge>
              )}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>Node Types</DropdownMenuLabel>
            {availableNodeTypes.map((type) => (
              <DropdownMenuItem
                key={type}
                onClick={() => toggleFilter('nodeTypes', type)}
                className="flex items-center gap-2"
              >
                <input
                  type="checkbox"
                  checked={filters.nodeTypes.has(type)}
                  onChange={() => {}}
                  className="h-4 w-4"
                />
                {type}
              </DropdownMenuItem>
            ))}

            {availableStatuses.length > 0 && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuLabel>Status</DropdownMenuLabel>
                {availableStatuses.map((status) => (
                  <DropdownMenuItem
                    key={status}
                    onClick={() => toggleFilter('statuses', status)}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="checkbox"
                      checked={filters.statuses.has(status)}
                      onChange={() => {}}
                      className="h-4 w-4"
                    />
                    {status}
                  </DropdownMenuItem>
                ))}
              </>
            )}

            {availableTags.length > 0 && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuLabel>Tags</DropdownMenuLabel>
                {availableTags.map((tag) => (
                  <DropdownMenuItem
                    key={tag}
                    onClick={() => toggleFilter('tags', tag)}
                    className="flex items-center gap-2"
                  >
                    <input
                      type="checkbox"
                      checked={filters.tags.has(tag)}
                      onChange={() => {}}
                      className="h-4 w-4"
                    />
                    {tag}
                  </DropdownMenuItem>
                ))}
              </>
            )}

            {activeFilterCount > 0 && (
              <>
                <DropdownMenuSeparator />
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start"
                  onClick={clearFilters}
                >
                  <X className="h-3 w-3 mr-2" />
                  Clear all filters
                </Button>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>

        {(searchQuery || activeFilterCount > 0) && (
          <Button variant="outline" size="icon" onClick={saveSearch}>
            <Save className="h-4 w-4" />
          </Button>
        )}

        {savedSearches.length > 0 && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon">
                <Bookmark className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Saved Searches</DropdownMenuLabel>
              {savedSearches.map((search, index) => (
                <DropdownMenuItem
                  key={index}
                  onClick={() => loadSearch(search)}
                >
                  {search.name}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>

      {/* Active filters display */}
      {(searchQuery || activeFilterCount > 0) && (
        <div className="flex flex-wrap gap-2 items-center">
          <span className="text-xs text-muted-foreground">
            {filteredNodes.length} of {nodes.length} nodes
          </span>
          {searchQuery && (
            <Badge variant="secondary" className="gap-1">
              Search: {searchQuery}
              <X
                className="h-3 w-3 cursor-pointer"
                onClick={() => handleSearchChange('')}
              />
            </Badge>
          )}
          {Array.from(filters.nodeTypes).map((type) => (
            <Badge key={type} variant="secondary" className="gap-1">
              Type: {type}
              <X
                className="h-3 w-3 cursor-pointer"
                onClick={() => toggleFilter('nodeTypes', type)}
              />
            </Badge>
          ))}
          {Array.from(filters.statuses).map((status) => (
            <Badge key={status} variant="secondary" className="gap-1">
              Status: {status}
              <X
                className="h-3 w-3 cursor-pointer"
                onClick={() => toggleFilter('statuses', status)}
              />
            </Badge>
          ))}
          {Array.from(filters.tags).map((tag) => (
            <Badge key={tag} variant="secondary" className="gap-1">
              Tag: {tag}
              <X
                className="h-3 w-3 cursor-pointer"
                onClick={() => toggleFilter('tags', tag)}
              />
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
