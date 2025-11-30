'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Library,
  Search,
  Star,
  Download,
  Upload,
  Code,
  Users,
  Clock,
  ChevronRight,
  Loader2,
  Heart,
  Copy,
  Check,
} from 'lucide-react';
import { toast } from 'sonner';

interface CodeSnippet {
  id: string;
  name: string;
  description: string;
  code: string;
  language: string;
  category: string;
  author: string;
  rating: number;
  uses: number;
  createdAt: string;
  tags: string[];
}

interface CodeLibraryProps {
  language: string;
  onInsertCode: (code: string) => void;
}

// 샘플 코드 라이브러리
const SAMPLE_SNIPPETS: CodeSnippet[] = [
  {
    id: '1',
    name: 'data_utils',
    description: 'JSON 데이터 변환 및 필터링 유틸리티',
    code: `def filter_data(data, key, value):
    """데이터 필터링"""
    return [item for item in data if item.get(key) == value]

def transform_keys(data, mapping):
    """키 이름 변환"""
    return {mapping.get(k, k): v for k, v in data.items()}`,
    language: 'python',
    category: 'Data Processing',
    author: 'system',
    rating: 4.8,
    uses: 234,
    createdAt: '2024-01-15',
    tags: ['data', 'filter', 'transform'],
  },
  {
    id: '2',
    name: 'api_helpers',
    description: 'API 호출 및 에러 처리 헬퍼',
    code: `import requests

def safe_api_call(url, method="GET", **kwargs):
    """안전한 API 호출"""
    try:
        response = requests.request(method, url, timeout=30, **kwargs)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except Exception as e:
        return {"success": False, "error": str(e)}`,
    language: 'python',
    category: 'API Integration',
    author: 'system',
    rating: 4.6,
    uses: 189,
    createdAt: '2024-01-20',
    tags: ['api', 'http', 'requests'],
  },
  {
    id: '3',
    name: 'validation',
    description: '데이터 유효성 검사 함수',
    code: `def validate_email(email):
    """이메일 형식 검증"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_required(data, fields):
    """필수 필드 검증"""
    missing = [f for f in fields if f not in data or not data[f]]
    return {"valid": len(missing) == 0, "missing": missing}`,
    language: 'python',
    category: 'Utilities',
    author: 'system',
    rating: 4.5,
    uses: 156,
    createdAt: '2024-02-01',
    tags: ['validation', 'email', 'required'],
  },
];

const CATEGORIES = ['All', 'Data Processing', 'API Integration', 'Utilities', 'File Handling'];

export default function CodeLibrary({ language, onInsertCode }: CodeLibraryProps) {
  const [snippets, setSnippets] = useState<CodeSnippet[]>(SAMPLE_SNIPPETS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // 필터링된 스니펫
  const filteredSnippets = snippets.filter(snippet => {
    const matchesSearch = searchQuery === '' ||
      snippet.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      snippet.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      snippet.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesCategory = selectedCategory === 'All' || snippet.category === selectedCategory;
    const matchesLanguage = snippet.language === language;
    
    return matchesSearch && matchesCategory && matchesLanguage;
  });

  // 코드 삽입
  const insertCode = (snippet: CodeSnippet) => {
    onInsertCode(snippet.code);
    toast.success(`${snippet.name} 코드가 삽입되었습니다.`);
  };

  // 코드 복사
  const copyCode = (snippet: CodeSnippet) => {
    navigator.clipboard.writeText(snippet.code);
    setCopiedId(snippet.id);
    setTimeout(() => setCopiedId(null), 2000);
    toast.success('코드가 복사되었습니다.');
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-indigo-50 to-violet-50 dark:from-indigo-950/30 dark:to-violet-950/30 rounded-lg border border-indigo-200 dark:border-indigo-800">
        <Library className="h-5 w-5 text-indigo-600" />
        <span className="font-medium flex-1">Code Library</span>
        <Badge variant="secondary" className="text-xs">Phase 4</Badge>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="코드 검색..."
          className="pl-9 h-9"
        />
      </div>

      {/* Categories */}
      <div className="flex gap-1 flex-wrap">
        {CATEGORIES.map((cat) => (
          <Button
            key={cat}
            size="sm"
            variant={selectedCategory === cat ? 'default' : 'ghost'}
            className="h-7 text-xs"
            onClick={() => setSelectedCategory(cat)}
          >
            {cat}
          </Button>
        ))}
      </div>

      {/* Snippets List */}
      <ScrollArea className="h-64">
        <div className="space-y-2">
          {filteredSnippets.map((snippet) => (
            <div
              key={snippet.id}
              className="border rounded-lg overflow-hidden"
            >
              {/* Snippet Header */}
              <div
                className="flex items-center gap-2 p-3 cursor-pointer hover:bg-muted/50"
                onClick={() => setExpandedId(expandedId === snippet.id ? null : snippet.id)}
              >
                <Code className="h-4 w-4 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{snippet.name}</span>
                    <Badge variant="outline" className="text-xs">{snippet.category}</Badge>
                  </div>
                  <p className="text-xs text-muted-foreground truncate">{snippet.description}</p>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Star className="h-3 w-3 text-yellow-500" />
                    {snippet.rating}
                  </span>
                  <span className="flex items-center gap-1">
                    <Download className="h-3 w-3" />
                    {snippet.uses}
                  </span>
                </div>
                <ChevronRight className={`h-4 w-4 transition-transform ${expandedId === snippet.id ? 'rotate-90' : ''}`} />
              </div>

              {/* Expanded Content */}
              {expandedId === snippet.id && (
                <div className="border-t p-3 bg-muted/30">
                  <pre className="text-xs bg-black/10 dark:bg-white/10 p-2 rounded overflow-auto max-h-40 font-mono mb-3">
                    {snippet.code}
                  </pre>
                  <div className="flex items-center gap-2 mb-2">
                    {snippet.tags.map((tag) => (
                      <Badge key={tag} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => insertCode(snippet)} className="gap-1">
                      <Download className="h-3 w-3" />
                      삽입
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => copyCode(snippet)} className="gap-1">
                      {copiedId === snippet.id ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                      복사
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}

          {filteredSnippets.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Library className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">검색 결과가 없습니다.</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Publish Button */}
      <Button variant="outline" size="sm" className="w-full gap-2">
        <Upload className="h-4 w-4" />
        내 코드 공유하기
      </Button>
    </div>
  );
}
