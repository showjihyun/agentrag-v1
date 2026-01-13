'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  ArrowRight,
  Zap,
  Users,
  GitBranch,
  MessageSquare,
  Route,
  Hexagon,
  Bell,
  RefreshCw,
  Brain,
  Atom,
  Leaf,
  TrendingUp,
  Network,
  Heart,
  Crystal,
  Clock,
  CheckCircle2,
  AlertCircle,
  Info,
  Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  CORE_ORCHESTRATION_TYPES,
  TRENDS_2025_ORCHESTRATION_TYPES,
  TRENDS_2026_ORCHESTRATION_TYPES,
  CATEGORY_COLORS,
  type OrchestrationTypeValue,
  type OrchestrationPattern,
} from '@/lib/constants/orchestration';

// 아이콘 매핑
const ICON_MAP = {
  ArrowRight,
  Zap,
  Users,
  GitBranch,
  MessageSquare,
  Route,
  Hexagon,
  Bell,
  RefreshCw,
  Brain,
  Atom,
  Leaf,
  TrendingUp,
  Network,
  Heart,
  Gem, // Crystal 대신 Gem 사용
};

interface OrchestrationPatternSelectorProps {
  selectedPattern?: OrchestrationTypeValue;
  onPatternSelect: (pattern: OrchestrationTypeValue) => void;
  onConfigurePattern?: (pattern: OrchestrationTypeValue) => void;
  className?: string;
}

interface PatternCardProps {
  pattern: OrchestrationPattern;
  isSelected: boolean;
  onSelect: () => void;
  onConfigure?: () => void; // optional로 변경
}

