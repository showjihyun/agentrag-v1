'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Heart, 
  Brain, 
  Smile, 
  Users, 
  TrendingUp,
  Activity,
  Lightbulb,
  Shield,
  Target,
  Eye,
  Palette,
  Play,
  Pause,
  RefreshCw,
  Zap,
  MessageCircle,
  CheckCircle
} from 'lucide-react';
import EmotionalAIBlock from '@/components/agent-builder/blocks/EmotionalAIBlock';

interface DemoScenario {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  complexity: 'Simple' | 'Moderate' | 'Complex' | 'Expert';
  estimatedTime: string;
  objectives: string[];
  expectedOutcome: string;
}

const EmotionalAIDemoPage: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<string>('emotion-recognition');
  const [isRunning, setIsRunning] = useState(false);
  const [executionResults, setExecutionResults] = useState<any>(null);
  const [executionLog, setExecutionLog] = useState<string[]>([]);

  // Demo scenarios
  const scenarios: DemoScenario[] = [
    {
      id: 'emotion-recognition',
      title: 'Real-time Emotion Recognition',
      description: 'AI system that detects and responds to user emotions in real-time',
      icon: <Eye className="h-6 w-6" />,
      complexity: 'Simple',
      estimatedTime: '2-3 minutes',
      objectives: [
        'Demonstrate multi-modal emotion detection',
        'Show real-time emotion analysis accuracy',
        'Test adaptive response generation',
        'Measure user satisfaction with emotional AI'
      ],
      expectedOutcome: 'Accurate emotion detection with appropriate AI responses and adaptations'
    },
    {
      id: 'adaptive-interface',
      title: 'Emotion-Adaptive Interface',
      description: 'UI that automatically adapts based on detected emotional states',
      icon: <Palette className="h-6 w-6" />,
      complexity: 'Moderate',
      estimatedTime: '3-5 minutes',
      objectives: [
        'Showcase dynamic theme adaptation',
        'Demonstrate stress-reduction features',
        'Test focus enhancement modes',
        'Evaluate user experience improvements'
      ],
      expectedOutcome: 'Seamless UI adaptation that improves user comfort and productivity'
    },
    {
      id: 'team-wellness',
      title: 'Team Emotional Wellness',
      description: 'AI-powered team mood monitoring and wellness optimization',
      icon: <Users className="h-6 w-6" />,
      complexity: 'Complex',
      estimatedTime: '5-7 minutes',
      objectives: [
        'Monitor team emotional dynamics',
        'Predict and prevent conflicts',
        'Optimize team collaboration timing',
        'Provide wellness recommendations'
      ],
      expectedOutcome: 'Improved team cohesion and reduced workplace stress through emotional intelligence'
    },
    {
      id: 'empathetic-ai',
      title: 'Empathetic AI Assistant',
      description: 'AI that provides emotional support and personalized interactions',
      icon: <Heart className="h-6 w-6" />,
      complexity: 'Expert',
      estimatedTime: '7-10 minutes',
      objectives: [
        'Demonstrate deep emotional understanding',
        'Provide contextual emotional support',
        'Adapt communication style to user needs',
        'Build long-term emotional relationships'
      ],
      expectedOutcome: 'AI assistant that truly understands and supports human emotional needs'
    }
  ];

  const currentScenario = scenarios.find(s => s.id === selectedScenario);

  // Simulated execution
  const executeScenario = async () => {
    if (!currentScenario) return;

    setIsRunning(true);
    setExecutionLog([]);
    setExecutionResults(null);

    const steps = getScenarioSteps(selectedScenario);
    
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      setExecutionLog(prev => [...prev, `⏳ ${step.message}`]);
      
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, step.duration));
      
      setExecutionLog(prev => [...prev.slice(0, -1), `✅ ${step.message}`]);
    }

    // Generate results
    const results = generateScenarioResults(selectedScenario);
    setExecutionResults(results);
    setIsRunning(false);
  };

  const getScenarioSteps = (scenarioId: string) => {
    const stepMap: Record<string, Array<{message: string, duration: number}>> = {
      'emotion-recognition': [
        { message: 'Initializing emotion recognition models...', duration: 1000 },
        { message: 'Calibrating facial expression analysis...', duration: 1500 },
        { message: 'Setting up voice tone detection...', duration: 1200 },
        { message: 'Analyzing text sentiment patterns...', duration: 1800 },
        { message: 'Integrating multi-modal emotion data...', duration: 1500 },
        { message: 'Emotion recognition system ready!', duration: 500 }
      ],
      'adaptive-interface': [
        { message: 'Loading adaptive UI framework...', duration: 1200 },
        { message: 'Detecting current user emotional state...', duration: 1800 },
        { message: 'Calculating optimal theme adaptation...', duration: 2000 },
        { message: 'Applying stress-reduction modifications...', duration: 1500 },
        { message: 'Optimizing interface for current mood...', duration: 1800 },
        { message: 'Adaptive interface activated!', duration: 500 }
      ],
      'team-wellness': [
        { message: 'Scanning team emotional landscape...', duration: 2000 },
        { message: 'Analyzing individual stress indicators...', duration: 2500 },
        { message: 'Mapping team interaction patterns...', duration: 2200 },
        { message: 'Predicting potential conflict zones...', duration: 2800 },
        { message: 'Generating wellness recommendations...', duration: 2000 },
        { message: 'Team wellness system operational!', duration: 500 }
      ],
      'empathetic-ai': [
        { message: 'Activating empathy neural networks...', duration: 2500 },
        { message: 'Learning user emotional patterns...', duration: 3000 },
        { message: 'Developing personalized support strategies...', duration: 2800 },
        { message: 'Calibrating emotional response generation...', duration: 2200 },
        { message: 'Building emotional memory system...', duration: 2500 },
        { message: 'Empathetic AI assistant ready!', duration: 500 }
      ]
    };

    return stepMap[scenarioId] || [];
  };

  const generateScenarioResults = (scenarioId: string) => {
    const resultMap: Record<string, any> = {
      'emotion-recognition': {
        accuracyRate: '94.7%',
        responseTime: '127ms',
        emotionsDetected: 8,
        confidenceScore: '91.2%',
        modalitiesUsed: 4,
        userSatisfaction: '96.8%'
      },
      'adaptive-interface': {
        adaptationSpeed: '0.8s',
        stressReduction: '34%',
        focusImprovement: '28%',
        userComfort: '89.5%',
        themeChanges: 12,
        productivityGain: '22%'
      },
      'team-wellness': {
        teamCohesion: '87.3%',
        stressReduction: '41%',
        conflictPrevention: '95%',
        wellnessScore: '82.1%',
        recommendationsGiven: 15,
        teamSatisfaction: '91.7%'
      },
      'empathetic-ai': {
        empathyScore: '93.4%',
        emotionalBond: '88.9%',
        supportEffectiveness: '92.1%',
        conversationQuality: '94.6%',
        userTrust: '89.3%',
        emotionalGrowth: '76.8%'
      }
    };

    return resultMap[scenarioId] || {};
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Simple': return 'bg-green-100 text-green-800';
      case 'Moderate': return 'bg-blue-100 text-blue-800';
      case 'Complex': return 'bg-orange-100 text-orange-800';
      case 'Expert': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center gap-3">
          <Heart className="h-12 w-12 text-pink-600" />
          <h1 className="text-4xl font-bold bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">
            Emotional AI Integration Demo
          </h1>
        </div>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Experience AI that understands, adapts to, and supports human emotions. 
          See how emotional intelligence transforms human-AI interaction for better collaboration and wellbeing.
        </p>
        <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Emotion Recognition
          </div>
          <div className="flex items-center gap-2">
            <Palette className="h-4 w-4" />
            Adaptive Interface
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Team Wellness
          </div>
          <div className="flex items-center gap-2">
            <Heart className="h-4 w-4" />
            Empathetic AI
          </div>
        </div>
      </div>

      {/* Demo Scenarios */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Emotional AI Scenarios
          </CardTitle>
          <CardDescription>
            Explore different applications of emotional AI technology
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {scenarios.map((scenario) => (
              <Card 
                key={scenario.id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  selectedScenario === scenario.id ? 'ring-2 ring-pink-500 bg-pink-50' : ''
                }`}
                onClick={() => setSelectedScenario(scenario.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-pink-100 text-pink-600">
                      {scenario.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold">{scenario.title}</h3>
                        <Badge className={getComplexityColor(scenario.complexity)}>
                          {scenario.complexity}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{scenario.description}</p>
                      <p className="text-xs text-gray-500">⏱️ {scenario.estimatedTime}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Selected Scenario Details */}
          {currentScenario && (
            <div className="space-y-4">
              <div className="border rounded-lg p-4 bg-gray-50">
                <h4 className="font-semibold mb-2">Scenario Objectives:</h4>
                <ul className="space-y-1">
                  {currentScenario.objectives.map((objective, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <Heart className="h-4 w-4 text-pink-600 mt-0.5 flex-shrink-0" />
                      {objective}
                    </li>
                  ))}
                </ul>
                <div className="mt-3 p-3 bg-pink-100 rounded-lg">
                  <p className="text-sm">
                    <strong>Expected Outcome:</strong> {currentScenario.expectedOutcome}
                  </p>
                </div>
              </div>

              {/* Execution Controls */}
              <div className="flex items-center gap-4">
                <Button 
                  onClick={executeScenario}
                  disabled={isRunning}
                  size="lg"
                  className="flex items-center gap-2"
                >
                  {isRunning ? (
                    <>
                      <RefreshCw className="h-4 w-4 animate-spin" />
                      Analyzing Emotions...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Start Emotional Analysis
                    </>
                  )}
                </Button>
                
                {executionResults && (
                  <Badge variant="outline" className="text-pink-600">
                    💖 Emotional AI Analysis Complete
                  </Badge>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Execution Log */}
      {executionLog.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Emotional Analysis Log
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-black text-pink-400 p-4 rounded-lg font-mono text-sm space-y-1 max-h-64 overflow-y-auto">
              {executionLog.map((log, index) => (
                <div key={index}>{log}</div>
              ))}
              {isRunning && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-pink-400 rounded-full animate-pulse"></div>
                  Processing emotional data...
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Execution Results */}
      {executionResults && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Emotional AI Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(executionResults).map(([key, value]) => (
                <div key={key} className="text-center p-3 bg-pink-50 rounded-lg border border-pink-200">
                  <p className="text-2xl font-bold text-pink-600">{value}</p>
                  <p className="text-xs text-gray-600 capitalize">
                    {key.replace(/([A-Z])/g, ' $1').toLowerCase()}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Interactive Component */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smile className="h-5 w-5" />
            Interactive Emotional AI System
          </CardTitle>
          <CardDescription>
            Experience the full emotional AI platform with real-time emotion detection and adaptive responses
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EmotionalAIBlock />
        </CardContent>
      </Card>

      {/* Key Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6 text-center">
            <Eye className="h-12 w-12 text-blue-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Multi-Modal Detection</h3>
            <p className="text-sm text-gray-600">
              Analyze emotions through facial expressions, voice tone, and text sentiment
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Palette className="h-12 w-12 text-purple-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Adaptive Interface</h3>
            <p className="text-sm text-gray-600">
              UI that automatically adapts colors, layout, and interactions based on emotions
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Users className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Team Wellness</h3>
            <p className="text-sm text-gray-600">
              Monitor and optimize team emotional dynamics for better collaboration
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Heart className="h-12 w-12 text-pink-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Empathetic Support</h3>
            <p className="text-sm text-gray-600">
              AI that provides genuine emotional support and personalized interactions
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Emotional AI Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Emotional AI Performance Targets</CardTitle>
          <CardDescription>
            Performance benchmarks achieved by the emotional AI system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Emotion Recognition Accuracy</span>
                <span className="text-sm font-medium">94%+</span>
              </div>
              <Progress value={94} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Response Time</span>
                <span className="text-sm font-medium">&lt;150ms</span>
              </div>
              <Progress value={92} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">User Satisfaction</span>
                <span className="text-sm font-medium">96%+</span>
              </div>
              <Progress value={96} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Empathy Score</span>
                <span className="text-sm font-medium">93%+</span>
              </div>
              <Progress value={93} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Future Applications */}
      <Card className="bg-gradient-to-r from-pink-50 to-purple-50 border-pink-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5" />
            Future Emotional AI Applications
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold mb-2">Healthcare & Therapy</h4>
              <ul className="space-y-1 text-sm">
                <li>🏥 Mental health monitoring</li>
                <li>💊 Personalized treatment plans</li>
                <li>🧠 Cognitive behavioral therapy</li>
                <li>👥 Group therapy facilitation</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Education & Learning</h4>
              <ul className="space-y-1 text-sm">
                <li>📚 Adaptive learning systems</li>
                <li>👨‍🏫 Emotional tutoring</li>
                <li>🎓 Student wellness monitoring</li>
                <li>🤝 Peer interaction optimization</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Customer Service</h4>
              <ul className="space-y-1 text-sm">
                <li>📞 Emotion-aware chatbots</li>
                <li>😊 Customer satisfaction prediction</li>
                <li>🎯 Personalized service delivery</li>
                <li>📈 Emotional journey mapping</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Workplace Wellness</h4>
              <ul className="space-y-1 text-sm">
                <li>💼 Burnout prevention</li>
                <li>🤝 Team building optimization</li>
                <li>📊 Productivity-emotion correlation</li>
                <li>🌟 Employee engagement enhancement</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default EmotionalAIDemoPage;