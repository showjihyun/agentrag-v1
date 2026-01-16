'use client';

/**
 * ToolRecommendations Component
 * 
 * Agent 타입과 설명을 기반으로 추천 도구를 표시하는 컴포넌트
 * - AI 기반 도구 추천
 * - 추천 이유 표시
 * - 원클릭 추가
 */

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Sparkles,
  Plus,
  Check,
  Lightbulb,
  TrendingUp,
  Info,
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface ToolRecommendation {
  tool: {
    id: string;
    name: string;
    description: string;
    category: string;
    icon: string;
    bg_color: string;
  };
  score: number;
  reasons: string[];
  recommended: boolean;
}

interface ToolRecommendationsProps {
  agentType?: string;
  agentDescription?: string;
  selectedToolIds: string[];
  onToolSelect: (toolId: string) => void;
  onToolDeselect: (toolId: string) => void;
}

export function ToolRecommendations({
  agentType,
  agentDescription,
  selectedToolIds,
  onToolSelect,
  onToolDeselect,
}: ToolRecommendationsProps) {
  const [recommendations, setRecommendations] = useState<ToolRecommendation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecommendations = async () => {
      if (!agentDescription || agentDescription.length < 10) {
        setRecommendations([]);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        if (agentType) params.append('agent_type', agentType);
        if (agentDescription) params.append('description', agentDescription);

        const response = await fetch(
          `/api/agent-builder/tools/recommend?${params.toString()}`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch recommendations');
        }

        const data = await response.json();
        setRecommendations(data.recommendations || []);
      } catch (err) {
        console.error('Failed to fetch tool recommendations:', err);
        setError('추천 도구를 불러오는데 실패했습니다');
      } finally {
        setIsLoading(false);
      }
    };

    // Debounce the API call
    const timeoutId = setTimeout(fetchRecommendations, 500);
    return () => clearTimeout(timeoutId);
  }, [agentType, agentDescription]);

  const isToolSelected = (toolId: string) => selectedToolIds.includes(toolId);

  const handleToggleTool = (toolId: string) => {
    if (isToolSelected(toolId)) {
      onToolDeselect(toolId);
    } else {
      onToolSelect(toolId);
    }
  };

  if (!agentDescription || agentDescription.length < 10) {
    return (
      <Card className="border-dashed">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground space-y-2">
            <Lightbulb className="h-8 w-8 mx-auto opacity-50" />
            <p className="text-sm">
              Agent 설명을 입력하면 AI가 적합한 도구를 추천해드립니다
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sparkles className="h-4 w-4 text-purple-500" />
            추천 도구
          </CardTitle>
          <CardDescription className="text-xs">
            AI가 분석 중입니다...
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-12 w-12 rounded" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <div className="text-center text-destructive space-y-2">
            <Info className="h-8 w-8 mx-auto" />
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (recommendations.length === 0) {
    return (
      <Card className="border-dashed">
        <CardContent className="pt-6">
          <div className="text-center text-muted-foreground space-y-2">
            <Sparkles className="h-8 w-8 mx-auto opacity-50" />
            <p className="text-sm">
              현재 설명에 맞는 추천 도구가 없습니다
            </p>
            <p className="text-xs">
              더 구체적인 설명을 입력해보세요
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Separate highly recommended and other recommendations
  const highlyRecommended = recommendations.filter(r => r.recommended);
  const others = recommendations.filter(r => !r.recommended);

  return (
    <Card className="border-purple-200 bg-purple-50/50 dark:border-purple-900 dark:bg-purple-950/20">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-purple-500" />
              AI 추천 도구
            </CardTitle>
            <CardDescription className="text-xs mt-1">
              Agent 설명을 분석하여 적합한 도구를 추천합니다
            </CardDescription>
          </div>
          <Badge variant="secondary" className="text-xs">
            {recommendations.length}개 발견
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <ScrollArea className="h-[300px] pr-4">
          <div className="space-y-4">
            {/* Highly Recommended */}
            {highlyRecommended.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center gap-2 text-xs font-medium text-purple-700 dark:text-purple-300">
                  <TrendingUp className="h-3 w-3" />
                  강력 추천
                </div>
                <div className="space-y-2">
                  {highlyRecommended.map((rec) => (
                    <ToolRecommendationCard
                      key={rec.tool.id}
                      recommendation={rec}
                      isSelected={isToolSelected(rec.tool.id)}
                      onToggle={() => handleToggleTool(rec.tool.id)}
                      highlighted
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Other Recommendations */}
            {others.length > 0 && (
              <div className="space-y-2">
                {highlyRecommended.length > 0 && (
                  <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                    <Lightbulb className="h-3 w-3" />
                    기타 추천
                  </div>
                )}
                <div className="space-y-2">
                  {others.map((rec) => (
                    <ToolRecommendationCard
                      key={rec.tool.id}
                      recommendation={rec}
                      isSelected={isToolSelected(rec.tool.id)}
                      onToggle={() => handleToggleTool(rec.tool.id)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

interface ToolRecommendationCardProps {
  recommendation: ToolRecommendation;
  isSelected: boolean;
  onToggle: () => void;
  highlighted?: boolean;
}

function ToolRecommendationCard({
  recommendation,
  isSelected,
  onToggle,
  highlighted = false,
}: ToolRecommendationCardProps) {
  const { tool, reasons, score } = recommendation;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Card
            className={cn(
              "cursor-pointer transition-all hover:shadow-md",
              isSelected 
                ? "border-primary bg-primary/5" 
                : "hover:border-primary/50",
              highlighted && !isSelected && "border-purple-300 dark:border-purple-700"
            )}
            onClick={onToggle}
          >
            <CardContent className="p-3">
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    "p-2 rounded-lg flex-shrink-0",
                    isSelected 
                      ? "bg-primary text-primary-foreground" 
                      : "bg-muted"
                  )}
                  style={!isSelected ? { backgroundColor: tool.bg_color + '20' } : {}}
                >
                  <div className="h-5 w-5 flex items-center justify-center text-xs font-bold">
                    {tool.icon || '🔧'}
                  </div>
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-sm truncate">{tool.name}</h4>
                    {highlighted && !isSelected && (
                      <Badge variant="secondary" className="text-xs bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200">
                        추천
                      </Badge>
                    )}
                    {isSelected && (
                      <Check className="h-4 w-4 text-primary flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                    {tool.description}
                  </p>
                  {reasons.length > 0 && (
                    <div className="flex items-center gap-1 mt-1">
                      <Lightbulb className="h-3 w-3 text-amber-500" />
                      <span className="text-xs text-amber-700 dark:text-amber-400 line-clamp-1">
                        {reasons[0]}
                      </span>
                    </div>
                  )}
                </div>
                
                <Button
                  variant={isSelected ? "secondary" : "ghost"}
                  size="sm"
                  className="flex-shrink-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggle();
                  }}
                >
                  {isSelected ? (
                    <>
                      <Check className="h-3 w-3 mr-1" />
                      선택됨
                    </>
                  ) : (
                    <>
                      <Plus className="h-3 w-3 mr-1" />
                      추가
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TooltipTrigger>
        <TooltipContent side="left" className="max-w-xs">
          <div className="space-y-2">
            <p className="font-medium">{tool.name}</p>
            <p className="text-xs">{tool.description}</p>
            {reasons.length > 0 && (
              <div className="space-y-1 pt-2 border-t">
                <p className="text-xs font-medium">추천 이유:</p>
                <ul className="text-xs space-y-0.5">
                  {reasons.map((reason, i) => (
                    <li key={i}>• {reason}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="pt-2 border-t">
              <Badge variant="outline" className="text-xs">
                추천 점수: {score}
              </Badge>
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default ToolRecommendations;
