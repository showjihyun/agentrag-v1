'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Sparkles, 
  Wand2,
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Lightbulb,
  Clock,
  Users,
  Zap,
  ArrowRight,
  Copy,
  Download,
  Eye,
  Settings,
  RefreshCw,
  BookOpen,
  Target,
  TrendingUp
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';

interface GeneratedWorkflow {
  success: boolean;
  workflow?: {
    id: string;
    name: string;
    description: string;
    nodes: any[];
    connections: any[];
    metadata: any;
  };
  analysis?: {
    complexity: string;
    estimated_execution_time: string;
    detected_nodes: string[];
  };
  generation_time_seconds: number;
  suggestions?: string[];
  error?: string;
}

interface NaturalLanguageGeneratorProps {
  onWorkflowGenerated?: (workflow: any) => void;
  onImportToCanvas?: (workflow: any) => void;
  className?: string;
}

export default function NaturalLanguageGenerator({
  onWorkflowGenerated,
  onImportToCanvas,
  className = ""
}: NaturalLanguageGeneratorProps) {
  const { toast } = useToast();
  
  // 상태 관리
  const [description, setDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedWorkflow, setGeneratedWorkflow] = useState<GeneratedWorkflow | null>(null);
  const [activeTab, setActiveTab] = useState('generator');
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // 고급 설정
  const [language, setLanguage] = useState('ko');
  const [complexityPreference, setComplexityPreference] = useState('auto');
  
  // 예시 및 템플릿
  const [examples, setExamples] = useState<any[]>([]);
  const [templates, setTemplates] = useState<any>({});
  const [loadingExamples, setLoadingExamples] = useState(false);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 예시 워크플로우 설명들
  const quickExamples = [
    {
      title: "고객 서비스 자동화",
      description: "고객 문의를 받아서 감정 분석하고 부정적이면 매니저에게 슬랙으로 알려줘",
      category: "고객 서비스",
      complexity: "simple",
      icon: "🎧"
    },
    {
      title: "일일 보고서 자동화", 
      description: "매일 오전 9시에 데이터베이스에서 신규 주문을 조회해서 요약 보고서를 만들어 이메일로 발송",
      category: "데이터 처리",
      complexity: "medium",
      icon: "📊"
    },
    {
      title: "콘텐츠 최적화",
      description: "블로그 포스트를 받아서 SEO 최적화 제안을 하고 소셜미디어용 요약본을 만들어줘",
      category: "콘텐츠 관리", 
      complexity: "medium",
      icon: "✍️"
    },
    {
      title: "회의 후속 조치",
      description: "회의록을 받아서 액션 아이템을 추출하고 담당자별로 슬랙 DM 발송",
      category: "업무 자동화",
      complexity: "simple", 
      icon: "📝"
    }
  ];

  // 컴포넌트 마운트 시 예시 로드
  useEffect(() => {
    loadExamples();
  }, []);

  // 예시 로드
  const loadExamples = useCallback(async () => {
    setLoadingExamples(true);
    try {
      const response = await fetch('/api/agent-builder/nl-generator/examples');
      if (response.ok) {
        const data = await response.json();
        setExamples(data.examples || []);
      }
    } catch (error) {
      console.error('Failed to load examples:', error);
    } finally {
      setLoadingExamples(false);
    }
  }, []);

  // 워크플로우 생성
  const handleGenerateWorkflow = useCallback(async () => {
    if (!description.trim()) {
      toast({
        title: '설명 필요',
        description: '워크플로우 설명을 입력해주세요.',
        variant: 'destructive'
      });
      return;
    }

    if (description.trim().length < 10) {
      toast({
        title: '설명이 너무 짧습니다',
        description: '최소 10자 이상의 구체적인 설명을 입력해주세요.',
        variant: 'destructive'
      });
      return;
    }

    setIsGenerating(true);
    setGeneratedWorkflow(null);

    try {
      const response = await fetch('/api/agent-builder/nl-generator/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          description: description.trim(),
          language,
          complexity_preference: complexityPreference,
          preferences: {
            include_error_handling: true,
            include_logging: true
          }
        })
      });
