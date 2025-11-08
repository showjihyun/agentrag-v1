'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { Calendar } from '@/components/ui/calendar';
import { Badge } from '@/components/ui/badge';
import { Filter, X, Calendar as CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';

export interface FilterOptions {
  status?: string[];
  llmProvider?: string[];
  dateFrom?: Date;
  dateTo?: Date;
  tags?: string[];
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

interface AdvancedFilterProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  availableTags?: string[];
}

export function AdvancedFilter({
  filters,
  onFiltersChange,
  availableTags = [],
}: AdvancedFilterProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [localFilters, setLocalFilters] = React.useState<FilterOptions>(filters);

  const activeFilterCount = React.useMemo(() => {
    let count = 0;
    if (localFilters.status?.length) count++;
    if (localFilters.llmProvider?.length) count++;
    if (localFilters.dateFrom) count++;
    if (localFilters.dateTo) count++;
    if (localFilters.tags?.length) count++;
    return count;
  }, [localFilters]);

  const handleApply = () => {
    onFiltersChange(localFilters);
    setIsOpen(false);
  };

  const handleReset = () => {
    const resetFilters: FilterOptions = {};
    setLocalFilters(resetFilters);
    onFiltersChange(resetFilters);
  };

  const toggleStatus = (status: string) => {
    const current = localFilters.status || [];
    const updated = current.includes(status)
      ? current.filter((s) => s !== status)
      : [...current, status];
    setLocalFilters({ ...localFilters, status: updated });
  };

  const toggleProvider = (provider: string) => {
    const current = localFilters.llmProvider || [];
    const updated = current.includes(provider)
      ? current.filter((p) => p !== provider)
      : [...current, provider];
    setLocalFilters({ ...localFilters, llmProvider: updated });
  };

  const toggleTag = (tag: string) => {
    const current = localFilters.tags || [];
    const updated = current.includes(tag)
      ? current.filter((t) => t !== tag)
      : [...current, tag];
    setLocalFilters({ ...localFilters, tags: updated });
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" className="relative">
          <Filter className="h-4 w-4 mr-2" />
          Filters
          {activeFilterCount > 0 && (
            <Badge
              variant="default"
              className="ml-2 h-5 w-5 rounded-full p-0 flex items-center justify-center"
            >
              {activeFilterCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px]" align="end">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="font-semibold">Advanced Filters</h4>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReset}
              disabled={activeFilterCount === 0}
            >
              Reset
            </Button>
          </div>

          {/* Status */}
          <div className="space-y-2">
            <Label>Status</Label>
            <div className="flex flex-wrap gap-2">
              {['active', 'draft', 'archived'].map((status) => (
                <Badge
                  key={status}
                  variant={
                    localFilters.status?.includes(status) ? 'default' : 'outline'
                  }
                  className="cursor-pointer"
                  onClick={() => toggleStatus(status)}
                >
                  {status}
                </Badge>
              ))}
            </div>
          </div>

          {/* LLM Provider */}
          <div className="space-y-2">
            <Label>LLM Provider</Label>
            <div className="flex flex-wrap gap-2">
              {['ollama', 'openai', 'claude'].map((provider) => (
                <Badge
                  key={provider}
                  variant={
                    localFilters.llmProvider?.includes(provider)
                      ? 'default'
                      : 'outline'
                  }
                  className="cursor-pointer"
                  onClick={() => toggleProvider(provider)}
                >
                  {provider}
                </Badge>
              ))}
            </div>
          </div>

          {/* Date Range */}
          <div className="space-y-2">
            <Label>Date Range</Label>
            <div className="grid grid-cols-2 gap-2">
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="justify-start text-left">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {localFilters.dateFrom
                      ? format(localFilters.dateFrom, 'PP')
                      : 'From'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={localFilters.dateFrom}
                    onSelect={(date) =>
                      setLocalFilters({ ...localFilters, dateFrom: date })
                    }
                  />
                </PopoverContent>
              </Popover>

              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="justify-start text-left">
                    <CalendarIcon className="mr-2 h-4 w-4" />
                    {localFilters.dateTo
                      ? format(localFilters.dateTo, 'PP')
                      : 'To'}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-auto p-0" align="start">
                  <Calendar
                    mode="single"
                    selected={localFilters.dateTo}
                    onSelect={(date) =>
                      setLocalFilters({ ...localFilters, dateTo: date })
                    }
                  />
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Tags */}
          {availableTags.length > 0 && (
            <div className="space-y-2">
              <Label>Tags</Label>
              <div className="flex flex-wrap gap-2 max-h-[100px] overflow-y-auto">
                {availableTags.map((tag) => (
                  <Badge
                    key={tag}
                    variant={
                      localFilters.tags?.includes(tag) ? 'default' : 'outline'
                    }
                    className="cursor-pointer"
                    onClick={() => toggleTag(tag)}
                  >
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Sort */}
          <div className="space-y-2">
            <Label>Sort By</Label>
            <div className="grid grid-cols-2 gap-2">
              <Select
                value={localFilters.sortBy}
                onValueChange={(value) =>
                  setLocalFilters({ ...localFilters, sortBy: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Sort by..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created">Created Date</SelectItem>
                  <SelectItem value="updated">Updated Date</SelectItem>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="executions">Executions</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={localFilters.sortOrder}
                onValueChange={(value: 'asc' | 'desc') =>
                  setLocalFilters({ ...localFilters, sortOrder: value })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Order..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="asc">Ascending</SelectItem>
                  <SelectItem value="desc">Descending</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleApply}>Apply Filters</Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
