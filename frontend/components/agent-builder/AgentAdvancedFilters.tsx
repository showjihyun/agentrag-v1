'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
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
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import {
  Search,
  Filter,
  X,
  Tag,
  Star,
  Zap,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

export interface AgentFilters {
  search: string;
  agent_type: string[];
  llm_provider: string[];
  tags: string[];
  is_public: boolean | null;
  is_favorite: boolean | null;
  created_date_from: Date | null;
  created_date_to: Date | null;
  updated_date_from: Date | null;
  updated_date_to: Date | null;
  has_tools: boolean | null;
  has_knowledgebases: boolean | null;
  execution_status: string[];
  complexity: string[];
  orchestration_compatibility: string[];
}

interface AgentAdvancedFiltersProps {
  filters: AgentFilters;
  onFiltersChange: (filters: AgentFilters) => void;
  availableTags?: string[];
  availableOrchestrationTypes?: string[];
}

const AGENT_TYPES = [
  { value: 'custom', label: '커스텀' },
  { value: 'template_based', label: '템플릿 기반' },
];

const LLM_PROVIDERS = [
  { value: 'ollama', label: 'Ollama' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'gemini', label: 'Google Gemini' },
];

const EXECUTION_STATUSES = [
  { value: 'active', label: '활성', icon: CheckCircle, color: 'text-green-600' },
  { value: 'inactive', label: '비활성', icon: AlertCircle, color: 'text-gray-600' },
  { value: 'error', label: '오류', icon: AlertCircle, color: 'text-red-600' },
];

const COMPLEXITY_LEVELS = [
  { value: 'beginner', label: '초급', color: 'bg-green-100 text-green-800' },
  { value: 'intermediate', label: '중급', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'advanced', label: '고급', color: 'bg-red-100 text-red-800' },
];

export function AgentAdvancedFilters({
  filters,
  onFiltersChange,
  availableTags = [],
  availableOrchestrationTypes = [],
}: AgentAdvancedFiltersProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchInput, setSearchInput] = useState(filters.search);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      onFiltersChange({ ...filters, search: searchInput });
    }, 300);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const updateFilter = (key: keyof AgentFilters, value: any) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const toggleArrayFilter = (key: keyof AgentFilters, value: string) => {
    const currentArray = filters[key] as string[];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    updateFilter(key, newArray);
  };

  const clearAllFilters = () => {
    onFiltersChange({
      search: '',
      agent_type: [],
      llm_provider: [],
      tags: [],
      is_public: null,
      is_favorite: null,
      created_date_from: null,
      created_date_to: null,
      updated_date_from: null,
      updated_date_to: null,
      has_tools: null,
      has_knowledgebases: null,
      execution_status: [],
      complexity: [],
      orchestration_compatibility: [],
    });
    setSearchInput('');
  };

  const getActiveFiltersCount = () => {
    let count = 0;
    if (filters.search) count++;
    if (filters.agent_type.length > 0) count++;
    if (filters.llm_provider.length > 0) count++;
    if (filters.tags.length > 0) count++;
    if (filters.is_public !== null) count++;
    if (filters.is_favorite !== null) count++;
    if (filters.created_date_from || filters.created_date_to) count++;
    if (filters.updated_date_from || filters.updated_date_to) count++;
    if (filters.has_tools !== null) count++;
    if (filters.has_knowledgebases !== null) count++;
    if (filters.execution_status.length > 0) count++;
    if (filters.complexity.length > 0) count++;
    if (filters.orchestration_compatibility.length > 0) count++;
    return count;
  };

  const activeFiltersCount = getActiveFiltersCount();

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="에이전트 이름, 설명, 태그로 검색..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="pl-10 pr-12"
        />
        {searchInput && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSearchInput('')}
            className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Filter Controls */}
      <div className="flex items-center gap-2 flex-wrap">
        <Popover open={isOpen} onOpenChange={setIsOpen}>
          <PopoverTrigger asChild>
            <Button variant="outline" className="gap-2">
              <Filter className="h-4 w-4" />
              고급 필터
              {activeFiltersCount > 0 && (
                <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                  {activeFiltersCount}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-96 p-0" align="start">
            <div className="p-4 space-y-4 max-h-96 overflow-y-auto">
              <div className="flex items-center justify-between">
                <h4 className="font-medium">고급 필터</h4>
                <Button variant="ghost" size="sm" onClick={clearAllFilters}>
                  전체 초기화
                </Button>
              </div>

              <Separator />

              {/* Agent Type */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">에이전트 유형</Label>
                <div className="space-y-2">
                  {AGENT_TYPES.map((type) => (
                    <div key={type.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={`type-${type.value}`}
                        checked={filters.agent_type.includes(type.value)}
                        onCheckedChange={() => toggleArrayFilter('agent_type', type.value)}
                      />
                      <Label htmlFor={`type-${type.value}`} className="text-sm">
                        {type.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              {/* LLM Provider */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">LLM 제공자</Label>
                <div className="space-y-2">
                  {LLM_PROVIDERS.map((provider) => (
                    <div key={provider.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={`provider-${provider.value}`}
                        checked={filters.llm_provider.includes(provider.value)}
                        onCheckedChange={() => toggleArrayFilter('llm_provider', provider.value)}
                      />
                      <Label htmlFor={`provider-${provider.value}`} className="text-sm">
                        {provider.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Complexity */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">복잡도</Label>
                <div className="space-y-2">
                  {COMPLEXITY_LEVELS.map((level) => (
                    <div key={level.value} className="flex items-center space-x-2">
                      <Checkbox
                        id={`complexity-${level.value}`}
                        checked={filters.complexity.includes(level.value)}
                        onCheckedChange={() => toggleArrayFilter('complexity', level.value)}
                      />
                      <Label htmlFor={`complexity-${level.value}`} className="text-sm">
                        <Badge className={level.color}>{level.label}</Badge>
                      </Label>
                    </div>
                  ))}
                </div>
              </div>

              <Separator />

              {/* Execution Status */}
              <div className="space-y-2">
                <Label className="text-sm font-medium">실행 상태</Label>
                <div className="space-y-2">
                  {EXECUTION_STATUSES.map((status) => {
                    const Icon = status.icon;
                    return (
                      <div key={status.value} className="flex items-center space-x-2">
                        <Checkbox
                          id={`status-${status.value}`}
                          checked={filters.execution_status.includes(status.value)}
                          onCheckedChange={() => toggleArrayFilter('execution_status', status.value)}
                        />
                        <Label htmlFor={`status-${status.value}`} className="text-sm flex items-center gap-2">
                          <Icon className={cn("h-3 w-3", status.color)} />
                          {status.label}
                        </Label>
                      </div>
                    );
                  })}
                </div>
              </div>

              <Separator />

              {/* Orchestration Compatibility */}
              {availableOrchestrationTypes.length > 0 && (
                <>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">오케스트레이션 호환성</Label>
                    <div className="space-y-2 max-h-32 overflow-y-auto">
                      {availableOrchestrationTypes.map((type) => (
                        <div key={type} className="flex items-center space-x-2">
                          <Checkbox
                            id={`orch-${type}`}
                            checked={filters.orchestration_compatibility.includes(type)}
                            onCheckedChange={() => toggleArrayFilter('orchestration_compatibility', type)}
                          />
                          <Label htmlFor={`orch-${type}`} className="text-sm">
                            {type}
                          </Label>
                        </div>
                      ))}
                    </div>
                  </div>
                  <Separator />
                </>
              )}

              {/* Boolean Filters */}
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="is-public"
                    checked={filters.is_public === true}
                    onCheckedChange={(checked) => updateFilter('is_public', checked ? true : null)}
                  />
                  <Label htmlFor="is-public" className="text-sm">공개 에이전트만</Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="is-favorite"
                    checked={filters.is_favorite === true}
                    onCheckedChange={(checked) => updateFilter('is_favorite', checked ? true : null)}
                  />
                  <Label htmlFor="is-favorite" className="text-sm flex items-center gap-2">
                    <Star className="h-3 w-3" />
                    즐겨찾기만
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="has-tools"
                    checked={filters.has_tools === true}
                    onCheckedChange={(checked) => updateFilter('has_tools', checked ? true : null)}
                  />
                  <Label htmlFor="has-tools" className="text-sm flex items-center gap-2">
                    <Zap className="h-3 w-3" />
                    도구 보유
                  </Label>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="has-knowledgebases"
                    checked={filters.has_knowledgebases === true}
                    onCheckedChange={(checked) => updateFilter('has_knowledgebases', checked ? true : null)}
                  />
                  <Label htmlFor="has-knowledgebases" className="text-sm">지식베이스 보유</Label>
                </div>
              </div>

              <Separator />

              {/* Date Filters */}
              <div className="space-y-3">
                <Label className="text-sm font-medium">생성일</Label>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">시작일</Label>
                    <Input
                      type="date"
                      value={filters.created_date_from ? filters.created_date_from.toISOString().split('T')[0] : ''}
                      onChange={(e) => {
                        const date = e.target.value ? new Date(e.target.value) : null;
                        updateFilter('created_date_from', date);
                      }}
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground">종료일</Label>
                    <Input
                      type="date"
                      value={filters.created_date_to ? filters.created_date_to.toISOString().split('T')[0] : ''}
                      onChange={(e) => {
                        const date = e.target.value ? new Date(e.target.value) : null;
                        updateFilter('created_date_to', date);
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Tags */}
              {availableTags.length > 0 && (
                <>
                  <Separator />
                  <div className="space-y-2">
                    <Label className="text-sm font-medium">태그</Label>
                    <div className="flex flex-wrap gap-1 max-h-24 overflow-y-auto">
                      {availableTags.map((tag) => (
                        <Badge
                          key={tag}
                          variant={filters.tags.includes(tag) ? "default" : "outline"}
                          className="cursor-pointer"
                          onClick={() => toggleArrayFilter('tags', tag)}
                        >
                          <Tag className="h-3 w-3 mr-1" />
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          </PopoverContent>
        </Popover>

        {/* Active Filters Display */}
        {activeFiltersCount > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            {filters.agent_type.map((type) => (
              <Badge key={`type-${type}`} variant="secondary" className="gap-1">
                유형: {AGENT_TYPES.find(t => t.value === type)?.label}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => toggleArrayFilter('agent_type', type)}
                />
              </Badge>
            ))}
            {filters.llm_provider.map((provider) => (
              <Badge key={`provider-${provider}`} variant="secondary" className="gap-1">
                LLM: {LLM_PROVIDERS.find(p => p.value === provider)?.label}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => toggleArrayFilter('llm_provider', provider)}
                />
              </Badge>
            ))}
            {filters.tags.map((tag) => (
              <Badge key={`tag-${tag}`} variant="secondary" className="gap-1">
                <Tag className="h-3 w-3" />
                {tag}
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => toggleArrayFilter('tags', tag)}
                />
              </Badge>
            ))}
            {filters.is_public && (
              <Badge variant="secondary" className="gap-1">
                공개
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => updateFilter('is_public', null)}
                />
              </Badge>
            )}
            {filters.is_favorite && (
              <Badge variant="secondary" className="gap-1">
                <Star className="h-3 w-3" />
                즐겨찾기
                <X 
                  className="h-3 w-3 cursor-pointer" 
                  onClick={() => updateFilter('is_favorite', null)}
                />
              </Badge>
            )}
          </div>
        )}
      </div>
    </div>
  );
}