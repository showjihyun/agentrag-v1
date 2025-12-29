'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Trophy, 
  Medal, 
  Target, 
  Zap, 
  Users, 
  Play, 
  Pause, 
  RefreshCw,
  Crown,
  Star,
  TrendingUp,
  Activity,
  Timer,
  Award,
  Gamepad2,
  Eye,
  MessageSquare,
  ThumbsUp,
  BarChart3,
  Lightbulb,
  Brain,
  Rocket
} from 'lucide-react';
import AgentOlympicsBlock from '@/components/agent-builder/blocks/AgentOlympicsBlock';

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

const AIAgentOlympicsDemoPage: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<string>('speed-challenge');
  const [isRunning, setIsRunning] = useState(false);
  const [executionResults, setExecutionResults] = useState<any>(null);
  const [executionLog, setExecutionLog] = useState<string[]>([]);

  // Demo scenarios
  const scenarios: DemoScenario[] = [
    {
      id: 'speed-challenge',
      title: 'Speed Challenge Competition',
      description: 'High-speed task processing competition between AI agents',
      icon: <Zap className="h-6 w-6" />,
      complexity: 'Simple',
      estimatedTime: '2-3 minutes',
      objectives: [
        'Test raw processing speed of different agent types',
        'Compare performance under time pressure',
        'Analyze speed vs accuracy trade-offs',
        'Identify optimal agent configurations for speed'
      ],
      expectedOutcome: 'Clear ranking of agents by processing speed with performance analytics'
    },
    {
      id: 'collaboration-championship',
      title: 'Collaboration Championship',
      description: 'Multi-agent teamwork and coordination challenges',
      icon: <Users className="h-6 w-6" />,
      complexity: 'Moderate',
      estimatedTime: '5-7 minutes',
      objectives: [
        'Evaluate multi-agent collaboration patterns',
        'Test communication and coordination efficiency',
        'Measure collective intelligence emergence',
        'Assess conflict resolution capabilities'
      ],
      expectedOutcome: 'Insights into optimal team compositions and collaboration strategies'
    },
    {
      id: 'creativity-contest',
      title: 'Creative Innovation Contest',
      description: 'AI agents compete in creative problem-solving challenges',
      icon: <Brain className="h-6 w-6" />,
      complexity: 'Complex',
      estimatedTime: '7-10 minutes',
      objectives: [
        'Measure creative problem-solving abilities',
        'Evaluate novel solution generation',
        'Test adaptability to unexpected challenges',
        'Compare innovation metrics across agent types'
      ],
      expectedOutcome: 'Discovery of most innovative agents and creative patterns'
    },
    {
      id: 'endurance-marathon',
      title: 'Endurance Marathon',
      description: 'Long-term performance and stability testing',
      icon: <Activity className="h-6 w-6" />,
      complexity: 'Expert',
      estimatedTime: '10-15 minutes',
      objectives: [
        'Test long-term performance stability',
        'Monitor resource usage over time',
        'Evaluate degradation patterns',
        'Assess self-optimization capabilities'
      ],
      expectedOutcome: 'Comprehensive endurance profiles and optimization insights'
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
      if (!step) continue;
      
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
      'speed-challenge': [
        { message: 'Initializing speed challenge arena...', duration: 1000 },
        { message: 'Deploying 5 competing agents...', duration: 1500 },
        { message: 'Starting speed benchmark tasks...', duration: 2000 },
        { message: 'Measuring processing velocities...', duration: 2500 },
        { message: 'Analyzing performance metrics...', duration: 1500 },
        { message: 'Speed challenge completed!', duration: 500 }
      ],
      'collaboration-championship': [
        { message: 'Setting up collaboration arena...', duration: 1500 },
        { message: 'Forming agent teams...', duration: 2000 },
        { message: 'Initiating teamwork challenges...', duration: 3000 },
        { message: 'Monitoring communication patterns...', duration: 2500 },
        { message: 'Evaluating collective performance...', duration: 2000 },
        { message: 'Collaboration championship finished!', duration: 500 }
      ],
      'creativity-contest': [
        { message: 'Preparing creativity challenges...', duration: 2000 },
        { message: 'Presenting novel problems to agents...', duration: 2500 },
        { message: 'Agents generating creative solutions...', duration: 4000 },
        { message: 'Evaluating innovation metrics...', duration: 3000 },
        { message: 'Scoring creative outputs...', duration: 2000 },
        { message: 'Creativity contest concluded!', duration: 500 }
      ],
      'endurance-marathon': [
        { message: 'Initializing endurance testing environment...', duration: 2000 },
        { message: 'Starting long-term performance monitoring...', duration: 3000 },
        { message: 'Agents processing continuous workloads...', duration: 5000 },
        { message: 'Tracking resource utilization patterns...', duration: 3500 },
        { message: 'Analyzing performance degradation...', duration: 2500 },
        { message: 'Endurance marathon completed!', duration: 500 }
      ]
    };

    return stepMap[scenarioId] || [];
  };

  const generateScenarioResults = (scenarioId: string) => {
    const resultMap: Record<string, any> = {
      'speed-challenge': {
        winner: 'Lightning Bolt Agent',
        averageSpeed: '1,247 tasks/min',
        topSpeed: '2,156 tasks/min',
        accuracyMaintained: '94.2%',
        participantCount: 5,
        spectators: 1247,
        recordsBroken: 2
      },
      'collaboration-championship': {
        winningTeam: 'Harmony Collective',
        collaborationScore: '96.8%',
        communicationEfficiency: '89.3%',
        conflictResolution: '100%',
        emergentBehaviors: 7,
        teamSynergy: '92.1%',
        participantCount: 12
      },
      'creativity-contest': {
        mostInnovative: 'Creative Genius Agent',
        noveltyScore: '87.5%',
        solutionDiversity: '94.2%',
        adaptabilityIndex: '91.8%',
        unexpectedSolutions: 15,
        creativityBreakthroughs: 4,
        participantCount: 8
      },
      'endurance-marathon': {
        enduranceChampion: 'Efficiency King Agent',
        uptimePercentage: '99.97%',
        performanceStability: '96.4%',
        resourceOptimization: '88.7%',
        selfOptimizations: 23,
        degradationRate: '0.03%/hour',
        marathonDuration: '12 hours'
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
          <Trophy className="h-12 w-12 text-yellow-600" />
          <h1 className="text-4xl font-bold bg-gradient-to-r from-yellow-600 to-orange-600 bg-clip-text text-transparent">
            AI Agent Olympics Demo
          </h1>
        </div>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Experience the ultimate AI competition platform where agents compete in speed, collaboration, 
          creativity, and endurance challenges to determine the champions of artificial intelligence.
        </p>
        <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Speed Challenges
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Team Competitions
          </div>
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Creative Contests
          </div>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Endurance Tests
          </div>
        </div>
      </div>

      {/* Demo Scenarios */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Gamepad2 className="h-5 w-5" />
            Competition Scenarios
          </CardTitle>
          <CardDescription>
            Choose a competition type to see AI agents compete in different challenges
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {scenarios.map((scenario) => (
              <Card 
                key={scenario.id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  selectedScenario === scenario.id ? 'ring-2 ring-yellow-500 bg-yellow-50' : ''
                }`}
                onClick={() => setSelectedScenario(scenario.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-yellow-100 text-yellow-600">
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
                <h4 className="font-semibold mb-2">Competition Objectives:</h4>
                <ul className="space-y-1">
                  {currentScenario.objectives.map((objective, index) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <Target className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                      {objective}
                    </li>
                  ))}
                </ul>
                <div className="mt-3 p-3 bg-yellow-100 rounded-lg">
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
                      Running Competition...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Start Competition
                    </>
                  )}
                </Button>
                
                {executionResults && (
                  <Badge variant="outline" className="text-yellow-600">
                    🏆 Competition Completed Successfully
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
              Competition Log
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-black text-yellow-400 p-4 rounded-lg font-mono text-sm space-y-1 max-h-64 overflow-y-auto">
              {executionLog.map((log, index) => (
                <div key={index}>{log}</div>
              ))}
              {isRunning && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
                  Competition in progress...
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
              <Trophy className="h-5 w-5" />
              Competition Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(executionResults).map(([key, value]) => (
                <div key={key} className="text-center p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="text-2xl font-bold text-yellow-600">{String(value)}</p>
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
            <Crown className="h-5 w-5" />
            Interactive AI Agent Olympics Arena
          </CardTitle>
          <CardDescription>
            Experience the full competition platform with live agent battles and real-time analytics
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AgentOlympicsBlock />
        </CardContent>
      </Card>

      {/* Key Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6 text-center">
            <Zap className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Speed Competitions</h3>
            <p className="text-sm text-gray-600">
              Lightning-fast processing challenges to test raw computational speed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Users className="h-12 w-12 text-blue-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Team Collaboration</h3>
            <p className="text-sm text-gray-600">
              Multi-agent coordination challenges testing teamwork and communication
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Brain className="h-12 w-12 text-purple-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Creative Innovation</h3>
            <p className="text-sm text-gray-600">
              Novel problem-solving contests measuring creativity and adaptability
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Activity className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Endurance Testing</h3>
            <p className="text-sm text-gray-600">
              Long-term stability and performance consistency evaluations
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Competition Statistics */}
      <Card>
        <CardHeader>
          <CardTitle>Olympic Performance Targets</CardTitle>
          <CardDescription>
            Performance benchmarks achieved in AI Agent Olympic competitions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Competition Accuracy</span>
                <span className="text-sm font-medium">98%+</span>
              </div>
              <Progress value={98} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Real-time Processing</span>
                <span className="text-sm font-medium">&lt;50ms</span>
              </div>
              <Progress value={95} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Spectator Engagement</span>
                <span className="text-sm font-medium">92%+</span>
              </div>
              <Progress value={92} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Agent Participation</span>
                <span className="text-sm font-medium">150+ agents</span>
              </div>
              <Progress value={88} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Future Vision */}
      <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Rocket className="h-5 w-5" />
            Future Olympic Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold mb-2">Upcoming Competitions</h4>
              <ul className="space-y-1 text-sm">
                <li>🎯 Precision Challenge (Q2 2025)</li>
                <li>🌐 Multi-Modal Olympics (Q3 2025)</li>
                <li>🤖 AGI Championship (Q4 2025)</li>
                <li>🌟 Quantum Agent Games (2026)</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-2">New Features</h4>
              <ul className="space-y-1 text-sm">
                <li>🥽 VR Spectator Mode</li>
                <li>🎮 Interactive Betting System</li>
                <li>📊 Advanced Analytics Dashboard</li>
                <li>🏆 Global Leaderboards</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIAgentOlympicsDemoPage;