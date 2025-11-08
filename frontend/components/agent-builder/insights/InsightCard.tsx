'use client';

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Insight } from '@/lib/insights/insight-engine';
import { useToast } from '@/hooks/use-toast';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Sparkles,
  CheckCircle,
  XCircle,
  Info,
  Shield,
  Zap,
  DollarSign,
  Target,
  Eye,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';

interface InsightCardProps {
  insight: Insight;
  onViewDetails: () => void;
}

export function InsightCard({ insight, onViewDetails }: InsightCardProps) {
  const { toast } = useToast();
  const [executing, setExecuting] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  const handleAction = async (actionId: string, handler: () => Promise<void>, requiresConfirmation: boolean) => {
    if (requiresConfirmation) {
      if (!confirm('이 작업을 실행하시겠습니까?')) {
        return;
      }
    }

    setExecuting(actionId);
    try {
      await handler();
      toast({
        title: '작업 완료',
        description: '인사이트 액션이 성공적으로 실행되었습니다',
      });
    } catch (error: any) {
      toast({
        title: '작업 실패',
        description: error.message || '작업 실행 중 오류가 발생했습니다',
        variant: 'destructive',
      });
    } finally {
      setExecuting(null);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-500 bg-red-50 dark:bg-red-950/50';
      case 'high':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/50';
      case 'medium':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950/50';
      case 'low':
        return 'border-green-500 bg-green-50 dark:bg-green-950/50';
      default:
        return 'border-gray-500 bg-gray-50 dark:bg-gray-950/50';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'performance':
        return <Zap className="h-5 w-5" />;
      case 'cost':
        return <DollarSign className="h-5 w-5" />;
      case 'quality':
        return <Target className="h-5 w-5" />;
      case 'security':
        return <Shield className="h-5 w-5" />;
      case 'optimization':
        return <Sparkles className="h-5 w-5" />;
      case 'anomaly':
        return <AlertTriangle className="h-5 w-5" />;
      case 'prediction':
        return <TrendingUp className="h-5 w-5" />;
      case 'alert':
        return <AlertTriangle className="h-5 w-5" />;
      default:
        return <Info className="h-5 w-5" />;
    }
  };

  const getSeverityBadge = (severity: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      critical: 'destructive',
      high: 'default',
      medium: 'secondary',
      low: 'outline',
      info: 'outline',
    };
    return (
      <Badge variant={variants[severity] || 'outline'} className="text-xs">
        {severity.toUpperCase()}
      </Badge>
    );
  };

  return (
    <Card className={`border-2 ${getSeverityColor(insight.severity)} transition-all hover:shadow-lg`}>
      <CardContent className="p-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3 flex-1">
              <div className="mt-1">{getTypeIcon(insight.type)}</div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-lg">{insight.title}</h3>
                  {getSeverityBadge(insight.severity)}
                  <Badge variant="outline" className="text-xs">
                    {insight.confidence}% 신뢰도
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{insight.description}</p>
              </div>
            </div>
          </div>

          {/* Impact */}
          {insight.impact && (
            <div className="p-3 bg-background/50 rounded-md border">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">예상 영향</span>
                <div className="flex items-center gap-1">
                  {insight.impact.change > 0 ? (
                    <TrendingUp className="h-4 w-4 text-red-500" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-green-500" />
                  )}
                  <span
                    className={`text-sm font-bold ${
                      insight.impact.change > 0 ? 'text-red-500' : 'text-green-500'
                    }`}
                  >
                    {insight.impact.changePercent > 0 ? '+' : ''}
                    {insight.impact.changePercent.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-muted-foreground">현재</div>
                  <div className="font-semibold">{insight.impact.current.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">예측</div>
                  <div className="font-semibold">{insight.impact.predicted.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-muted-foreground">변화</div>
                  <div className="font-semibold">
                    {insight.impact.change > 0 ? '+' : ''}
                    {insight.impact.change.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Tags */}
          {insight.tags && insight.tags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {insight.tags.map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          )}

          {/* Actions */}
          {insight.actions && insight.actions.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-2 border-t">
              {insight.actions.map((action) => (
                <Button
                  key={action.id}
                  variant={action.type === 'primary' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleAction(action.id, action.handler, action.requiresConfirmation)}
                  disabled={executing === action.id}
                >
                  {executing === action.id ? '실행 중...' : action.label}
                  {action.estimatedImpact && (
                    <span className="ml-2 text-xs opacity-75">
                      ({action.estimatedImpact.value > 0 ? '+' : ''}
                      {action.estimatedImpact.value}
                      {action.estimatedImpact.unit})
                    </span>
                  )}
                </Button>
              ))}
              <Button variant="ghost" size="sm" onClick={onViewDetails}>
                <Eye className="h-4 w-4 mr-1" />
                상세보기
              </Button>
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
            <div className="flex items-center gap-4">
              <span>{new Date(insight.timestamp).toLocaleString()}</span>
              {insight.expiresAt && (
                <span>만료: {new Date(insight.expiresAt).toLocaleDateString()}</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2"
                onClick={() => {
                  toast({ title: '피드백 감사합니다', description: '인사이트가 개선됩니다' });
                }}
              >
                <ThumbsUp className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2"
                onClick={() => {
                  toast({ title: '피드백 감사합니다', description: '인사이트가 개선됩니다' });
                }}
              >
                <ThumbsDown className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2"
                onClick={() => setDismissed(true)}
              >
                <XCircle className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
