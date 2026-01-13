/**
 * Pattern-Specific Configuration Panel
 * 각 오케스트레이션 패턴에 특화된 설정 UI 컴포넌트
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Settings, 
  Zap, 
  Users, 
  MessageSquare, 
  Route, 
  Hexagon, 
  Bell, 
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Info,
  Save,
  RotateCcw,
  Download,
  Upload,
  Plus,
  Minus,
  HelpCircle
} from 'lucide-react';
import { OrchestrationTypeValue, ORCHESTRATION_TYPES } from '@/lib/constants/orchestration';

interface PatternSpecificConfigPanelProps {
  patternType: OrchestrationTypeValue;
  config: Record<string, any>;
  onConfigChange: (config: Record<string, any>) => void;
  onValidationChange?: (isValid: boolean, errors: string[]) => void;
}

interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  suggestions: string[];
}

export const PatternSpecificConfigPanel: React.FC<PatternSpecificConfigPanelProps> = ({
  patternType,
  config,
  onConfigChange,
  onValidationChange
}) => {
  const [validation, setValidation] = useState<ValidationResult>({
    isValid: true,
    errors: [],
    warnings: [],
    suggestions: []
  });
  const [activeTab, setActiveTab] = useState('basic');

  const patternInfo = ORCHESTRATION_TYPES[patternType];

  // 설정 검증 함수
  const validateConfig = useCallback((currentConfig: Record<string, any>): ValidationResult => {
    const errors: string[] = [];
    const warnings: string[] = [];
    const suggestions: string[] = [];

    // 패턴별 검증 로직
    switch (patternType) {
      case 'consensus_building':
        if (!currentConfig.voting_mechanism) {
          errors.push('투표 메커니즘을 선택해주세요.');
        }
        if (currentConfig.consensus_threshold < 0.5) {
          warnings.push('합의 임계값이 낮습니다. 50% 이상을 권장합니다.');
        }
        if (currentConfig.max_rounds > 10) {
          suggestions.push('라운드 수가 많습니다. 효율성을 위해 10라운드 이하를 권장합니다.');
        }
        break;

      case 'dynamic_routing':
        if (!currentConfig.performance_metrics || currentConfig.performance_metrics.length === 0) {
          errors.push('최소 하나의 성능 메트릭을 선택해주세요.');
        }
        if (currentConfig.routing_update_interval < 1000) {
          warnings.push('라우팅 업데이트 간격이 너무 짧습니다. 1초 이상을 권장합니다.');
        }
        break;

      case 'swarm_intelligence':
        if (currentConfig.swarm_size < 3) {
          errors.push('군집 크기는 최소 3개 이상이어야 합니다.');
        }
        if (currentConfig.inertia_weight < 0 || currentConfig.inertia_weight > 1) {
          errors.push('관성 가중치는 0과 1 사이의 값이어야 합니다.');
        }
        break;

      case 'event_driven':
        if (!currentConfig.event_types || currentConfig.event_types.length === 0) {
          errors.push('최소 하나의 이벤트 타입을 선택해주세요.');
        }
        if (currentConfig.event_timeout < 1000) {
          warnings.push('이벤트 타임아웃이 너무 짧습니다. 1초 이상을 권장합니다.');
        }
        break;

      case 'reflection':
        if (currentConfig.reflection_interval < 30) {
          warnings.push('성찰 간격이 너무 짧습니다. 30초 이상을 권장합니다.');
        }
        if (currentConfig.min_data_points < 3) {
          errors.push('최소 데이터 포인트는 3개 이상이어야 합니다.');
        }
        break;
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      suggestions
    };
  }, [patternType]);

  // 설정 변경 핸들러
  const handleConfigChange = useCallback((key: string, value: any) => {
    const newConfig = { ...config, [key]: value };
    onConfigChange(newConfig);
    
    const validationResult = validateConfig(newConfig);
    setValidation(validationResult);
    onValidationChange?.(validationResult.isValid, validationResult.errors);
  }, [config, onConfigChange, validateConfig, onValidationChange]);

  // 초기 검증
  useEffect(() => {
    const validationResult = validateConfig(config);
    setValidation(validationResult);
    onValidationChange?.(validationResult.isValid, validationResult.errors);
  }, [config, validateConfig, onValidationChange]);

  // 설정 초기화
  const resetConfig = () => {
    const defaultConfig = getDefaultConfig(patternType);
    onConfigChange(defaultConfig);
  };

  // 패턴별 기본 설정
  const getDefaultConfig = (pattern: OrchestrationTypeValue): Record<string, any> => {
    switch (pattern) {
      case 'consensus_building':
        return {
          voting_mechanism: 'majority',
          consensus_threshold: 0.7,
          max_rounds: 5,
          enable_negotiation: true,
          mediator_enabled: false,
          discussion_timeout: 300
        };
      case 'dynamic_routing':
        return {
          performance_metrics: ['response_time', 'success_rate'],
          routing_algorithm: 'weighted_round_robin',
          routing_update_interval: 5000,
          circuit_breaker_enabled: true,
          failure_threshold: 0.5,
          recovery_timeout: 30000
        };
      case 'swarm_intelligence':
        return {
          swarm_size: 10,
          inertia_weight: 0.7,
          cognitive_weight: 1.4,
          social_weight: 1.4,
          max_iterations: 50,
          convergence_threshold: 0.01
        };
      case 'event_driven':
        return {
          event_types: ['agent_completed', 'agent_failed'],
          event_timeout: 300000,
          max_concurrent_events: 50,
          event_processing_delay: 100,
          enable_event_history: true
        };
      case 'reflection':
        return {
          reflection_interval: 60,
          min_data_points: 5,
          improvement_threshold: 0.1,
          learning_decay: 0.95,
          adaptation_sensitivity: 0.15
        };
      default:
        return {};
    }
  };

  // 패턴별 설정 UI 렌더링
  const renderPatternSpecificConfig = () => {
    switch (patternType) {
      case 'consensus_building':
        return renderConsensusConfig();
      case 'dynamic_routing':
        return renderDynamicRoutingConfig();
      case 'swarm_intelligence':
        return renderSwarmConfig();
      case 'event_driven':
        return renderEventDrivenConfig();
      case 'reflection':
        return renderReflectionConfig();
      default:
        return renderGenericConfig();
    }
  };

  const renderConsensusConfig = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="voting_mechanism">투표 메커니즘</Label>
          <Select
            value={config.voting_mechanism || 'majority'}
            onValueChange={(value) => handleConfigChange('voting_mechanism', value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="투표 방식 선택" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="majority">단순 다수결</SelectItem>
              <SelectItem value="weighted">가중 투표</SelectItem>
              <SelectItem value="unanimous">만장일치</SelectItem>
              <SelectItem value="supermajority">절대 다수결</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="consensus_threshold">합의 임계값: {config.consensus_threshold || 0.7}</Label>
          <Slider
            value={[config.consensus_threshold || 0.7]}
            onValueChange={([value]) => handleConfigChange('consensus_threshold', value)}
            min={0.5}
            max={1.0}
            step={0.05}
            className="w-full"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="max_rounds">최대 라운드 수</Label>
          <Input
            type="number"
            value={config.max_rounds || 5}
            onChange={(e) => handleConfigChange('max_rounds', parseInt(e.target.value))}
            min={1}
            max={20}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="discussion_timeout">토론 타임아웃 (초)</Label>
          <Input
            type="number"
            value={config.discussion_timeout || 300}
            onChange={(e) => handleConfigChange('discussion_timeout', parseInt(e.target.value))}
            min={60}
            max={1800}
          />
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <Switch
            checked={config.enable_negotiation || true}
            onCheckedChange={(checked) => handleConfigChange('enable_negotiation', checked)}
          />
          <Label>협상 활성화</Label>
        </div>

        <div className="flex items-center space-x-2">
          <Switch
            checked={config.mediator_enabled || false}
            onCheckedChange={(checked) => handleConfigChange('mediator_enabled', checked)}
          />
          <Label>중재자 사용</Label>
        </div>
      </div>
    </div>
  );

  const renderDynamicRoutingConfig = () => (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label>성능 메트릭</Label>
        <div className="grid grid-cols-2 gap-2">
          {['response_time', 'success_rate', 'throughput', 'error_rate', 'resource_usage'].map((metric) => (
            <div key={metric} className="flex items-center space-x-2">
              <Switch
                checked={config.performance_metrics?.includes(metric) || false}
                onCheckedChange={(checked) => {
                  const metrics = config.performance_metrics || [];
                  const newMetrics = checked 
                    ? [...metrics, metric]
                    : metrics.filter((m: string) => m !== metric);
                  handleConfigChange('performance_metrics', newMetrics);
                }}
              />
              <Label className="text-sm">{metric.replace('_', ' ')}</Label>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="routing_algorithm">라우팅 알고리즘</Label>
          <Select
            value={config.routing_algorithm || 'weighted_round_robin'}
            onValueChange={(value) => handleConfigChange('routing_algorithm', value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="round_robin">라운드 로빈</SelectItem>
              <SelectItem value="weighted_round_robin">가중 라운드 로빈</SelectItem>
              <SelectItem value="least_connections">최소 연결</SelectItem>
              <SelectItem value="performance_based">성능 기반</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="routing_update_interval">업데이트 간격 (ms)</Label>
          <Input
            type="number"
            value={config.routing_update_interval || 5000}
            onChange={(e) => handleConfigChange('routing_update_interval', parseInt(e.target.value))}
            min={1000}
            max={60000}
          />
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <Switch
            checked={config.circuit_breaker_enabled || true}
            onCheckedChange={(checked) => handleConfigChange('circuit_breaker_enabled', checked)}
          />
          <Label>회로 차단기 활성화</Label>
        </div>

        {config.circuit_breaker_enabled && (
          <div className="grid grid-cols-2 gap-4 ml-6">
            <div className="space-y-2">
              <Label htmlFor="failure_threshold">실패 임계값</Label>
              <Slider
                value={[config.failure_threshold || 0.5]}
                onValueChange={([value]) => handleConfigChange('failure_threshold', value)}
                min={0.1}
                max={1.0}
                step={0.1}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="recovery_timeout">복구 타임아웃 (ms)</Label>
              <Input
                type="number"
                value={config.recovery_timeout || 30000}
                onChange={(e) => handleConfigChange('recovery_timeout', parseInt(e.target.value))}
                min={5000}
                max={300000}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderSwarmConfig = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="swarm_size">군집 크기</Label>
          <Input
            type="number"
            value={config.swarm_size || 10}
            onChange={(e) => handleConfigChange('swarm_size', parseInt(e.target.value))}
            min={3}
            max={100}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="max_iterations">최대 반복 수</Label>
          <Input
            type="number"
            value={config.max_iterations || 50}
            onChange={(e) => handleConfigChange('max_iterations', parseInt(e.target.value))}
            min={10}
            max={1000}
          />
        </div>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="inertia_weight">관성 가중치: {config.inertia_weight || 0.7}</Label>
          <Slider
            value={[config.inertia_weight || 0.7]}
            onValueChange={([value]) => handleConfigChange('inertia_weight', value)}
            min={0.1}
            max={1.0}
            step={0.1}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="cognitive_weight">인지 가중치: {config.cognitive_weight || 1.4}</Label>
          <Slider
            value={[config.cognitive_weight || 1.4]}
            onValueChange={([value]) => handleConfigChange('cognitive_weight', value)}
            min={0.1}
            max={3.0}
            step={0.1}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="social_weight">사회 가중치: {config.social_weight || 1.4}</Label>
          <Slider
            value={[config.social_weight || 1.4]}
            onValueChange={([value]) => handleConfigChange('social_weight', value)}
            min={0.1}
            max={3.0}
            step={0.1}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="convergence_threshold">수렴 임계값: {config.convergence_threshold || 0.01}</Label>
          <Slider
            value={[config.convergence_threshold || 0.01]}
            onValueChange={([value]) => handleConfigChange('convergence_threshold', value)}
            min={0.001}
            max={0.1}
            step={0.001}
          />
        </div>
      </div>
    </div>
  );

  const renderEventDrivenConfig = () => (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label>이벤트 타입</Label>
        <div className="grid grid-cols-2 gap-2">
          {[
            'agent_completed', 'agent_failed', 'threshold_reached', 
            'time_elapsed', 'data_available', 'user_input', 
            'external_trigger', 'condition_met'
          ].map((eventType) => (
            <div key={eventType} className="flex items-center space-x-2">
              <Switch
                checked={config.event_types?.includes(eventType) || false}
                onCheckedChange={(checked) => {
                  const types = config.event_types || [];
                  const newTypes = checked 
                    ? [...types, eventType]
                    : types.filter((t: string) => t !== eventType);
                  handleConfigChange('event_types', newTypes);
                }}
              />
              <Label className="text-sm">{eventType.replace('_', ' ')}</Label>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="event_timeout">이벤트 타임아웃 (ms)</Label>
          <Input
            type="number"
            value={config.event_timeout || 300000}
            onChange={(e) => handleConfigChange('event_timeout', parseInt(e.target.value))}
            min={1000}
            max={3600000}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="max_concurrent_events">최대 동시 이벤트</Label>
          <Input
            type="number"
            value={config.max_concurrent_events || 50}
            onChange={(e) => handleConfigChange('max_concurrent_events', parseInt(e.target.value))}
            min={1}
            max={1000}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="event_processing_delay">처리 지연 (ms)</Label>
          <Input
            type="number"
            value={config.event_processing_delay || 100}
            onChange={(e) => handleConfigChange('event_processing_delay', parseInt(e.target.value))}
            min={10}
            max={5000}
          />
        </div>

        <div className="flex items-center space-x-2">
          <Switch
            checked={config.enable_event_history || true}
            onCheckedChange={(checked) => handleConfigChange('enable_event_history', checked)}
          />
          <Label>이벤트 히스토리 활성화</Label>
        </div>
      </div>
    </div>
  );

  const renderReflectionConfig = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="reflection_interval">성찰 간격 (초)</Label>
          <Input
            type="number"
            value={config.reflection_interval || 60}
            onChange={(e) => handleConfigChange('reflection_interval', parseInt(e.target.value))}
            min={10}
            max={3600}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="min_data_points">최소 데이터 포인트</Label>
          <Input
            type="number"
            value={config.min_data_points || 5}
            onChange={(e) => handleConfigChange('min_data_points', parseInt(e.target.value))}
            min={3}
            max={100}
          />
        </div>
      </div>

      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="improvement_threshold">개선 임계값: {config.improvement_threshold || 0.1}</Label>
          <Slider
            value={[config.improvement_threshold || 0.1]}
            onValueChange={([value]) => handleConfigChange('improvement_threshold', value)}
            min={0.01}
            max={0.5}
            step={0.01}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="learning_decay">학습 감쇠: {config.learning_decay || 0.95}</Label>
          <Slider
            value={[config.learning_decay || 0.95]}
            onValueChange={([value]) => handleConfigChange('learning_decay', value)}
            min={0.8}
            max={0.99}
            step={0.01}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="adaptation_sensitivity">적응 민감도: {config.adaptation_sensitivity || 0.15}</Label>
          <Slider
            value={[config.adaptation_sensitivity || 0.15]}
            onValueChange={([value]) => handleConfigChange('adaptation_sensitivity', value)}
            min={0.05}
            max={0.5}
            step={0.05}
          />
        </div>
      </div>
    </div>
  );

  const renderGenericConfig = () => (
    <div className="space-y-4">
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          이 패턴에 대한 특화된 설정 UI가 아직 구현되지 않았습니다.
        </AlertDescription>
      </Alert>
      
      <div className="space-y-2">
        <Label htmlFor="generic_config">설정 (JSON)</Label>
        <Textarea
          value={JSON.stringify(config, null, 2)}
          onChange={(e) => {
            try {
              const newConfig = JSON.parse(e.target.value);
              onConfigChange(newConfig);
            } catch (error) {
              // Invalid JSON, ignore
            }
          }}
          rows={10}
          className="font-mono text-sm"
        />
      </div>
    </div>
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-lg" style={{ backgroundColor: `${patternInfo?.color}20` }}>
              {patternType === 'consensus_building' && <MessageSquare className="h-5 w-5" style={{ color: patternInfo?.color }} />}
              {patternType === 'dynamic_routing' && <Route className="h-5 w-5" style={{ color: patternInfo?.color }} />}
              {patternType === 'swarm_intelligence' && <Hexagon className="h-5 w-5" style={{ color: patternInfo?.color }} />}
              {patternType === 'event_driven' && <Bell className="h-5 w-5" style={{ color: patternInfo?.color }} />}
              {patternType === 'reflection' && <RefreshCw className="h-5 w-5" style={{ color: patternInfo?.color }} />}
            </div>
            <div>
              <CardTitle>{patternInfo?.name} 설정</CardTitle>
              <CardDescription>{patternInfo?.description}</CardDescription>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" onClick={resetConfig}>
              <RotateCcw className="h-4 w-4 mr-1" />
              초기화
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">기본 설정</TabsTrigger>
            <TabsTrigger value="advanced">고급 설정</TabsTrigger>
            <TabsTrigger value="validation">검증 결과</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="mt-6">
            {renderPatternSpecificConfig()}
          </TabsContent>

          <TabsContent value="advanced" className="mt-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="custom_parameters">사용자 정의 매개변수</Label>
                <Textarea
                  placeholder="추가 설정을 JSON 형태로 입력하세요..."
                  value={JSON.stringify(config.custom_parameters || {}, null, 2)}
                  onChange={(e) => {
                    try {
                      const customParams = JSON.parse(e.target.value);
                      handleConfigChange('custom_parameters', customParams);
                    } catch (error) {
                      // Invalid JSON, ignore
                    }
                  }}
                  rows={8}
                  className="font-mono text-sm"
                />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="validation" className="mt-6">
            <div className="space-y-4">
              {validation.errors.length > 0 && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="font-medium mb-2">오류</div>
                    <ul className="list-disc list-inside space-y-1">
                      {validation.errors.map((error, index) => (
                        <li key={index} className="text-sm">{error}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {validation.warnings.length > 0 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>
                    <div className="font-medium mb-2">경고</div>
                    <ul className="list-disc list-inside space-y-1">
                      {validation.warnings.map((warning, index) => (
                        <li key={index} className="text-sm">{warning}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {validation.suggestions.length > 0 && (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    <div className="font-medium mb-2">제안</div>
                    <ul className="list-disc list-inside space-y-1">
                      {validation.suggestions.map((suggestion, index) => (
                        <li key={index} className="text-sm">{suggestion}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {validation.isValid && validation.errors.length === 0 && validation.warnings.length === 0 && (
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    설정이 유효합니다. 모든 검증을 통과했습니다.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};