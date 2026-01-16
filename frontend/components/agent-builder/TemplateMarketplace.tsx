'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Search,
  Filter,
  Star,
  Download,
  Upload,
  Users,
  TrendingUp,
  Clock,
  Eye,
  Heart,
  Share2,
  MoreVertical,
  Plus,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Crown,
  Award,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  orchestration_type: string;
  agents: Array<{
    id: string;
    name: string;
    role: string;
    agent_id?: string;
  }>;
  tags: string[];
  is_public: boolean;
  is_featured: boolean;
  is_verified: boolean;
  created_by: {
    id: string;
    name: string;
    avatar?: string;
    is_premium?: boolean;
  };
  created_at: string;
  updated_at: string;
  usage_count: number;
  rating: number;
  rating_count: number;
  preview_image?: string;
  complexity_level: 'beginner' | 'intermediate' | 'advanced';
  estimated_execution_time: number;
  cost_estimate: number;
}

const TEMPLATE_CATEGORIES = [
  { value: 'all', label: 'All', icon: '🌟' },
  { value: 'customer_service', label: 'Customer Service', icon: '🎧' },
  { value: 'content_creation', label: 'Content Creation', icon: '✍️' },
  { value: 'data_analysis', label: 'Data Analysis', icon: '📊' },
  { value: 'automation', label: 'Automation', icon: '🤖' },
  { value: 'research', label: 'Research', icon: '🔍' },
  { value: 'marketing', label: 'Marketing', icon: '📢' },
  { value: 'development', label: 'Development', icon: '💻' },
  { value: 'education', label: 'Education', icon: '🎓' },
];

const COMPLEXITY_COLORS = {
  beginner: 'bg-green-100 text-green-800',
  intermediate: 'bg-yellow-100 text-yellow-800',
  advanced: 'bg-red-100 text-red-800',
};

const COMPLEXITY_LABELS = {
  beginner: 'Beginner',
  intermediate: 'Intermediate',
  advanced: 'Advanced',
};

