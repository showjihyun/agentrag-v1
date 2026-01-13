/**
 * Optimization Settings Component
 * 
 * 최적화 설정을 관리하는 컴포넌트
 */
import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Settings,
  Save,
  RotateCcw,
  AlertTriangle,
  Info,
  CheckCircle,
  Clock,
  DollarSign,
  Zap,
  Target,
  Shield
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface OptimizationSettings {
  // 자동 튜닝 설정
  autoTuning: {
    enabled: boolean;
    strategy: 'conservative' | 'balanced' | 'aggressive' | 'cost_focused';
    autoApply: boolean;
    intervalHours: number;
    minImprovementThreshold: number;
    maxRiskTolerance: number;
  };
  
  // 성능 임계값
  performanceThresholds: {
    maxExecutionTime: number;
    minSuccessRate: number;
    maxCostPerExecution: number;
    maxMemoryUsage: number;
  };
  
  // ML 최적화 설정
  mlOptimization: {
    enabled: boolean;
    learningRate: number;
    minDataPoints: number;
    confidenceThreshold: number;
    objectivePriority: {
      performance: number;
      cost: number;
      reliability: number;
    };
  };
  
  // 비용 최적화 설정
  costOptimization: {
    enabled: boolean;
    strategy: 'aggressive' | 'balanced' | 'conservative';
    maxMonthlyCost: number;
    costIncreaseAlertThreshold: number;
    autoImplementLowRisk: boolean;
  };
  
  // 알림 설정
  notifications: {
    emailEnabled: boolean;
    slackEnabled: boolean;
    thresholdViolations: boolean;
    optimizationResults: boolean;
    weeklyReports: boolean;
  };
}

interface Props {
  initialSettings?: Partial<OptimizationSettings>;
  onSave: (settings: OptimizationSettings) => Promise<void>;
  onReset: () => void;
  className?: string;
}

const defaultSettings: OptimizationSettings = {
  autoTuning: {
    enabled: true,
    strategy: 'balanced',
    autoApply: false,
    intervalHours: 24,
    minImprovementThreshold: 5.0,
    maxRiskTolerance: 0.1
  },
  performanceThresholds: {
    maxExecutionTime: 10.0,
    minSuccessRate: 0.9,
    maxCostPerExecution: 0.2,
    maxMemoryUsage: 1000.0
  },
  mlOptimization: {
    enabled: true,
    learningRate: 0.1,
    minDataPoints: 10,
    confidenceThreshold: 0.7,
    objectivePriority: {
      performance: 40,
      cost: 30,
      reliability: 30
    }
  },
  costOptimization: {
    enabled: true,
    strategy: 'balanced',
    maxMonthlyCost: 1000.0,
    costIncreaseAlertThreshold: 0.2,
    autoImplementLowRisk: true
  },
  notifications: {
    emailEnabled: true,
    slackEnabled: false,
    thresholdViolations: true,
    optimizationResults: true,
    weeklyReports: false
  }
};

