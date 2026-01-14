'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Bot, 
  Zap, 
  Users, 
  Brain, 
  Search, 
  FileText, 
  MessageSquare, 
  BarChart3,
  Shield,
  Globe,
  Workflow,
  Sparkles
} from 'lucide-react';

interface AgentTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  orchestrationType: string[];
  icon: React.ComponentType<{ className?: string }>;
  capabilities: string[];
  tools: string[];
  configuration: {
    llm_provider: string;
    llm_model: string;
    system_prompt: string;
    temperature: number;
  };
  useCase: string;
  complexity: 'beginner' | 'intermediate' | 'advanced';
}

const AGENT_TEMPLATES: AgentTemplate[] = [
  // Sequential optimized templates
  {
    id: 'data-analyst',
    name: 'Data Analyst',
    description: 'Specialized agent that collects and analyzes data to provide insights',
    category: 'analysis',
    orchestrationType: ['sequential', 'pipeline'],
    icon: BarChart3,
    capabilities: ['Data Analysis', 'Statistical Processing', 'Visualization', 'Report Generation'],
    tools: ['python_code', 'data_visualization', 'statistical_analysis'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: 'You are a data analysis expert. Systematically analyze given data and provide clear insights.',
      temperature: 0.3
    },
    useCase: 'Handles analysis stage in sequential data processing pipelines',
    complexity: 'intermediate'
  },
  {
    id: 'content-writer',
    name: 'Content Writer',
    description: 'Creative agent that generates and edits various forms of content',
    category: 'content',
    orchestrationType: ['sequential', 'pipeline'],
    icon: FileText,
    capabilities: ['Writing', 'Editing', 'Translation', 'SEO Optimization'],
    tools: ['text_generation', 'grammar_check', 'seo_optimizer'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: 'You are a professional content writer. Create engaging and accurate content.',
      temperature: 0.7
    },
    useCase: 'Handles writing and editing in content production workflows',
    complexity: 'beginner'
  },

  // Parallel optimized templates
  {
    id: 'search-specialist',
    name: 'Search Specialist',
    description: 'Agent that simultaneously searches and collects information from various sources',
    category: 'search',
    orchestrationType: ['parallel', 'swarm'],
    icon: Search,
    capabilities: ['Web Search', 'Document Search', 'Database Query', 'Information Filtering'],
    tools: ['web_search', 'vector_search', 'database_query'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-3.5-turbo',
      system_prompt: 'You are an information search expert. Efficiently find and organize relevant information.',
      temperature: 0.2
    },
    useCase: 'Handles specific domain in parallel search tasks',
    complexity: 'intermediate'
  },
  {
    id: 'translator',
    name: 'Translation Expert',
    description: 'Language specialist agent handling multilingual translation and localization',
    category: 'language',
    orchestrationType: ['parallel', 'map_reduce'],
    icon: Globe,
    capabilities: ['Multilingual Translation', 'Localization', 'Cultural Adaptation', 'Language Verification'],
    tools: ['translation_api', 'language_detection', 'cultural_adapter'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: 'You are a professional translator. Provide accurate and natural translations.',
      temperature: 0.4
    },
    useCase: 'Parallel processing of multilingual content',
    complexity: 'intermediate'
  },

  // Hierarchical optimized templates
  {
    id: 'project-manager',
    name: 'Project Manager',
    description: 'Leadership agent that coordinates teams and manages tasks',
    category: 'management',
    orchestrationType: ['hierarchical', 'adaptive'],
    icon: Users,
    capabilities: ['Team Management', 'Task Distribution', 'Progress Monitoring', 'Decision Making'],
    tools: ['task_scheduler', 'progress_tracker', 'decision_maker'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: 'You are a project manager. Efficiently coordinate the team and lead goal achievement.',
      temperature: 0.5
    },
    useCase: 'Upper manager role in hierarchical structures',
    complexity: 'advanced'
  },
  {
    id: 'specialist-researcher',
    name: 'Specialist Researcher',
    description: 'Expert agent conducting in-depth research in specific fields',
    category: 'research',
    orchestrationType: ['hierarchical', 'consensus'],
    icon: Brain,
    capabilities: ['Specialized Research', 'Literature Review', 'Hypothesis Verification', 'Report Writing'],
    tools: ['academic_search', 'citation_manager', 'research_analyzer'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: 'You are a specialist researcher. Conduct systematic and in-depth research.',
      temperature: 0.3
    },
    useCase: 'Handles specialized field in hierarchical research teams',
    complexity: 'advanced'
  },

  // Consensus & Debate optimized templates
  {
    id: 'expert-advisor',
    name: 'Expert Advisor',
    description: 'Advisory agent providing expert opinions from specific perspectives',
    category: 'advisory',
    orchestrationType: ['consensus', 'debate'],
    icon: Shield,
    capabilities: ['Expert Consultation', 'Opinion Presentation', 'Evidence Analysis', 'Risk Assessment'],
    tools: ['expert_knowledge', 'risk_analyzer', 'evidence_evaluator'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: 'You are an expert in this field. Provide evidence-based opinions and advice.',
      temperature: 0.4
    },
    useCase: 'Provides expert opinions in consensus building or debates',
    complexity: 'advanced'
  },

  // Multi-modal & Advanced templates
  {
    id: 'multimodal-analyst',
    name: 'Multimodal Analyst',
    description: 'Agent analyzing various forms of data including text, images, and audio',
    category: 'multimodal',
    orchestrationType: ['multi_modal', 'neural_swarm'],
    icon: Sparkles,
    capabilities: ['Image Analysis', 'Text Analysis', 'Audio Processing', 'Integrated Analysis'],
    tools: ['image_analyzer', 'text_processor', 'audio_processor', 'multimodal_fusion'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4-vision',
      system_prompt: 'You are a multimodal analysis expert. Comprehensively analyze various forms of data.',
      temperature: 0.3
    },
    useCase: 'Advanced analysis processing multiple data types simultaneously',
    complexity: 'advanced'
  },

  // Adaptive & Self-healing templates
  {
    id: 'adaptive-optimizer',
    name: 'Adaptive Optimizer',
    description: 'Intelligent agent that adjusts and optimizes strategies based on situations',
    category: 'optimization',
    orchestrationType: ['adaptive', 'self_healing'],
    icon: Zap,
    capabilities: ['Situation Analysis', 'Strategy Modification', 'Performance Optimization', 'Auto Recovery'],
    tools: ['performance_monitor', 'strategy_optimizer', 'auto_healer'],
    configuration: {
      llm_provider: 'openai',
      llm_model: 'gpt-4',
      system_prompt: 'You are an adaptive optimization expert. Analyze situations and present optimal strategies.',
      temperature: 0.6
    },
    useCase: 'Auto adaptation and optimization in dynamic environments',
    complexity: 'advanced'
  }
];