// Mock template data
const MOCK_TEMPLATES: AgentTemplate[] = [
  {
    id: '1',
    name: 'Customer Support Automation',
    description: 'Automated customer inquiry handling with intelligent routing, response generation, and escalation management',
    category: 'customer_service',
    orchestration_type: 'sequential',
    agents: [
      { id: 'a1', name: 'Inquiry Classifier', role: 'Categorizes customer inquiries by type and urgency', agent_id: 'classifier-001' },
      { id: 'a2', name: 'Response Generator', role: 'Generates contextual responses based on inquiry type', agent_id: 'responder-001' },
      { id: 'a3', name: 'Quality Checker', role: 'Reviews responses for accuracy and tone', agent_id: 'qa-001' },
    ],
    tags: ['customer-service', 'automation', 'support', 'chatbot'],
    is_public: true,
    is_featured: true,
    is_verified: true,
    created_by: { id: 'u1', name: 'Sarah Johnson', is_premium: true },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    usage_count: 1247,
    rating: 4.9,
    rating_count: 342,
    complexity_level: 'intermediate',
    estimated_execution_time: 45,
    cost_estimate: 0.0125,
  },
  {
    id: '2',
    name: 'Content Marketing Pipeline',
    description: 'End-to-end content creation from ideation to publication with SEO optimization and social media distribution',
    category: 'content_creation',
    orchestration_type: 'sequential',
    agents: [
      { id: 'b1', name: 'Topic Researcher', role: 'Identifies trending topics and keywords', agent_id: 'researcher-001' },
      { id: 'b2', name: 'Content Writer', role: 'Creates engaging, SEO-optimized content', agent_id: 'writer-001' },
      { id: 'b3', name: 'SEO Optimizer', role: 'Optimizes content for search engines', agent_id: 'seo-001' },
      { id: 'b4', name: 'Social Media Adapter', role: 'Adapts content for different platforms', agent_id: 'social-001' },
    ],
    tags: ['content', 'marketing', 'seo', 'social-media'],
    is_public: true,
    is_featured: true,
    is_verified: true,
    created_by: { id: 'u2', name: 'Michael Chen', is_premium: true },
    created_at: '2024-01-14T14:30:00Z',
    updated_at: '2024-01-14T14:30:00Z',
    usage_count: 892,
    rating: 4.8,
    rating_count: 256,
    complexity_level: 'advanced',
    estimated_execution_time: 120,
    cost_estimate: 0.0340,
  },
  {
    id: '3',
    name: 'Data Analysis & Reporting',
    description: 'Automated data collection, analysis, visualization, and report generation with actionable insights',
    category: 'data_analysis',
    orchestration_type: 'parallel',
    agents: [
      { id: 'c1', name: 'Data Collector', role: 'Gathers data from multiple sources', agent_id: 'collector-001' },
      { id: 'c2', name: 'Statistical Analyzer', role: 'Performs statistical analysis and trend detection', agent_id: 'analyzer-001' },
      { id: 'c3', name: 'Visualization Creator', role: 'Creates charts and visual representations', agent_id: 'viz-001' },
      { id: 'c4', name: 'Report Generator', role: 'Compiles findings into comprehensive reports', agent_id: 'reporter-001' },
    ],
    tags: ['data', 'analytics', 'reporting', 'insights'],
    is_public: true,
    is_featured: false,
    is_verified: true,
    created_by: { id: 'u3', name: 'Emily Rodriguez', is_premium: false },
    created_at: '2024-01-13T09:15:00Z',
    updated_at: '2024-01-13T09:15:00Z',
    usage_count: 654,
    rating: 4.7,
    rating_count: 189,
    complexity_level: 'advanced',
    estimated_execution_time: 180,
    cost_estimate: 0.0450,
  },
  {
    id: '4',
    name: 'Email Campaign Manager',
    description: 'Automated email marketing campaign creation, personalization, and performance tracking',
    category: 'marketing',
    orchestration_type: 'sequential',
    agents: [
      { id: 'd1', name: 'Audience Segmenter', role: 'Segments audience based on behavior and demographics', agent_id: 'segment-001' },
      { id: 'd2', name: 'Email Composer', role: 'Creates personalized email content', agent_id: 'composer-001' },
      { id: 'd3', name: 'A/B Test Manager', role: 'Manages A/B testing and optimization', agent_id: 'abtest-001' },
    ],
    tags: ['email', 'marketing', 'automation', 'personalization'],
    is_public: true,
    is_featured: false,
    is_verified: true,
    created_by: { id: 'u4', name: 'David Kim', is_premium: true },
    created_at: '2024-01-12T16:45:00Z',
    updated_at: '2024-01-12T16:45:00Z',
    usage_count: 523,
    rating: 4.6,
    rating_count: 145,
    complexity_level: 'intermediate',
    estimated_execution_time: 60,
    cost_estimate: 0.0180,
  },
  {
    id: '5',
    name: 'Code Review Assistant',
    description: 'Automated code review with security scanning, best practices checking, and improvement suggestions',
    category: 'development',
    orchestration_type: 'parallel',
    agents: [
      { id: 'e1', name: 'Security Scanner', role: 'Identifies security vulnerabilities', agent_id: 'security-001' },
      { id: 'e2', name: 'Code Quality Checker', role: 'Checks code quality and best practices', agent_id: 'quality-001' },
      { id: 'e3', name: 'Performance Analyzer', role: 'Analyzes performance bottlenecks', agent_id: 'perf-001' },
      { id: 'e4', name: 'Documentation Reviewer', role: 'Reviews and suggests documentation improvements', agent_id: 'docs-001' },
    ],
    tags: ['development', 'code-review', 'security', 'quality'],
    is_public: true,
    is_featured: false,
    is_verified: true,
    created_by: { id: 'u5', name: 'Alex Thompson', is_premium: false },
    created_at: '2024-01-11T11:20:00Z',
    updated_at: '2024-01-11T11:20:00Z',
    usage_count: 789,
    rating: 4.8,
    rating_count: 234,
    complexity_level: 'advanced',
    estimated_execution_time: 90,
    cost_estimate: 0.0280,
  },
  {
    id: '6',
    name: 'Research Paper Summarizer',
    description: 'Automated academic paper analysis with key findings extraction, citation management, and literature review',
    category: 'research',
    orchestration_type: 'sequential',
    agents: [
      { id: 'f1', name: 'Paper Analyzer', role: 'Analyzes paper structure and content', agent_id: 'analyzer-002' },
      { id: 'f2', name: 'Key Findings Extractor', role: 'Extracts main findings and contributions', agent_id: 'extractor-001' },
      { id: 'f3', name: 'Citation Manager', role: 'Manages citations and references', agent_id: 'citation-001' },
    ],
    tags: ['research', 'academic', 'summarization', 'literature'],
    is_public: true,
    is_featured: false,
    is_verified: false,
    created_by: { id: 'u6', name: 'Dr. Lisa Wang', is_premium: false },
    created_at: '2024-01-10T13:00:00Z',
    updated_at: '2024-01-10T13:00:00Z',
    usage_count: 412,
    rating: 4.5,
    rating_count: 98,
    complexity_level: 'intermediate',
    estimated_execution_time: 75,
    cost_estimate: 0.0220,
  },
  {
    id: '7',
    name: 'Social Media Manager',
    description: 'Multi-platform social media content creation, scheduling, and engagement tracking',
    category: 'marketing',
    orchestration_type: 'parallel',
    agents: [
      { id: 'g1', name: 'Content Creator', role: 'Creates platform-specific content', agent_id: 'creator-002' },
      { id: 'g2', name: 'Hashtag Optimizer', role: 'Optimizes hashtags for reach', agent_id: 'hashtag-001' },
      { id: 'g3', name: 'Engagement Tracker', role: 'Tracks and analyzes engagement metrics', agent_id: 'tracker-001' },
    ],
    tags: ['social-media', 'marketing', 'engagement', 'content'],
    is_public: true,
    is_featured: false,
    is_verified: true,
    created_by: { id: 'u7', name: 'Jessica Martinez', is_premium: true },
    created_at: '2024-01-09T15:30:00Z',
    updated_at: '2024-01-09T15:30:00Z',
    usage_count: 967,
    rating: 4.7,
    rating_count: 287,
    complexity_level: 'beginner',
    estimated_execution_time: 30,
    cost_estimate: 0.0095,
  },
  {
    id: '8',
    name: 'E-Learning Course Builder',
    description: 'Automated course content creation with quizzes, assessments, and personalized learning paths',
    category: 'education',
    orchestration_type: 'sequential',
    agents: [
      { id: 'h1', name: 'Curriculum Designer', role: 'Designs course structure and learning objectives', agent_id: 'curriculum-001' },
      { id: 'h2', name: 'Content Developer', role: 'Creates educational content and materials', agent_id: 'developer-001' },
      { id: 'h3', name: 'Assessment Creator', role: 'Creates quizzes and assessments', agent_id: 'assessment-001' },
      { id: 'h4', name: 'Learning Path Optimizer', role: 'Personalizes learning paths for students', agent_id: 'optimizer-001' },
    ],
    tags: ['education', 'e-learning', 'course', 'assessment'],
    is_public: true,
    is_featured: false,
    is_verified: true,
    created_by: { id: 'u8', name: 'Prof. James Wilson', is_premium: false },
    created_at: '2024-01-08T10:00:00Z',
    updated_at: '2024-01-08T10:00:00Z',
    usage_count: 345,
    rating: 4.6,
    rating_count: 112,
    complexity_level: 'advanced',
    estimated_execution_time: 150,
    cost_estimate: 0.0380,
  },
  {
    id: '9',
    name: 'Invoice Processing System',
    description: 'Automated invoice extraction, validation, and payment processing with fraud detection',
    category: 'automation',
    orchestration_type: 'sequential',
    agents: [
      { id: 'i1', name: 'Document Parser', role: 'Extracts data from invoice documents', agent_id: 'parser-001' },
      { id: 'i2', name: 'Data Validator', role: 'Validates invoice data and checks for errors', agent_id: 'validator-001' },
      { id: 'i3', name: 'Fraud Detector', role: 'Detects potential fraudulent invoices', agent_id: 'fraud-001' },
      { id: 'i4', name: 'Payment Processor', role: 'Processes approved payments', agent_id: 'payment-001' },
    ],
    tags: ['automation', 'finance', 'invoice', 'fraud-detection'],
    is_public: true,
    is_featured: false,
    is_verified: true,
    created_by: { id: 'u9', name: 'Robert Brown', is_premium: true },
    created_at: '2024-01-07T14:15:00Z',
    updated_at: '2024-01-07T14:15:00Z',
    usage_count: 678,
    rating: 4.8,
    rating_count: 201,
    complexity_level: 'advanced',
    estimated_execution_time: 100,
    cost_estimate: 0.0310,
  },
  {
    id: '10',
    name: 'Product Launch Coordinator',
    description: 'Coordinates all aspects of product launch including marketing, PR, and customer communication',
    category: 'marketing',
    orchestration_type: 'parallel',
    agents: [
      { id: 'j1', name: 'Launch Planner', role: 'Creates comprehensive launch timeline', agent_id: 'planner-001' },
      { id: 'j2', name: 'PR Manager', role: 'Manages press releases and media outreach', agent_id: 'pr-001' },
      { id: 'j3', name: 'Marketing Coordinator', role: 'Coordinates marketing campaigns', agent_id: 'marketing-001' },
      { id: 'j4', name: 'Customer Communicator', role: 'Manages customer communications', agent_id: 'comms-001' },
    ],
    tags: ['marketing', 'product-launch', 'coordination', 'pr'],
    is_public: true,
    is_featured: false,
    is_verified: false,
    created_by: { id: 'u10', name: 'Amanda Lee', is_premium: false },
    created_at: '2024-01-06T09:45:00Z',
    updated_at: '2024-01-06T09:45:00Z',
    usage_count: 234,
    rating: 4.4,
    rating_count: 67,
    complexity_level: 'intermediate',
    estimated_execution_time: 85,
    cost_estimate: 0.0260,
  },
];

