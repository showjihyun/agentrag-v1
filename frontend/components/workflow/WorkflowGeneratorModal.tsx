'use client';

import React, { useState } from 'react';
import { X, Sparkles, Loader2, Lightbulb, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface WorkflowGeneratorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (workflow: any) => void;
}

const EXAMPLE_PROMPTS = [
  {
    title: '고객 지원 자동화',
    description: '고객이 이메일을 보내면 이슈를 분류하고 AI로 답변을 생성해서 회신',
    category: 'customer-service',
  },
  {
    title: 'Slack 알림',
    description: 'Webhook이 트리거되면 #alerts 채널에 Slack 메시지 전송',
    category: 'notifications',
  },
  {
    title: '문서 분석',
    description: 'PDF를 업로드하면 텍스트를 추출하고 AI로 요약해서 팀에게 이메일 전송',
    category: 'document-processing',
  },
  {
    title: '승인 워크플로우',
    description: '구매 요청이 들어오면 금액이 $1000 이상이면 관리자 승인 필요, 그 후 결제 처리',
    category: 'approval',
  },
];

export function WorkflowGeneratorModal({
  isOpen,
  onClose,
  onGenerate,
}: WorkflowGeneratorModalProps) {
  const [description, setDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedWorkflow, setGeneratedWorkflow] = useState<any>(null);
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const { toast } = useToast();

  if (!isOpen) return null;

  const handleGenerate = async () => {
    if (!description.trim()) {
      toast({
        title: '❌ 설명 필요',
        description: '워크플로우 설명을 입력해주세요',
        duration: 2000,
      });
      return;
    }

    setIsGenerating(true);

    try {
      const response = await fetch('/api/workflow-generator/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate workflow');
      }

      const data = await response.json();
      setGeneratedWorkflow(data.workflow);
      setSuggestions(data.suggestions || []);

      toast({
        title: '✨ 워크플로우 생성 완료',
        description: `"${data.workflow.name}" 워크플로우가 생성되었습니다`,
        duration: 3000,
      });
    } catch (error) {
      console.error('Failed to generate workflow:', error);
      toast({
        title: '❌ 생성 실패',
        description: '워크플로우 생성 중 오류가 발생했습니다',
        duration: 3000,
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleApply = () => {
    if (generatedWorkflow) {
      onGenerate(generatedWorkflow);
      onClose();
      toast({
        title: '✅ 워크플로우 적용됨',
        description: '생성된 워크플로우가 캔버스에 적용되었습니다',
        duration: 2000,
      });
    }
  };

  const handleUseExample = (example: typeof EXAMPLE_PROMPTS[0]) => {
    setDescription(example.description);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                AI 워크플로우 생성기
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                자연어로 설명하면 AI가 워크플로우를 자동으로 생성합니다
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Input Section */}
          {!generatedWorkflow && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  워크플로우 설명
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="예: 고객이 문의를 제출하면 감정을 분석하고, 긍정적이면 자동 답변, 부정적이면 담당자에게 알림"
                  className="w-full h-32 p-4 border border-gray-300 dark:border-gray-600 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white"
                  disabled={isGenerating}
                />
              </div>

              {/* Examples */}
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="w-4 h-4 text-yellow-500" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    예시 프롬프트
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {EXAMPLE_PROMPTS.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => handleUseExample(example)}
                      className="p-3 text-left border border-gray-200 dark:border-gray-700 rounded-lg hover:border-purple-500 hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-all group"
                      disabled={isGenerating}
                    >
                      <div className="font-medium text-sm text-gray-900 dark:text-white mb-1 group-hover:text-purple-600 dark:group-hover:text-purple-400">
                        {example.title}
                      </div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                        {example.description}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* Generated Workflow Preview */}
          {generatedWorkflow && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                    {generatedWorkflow.name}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {generatedWorkflow.description}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setGeneratedWorkflow(null);
                    setSuggestions([]);
                  }}
                >
                  다시 생성
                </Button>
              </div>

              {/* Workflow Stats */}
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {generatedWorkflow.nodes?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">노드</div>
                </div>
                <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {generatedWorkflow.edges?.length || 0}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">연결</div>
                </div>
                <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {new Set(generatedWorkflow.nodes?.map((n: any) => n.type) || []).size}
                  </div>
                  <div className="text-sm text-gray-600 dark:text-gray-400">노드 타입</div>
                </div>
              </div>

              {/* Node List */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  포함된 노드
                </h4>
                <div className="space-y-2">
                  {generatedWorkflow.nodes?.map((node: any, index: number) => (
                    <div
                      key={index}
                      className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                    >
                      <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white text-sm font-bold">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="font-medium text-sm text-gray-900 dark:text-white">
                          {node.data?.label || node.data?.name || node.type}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">
                          {node.type}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Suggestions */}
              {suggestions.length > 0 && (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Zap className="w-4 h-4 text-yellow-500" />
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      개선 제안
                    </h4>
                  </div>
                  <div className="space-y-2">
                    {suggestions.map((suggestion, index) => (
                      <div
                        key={index}
                        className="p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg"
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-yellow-600 dark:text-yellow-400 text-xs font-medium uppercase">
                            {suggestion.severity}
                          </span>
                          <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                            {suggestion.message}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <Button variant="ghost" onClick={onClose} disabled={isGenerating}>
            취소
          </Button>
          <div className="flex gap-2">
            {!generatedWorkflow ? (
              <Button
                onClick={handleGenerate}
                disabled={isGenerating || !description.trim()}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    생성 중...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    워크플로우 생성
                  </>
                )}
              </Button>
            ) : (
              <Button
                onClick={handleApply}
                className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600"
              >
                워크플로우 적용
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
