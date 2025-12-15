'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Store,
  Download,
  Star,
  Users,
  MessageSquare,
  Sparkles,
  CheckCircle,
  Clock,
  TrendingUp,
  Filter,
  Search,
  ExternalLink,
  Share2,
  Heart,
  Eye,
  Package,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface MarketplaceItem {
  id: string;
  name: string;
  description: string;
  type: 'agentflow' | 'chatflow' | 'workflow' | 'tool' | 'template';
  category: string;
  rating: number;
  rating_count: number;
  install_count: number;
  author: {
    name: string;
    avatar?: string;
    verified?: boolean;
  };
  tags: string[];
  preview_image?: string;
  is_featured?: boolean;
  is_official?: boolean;
  price: 'free' | 'premium';
  created_at: string;
  updated_at: string;
}

const TYPE_ICONS = {
  agentflow: Users,
  chatflow: MessageSquare,
  workflow: Package,
  tool: Sparkles,
  template: Package,
};

const TYPE_COLORS = {
  agentflow: 'text-purple-500 bg-purple-50 dark:bg-purple-950',
  chatflow: 'text-blue-500 bg-blue-50 dark:bg-blue-950',
  workflow: 'text-green-500 bg-green-50 dark:bg-green-950',
  tool: 'text-orange-500 bg-orange-50 dark:bg-orange-950',
  template: 'text-pink-500 bg-pink-50 dark:bg-pink-950',
};