interface TemplateMarketplaceProps {
  onTemplateSelect?: (template: AgentTemplate) => void;
  showCreateButton?: boolean;
}

export function TemplateMarketplace({
  onTemplateSelect,
  showCreateButton = true,
}: TemplateMarketplaceProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  // State
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'popular' | 'recent' | 'rating'>('popular');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<AgentTemplate | null>(null);
  const [showTemplateDetails, setShowTemplateDetails] = useState(false);

  // Fetch templates (using mock data for now)
  const { data: templatesData, isLoading } = useQuery({
    queryKey: ['team-templates', selectedCategory, searchQuery, sortBy],
    queryFn: async () => {
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Filter mock data
      let filtered = MOCK_TEMPLATES;
      
      if (selectedCategory !== 'all') {
        filtered = filtered.filter(t => t.category === selectedCategory);
      }
      
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filtered = filtered.filter(t => 
          t.name.toLowerCase().includes(query) ||
          t.description.toLowerCase().includes(query) ||
          t.tags.some(tag => tag.toLowerCase().includes(query))
        );
      }
      
      return { templates: filtered };
    },
  });

  // Create template mutation
  const createTemplateMutation = useMutation({
    mutationFn: (data: Partial<AgentTemplate>) =>
      agentBuilderAPI.createTeamTemplate(data),
    onSuccess: () => {
      toast({
        title: 'Template Created',
        description: 'New team template has been added to the marketplace.',
      });
      queryClient.invalidateQueries({ queryKey: ['team-templates'] });
      setShowCreateDialog(false);
    },
    onError: () => {
      toast({
        title: 'Template Creation Failed',
        description: 'An error occurred while creating the template.',
        variant: 'destructive',
      });
    },
  });

  // Use template mutation
  const useTemplateMutation = useMutation({
    mutationFn: async (template: AgentTemplate) => {
      // Create agentflow from template
      return agentBuilderAPI.createAgentflowWithAgents({
        name: `${template.name} (Copy)`,
        description: template.description,
        orchestration_type: template.orchestration_type,
        tags: [...template.tags, 'from_template'],
        agents_config: template.agents.map((agent, index) => ({
          agent_id: agent.agent_id || '',
          name: agent.name,
          role: agent.role,
          priority: index + 1,
          position_x: 100 + (index % 3) * 200,
          position_y: 100 + Math.floor(index / 3) * 150,
        })),
      });
    },
    onSuccess: (result) => {
      toast({
        title: 'Template Applied',
        description: 'A new workflow has been created based on the template.',
      });
      if (onTemplateSelect && selectedTemplate) {
        onTemplateSelect(selectedTemplate);
      }
    },
    onError: () => {
      toast({
        title: 'Template Application Failed',
        description: 'An error occurred while applying the template.',
        variant: 'destructive',
      });
    },
  });

  // Filter and sort templates
  const filteredTemplates = React.useMemo(() => {
    if (!templatesData?.templates) return [];

    let filtered = templatesData.templates;

    // Apply sorting
    switch (sortBy) {
      case 'popular':
        filtered = filtered.sort((a, b) => b.usage_count - a.usage_count);
        break;
      case 'recent':
        filtered = filtered.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        break;
      case 'rating':
        filtered = filtered.sort((a, b) => b.rating - a.rating);
        break;
    }

    return filtered;
  }, [templatesData?.templates, sortBy]);

  // Handle template selection
  const handleTemplateSelect = (template: AgentTemplate) => {
    setSelectedTemplate(template);
    setShowTemplateDetails(true);
  };

  // Handle template use
  const handleUseTemplate = (template: AgentTemplate) => {
    useTemplateMutation.mutate(template);
  };

  // Render template card
  const renderTemplateCard = (template: AgentTemplate) => (
    <Card
      key={template.id}
      className="cursor-pointer hover:shadow-lg transition-all duration-300 group relative overflow-hidden"
      onClick={() => handleTemplateSelect(template)}
    >
      {/* Featured/Verified badges */}
      <div className="absolute top-2 right-2 z-10 flex gap-1">
        {template.is_featured && (
          <Badge className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white">
            <Crown className="w-3 h-3 mr-1" />
            Featured
          </Badge>
        )}
        {template.is_verified && (
          <Badge className="bg-blue-500 text-white">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            Verified
          </Badge>
        )}
      </div>

      {/* Preview image or gradient */}
      <div className="h-32 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 relative overflow-hidden">
        {template.preview_image ? (
          <img
            src={template.preview_image}
            alt={template.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-white text-4xl opacity-80">
              {TEMPLATE_CATEGORIES.find(c => c.value === template.category)?.icon || '🤖'}
            </div>
          </div>
        )}
        <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors" />
      </div>

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg line-clamp-1">{template.name}</CardTitle>
            <CardDescription className="line-clamp-2 mt-1">
              {template.description}
            </CardDescription>
          </div>
        </div>

        {/* Metadata */}
        <div className="flex items-center gap-2 mt-2">
          <Badge
            variant="secondary"
            className={COMPLEXITY_COLORS[template.complexity_level]}
          >
            {COMPLEXITY_LABELS[template.complexity_level]}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {template.orchestration_type}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {template.agents.length} agents
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {/* Tags */}
        <div className="flex flex-wrap gap-1 mb-3">
          {template.tags.slice(0, 3).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
          {template.tags.length > 3 && (
            <Badge variant="outline" className="text-xs">
              +{template.tags.length - 3}
            </Badge>
          )}
        </div>

        {/* Stats */}
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
              <span>{template.rating.toFixed(1)}</span>
              <span className="text-xs">({template.rating_count})</span>
            </div>
            <div className="flex items-center gap-1">
              <Download className="w-4 h-4" />
              <span>{template.usage_count}</span>
            </div>
          </div>
          
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>~{template.estimated_execution_time}s</span>
          </div>
        </div>

        {/* Creator */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t">
          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-medium">
            {template.created_by.name.charAt(0).toUpperCase()}
          </div>
          <span className="text-sm text-muted-foreground">
            {template.created_by.name}
          </span>
          {template.created_by.is_premium && (
            <Badge variant="outline" className="text-xs">
              <Sparkles className="w-3 h-3 mr-1" />
              Pro
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Template Marketplace</h2>
          <p className="text-muted-foreground">
            Discover and deploy verified agent team configurations
          </p>
        </div>
        {showCreateButton && (
          <Button onClick={() => setShowCreateDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Create Template
          </Button>
        )}
      </div>

      {/* Filters and Search */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <Input
              placeholder="Search templates..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="popular">Most Popular</SelectItem>
            <SelectItem value="recent">Most Recent</SelectItem>
            <SelectItem value="rating">Highest Rated</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Categories */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="grid w-full grid-cols-4 lg:grid-cols-9">
          {TEMPLATE_CATEGORIES.map((category) => (
            <TabsTrigger
              key={category.value}
              value={category.value}
              className="text-xs"
            >
              <span className="mr-1">{category.icon}</span>
              <span className="hidden sm:inline">{category.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {TEMPLATE_CATEGORIES.map((category) => (
          <TabsContent key={category.value} value={category.value} className="mt-6">
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <Card key={i} className="animate-pulse">
                    <div className="h-32 bg-gray-200" />
                    <CardHeader>
                      <div className="h-4 bg-gray-200 rounded w-3/4" />
                      <div className="h-3 bg-gray-200 rounded w-full mt-2" />
                    </CardHeader>
                    <CardContent>
                      <div className="h-3 bg-gray-200 rounded w-1/2" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredTemplates.map(renderTemplateCard)}
              </div>
            )}
          </TabsContent>
        ))}
      </Tabs>

      {/* Template Details Dialog */}
      <Dialog open={showTemplateDetails} onOpenChange={setShowTemplateDetails}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          {selectedTemplate && (
            <>
              <DialogHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <DialogTitle className="text-xl">{selectedTemplate.name}</DialogTitle>
                    <DialogDescription className="mt-2">
                      {selectedTemplate.description}
                    </DialogDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleUseTemplate(selectedTemplate)}
                      disabled={useTemplateMutation.isPending}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      {useTemplateMutation.isPending ? 'Applying...' : 'Use Template'}
                    </Button>
                  </div>
                </div>
              </DialogHeader>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                  {/* Agents */}
                  <div>
                    <h3 className="font-semibold mb-3">Included Agents ({selectedTemplate.agents.length})</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {selectedTemplate.agents.map((agent, index) => (
                        <Card key={agent.id} className="p-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                              <Users className="w-4 h-4 text-blue-600" />
                            </div>
                            <div>
                              <p className="font-medium text-sm">{agent.name}</p>
                              <p className="text-xs text-muted-foreground">{agent.role}</p>
                            </div>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>

                  {/* Tags */}
                  <div>
                    <h3 className="font-semibold mb-3">Tags</h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedTemplate.tags.map((tag) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Sidebar */}
                <div className="space-y-4">
                  {/* Stats */}
                  <Card className="p-4">
                    <h3 className="font-semibold mb-3">Statistics</h3>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Rating</span>
                        <div className="flex items-center gap-1">
                          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm font-medium">
                            {selectedTemplate.rating.toFixed(1)} ({selectedTemplate.rating_count})
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Usage Count</span>
                        <span className="text-sm font-medium">{selectedTemplate.usage_count}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Complexity</span>
                        <Badge className={COMPLEXITY_COLORS[selectedTemplate.complexity_level]}>
                          {COMPLEXITY_LABELS[selectedTemplate.complexity_level]}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Est. Execution Time</span>
                        <span className="text-sm font-medium">~{selectedTemplate.estimated_execution_time}s</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-muted-foreground">Est. Cost</span>
                        <span className="text-sm font-medium">${selectedTemplate.cost_estimate.toFixed(4)}</span>
                      </div>
                    </div>
                  </Card>

                  {/* Creator */}
                  <Card className="p-4">
                    <h3 className="font-semibold mb-3">Creator</h3>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white font-medium">
                        {selectedTemplate.created_by.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <p className="font-medium">{selectedTemplate.created_by.name}</p>
                        <p className="text-xs text-muted-foreground">
                          Created on {new Date(selectedTemplate.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Template Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Template</DialogTitle>
            <DialogDescription>
              Create an agent team template to share with other users.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Template Name</Label>
              <Input placeholder="e.g., Customer Service Automation Team" />
            </div>
            
            <div>
              <Label>Description</Label>
              <Textarea
                placeholder="Describe the purpose and features of this template"
                rows={3}
              />
            </div>
            
            <div>
              <Label>Category</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="Select category" />
                </SelectTrigger>
                <SelectContent>
                  {TEMPLATE_CATEGORIES.slice(1).map((category) => (
                    <SelectItem key={category.value} value={category.value}>
                      {category.icon} {category.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="flex gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)} className="flex-1">
                Cancel
              </Button>
              <Button
                onClick={() => {
                  // Handle template creation
                  setShowCreateDialog(false);
                }}
                className="flex-1"
              >
                Create Template
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}