/**
 * Intelligent Block Suggestions Component
 * 
 * AI 기반 지능형 블록 추천 컴포넌트
 */
import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Lightbulb, 
  Plus, 
  X, 
  TrendingUp, 
  Clock, 
  Target,
  ChevronRight,
  Sparkles,
  Brain
} from 'lucide-react';
import { Node, Edge } from 'reactflow';
import { useAIAssistant, BlockSuggestion, WorkflowContext } from '@/hooks/useAIAssistant';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface IntelligentBlockSuggestionsProps {
  workflowContext: WorkflowContext;
  onAddBlock: (blockType: string, config?: any, position?: { x: number; y: number }) => void;
  onClose?: () => void;
  className?: string;
}

export const IntelligentBlockSuggestions: React.FC<IntelligentBlockSuggestionsProps> = ({
  workflowContext,
  onAddBlock,
  onClose,
  className = ''
}) => {
  const {
    isLoading,
    suggestions,
    suggestNextBlocks,
    analyzeWorkflowPattern,
    recordUserAction
  } = useAIAssistant({
    enabled: true,
    suggestionLimit: 5,
    autoSuggest: true
  });

  const [selectedSuggestion, setSelectedSuggestion] = useState<BlockSuggestion | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const [workflowAnalysis, setWorkflowAnalysis] = useState<any>(null);

  // 워크플로우 컨텍스트 변경 시 자동 추천
  useEffect(() => {
    if (workflowContext.blocks.length > 0) {
      suggestNextBlocks(workflowContext);
      
      // 워크플로우 패턴 분석
      const analysis = analyzeWorkflowPattern(workflowContext);
      setWorkflowAnalysis(analysis);
    }
  }, [workflowContext, suggestNextBlocks, analyzeWorkflowPattern]);

  // 블록 추가 처리
  const handleAddBlock = useCallback(async (suggestion: BlockSuggestion) => {
    // 블록 추가
    onAddBlock(
      suggestion.block_type,
      suggestion.configuration_suggestion,
      suggestion.position_suggestion
    );

    // 사용자 액션 기록
    await recordUserAction({
      type: 'suggestion_accepted',
      blockType: suggestion.block_type,
      suggestionId: suggestion.id,
      context: workflowContext
    });

    // 추천 목록에서 제거
    setSelectedSuggestion(null);
  }, [onAddBlock, recordUserAction, workflowContext]);

  // 추천 거부 처리
  const handleRejectSuggestion = useCallback(async (suggestion: BlockSuggestion) => {
    await recordUserAction({
      type: 'suggestion_rejected',
      suggestionId: suggestion.id,
      context: workflowContext
    });
  }, [recordUserAction, workflowContext]);

  // 신뢰도에 따른 색상
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-blue-600 bg-blue-100';
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-gray-600 bg-gray-100';
  };

  // 신뢰도 레벨
  const getConfidenceLevel = (confidence: number) => {
    if (confidence >= 0.8) return '높음';
    if (confidence >= 0.6) return '보통';
    if (confidence >= 0.4) return '낮음';
    return '매우 낮음';
  };

  if (suggestions.length === 0 && !isLoading) {
    return null;
  }

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 20 }}
        className={`${className}`}
      >
        <Card className="w-80 shadow-lg border-blue-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-1 bg-blue-100 rounded">
                  <Brain className="w-4 h-4 text-blue-600" />
                </div>
                <CardTitle className="text-sm">AI 추천</CardTitle>
                <Sparkles className="w-3 h-3 text-yellow-500" />
              </div>
              
              {onClose && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-6 w-6 p-0"
                >
                  <X className="w-3 h-3" />
                </Button>
              )}
            </div>
            
            {/* 워크플로우 분석 요약 */}
            {workflowAnalysis && (
              <div className="mt-2 p-2 bg-gray-50 rounded text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-gray-600">복잡도</span>
                  <Badge variant="outline" className="text-xs">
                    {workflowAnalysis.complexity.level}
                  </Badge>
                </div>
                <Progress 
                  value={workflowAnalysis.complexity.score} 
                  className="h-1"
                />
              </div>
            )}
          </CardHeader>

          <CardContent className="space-y-3">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full" />
                <span className="ml-2 text-sm text-gray-600">분석 중...</span>
              </div>
            ) : (
              <AnimatePresence>
                {suggestions.map((suggestion, index) => (
                  <motion.div
                    key={suggestion.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.1 }}
                    className="border rounded-lg p-3 hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedSuggestion(suggestion)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-sm font-medium">
                            {suggestion.display_name}
                          </h4>
                          <Badge 
                            className={`text-xs ${getConfidenceColor(suggestion.confidence)}`}
                          >
                            {getConfidenceLevel(suggestion.confidence)}
                          </Badge>
                        </div>
                        
                        <p className="text-xs text-gray-600 mb-2">
                          {suggestion.description}
                        </p>
                        
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Target className="w-3 h-3" />
                          <span>{suggestion.estimated_benefit}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-1 ml-2">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                setShowDetails(!showDetails);
                                setSelectedSuggestion(suggestion);
                              }}
                              className="h-6 w-6 p-0"
                            >
                              <Lightbulb className="w-3 h-3" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>추천 이유 보기</TooltipContent>
                        </Tooltip>
                        
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAddBlock(suggestion);
                              }}
                              className="h-6 w-6 p-0 text-green-600 hover:text-green-700"
                            >
                              <Plus className="w-3 h-3" />
                            </Button>
                          </TooltipTrigger>
                          <TooltipContent>블록 추가</TooltipContent>
                        </Tooltip>
                      </div>
                    </div>
                    
                    {/* 신뢰도 바 */}
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-gray-500">신뢰도</span>
                        <span className="text-gray-700">
                          {Math.round(suggestion.confidence * 100)}%
                        </span>
                      </div>
                      <Progress 
                        value={suggestion.confidence * 100} 
                        className="h-1"
                      />
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            )}

            {/* 상세 정보 패널 */}
            <AnimatePresence>
              {showDetails && selectedSuggestion && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="border-t pt-3 mt-3"
                >
                  <div className="space-y-2">
                    <h5 className="text-sm font-medium flex items-center gap-1">
                      <Lightbulb className="w-3 h-3" />
                      추천 이유
                    </h5>
                    
                    <p className="text-xs text-gray-600 bg-blue-50 p-2 rounded">
                      {selectedSuggestion.reasoning}
                    </p>
                    
                    {/* 연결 제안 */}
                    {selectedSuggestion.connection_suggestions && 
                     selectedSuggestion.connection_suggestions.length > 0 && (
                      <div>
                        <h6 className="text-xs font-medium text-gray-700 mb-1">
                          연결 제안
                        </h6>
                        <div className="space-y-1">
                          {selectedSuggestion.connection_suggestions.map((conn, idx) => (
                            <div key={idx} className="flex items-center gap-2 text-xs">
                              <ChevronRight className="w-3 h-3 text-gray-400" />
                              <span className="text-gray-600">
                                {conn.target} ({conn.type})
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    <div className="flex gap-2 pt-2">
                      <Button
                        size="sm"
                        onClick={() => handleAddBlock(selectedSuggestion)}
                        className="flex-1 h-7 text-xs"
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        추가
                      </Button>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          handleRejectSuggestion(selectedSuggestion);
                          setShowDetails(false);
                          setSelectedSuggestion(null);
                        }}
                        className="h-7 text-xs"
                      >
                        거부
                      </Button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* 패턴 기반 추천 */}
            {workflowAnalysis?.recommendations && workflowAnalysis.recommendations.length > 0 && (
              <div className="border-t pt-3">
                <h5 className="text-xs font-medium text-gray-700 mb-2 flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  패턴 기반 제안
                </h5>
                
                {workflowAnalysis.recommendations.slice(0, 2).map((rec: any, idx: number) => (
                  <div key={idx} className="text-xs p-2 bg-yellow-50 rounded mb-2">
                    <p className="font-medium text-yellow-800">{rec.title}</p>
                    <p className="text-yellow-700 mt-1">
                      신뢰도: {Math.round(rec.confidence * 100)}%
                    </p>
                  </div>
                ))}
              </div>
            )}

            {/* 학습 상태 */}
            <div className="text-xs text-gray-500 text-center pt-2 border-t">
              <div className="flex items-center justify-center gap-1">
                <Brain className="w-3 h-3" />
                <span>AI가 사용 패턴을 학습하여 추천을 개선합니다</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </TooltipProvider>
  );
};