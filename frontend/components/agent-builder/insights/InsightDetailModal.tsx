'use client';

import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Insight } from '@/lib/insights/insight-engine';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useTheme } from '@/contexts/ThemeContext';

interface InsightDetailModalProps {
  insight: Insight;
  open: boolean;
  onClose: () => void;
}

export function InsightDetailModal({ insight, open, onClose }: InsightDetailModalProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // 샘플 데이터 (실제로는 API에서 가져옴)
  const historicalData = Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
    value: Math.random() * 100 + 50,
  }));

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {insight.title}
            <Badge variant="outline">{insight.type}</Badge>
          </DialogTitle>
          <DialogDescription>{insight.description}</DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList>
            <TabsTrigger value="overview">개요</TabsTrigger>
            <TabsTrigger value="analysis">상세 분석</TabsTrigger>
            <TabsTrigger value="history">이력</TabsTrigger>
            <TabsTrigger value="recommendations">추천</TabsTrigger>
          </TabsList>

          <ScrollArea className="h-[500px] mt-4">
            <TabsContent value="overview" className="space-y-4">
              {/* Impact Details */}
              {insight.impact && (
                <div className="p-4 border rounded-md">
                  <h3 className="font-semibold mb-3">영향 분석</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-muted-foreground">메트릭</div>
                      <div className="text-lg font-semibold">{insight.impact.metric}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">신뢰도</div>
                      <div className="text-lg font-semibold">{insight.confidence}%</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">현재 값</div>
                      <div className="text-lg font-semibold">{insight.impact.current.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">예측 값</div>
                      <div className="text-lg font-semibold">{insight.impact.predicted.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="p-4 border rounded-md">
                <h3 className="font-semibold mb-3">실행 가능한 액션</h3>
                <div className="space-y-2">
                  {insight.actions.map((action) => (
                    <div key={action.id} className="flex items-center justify-between p-3 bg-muted rounded-md">
                      <div>
                        <div className="font-medium">{action.label}</div>
                        {action.estimatedImpact && (
                          <div className="text-sm text-muted-foreground">
                            예상 효과: {action.estimatedImpact.value > 0 ? '+' : ''}
                            {action.estimatedImpact.value}
                            {action.estimatedImpact.unit} {action.estimatedImpact.metric}
                          </div>
                        )}
                      </div>
                      <Button size="sm" variant={action.type === 'primary' ? 'default' : 'outline'}>
                        실행
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tags */}
              <div className="p-4 border rounded-md">
                <h3 className="font-semibold mb-3">태그</h3>
                <div className="flex flex-wrap gap-2">
                  {insight.tags.map((tag) => (
                    <Badge key={tag} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="analysis" className="space-y-4">
              <div className="p-4 border rounded-md">
                <h3 className="font-semibold mb-3">트렌드 분석</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={historicalData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke={isDark ? '#374151' : '#e5e7eb'} />
                    <XAxis dataKey="date" stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
                    <YAxis stroke={isDark ? '#9ca3af' : '#6b7280'} fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: isDark ? '#1f2937' : '#ffffff',
                        border: `1px solid ${isDark ? '#374151' : '#e5e7eb'}`,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#3b82f6"
                      fillOpacity={1}
                      fill="url(#colorValue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="p-4 border rounded-md">
                <h3 className="font-semibold mb-3">통계 정보</h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">평균</div>
                    <div className="text-lg font-semibold">75.3</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">표준편차</div>
                    <div className="text-lg font-semibold">12.4</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">변동계수</div>
                    <div className="text-lg font-semibold">16.5%</div>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="history" className="space-y-4">
              <div className="p-4 border rounded-md">
                <h3 className="font-semibold mb-3">유사 인사이트 이력</h3>
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="p-3 bg-muted rounded-md">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">유사 인사이트 #{i}</div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(Date.now() - i * 7 * 24 * 60 * 60 * 1000).toLocaleDateString()}
                          </div>
                        </div>
                        <Badge variant="outline">해결됨</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="recommendations" className="space-y-4">
              <div className="p-4 border rounded-md">
                <h3 className="font-semibold mb-3">AI 추천 사항</h3>
                <div className="space-y-3">
                  <div className="p-3 bg-blue-50 dark:bg-blue-950/50 border border-blue-200 dark:border-blue-900 rounded-md">
                    <div className="font-medium mb-1">즉시 실행 가능</div>
                    <p className="text-sm text-muted-foreground">
                      프롬프트 길이를 30% 줄이면 응답 시간이 개선됩니다
                    </p>
                  </div>
                  <div className="p-3 bg-green-50 dark:bg-green-950/50 border border-green-200 dark:border-green-900 rounded-md">
                    <div className="font-medium mb-1">장기 개선</div>
                    <p className="text-sm text-muted-foreground">
                      캐싱을 활성화하면 월 비용을 25% 절감할 수 있습니다
                    </p>
                  </div>
                </div>
              </div>
            </TabsContent>
          </ScrollArea>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