interface AgentTemplateSelectorProps {
  onSelect: (template: AgentTemplate) => void;
  orchestrationType?: string;
  trigger?: React.ReactNode;
}

export function AgentTemplateSelector({ 
  onSelect, 
  orchestrationType,
  trigger 
}: AgentTemplateSelectorProps) {
  const [open, setOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Filter templates based on orchestration type
  const filteredTemplates = React.useMemo(() => {
    let templates = AGENT_TEMPLATES;
    
    if (orchestrationType) {
      templates = templates.filter(template => 
        template.orchestrationType.includes(orchestrationType)
      );
    }
    
    if (selectedCategory !== 'all') {
      templates = templates.filter(template => 
        template.category === selectedCategory
      );
    }
    
    // Sort templates matching orchestration type to top
    if (orchestrationType) {
      templates.sort((a, b) => {
        const aMatch = a.orchestrationType.includes(orchestrationType);
        const bMatch = b.orchestrationType.includes(orchestrationType);
        if (aMatch && !bMatch) return -1;
        if (!aMatch && bMatch) return 1;
        return 0;
      });
    }
    
    return templates;
  }, [orchestrationType, selectedCategory]);

  // Category list
  const categories = [
    { id: 'all', name: 'All', icon: Workflow },
    { id: 'analysis', name: 'Analysis', icon: BarChart3 },
    { id: 'content', name: 'Content', icon: FileText },
    { id: 'search', name: 'Search', icon: Search },
    { id: 'language', name: 'Language', icon: Globe },
    { id: 'management', name: 'Management', icon: Users },
    { id: 'research', name: 'Research', icon: Brain },
    { id: 'advisory', name: 'Advisory', icon: Shield },
    { id: 'multimodal', name: 'Multimodal', icon: Sparkles },
    { id: 'optimization', name: 'Optimization', icon: Zap }
  ];

  const handleSelectTemplate = (template: AgentTemplate) => {
    onSelect(template);
    setOpen(false);
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'beginner': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      case 'advanced': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button variant="outline">
            <Bot className="h-4 w-4 mr-2" />
            Create from Template
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-6xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            Select Agent Template
            {orchestrationType && (
              <Badge variant="outline" className="ml-2">
                {orchestrationType} optimized
              </Badge>
            )}
          </DialogTitle>
          <DialogDescription>
            {orchestrationType 
              ? `Select an Agent template optimized for ${orchestrationType} orchestration`
              : 'Select a pre-configured Agent template to get started quickly'
            }
          </DialogDescription>
        </DialogHeader>

        <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
          <TabsList className="grid w-full grid-cols-5 lg:grid-cols-10">
            {categories.map((category) => {
              const Icon = category.icon;
              return (
                <TabsTrigger 
                  key={category.id} 
                  value={category.id}
                  className="flex items-center gap-1 text-xs"
                >
                  <Icon className="h-3 w-3" />
                  <span className="hidden sm:inline">{category.name}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          <TabsContent value={selectedCategory} className="mt-4">
            <ScrollArea className="h-[500px]">
              {filteredTemplates.length === 0 ? (
                <div className="text-center py-12">
                  <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No templates found</h3>
                  <p className="text-muted-foreground">
                    No templates match the selected criteria. Try selecting a different category.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredTemplates.map((template) => {
                    const Icon = template.icon;
                    const isRecommended = orchestrationType && 
                      template.orchestrationType.includes(orchestrationType);
                    
                    return (
                      <Card
                        key={template.id}
                        className={`cursor-pointer transition-all duration-200 hover:shadow-lg hover:scale-[1.02] ${
                          isRecommended 
                            ? 'border-blue-400 bg-blue-50 dark:bg-blue-950/20' 
                            : 'hover:border-purple-300'
                        }`}
                        onClick={() => handleSelectTemplate(template)}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                              <div className={`p-2 rounded-lg ${
                                isRecommended 
                                  ? 'bg-blue-500 text-white' 
                                  : 'bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400'
                              }`}>
                                <Icon className="h-5 w-5" />
                              </div>
                              <div>
                                <CardTitle className="text-base">{template.name}</CardTitle>
                                <div className="flex gap-1 mt-1">
                                  <Badge className={getComplexityColor(template.complexity)}>
                                    {template.complexity}
                                  </Badge>
                                  {isRecommended && (
                                    <Badge className="bg-blue-500 hover:bg-blue-600 text-white">
                                      ⭐ Recommended
                                    </Badge>
                                  )}
                                </div>
                              </div>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <CardDescription className="text-sm">
                            {template.description}
                          </CardDescription>
                          
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-2">
                              Suitable orchestration:
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {template.orchestrationType.map((type) => (
                                <Badge 
                                  key={type} 
                                  variant="outline" 
                                  className={`text-xs ${
                                    type === orchestrationType 
                                      ? 'border-blue-500 text-blue-700 dark:text-blue-300' 
                                      : ''
                                  }`}
                                >
                                  {type}
                                </Badge>
                              ))}
                            </div>
                          </div>

                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-2">
                              Key features:
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {template.capabilities.slice(0, 3).map((capability) => (
                                <Badge key={capability} variant="secondary" className="text-xs">
                                  {capability}
                                </Badge>
                              ))}
                              {template.capabilities.length > 3 && (
                                <Badge variant="outline" className="text-xs">
                                  +{template.capabilities.length - 3} more
                                </Badge>
                              )}
                            </div>
                          </div>

                          <div className="pt-2 border-t">
                            <p className="text-xs text-muted-foreground">
                              <strong>Use case:</strong> {template.useCase}
                            </p>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}