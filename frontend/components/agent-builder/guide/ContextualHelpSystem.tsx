/**
 * Contextual Help System
 * Context-aware help and guide system
 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  HelpCircle,
  Search,
  BookOpen,
  MessageSquare,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  ExternalLink,
  ChevronRight,
  ChevronDown,
  Star,
  ThumbsUp,
  ThumbsDown,
  X,
  Minimize2,
  Maximize2,
  RotateCcw,
  Send,
  Bot,
  User,
  Zap,
  Target,
  Settings,
  Code,
  Play,
  FileText,
  Video,
  Headphones
} from 'lucide-react';
import { OrchestrationTypeValue, ORCHESTRATION_TYPES } from '@/lib/constants/orchestration';

interface HelpArticle {
  id: string;
  title: string;
  content: string;
  category: 'getting-started' | 'patterns' | 'configuration' | 'troubleshooting' | 'best-practices';
  tags: string[];
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  estimatedReadTime: number; // in minutes
  lastUpdated: string;
  helpful: number;
  notHelpful: number;
  relatedArticles?: string[];
}

interface FAQ {
  id: string;
  question: string;
  answer: string;
  category: string;
  popularity: number;
  tags: string[];
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  helpful?: boolean;
}

interface ContextualHelpSystemProps {
  context?: {
    currentPage?: string;
    selectedPattern?: OrchestrationTypeValue;
    userAction?: string;
    errorMessage?: string;
  };
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
  onClose?: () => void;
}

export const ContextualHelpSystem: React.FC<ContextualHelpSystemProps> = ({
  context,
  isMinimized = false,
  onToggleMinimize,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState('help');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFAQ, setExpandedFAQ] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Mock data
  const helpArticles: HelpArticle[] = [
    {
      id: 'consensus-getting-started',
      title: 'Getting Started with Consensus Building Pattern',
      content: `
# Getting Started with Consensus Building Pattern

The consensus building pattern is a powerful method where multiple Agents collaborate to make optimal decisions.

## Basic Configuration

1. **Select Voting Mechanism**
   - Simple Majority: When quick decisions are needed
   - Weighted Voting: When you want to reflect each Agent's expertise
   - Unanimous: For important decisions requiring strong consensus

2. **Set Consensus Threshold**
   - Generally recommended between 60-80%
   - Too high makes reaching consensus difficult
   - Too low may result in weak consensus

3. **Maximum Rounds**
   - Must be set to prevent infinite loops
   - Usually 3-7 rounds is appropriate

## Best Practices

- Clearly define Agent roles
- Set discussion time limits to improve efficiency
- Use a mediator Agent to prevent deadlocks
      `,
      category: 'getting-started',
      tags: ['consensus', 'voting', 'configuration'],
      difficulty: 'beginner',
      estimatedReadTime: 5,
      lastUpdated: '2026-01-09',
      helpful: 24,
      notHelpful: 2
    },
    {
      id: 'swarm-optimization',
      title: 'Swarm Intelligence Optimization Guide',
      content: `
# Swarm Intelligence Optimization Guide

Learn how to maximize the performance of swarm intelligence patterns.

## Key Parameters

### Inertia Weight
- Range: 0.1 - 1.0
- High value: Exploration-focused
- Low value: Exploitation-focused

### Cognitive/Social Weights
- Cognitive weight: Degree of personal experience reflection
- Social weight: Degree of collective knowledge reflection
- Balance is important (usually 1.4 - 2.0)

## Performance Tuning Tips

1. **Initial Swarm Size**
   - Adjust according to problem complexity
   - Generally 10-50 is appropriate

2. **Convergence Conditions**
   - Too strict causes early termination
   - Too loose causes unnecessary computation

3. **Adaptive Parameters**
   - Consider dynamic adjustment during execution
   - Auto-tuning based on performance monitoring
      `,
      category: 'best-practices',
      tags: ['swarm', 'optimization', 'performance'],
      difficulty: 'advanced',
      estimatedReadTime: 8,
      lastUpdated: '2026-01-08',
      helpful: 18,
      notHelpful: 1
    },
    {
      id: 'troubleshooting-timeouts',
      title: 'Troubleshooting Timeout Issues',
      content: `
# Troubleshooting Timeout Issues

Solutions for timeout issues during orchestration execution.

## Common Causes

1. **Agent Response Delays**
   - Check LLM model response time
   - Verify network connection status
   - Monitor resource usage

2. **Complex Tasks**
   - Split tasks into smaller units
   - Consider parallel processing
   - Utilize caching

## Solutions

### Adjust Timeout Settings
\`\`\`json
{
  "execution_timeout": 300000,  // 5 minutes
  "agent_timeout": 60000,       // 1 minute
  "retry_attempts": 3
}
\`\`\`

### Performance Optimization
- Remove unnecessary Agents
- Improve cache strategy
- Optimize resource allocation
      `,
      category: 'troubleshooting',
      tags: ['timeout', 'performance', 'debugging'],
      difficulty: 'intermediate',
      estimatedReadTime: 6,
      lastUpdated: '2026-01-07',
      helpful: 31,
      notHelpful: 4
    }
  ];

  const faqs: FAQ[] = [
    {
      id: 'faq-1',
      question: 'Which orchestration pattern should I choose?',
      answer: 'Choose based on the nature of your task. Use Sequential for sequential processing, Parallel for independent tasks, and Consensus Building for complex decision-making.',
      category: 'patterns',
      popularity: 95,
      tags: ['pattern-selection', 'getting-started']
    },
    {
      id: 'faq-2',
      question: 'What happens if consensus is not reached in consensus building?',
      answer: 'When the maximum number of rounds is reached, the option with the highest score is automatically selected, or the mediator Agent makes the final decision.',
      category: 'consensus',
      popularity: 87,
      tags: ['consensus', 'troubleshooting']
    },
    {
      id: 'faq-3',
      question: 'Why is the swarm intelligence pattern not converging?',
      answer: 'The convergence threshold may be too strict, or the parameter settings may be inappropriate. Try adjusting the inertia weight and learning rate.',
      category: 'swarm',
      popularity: 73,
      tags: ['swarm', 'convergence', 'parameters']
    },
    {
      id: 'faq-4',
      question: 'How does the number of Agents affect performance?',
      answer: 'More Agents provide diverse perspectives, but communication overhead and consensus time increase. Usually 3-10 is appropriate.',
      category: 'performance',
      popularity: 68,
      tags: ['agents', 'performance', 'scaling']
    }
  ];

  // Filter articles based on search and context
  const filteredArticles = helpArticles.filter(article => {
    const matchesSearch = searchQuery === '' || 
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesContext = !context?.selectedPattern || 
      article.tags.includes(context.selectedPattern) ||
      article.content.toLowerCase().includes(context.selectedPattern);
    
    return matchesSearch && matchesContext;
  });

  // Get contextual suggestions
  const getContextualSuggestions = () => {
    const suggestions = [];
    
    if (context?.selectedPattern) {
      const patternInfo = ORCHESTRATION_TYPES[context.selectedPattern];
      suggestions.push({
        type: 'pattern-help',
        title: `${patternInfo?.name} Pattern Guide`,
        description: `Check usage and best practices for the ${patternInfo?.name} pattern.`,
        action: () => setSearchQuery(context.selectedPattern)
      });
    }
    
    if (context?.errorMessage) {
      suggestions.push({
        type: 'error-help',
        title: 'Error Resolution Guide',
        description: 'Find solutions for the current error.',
        action: () => setActiveTab('chat')
      });
    }
    
    if (context?.currentPage === 'configuration') {
      suggestions.push({
        type: 'config-help',
        title: 'Configuration Help',
        description: 'Check proper configuration methods and recommended values.',
        action: () => setSearchQuery('configuration')
      });
    }
    
    return suggestions;
  };

  // Simulate AI chat response
  const simulateAIResponse = async (userMessage: string) => {
    setIsTyping(true);
    
    // Simulate thinking time
    await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
    
    let response = '';
    
    // Context-aware responses
    if (userMessage.toLowerCase().includes('합의') || userMessage.toLowerCase().includes('consensus')) {
      response = `You asked about the consensus building pattern!

The consensus building pattern is a method where multiple Agents make optimal decisions through discussion. Key configuration items are:

1. **Voting Mechanism**: Choose from simple majority, weighted voting, or unanimous
2. **Consensus Threshold**: Usually 60-80% recommended
3. **Maximum Rounds**: 3-7 rounds is appropriate

What specific aspect would you like to know more about?`;
    } else if (userMessage.toLowerCase().includes('군집') || userMessage.toLowerCase().includes('swarm')) {
      response = `You're asking about the swarm intelligence pattern!

Swarm intelligence is an optimization method that mimics collective behavior in nature:

🐜 **Ant Colony Optimization (ACO)**: Path finding using pheromone trails
🐦 **Particle Swarm Optimization (PSO)**: Cooperative search by individuals

Key parameters:
- Inertia weight: 0.7 (exploration/exploitation balance)
- Cognitive/Social weight: 1.4 (personal/collective experience reflection)

What would you like to know more about?`;
    } else if (userMessage.toLowerCase().includes('오류') || userMessage.toLowerCase().includes('error')) {
      response = `I'll help you resolve the error!

Common error types and solutions:

🔴 **Timeout Errors**
- Increase execution time limit
- Reduce number of Agents
- Reduce task size

🟡 **Configuration Errors**
- Check required parameters
- Validate value ranges
- Check dependencies

🟢 **Performance Issues**
- Monitor resource usage
- Utilize caching
- Optimize parallel processing

Please provide the specific error message for a more accurate solution.`;
    } else {
      response = `Hello! I'll help you with orchestration patterns.

Please ask about the following topics:
- Pattern selection guide
- Configuration methods
- Performance optimization
- Error resolution
- Best practices

Feel free to ask any specific questions! 😊`;
    }
    
    setIsTyping(false);
    
    const aiMessage: ChatMessage = {
      id: `ai-${Date.now()}`,
      type: 'assistant',
      content: response,
      timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, aiMessage]);
  };

  const handleSendMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: chatInput,
      timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    
    await simulateAIResponse(chatInput);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={onToggleMinimize}
          className="rounded-full w-12 h-12 shadow-lg"
        >
          <HelpCircle className="h-6 w-6" />
        </Button>
      </div>
    );
  }

  return (
    <Card className="fixed bottom-4 right-4 w-96 h-[600px] z-50 shadow-xl">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <HelpCircle className="h-5 w-5 text-blue-600" />
            <CardTitle className="text-lg">Help</CardTitle>
          </div>
          
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="sm" onClick={onToggleMinimize}>
              <Minimize2 className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 h-[calc(100%-80px)]">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
          <TabsList className="grid w-full grid-cols-3 mx-4">
            <TabsTrigger value="help">Help</TabsTrigger>
            <TabsTrigger value="faq">FAQ</TabsTrigger>
            <TabsTrigger value="chat">AI Chat</TabsTrigger>
          </TabsList>

          <TabsContent value="help" className="h-[calc(100%-50px)] overflow-hidden">
            <div className="p-4 space-y-4 h-full overflow-y-auto">
              {/* Contextual Suggestions */}
              {getContextualSuggestions().length > 0 && (
                <div className="space-y-2">
                  <h4 className="font-semibold text-sm text-blue-600">Recommended Help</h4>
                  {getContextualSuggestions().map((suggestion, index) => (
                    <Alert key={index} className="cursor-pointer hover:bg-blue-50" onClick={suggestion.action}>
                      <Lightbulb className="h-4 w-4" />
                      <AlertDescription>
                        <div>
                          <p className="font-medium">{suggestion.title}</p>
                          <p className="text-sm text-gray-600">{suggestion.description}</p>
                        </div>
                      </AlertDescription>
                    </Alert>
                  ))}
                  <Separator />
                </div>
              )}

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search help..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>

              {/* Articles */}
              <div className="space-y-3">
                {filteredArticles.map((article) => (
                  <Card key={article.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-3">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium text-sm">{article.title}</h4>
                        <Badge variant="outline" className="text-xs">
                          {article.difficulty === 'beginner' ? 'Beginner' :
                           article.difficulty === 'intermediate' ? 'Intermediate' : 'Advanced'}
                        </Badge>
                      </div>
                      
                      <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                        {article.content.substring(0, 100)}...
                      </p>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center space-x-2">
                          <span>{article.estimatedReadTime} min read</span>
                          <span>•</span>
                          <div className="flex items-center space-x-1">
                            <ThumbsUp className="h-3 w-3" />
                            <span>{article.helpful}</span>
                          </div>
                        </div>
                        <ExternalLink className="h-3 w-3" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="faq" className="h-[calc(100%-50px)] overflow-hidden">
            <div className="p-4 space-y-3 h-full overflow-y-auto">
              {faqs.map((faq) => (
                <Card key={faq.id} className="cursor-pointer">
                  <CardContent className="p-3">
                    <div 
                      className="flex items-center justify-between"
                      onClick={() => setExpandedFAQ(expandedFAQ === faq.id ? null : faq.id)}
                    >
                      <h4 className="font-medium text-sm">{faq.question}</h4>
                      {expandedFAQ === faq.id ? 
                        <ChevronDown className="h-4 w-4" /> : 
                        <ChevronRight className="h-4 w-4" />
                      }
                    </div>
                    
                    {expandedFAQ === faq.id && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-sm text-gray-700">{faq.answer}</p>
                        <div className="flex items-center justify-between mt-3">
                          <div className="flex items-center space-x-2 text-xs text-gray-500">
                            <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                            <span>{faq.popularity}% helpful</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Button variant="ghost" size="sm">
                              <ThumbsUp className="h-3 w-3" />
                            </Button>
                            <Button variant="ghost" size="sm">
                              <ThumbsDown className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="chat" className="h-[calc(100%-50px)] overflow-hidden flex flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {chatMessages.length === 0 && (
                <div className="text-center text-gray-500 mt-8">
                  <Bot className="h-12 w-12 mx-auto mb-2 text-blue-600" />
                  <p className="text-sm">Ask the AI assistant a question!</p>
                  <p className="text-xs">I'll help you with orchestration patterns.</p>
                </div>
              )}
              
              {chatMessages.map((message) => (
                <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-3 rounded-lg ${
                    message.type === 'user' 
                      ? 'bg-blue-600 text-white' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    <div className="flex items-start space-x-2">
                      {message.type === 'assistant' && <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />}
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                      {message.type === 'user' && <User className="h-4 w-4 mt-0.5 flex-shrink-0" />}
                    </div>
                    <div className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              ))}
              
              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 p-3 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <Bot className="h-4 w-4" />
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </div>
            
            <div className="p-4 border-t">
              <div className="flex space-x-2">
                <Input
                  placeholder="Enter your question..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="flex-1"
                />
                <Button onClick={handleSendMessage} disabled={!chatInput.trim()}>
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};