export const OptimizationSettings: React.FC<Props> = ({
  initialSettings = {},
  onSave,
  onReset,
  className = ''
}) => {
  const [settings, setSettings] = useState<OptimizationSettings>({
    ...defaultSettings,
    ...initialSettings
  });
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  // 설정 변경 감지
  useEffect(() => {
    const hasChanged = JSON.stringify(settings) !== JSON.stringify({
      ...defaultSettings,
      ...initialSettings
    });
    setHasChanges(hasChanged);
  }, [settings, initialSettings]);

  // 설정 업데이트 헬퍼
  const updateSettings = (path: string, value: any) => {
    setSettings(prev => {
      const keys = path.split('.');
      const newSettings = { ...prev };
      let current: any = newSettings;
      
      for (let i = 0; i < keys.length - 1; i++) {
        current[keys[i]] = { ...current[keys[i]] };
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newSettings;
    });
  };

  // 설정 검증
  const validateSettings = (): string[] => {
    const errors: string[] = [];
    
    // 성능 임계값 검증
    if (settings.performanceThresholds.maxExecutionTime <= 0) {
      errors.push('최대 실행 시간은 0보다 커야 합니다.');
    }
    
    if (settings.performanceThresholds.minSuccessRate < 0 || settings.performanceThresholds.minSuccessRate > 1) {
      errors.push('최소 성공률은 0과 1 사이여야 합니다.');
    }
    
    // ML 최적화 설정 검증
    const prioritySum = Object.values(settings.mlOptimization.objectivePriority).reduce((sum, val) => sum + val, 0);
    if (Math.abs(prioritySum - 100) > 0.1) {
      errors.push('목표 우선순위의 합은 100%여야 합니다.');
    }
    
    // 비용 설정 검증
    if (settings.costOptimization.maxMonthlyCost <= 0) {
      errors.push('최대 월간 비용은 0보다 커야 합니다.');
    }
    
    return errors;
  };

  // 설정 저장
  const handleSave = async () => {
    const errors = validateSettings();
    setValidationErrors(errors);
    
    if (errors.length > 0) {
      return;
    }
    
    setIsSaving(true);
    try {
      await onSave(settings);
      setHasChanges(false);
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // 설정 초기화
  const handleReset = () => {
    setSettings({ ...defaultSettings, ...initialSettings });
    setValidationErrors([]);
    onReset();
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="w-6 h-6 text-gray-700" />
          <h2 className="text-xl font-semibold text-gray-900">최적화 설정</h2>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={!hasChanges}
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            초기화
          </Button>
          
          <Button
            onClick={handleSave}
            disabled={!hasChanges || isSaving}
          >
            <Save className="w-4 h-4 mr-2" />
            {isSaving ? '저장 중...' : '저장'}
          </Button>
        </div>
      </div>

      {/* 검증 오류 표시 */}
      {validationErrors.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1">
              {validationErrors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {/* 설정 탭 */}
      <Tabs defaultValue="auto-tuning" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="auto-tuning">자동 튜닝</TabsTrigger>
          <TabsTrigger value="thresholds">성능 임계값</TabsTrigger>
          <TabsTrigger value="ml-optimization">ML 최적화</TabsTrigger>
          <TabsTrigger value="cost-optimization">비용 최적화</TabsTrigger>
          <TabsTrigger value="notifications">알림</TabsTrigger>
        </TabsList>

        {/* 자동 튜닝 설정 */}
        <TabsContent value="auto-tuning" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                자동 성능 튜닝
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base font-medium">자동 튜닝 활성화</Label>
                  <p className="text-sm text-gray-600">워크플로우 성능을 자동으로 모니터링하고 최적화합니다.</p>
                </div>
                <Switch
                  checked={settings.autoTuning.enabled}
                  onCheckedChange={(checked) => updateSettings('autoTuning.enabled', checked)}
                />
              </div>

              {settings.autoTuning.enabled && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="space-y-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>튜닝 전략</Label>
                      <Select
                        value={settings.autoTuning.strategy}
                        onValueChange={(value) => updateSettings('autoTuning.strategy', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="conservative">보수적 (안정성 우선)</SelectItem>
                          <SelectItem value="balanced">균형 (성능과 안정성)</SelectItem>
                          <SelectItem value="aggressive">적극적 (성능 우선)</SelectItem>
                          <SelectItem value="cost_focused">비용 중심</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>튜닝 주기 (시간)</Label>
                      <Input
                        type="number"
                        value={settings.autoTuning.intervalHours}
                        onChange={(e) => updateSettings('autoTuning.intervalHours', parseInt(e.target.value))}
                        min={1}
                        max={168}
                      />
                    </div>
                  </div>

                  <div>
                    <Label>최소 개선 임계값: {settings.autoTuning.minImprovementThreshold}%</Label>
                    <Slider
                      value={[settings.autoTuning.minImprovementThreshold]}
                      onValueChange={([value]) => updateSettings('autoTuning.minImprovementThreshold', value)}
                      min={1}
                      max={50}
                      step={1}
                      className="mt-2"
                    />
                    <p className="text-xs text-gray-600 mt-1">
                      이 값보다 낮은 개선은 적용하지 않습니다.
                    </p>
                  </div>

                  <div>
                    <Label>최대 위험 허용도: {(settings.autoTuning.maxRiskTolerance * 100).toFixed(0)}%</Label>
                    <Slider
                      value={[settings.autoTuning.maxRiskTolerance * 100]}
                      onValueChange={([value]) => updateSettings('autoTuning.maxRiskTolerance', value / 100)}
                      min={1}
                      max={50}
                      step={1}
                      className="mt-2"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-base font-medium">자동 적용</Label>
                      <p className="text-sm text-gray-600">위험도가 낮은 최적화를 자동으로 적용합니다.</p>
                    </div>
                    <Switch
                      checked={settings.autoTuning.autoApply}
                      onCheckedChange={(checked) => updateSettings('autoTuning.autoApply', checked)}
                    />
                  </div>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 성능 임계값 설정 */}
        <TabsContent value="thresholds" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                성능 임계값
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>최대 실행 시간 (초)</Label>
                  <Input
                    type="number"
                    value={settings.performanceThresholds.maxExecutionTime}
                    onChange={(e) => updateSettings('performanceThresholds.maxExecutionTime', parseFloat(e.target.value))}
                    min={0.1}
                    step={0.1}
                  />
                </div>

                <div>
                  <Label>최소 성공률</Label>
                  <Input
                    type="number"
                    value={settings.performanceThresholds.minSuccessRate}
                    onChange={(e) => updateSettings('performanceThresholds.minSuccessRate', parseFloat(e.target.value))}
                    min={0}
                    max={1}
                    step={0.01}
                  />
                </div>

                <div>
                  <Label>최대 실행당 비용 ($)</Label>
                  <Input
                    type="number"
                    value={settings.performanceThresholds.maxCostPerExecution}
                    onChange={(e) => updateSettings('performanceThresholds.maxCostPerExecution', parseFloat(e.target.value))}
                    min={0}
                    step={0.01}
                  />
                </div>

                <div>
                  <Label>최대 메모리 사용량 (MB)</Label>
                  <Input
                    type="number"
                    value={settings.performanceThresholds.maxMemoryUsage}
                    onChange={(e) => updateSettings('performanceThresholds.maxMemoryUsage', parseFloat(e.target.value))}
                    min={1}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ML 최적화 설정 */}
        <TabsContent value="ml-optimization" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                ML 기반 최적화
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base font-medium">ML 최적화 활성화</Label>
                  <p className="text-sm text-gray-600">머신러닝을 사용하여 성능을 예측하고 최적화합니다.</p>
                </div>
                <Switch
                  checked={settings.mlOptimization.enabled}
                  onCheckedChange={(checked) => updateSettings('mlOptimization.enabled', checked)}
                />
              </div>

              {settings.mlOptimization.enabled && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="space-y-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>학습률</Label>
                      <Input
                        type="number"
                        value={settings.mlOptimization.learningRate}
                        onChange={(e) => updateSettings('mlOptimization.learningRate', parseFloat(e.target.value))}
                        min={0.01}
                        max={1}
                        step={0.01}
                      />
                    </div>

                    <div>
                      <Label>최소 데이터 포인트</Label>
                      <Input
                        type="number"
                        value={settings.mlOptimization.minDataPoints}
                        onChange={(e) => updateSettings('mlOptimization.minDataPoints', parseInt(e.target.value))}
                        min={5}
                        max={100}
                      />
                    </div>
                  </div>

                  <div>
                    <Label>신뢰도 임계값: {(settings.mlOptimization.confidenceThreshold * 100).toFixed(0)}%</Label>
                    <Slider
                      value={[settings.mlOptimization.confidenceThreshold * 100]}
                      onValueChange={([value]) => updateSettings('mlOptimization.confidenceThreshold', value / 100)}
                      min={50}
                      max={95}
                      step={5}
                      className="mt-2"
                    />
                  </div>

                  <div>
                    <Label className="text-base font-medium mb-3 block">목표 우선순위</Label>
                    <div className="space-y-3">
                      <div>
                        <Label>성능: {settings.mlOptimization.objectivePriority.performance}%</Label>
                        <Slider
                          value={[settings.mlOptimization.objectivePriority.performance]}
                          onValueChange={([value]) => {
                            const remaining = 100 - value;
                            const costRatio = settings.mlOptimization.objectivePriority.cost / 
                              (settings.mlOptimization.objectivePriority.cost + settings.mlOptimization.objectivePriority.reliability);
                            updateSettings('mlOptimization.objectivePriority', {
                              performance: value,
                              cost: Math.round(remaining * costRatio),
                              reliability: Math.round(remaining * (1 - costRatio))
                            });
                          }}
                          min={10}
                          max={80}
                          step={5}
                          className="mt-1"
                        />
                      </div>
                      
                      <div>
                        <Label>비용: {settings.mlOptimization.objectivePriority.cost}%</Label>
                        <Slider
                          value={[settings.mlOptimization.objectivePriority.cost]}
                          onValueChange={([value]) => {
                            const remaining = 100 - settings.mlOptimization.objectivePriority.performance - value;
                            updateSettings('mlOptimization.objectivePriority', {
                              ...settings.mlOptimization.objectivePriority,
                              cost: value,
                              reliability: remaining
                            });
                          }}
                          min={10}
                          max={80}
                          step={5}
                          className="mt-1"
                        />
                      </div>
                      
                      <div>
                        <Label>안정성: {settings.mlOptimization.objectivePriority.reliability}%</Label>
                        <div className="text-sm text-gray-600">
                          (자동 계산됨: {100 - settings.mlOptimization.objectivePriority.performance - settings.mlOptimization.objectivePriority.cost}%)
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 비용 최적화 설정 */}
        <TabsContent value="cost-optimization" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="w-5 h-5" />
                비용 최적화
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base font-medium">비용 최적화 활성화</Label>
                  <p className="text-sm text-gray-600">워크플로우 실행 비용을 자동으로 최적화합니다.</p>
                </div>
                <Switch
                  checked={settings.costOptimization.enabled}
                  onCheckedChange={(checked) => updateSettings('costOptimization.enabled', checked)}
                />
              </div>

              {settings.costOptimization.enabled && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="space-y-4"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label>최적화 전략</Label>
                      <Select
                        value={settings.costOptimization.strategy}
                        onValueChange={(value) => updateSettings('costOptimization.strategy', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="conservative">보수적</SelectItem>
                          <SelectItem value="balanced">균형</SelectItem>
                          <SelectItem value="aggressive">적극적</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <Label>최대 월간 비용 ($)</Label>
                      <Input
                        type="number"
                        value={settings.costOptimization.maxMonthlyCost}
                        onChange={(e) => updateSettings('costOptimization.maxMonthlyCost', parseFloat(e.target.value))}
                        min={1}
                      />
                    </div>
                  </div>

                  <div>
                    <Label>비용 증가 알림 임계값: {(settings.costOptimization.costIncreaseAlertThreshold * 100).toFixed(0)}%</Label>
                    <Slider
                      value={[settings.costOptimization.costIncreaseAlertThreshold * 100]}
                      onValueChange={([value]) => updateSettings('costOptimization.costIncreaseAlertThreshold', value / 100)}
                      min={5}
                      max={50}
                      step={5}
                      className="mt-2"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <Label className="text-base font-medium">저위험 최적화 자동 적용</Label>
                      <p className="text-sm text-gray-600">위험도가 낮은 비용 최적화를 자동으로 적용합니다.</p>
                    </div>
                    <Switch
                      checked={settings.costOptimization.autoImplementLowRisk}
                      onCheckedChange={(checked) => updateSettings('costOptimization.autoImplementLowRisk', checked)}
                    />
                  </div>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 알림 설정 */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                알림 설정
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-base font-medium">이메일 알림</Label>
                    <p className="text-sm text-gray-600">이메일로 최적화 알림을 받습니다.</p>
                  </div>
                  <Switch
                    checked={settings.notifications.emailEnabled}
                    onCheckedChange={(checked) => updateSettings('notifications.emailEnabled', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-base font-medium">Slack 알림</Label>
                    <p className="text-sm text-gray-600">Slack으로 최적화 알림을 받습니다.</p>
                  </div>
                  <Switch
                    checked={settings.notifications.slackEnabled}
                    onCheckedChange={(checked) => updateSettings('notifications.slackEnabled', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-base font-medium">임계값 위반 알림</Label>
                    <p className="text-sm text-gray-600">성능 임계값 위반 시 알림을 받습니다.</p>
                  </div>
                  <Switch
                    checked={settings.notifications.thresholdViolations}
                    onCheckedChange={(checked) => updateSettings('notifications.thresholdViolations', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-base font-medium">최적화 결과 알림</Label>
                    <p className="text-sm text-gray-600">최적화 완료 시 결과를 알림으로 받습니다.</p>
                  </div>
                  <Switch
                    checked={settings.notifications.optimizationResults}
                    onCheckedChange={(checked) => updateSettings('notifications.optimizationResults', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-base font-medium">주간 리포트</Label>
                    <p className="text-sm text-gray-600">주간 최적화 성과 리포트를 받습니다.</p>
                  </div>
                  <Switch
                    checked={settings.notifications.weeklyReports}
                    onCheckedChange={(checked) => updateSettings('notifications.weeklyReports', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 변경사항 알림 */}
      {hasChanges && (
        <Alert>
          <Info className="h-4 w-4" />
          <AlertDescription>
            설정이 변경되었습니다. 저장 버튼을 클릭하여 변경사항을 적용하세요.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
};