const PatternCard: React.FC<PatternCardProps> = ({
  pattern,
  isSelected,
  onSelect,
  onConfigure,
}) => {
  const IconComponent = ICON_MAP[pattern.icon as keyof typeof ICON_MAP] || Users;
  const categoryColor = CATEGORY_COLORS[pattern.category];

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'simple':
        return 'text-green-600 bg-green-50';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50';
      case 'complex':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getComplexityIcon = (complexity: string) => {
    switch (complexity) {
      case 'simple':
        return CheckCircle2;
      case 'medium':
        return AlertCircle;
      case 'complex':
        return Info;
      default:
        return Info;
    }
  };

  const ComplexityIcon = getComplexityIcon(pattern.complexity);

  return (
    <Card
      className={cn(
        'cursor-pointer transition-all duration-200 hover:shadow-md',
        isSelected && 'ring-2 ring-blue-500 shadow-lg'
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className="p-2 rounded-lg"
              style={{ backgroundColor: `${categoryColor}20`, color: categoryColor }}
            >
              <IconComponent className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-lg">{pattern.name}</CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <Badge
                  variant="outline"
                  className={cn('text-xs', getComplexityColor(pattern.complexity))}
                >
                  <ComplexityIcon className="w-3 h-3 mr-1" />
                  {pattern.complexity === 'simple' && '간단'}
                  {pattern.complexity === 'medium' && '보통'}
                  {pattern.complexity === 'complex' && '복잡'}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  <Clock className="w-3 h-3 mr-1" />
                  {pattern.estimatedSetupTime}
                </Badge>
              </div>
            </div>
          </div>
          {isSelected && (
            <CheckCircle2 className="w-5 h-5 text-blue-500" />
          )}
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <CardDescription className="text-sm mb-3 line-clamp-2">
          {pattern.description}
        </CardDescription>
        
        <div className="space-y-3">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-1">사용 사례</h4>
            <p className="text-xs text-gray-600">{pattern.useCase}</p>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-1">주요 장점</h4>
            <div className="flex flex-wrap gap-1">
              {pattern.benefits.slice(0, 2).map((benefit, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {benefit}
                </Badge>
              ))}
              {pattern.benefits.length > 2 && (
                <Badge variant="outline" className="text-xs">
                  +{pattern.benefits.length - 2}개 더
                </Badge>
              )}
            </div>
          </div>
        </div>

        {onConfigure && (
          <div className="mt-4 pt-3 border-t">
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={(e) => {
                e.stopPropagation();
                onConfigure();
              }}
            >
              <Sparkles className="w-4 h-4 mr-2" />
              상세 설정
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

interface PatternDetailDialogProps {
  pattern: OrchestrationPattern | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: () => void;
}

const PatternDetailDialog: React.FC<PatternDetailDialogProps> = ({
  pattern,
  open,
  onOpenChange,
  onSelect,
}) => {
  if (!pattern) return null;

  const IconComponent = ICON_MAP[pattern.icon as keyof typeof ICON_MAP] || Users;
  const categoryColor = CATEGORY_COLORS[pattern.category];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div
              className="p-3 rounded-lg"
              style={{ backgroundColor: `${categoryColor}20`, color: categoryColor }}
            >
              <IconComponent className="w-6 h-6" />
            </div>
            <div>
              <DialogTitle className="text-xl">{pattern.name}</DialogTitle>
              <DialogDescription className="mt-1">
                {pattern.description}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-3">사용 사례</h3>
            <p className="text-gray-700">{pattern.useCase}</p>
          </div>

          <Separator />

          <div>
            <h3 className="text-lg font-semibold mb-3">주요 장점</h3>
            <ul className="space-y-2">
              {pattern.benefits.map((benefit, index) => (
                <li key={index} className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                  <span className="text-gray-700">{benefit}</span>
                </li>
              ))}
            </ul>
          </div>

          <Separator />

          <div>
            <h3 className="text-lg font-semibold mb-3">요구사항</h3>
            <ul className="space-y-2">
              {pattern.requirements.map((requirement, index) => (
                <li key={index} className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-yellow-500" />
                  <span className="text-gray-700">{requirement}</span>
                </li>
              ))}
            </ul>
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="text-center">
                <div className="text-sm text-gray-500">복잡도</div>
                <Badge
                  variant="outline"
                  className={cn(
                    'mt-1',
                    pattern.complexity === 'simple' && 'text-green-600 bg-green-50',
                    pattern.complexity === 'medium' && 'text-yellow-600 bg-yellow-50',
                    pattern.complexity === 'complex' && 'text-red-600 bg-red-50'
                  )}
                >
                  {pattern.complexity === 'simple' && '간단'}
                  {pattern.complexity === 'medium' && '보통'}
                  {pattern.complexity === 'complex' && '복잡'}
                </Badge>
              </div>
              <div className="text-center">
                <div className="text-sm text-gray-500">예상 설정 시간</div>
                <Badge variant="secondary" className="mt-1">
                  <Clock className="w-3 h-3 mr-1" />
                  {pattern.estimatedSetupTime}
                </Badge>
              </div>
            </div>
            <Button onClick={onSelect} className="px-6">
              이 패턴 선택
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export const OrchestrationPatternSelector: React.FC<OrchestrationPatternSelectorProps> = ({
  selectedPattern,
  onPatternSelect,
  onConfigurePattern,
  className,
}) => {
  const [detailPattern, setDetailPattern] = useState<OrchestrationPattern | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);

  const handlePatternSelect = (pattern: OrchestrationTypeValue) => {
    onPatternSelect(pattern);
  };

  const handlePatternDetail = (pattern: OrchestrationPattern) => {
    setDetailPattern(pattern);
    setDetailDialogOpen(true);
  };

  const handleDetailSelect = () => {
    if (detailPattern) {
      onPatternSelect(detailPattern.id);
      setDetailDialogOpen(false);
    }
  };

  const renderPatternGrid = (patterns: Record<string, OrchestrationPattern>) => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Object.values(patterns).map((pattern) => (
        <PatternCard
          key={pattern.id}
          pattern={pattern}
          isSelected={selectedPattern === pattern.id}
          onSelect={() => handlePatternSelect(pattern.id)}
          onConfigure={onConfigurePattern ? () => onConfigurePattern(pattern.id) : undefined}
        />
      ))}
    </div>
  );

  return (
    <div className={cn('space-y-6', className)}>
      <div>
        <h2 className="text-2xl font-bold mb-2">오케스트레이션 패턴 선택</h2>
        <p className="text-gray-600">
          Agent들이 협력하는 방식을 선택하세요. 각 패턴은 서로 다른 장점과 사용 사례를 가지고 있습니다.
        </p>
      </div>

      <Tabs defaultValue="core" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="core" className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            핵심 패턴
          </TabsTrigger>
          <TabsTrigger value="2025" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            2025 트렌드
          </TabsTrigger>
          <TabsTrigger value="2026" className="flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            2026 차세대
          </TabsTrigger>
        </TabsList>

        <TabsContent value="core" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">핵심 패턴</h3>
            <p className="text-sm text-gray-600 mb-4">
              검증된 기본 오케스트레이션 패턴으로, 대부분의 사용 사례에 적합합니다.
            </p>
          </div>
          <ScrollArea className="h-[600px]">
            {renderPatternGrid(CORE_ORCHESTRATION_TYPES)}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="2025" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">2025년 트렌드 패턴</h3>
            <p className="text-sm text-gray-600 mb-4">
              최신 AI 연구를 반영한 고급 협업 패턴으로, 복잡한 의사결정과 동적 최적화에 특화되어 있습니다.
            </p>
          </div>
          <ScrollArea className="h-[600px]">
            {renderPatternGrid(TRENDS_2025_ORCHESTRATION_TYPES)}
          </ScrollArea>
        </TabsContent>

        <TabsContent value="2026" className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold mb-2">2026년 차세대 패턴</h3>
            <p className="text-sm text-gray-600 mb-4">
              미래 지향적인 실험적 패턴으로, 뇌과학, 양자컴퓨팅, 생물학적 영감을 활용합니다.
            </p>
          </div>
          <ScrollArea className="h-[600px]">
            {renderPatternGrid(TRENDS_2026_ORCHESTRATION_TYPES)}
          </ScrollArea>
        </TabsContent>
      </Tabs>

      <PatternDetailDialog
        pattern={detailPattern}
        open={detailDialogOpen}
        onOpenChange={setDetailDialogOpen}
        onSelect={handleDetailSelect}
      />
    </div>
  );
};