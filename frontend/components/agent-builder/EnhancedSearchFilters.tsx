'use client';

import React, { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { 
  Search, 
  Filter, 
  SortAsc, 
  X,
  Calendar,
  Tag,
  Activity,
  Users,
  MessageSquare
} from 'lucide-react';

interface FilterState {
  status: 'all' | 'active' | 'inactive';
  sortBy: 'name' | 'created_at' | 'updated_at' | 'execution_count';
  tags: string[];
  dateRange: 'all' | 'week' | 'month' | 'quarter';
}

interface EnhancedSearchFiltersProps {
  type: 'agentflow' | 'chatflow';
  searchQuery: string;
  onSearchChange: (query: string) => void;
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
  availableTags: string[];
}

export function EnhancedSearchFilters({
  type,
  searchQuery,
  onSearchChange,
  filters,
  onFiltersChange,
  availableTags
}: EnhancedSearchFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const isAgentflow = type === 'agentflow';

  const activeFiltersCount = [
    filters.status !== 'all',
    filters.tags.length > 0,
    filters.dateRange !== 'all'
  ].filter(Boolean).length;

  const clearAllFilters = () => {
    onFiltersChange({
      status: 'all',
      sortBy: 'updated_at',
      tags: [],
      dateRange: 'all'
    });
  };

  const removeTag = (tagToRemove: string) => {
    onFiltersChange({
      ...filters,
      tags: filters.tags.filter(tag => tag !== tagToRemove)
    });
  };

  return (
    <div className="space-y-4">
      {/* Main Search Bar */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={`Search ${isAgentflow ? 'Agentflow' : 'Chatflow'} by name, description, tags...`}
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 h-11"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-2 top-1/2 transform -translate-y-1/2 h-7 w-7"
              onClick={() => onSearchChange('')}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Quick Filters */}
        <div className="flex gap-2">
          <Select 
            value={filters.status} 
            onValueChange={(value) => onFiltersChange({ ...filters, status: value as any })}
          >
            <SelectTrigger className="w-[140px] h-11">
              <Activity className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>

          <Select 
            value={filters.sortBy} 
            onValueChange={(value) => onFiltersChange({ ...filters, sortBy: value as any })}
          >
            <SelectTrigger className="w-[160px] h-11">
              <SortAsc className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="updated_at">Recently Updated</SelectItem>
              <SelectItem value="created_at">Date Created</SelectItem>
              <SelectItem value="name">Name</SelectItem>
              <SelectItem value="execution_count">
                {isAgentflow ? 'Execution Count' : 'Conversation Count'}
              </SelectItem>
            </SelectContent>
          </Select>

          <Popover>
            <PopoverTrigger className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-11 px-4 py-2">
              <Filter className="h-4 w-4 mr-2" />
              Advanced Filters
              {activeFiltersCount > 0 && (
                <Badge variant="secondary" className="ml-2 h-5 w-5 p-0 text-xs">
                  {activeFiltersCount}
                </Badge>
              )}
            </PopoverTrigger>
            <PopoverContent className="w-80" align="end">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold">Advanced Filters</h4>
                  {activeFiltersCount > 0 && (
                    <Button variant="ghost" size="sm" onClick={clearAllFilters}>
                      Clear All
                    </Button>
                  )}
                </div>

                {/* Date Range */}
                <div>
                  <label className="text-sm font-medium mb-2 block">Created Date</label>
                  <Select 
                    value={filters.dateRange} 
                    onValueChange={(value) => onFiltersChange({ ...filters, dateRange: value as any })}
                  >
                    <SelectTrigger>
                      <Calendar className="h-4 w-4 mr-2" />
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Time</SelectItem>
                      <SelectItem value="week">Last Week</SelectItem>
                      <SelectItem value="month">Last Month</SelectItem>
                      <SelectItem value="quarter">Last 3 Months</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Tag Filter */}
                {availableTags.length > 0 && (
                  <div>
                    <label className="text-sm font-medium mb-2 block">Tags</label>
                    <div className="space-y-2">
                      <div className="flex flex-wrap gap-1 max-h-20 overflow-y-auto">
                        {availableTags.map((tag) => (
                          <Badge
                            key={tag}
                            variant={filters.tags.includes(tag) ? "default" : "outline"}
                            className="cursor-pointer text-xs"
                            onClick={() => {
                              const newTags = filters.tags.includes(tag)
                                ? filters.tags.filter(t => t !== tag)
                                : [...filters.tags, tag];
                              onFiltersChange({ ...filters, tags: newTags });
                            }}
                          >
                            <Tag className="h-3 w-3 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      {/* Active Filters Display */}
      {(searchQuery || activeFiltersCount > 0) && (
        <Card className="p-3 bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
              Active Filters:
            </span>
            
            {searchQuery && (
              <Badge variant="secondary" className="gap-1">
                Search: "{searchQuery}"
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => onSearchChange('')}
                />
              </Badge>
            )}
            
            {filters.status !== 'all' && (
              <Badge variant="secondary" className="gap-1">
                Status: {filters.status === 'active' ? 'Active' : 'Inactive'}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => onFiltersChange({ ...filters, status: 'all' })}
                />
              </Badge>
            )}
            
            {filters.dateRange !== 'all' && (
              <Badge variant="secondary" className="gap-1">
                Period: {
                  filters.dateRange === 'week' ? 'Last Week' :
                  filters.dateRange === 'month' ? 'Last Month' : 'Last 3 Months'
                }
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => onFiltersChange({ ...filters, dateRange: 'all' })}
                />
              </Badge>
            )}
            
            {filters.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="gap-1">
                Tag: {tag}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => removeTag(tag)}
                />
              </Badge>
            ))}
            
            {(searchQuery || activeFiltersCount > 0) && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => {
                  onSearchChange('');
                  clearAllFilters();
                }}
                className="ml-auto"
              >
                Clear All
              </Button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}