// Mock data for demonstration
const FEATURED_ITEMS: MarketplaceItem[] = [
  {
    id: 'featured-1',
    name: 'Customer Support Multi-Agent',
    description: '고객 문의를 자동으로 분류하고 적절한 에이전트에게 라우팅하는 멀티 에이전트 시스템',
    type: 'agentflow',
    category: 'customer-service',
    rating: 4.9,
    rating_count: 234,
    install_count: 1520,
    author: { name: 'AgenticRAG Team', verified: true },
    tags: ['customer-service', 'multi-agent', 'routing'],
    is_featured: true,
    is_official: true,
    price: 'free',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'featured-2',
    name: 'RAG Document Q&A Chatbot',
    description: '문서 기반 질의응답 챗봇. 지식베이스와 연동하여 정확한 답변 제공',
    type: 'chatflow',
    category: 'knowledge',
    rating: 4.8,
    rating_count: 189,
    install_count: 2340,
    author: { name: 'AgenticRAG Team', verified: true },
    tags: ['rag', 'chatbot', 'knowledge-base'],
    is_featured: true,
    is_official: true,
    price: 'free',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'featured-3',
    name: 'Data Pipeline Workflow',
    description: '데이터 수집, 변환, 분석을 자동화하는 워크플로우 템플릿',
    type: 'workflow',
    category: 'data-analysis',
    rating: 4.7,
    rating_count: 156,
    install_count: 890,
    author: { name: 'DataOps', verified: false },
    tags: ['data', 'etl', 'automation'],
    is_featured: true,
    price: 'free',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

interface MarketplaceIntegrationProps {
  onItemInstall?: (item: MarketplaceItem) => void;
  showHeader?: boolean;
  maxItems?: number;
  filterType?: string;
}

export function MarketplaceIntegration({
  onItemInstall,
  showHeader = true,
  maxItems,
  filterType,
}: MarketplaceIntegrationProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [items, setItems] = useState<MarketplaceItem[]>([]);
  const [filteredItems, setFilteredItems] = useState<MarketplaceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedType, setSelectedType] = useState(filterType || 'all');
  const [sortBy, setSortBy] = useState('popular');
  const [selectedItem, setSelectedItem] = useState<MarketplaceItem | null>(null);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [installing, setInstalling] = useState(false);

  useEffect(() => {
    loadMarketplaceItems();
  }, []);

  useEffect(() => {
    filterAndSortItems();
  }, [items, searchQuery, selectedCategory, selectedType, sortBy]);

  const loadMarketplaceItems = async () => {
    try {
      setLoading(true);
      // Use mock data for now - replace with actual API call
      setItems(FEATURED_ITEMS);
    } catch (error) {
      console.error('Failed to load marketplace items:', error);
      toast({
        title: '오류',
        description: '마켓플레이스 항목을 불러오는데 실패했습니다',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const filterAndSortItems = () => {
    let filtered = [...items];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (item) =>
          item.name.toLowerCase().includes(query) ||
          item.description?.toLowerCase().includes(query) ||
          item.tags?.some((tag) => tag.toLowerCase().includes(query))
      );
    }

    // Type filter
    if (selectedType !== 'all') {
      filtered = filtered.filter((item) => item.type === selectedType);
    }

    // Category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter((item) => item.category === selectedCategory);
    }

    // Sorting
    switch (sortBy) {
      case 'popular':
        filtered.sort((a, b) => (b.install_count || 0) - (a.install_count || 0));
        break;
      case 'rating':
        filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0));
        break;
      case 'recent':
        filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        break;
      case 'name':
        filtered.sort((a, b) => a.name.localeCompare(b.name));
        break;
    }

    // Apply max items limit
    if (maxItems) {
      filtered = filtered.slice(0, maxItems);
    }

    setFilteredItems(filtered);
  };

  const handleInstall = async (item: MarketplaceItem) => {
    try {
      setInstalling(true);
      
      // Mock installation - replace with actual API call
      await new Promise((resolve) => setTimeout(resolve, 1500));

      toast({
        title: '설치 완료',
        description: `"${item.name}"이(가) 성공적으로 설치되었습니다`,
      });

      // Call callback if provided
      if (onItemInstall) {
        onItemInstall(item);
      } else {
        // Navigate to the appropriate page
        const routes = {
          agentflow: '/agent-builder/agentflows',
          chatflow: '/agent-builder/chatflows',
          workflow: '/agent-builder/workflows',
          tool: '/agent-builder/tools',
          template: '/agent-builder/templates',
        };
        router.push(routes[item.type]);
      }
    } catch (error) {
      toast({
        title: '오류',
        description: '설치에 실패했습니다',
        variant: 'destructive',
      });
    } finally {
      setInstalling(false);
      setDetailDialogOpen(false);
    }
  };

  const handleItemClick = (item: MarketplaceItem) => {
    setSelectedItem(item);
    setDetailDialogOpen(true);
  };

  const categories = [
    { value: 'all', label: '전체 카테고리' },
    { value: 'customer-service', label: '고객 서비스' },
    { value: 'knowledge', label: '지식 관리' },
    { value: 'data-analysis', label: '데이터 분석' },
    { value: 'automation', label: '자동화' },
    { value: 'development', label: '개발' },
    { value: 'research', label: '리서치' },
    { value: 'integration', label: '통합' },
  ];

  const types = [
    { value: 'all', label: '전체 유형' },
    { value: 'agentflow', label: 'Agentflow' },
    { value: 'chatflow', label: 'Chatflow' },
    { value: 'workflow', label: 'Workflow' },
    { value: 'tool', label: 'Tool' },
    { value: 'template', label: 'Template' },
  ];

  if (loading) {
    return (
      <div className="space-y-4">
        {showHeader && (
          <div className="flex items-center gap-2">
            <Store className="h-5 w-5 text-pink-500" />
            <h3 className="text-lg font-semibold">마켓플레이스</h3>
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2" />
              </CardHeader>
              <CardContent>
                <div className="h-3 bg-muted rounded w-full mb-2" />
                <div className="h-3 bg-muted rounded w-2/3" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {showHeader && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Store className="h-5 w-5 text-pink-500" />
            <h3 className="text-lg font-semibold">마켓플레이스</h3>
          </div>
          <Button variant="outline" onClick={() => router.push('/agent-builder/marketplace')}>
            <ExternalLink className="h-4 w-4 mr-2" />
            전체 보기
          </Button>
        </div>
      )}

      {/* Filters */}
      {!maxItems && (
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="이름, 설명, 태그로 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          
          {!filterType && (
            <Select value={selectedType} onValueChange={setSelectedType}>
              <SelectTrigger className="w-full md:w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {types.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}

          <Select value={selectedCategory} onValueChange={setSelectedCategory}>
            <SelectTrigger className="w-full md:w-[180px]">
              <Filter className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {categories.map((cat) => (
                <SelectItem key={cat.value} value={cat.value}>
                  {cat.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-full md:w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="popular">인기순</SelectItem>
              <SelectItem value="rating">평점순</SelectItem>
              <SelectItem value="recent">최신순</SelectItem>
              <SelectItem value="name">이름순</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredItems.map((item) => {
          const TypeIcon = TYPE_ICONS[item.type];
          return (
            <Card
              key={item.id}
              className="cursor-pointer hover:shadow-lg transition-all border-2 hover:border-primary"
              onClick={() => handleItemClick(item)}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className={`p-2 rounded-lg ${TYPE_COLORS[item.type]}`}>
                    <TypeIcon className="h-5 w-5" />
                  </div>
                  <div className="flex items-center gap-1">
                    {item.is_official && (
                      <Badge variant="default" className="bg-blue-500">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        공식
                      </Badge>
                    )}
                    {item.is_featured && (
                      <Badge variant="secondary">
                        <Star className="h-3 w-3 mr-1 fill-current" />
                        추천
                      </Badge>
                    )}
                  </div>
                </div>
                <CardTitle className="mt-2">{item.name}</CardTitle>
                <CardDescription className="line-clamp-2">{item.description}</CardDescription>
              </CardHeader>
              
              <CardContent>
                <div className="flex items-center gap-4 text-sm mb-3">
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    <span className="font-medium">{item.rating.toFixed(1)}</span>
                    <span className="text-muted-foreground">({item.rating_count})</span>
                  </div>
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Download className="h-4 w-4" />
                    <span>{item.install_count.toLocaleString()}</span>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 mb-3">
                  <Avatar className="h-6 w-6">
                    <AvatarImage src={item.author.avatar} />
                    <AvatarFallback>{item.author.name[0]}</AvatarFallback>
                  </Avatar>
                  <span className="text-sm text-muted-foreground">{item.author.name}</span>
                  {item.author.verified && (
                    <CheckCircle className="h-4 w-4 text-blue-500" />
                  )}
                </div>

                <div className="flex flex-wrap gap-1">
                  {item.tags.slice(0, 3).map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                  {item.tags.length > 3 && (
                    <Badge variant="outline" className="text-xs">
                      +{item.tags.length - 3}
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredItems.length === 0 && (
        <Card className="p-12">
          <div className="text-center">
            <Package className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">항목을 찾을 수 없습니다</h3>
            <p className="text-muted-foreground">다른 검색어나 필터를 시도해보세요</p>
          </div>
        </Card>
      )}

      {/* Detail Dialog */}
      <Dialog open={detailDialogOpen} onOpenChange={setDetailDialogOpen}>
        <DialogContent className="max-w-2xl">
          {selectedItem && (
            <>
              <DialogHeader>
                <div className="flex items-start gap-4">
                  <div className={`p-3 rounded-lg ${TYPE_COLORS[selectedItem.type]}`}>
                    {React.createElement(TYPE_ICONS[selectedItem.type], { className: 'h-8 w-8' })}
                  </div>
                  <div className="flex-1">
                    <DialogTitle className="text-xl flex items-center gap-2">
                      {selectedItem.name}
                      {selectedItem.is_official && (
                        <Badge variant="default" className="bg-blue-500">
                          공식
                        </Badge>
                      )}
                    </DialogTitle>
                    <DialogDescription className="mt-1">
                      {selectedItem.description}
                    </DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {/* Stats */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <div className="flex items-center justify-center gap-1">
                      <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                      <span className="text-xl font-bold">{selectedItem.rating.toFixed(1)}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">{selectedItem.rating_count} 리뷰</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <div className="flex items-center justify-center gap-1">
                      <Download className="h-5 w-5 text-green-500" />
                      <span className="text-xl font-bold">{selectedItem.install_count.toLocaleString()}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">설치</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded-lg">
                    <div className="flex items-center justify-center gap-1">
                      <Clock className="h-5 w-5 text-blue-500" />
                      <span className="text-xl font-bold">
                        {new Date(selectedItem.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">최근 업데이트</p>
                  </div>
                </div>

                {/* Author */}
                <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                  <Avatar>
                    <AvatarImage src={selectedItem.author.avatar} />
                    <AvatarFallback>{selectedItem.author.name[0]}</AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="font-medium flex items-center gap-1">
                      {selectedItem.author.name}
                      {selectedItem.author.verified && (
                        <CheckCircle className="h-4 w-4 text-blue-500" />
                      )}
                    </p>
                    <p className="text-sm text-muted-foreground">제작자</p>
                  </div>
                </div>

                {/* Tags */}
                <div>
                  <p className="text-sm font-medium mb-2">태그</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedItem.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>

              <DialogFooter className="flex gap-2">
                <Button variant="outline" onClick={() => setDetailDialogOpen(false)}>
                  취소
                </Button>
                <Button variant="outline">
                  <Eye className="h-4 w-4 mr-2" />
                  미리보기
                </Button>
                <Button onClick={() => handleInstall(selectedItem)} disabled={installing}>
                  {installing ? (
                    <>
                      <Clock className="h-4 w-4 mr-2 animate-spin" />
                      설치 중...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      설치
                    </>
                  )}
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}