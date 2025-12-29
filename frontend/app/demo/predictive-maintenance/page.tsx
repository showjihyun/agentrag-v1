'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Shield, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Zap, 
  TrendingUp,
  Play,
  Pause,
  RefreshCw,
  Settings,
  BarChart3,
  Cpu,
  MemoryStick,
  HardDrive,
  Network,
  Clock,
  Wrench,
  Brain,
  Target,
  Lightbulb
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import PredictiveMaintenanceBlock from '@/components/agent-builder/blocks/PredictiveMaintenanceBlock';

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

const PredictiveMaintenanceDemoPage: React.FC = () => {
  const [selectedScenario, setSelectedScenario] = useState<string>('system-monitoring');
  const [isRunning, setIsRunning] = useState(false);
  const [executionResults, setExecutionResults] = useState<any>(null);
  const [executionLog, setExecutionLog] = useState<string[]>([]);

  // Demo scenarios
  const scenarios: DemoScenario[] = [
    {
      id: 'system-monitoring',
      title: 'Real-time System Monitoring',
      description: 'Monitor system health with live metrics and automated anomaly detection',
      icon: <Activity className="h-6 w-6" />,
      complexity: 'Simple',
      estimatedTime: '2-3 minutes',
      objectives: [
        'Monitor CPU, memory, and disk usage in real-time',
        'Detect performance anomalies automatically',
        'Track system health across all components',
        'Generate health reports with risk assessment'
      ],
      expectedOutcome: 'Comprehensive system monitoring with proactive issue detection'
    },
    {
      id: 'anomaly-detection',
      title: 'ML-Powered Anomaly Detection',
      description: 'Advanced machine learning algorithms for intelligent anomaly detection',
      icon: <Brain className="h-6 w-6" />,
      complexity: 'Moderate',
      estimatedTime: '3-5 minutes',
      objectives: [
        'Use ML models (Isolation Forest, Random Forest) for anomaly detection',
        'Implement rule-based and trend-based detection',
        'Classify anomaly types and severity levels',
        'Provide confidence scores and impact predictions'
      ],
      expectedOutcome: 'Intelligent anomaly detection with high accuracy and low false positives'
    },
    {
      id: 'predictive-maintenance',
      title: 'Predictive Maintenance Planning',
      description: 'AI-driven maintenance scheduling and task optimization',
      icon: <Target className="h-6 w-6" />,
      complexity: 'Complex',
      estimatedTime: '5-7 minutes',
      objectives: [
        'Predict maintenance needs before failures occur',
        'Optimize maintenance schedules for minimal disruption',
        'Estimate task duration and success probability',
        'Handle dependencies and resource constraints'
      ],
      expectedOutcome: 'Proactive maintenance planning that prevents system failures'
    },
    {
      id: 'self-healing',
      title: 'Automated Self-Healing',
      description: 'Autonomous system recovery and emergency response capabilities',
      icon: <Zap className="h-6 w-6" />,
      complexity: 'Expert',
      estimatedTime: '7-10 minutes',
      objectives: [
        'Automatically respond to critical system issues',
        'Execute emergency scaling and resource optimization',
        'Implement rollback strategies for failed operations',
        'Maintain system availability during incidents'
      ],
      expectedOutcome: 'Fully autonomous system that heals itself without human intervention'
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
      'system-monitoring': [
        { message: 'Initializing system monitoring...', duration: 1000 },
        { message: 'Collecting real-time metrics...', duration: 2000 },
        { message: 'Analyzing system performance...', duration: 1500 },
        { message: 'Generating health report...', duration: 1000 },
        { message: 'System monitoring active', duration: 500 }
      ],
      'anomaly-detection': [
        { message: 'Loading ML models...', duration: 1500 },
        { message: 'Training anomaly detection models...', duration: 3000 },
        { message: 'Analyzing historical patterns...', duration: 2000 },
        { message: 'Detecting current anomalies...', duration: 1500 },
        { message: 'Classifying anomaly types...', duration: 1000 },
        { message: 'Anomaly detection system ready', duration: 500 }
      ],
      'predictive-maintenance': [
        { message: 'Analyzing system wear patterns...', duration: 2000 },
        { message: 'Predicting failure probabilities...', duration: 2500 },
        { message: 'Optimizing maintenance schedules...', duration: 2000 },
        { message: 'Calculating resource requirements...', duration: 1500 },
        { message: 'Generating maintenance plan...', duration: 1000 },
        { message: 'Predictive maintenance system active', duration: 500 }
      ],
      'self-healing': [
        { message: 'Initializing self-healing protocols...', duration: 1500 },
        { message: 'Setting up emergency response systems...', duration: 2000 },
        { message: 'Configuring automated recovery procedures...', duration: 2500 },
        { message: 'Testing rollback mechanisms...', duration: 2000 },
        { message: 'Activating autonomous monitoring...', duration: 1500 },
        { message: 'Self-healing system operational', duration: 500 }
      ]
    };

    return stepMap[scenarioId] || [];
  };

  const generateScenarioResults = (scenarioId: string) => {
    const resultMap: Record<string, any> = {
      'system-monitoring': {
        systemStatus: 'Healthy',
        componentsMonitored: 8,
        metricsCollected: 12,
        healthScore: 94,
        alertsGenerated: 0,
        monitoringAccuracy: 98.5
      },
      'anomaly-detection': {
        modelsDeployed: 3,
        anomaliesDetected: 2,
        detectionAccuracy: 96.2,
        falsePositiveRate: 2.1,
        averageConfidence: 89.7,
        responseTime: 150
      },
      'predictive-maintenance': {
        tasksScheduled: 5,
        maintenanceWindows: 3,
        predictedFailures: 1,
        preventedDowntime: '4.2 hours',
        costSavings: '$2,340',
        scheduleOptimization: 87.3
      },
      'self-healing': {
        healingRulesActive: 12,
        emergencyResponseTime: '45 seconds',
        automaticRecoveries: 3,
        systemAvailability: 99.97,
        interventionReduction: 78.5,
        healingSuccessRate: 94.2
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
          <Shield className="h-12 w-12 text-blue-600" />
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Predictive Maintenance & Self-Healing Demo
          </h1>
        </div>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          Experience AI-powered system monitoring, anomaly detection, and automated maintenance 
          that keeps your infrastructure running smoothly 24/7.
        </p>
        <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Real-time Monitoring
          </div>
          <div className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            ML-Powered Detection
          </div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Automated Healing
          </div>
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Predictive Planning
          </div>
        </div>
      </div>

      {/* Demo Scenarios */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5" />
            Demo Scenarios
          </CardTitle>
          <CardDescription>
            Choose a scenario to explore different aspects of predictive maintenance and self-healing
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {scenarios.map((scenario) => (
              <Card 
                key={scenario.id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  selectedScenario === scenario.id ? 'ring-2 ring-blue-500 bg-blue-50' : ''
                }`}
                onClick={() => setSelectedScenario(scenario.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <div className="p-2 rounded-lg bg-blue-100 text-blue-600">
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
                      <CheckCircle className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                      {objective}
                    </li>
                  ))}
                </ul>
                <div className="mt-3 p-3 bg-blue-100 rounded-lg">
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
                      Running Scenario...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4" />
                      Execute Scenario
                    </>
                  )}
                </Button>
                
                {executionResults && (
                  <Badge variant="outline" className="text-green-600">
                    ✅ Scenario Completed Successfully
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
              <BarChart3 className="h-5 w-5" />
              Execution Log
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm space-y-1 max-h-64 overflow-y-auto">
              {executionLog.map((log, index) => (
                <div key={index}>{log}</div>
              ))}
              {isRunning && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  Processing...
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
              Execution Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(executionResults).map(([key, value]) => (
                <div key={key} className="text-center p-3 bg-gray-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{String(value)}</p>
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
            <Settings className="h-5 w-5" />
            Interactive Predictive Maintenance System
          </CardTitle>
          <CardDescription>
            Explore the full predictive maintenance and self-healing system with live data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PredictiveMaintenanceBlock />
        </CardContent>
      </Card>

      {/* Key Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6 text-center">
            <Activity className="h-12 w-12 text-blue-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Real-time Monitoring</h3>
            <p className="text-sm text-gray-600">
              Continuous system monitoring with live metrics and performance tracking
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Brain className="h-12 w-12 text-purple-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">ML-Powered Detection</h3>
            <p className="text-sm text-gray-600">
              Advanced machine learning algorithms for intelligent anomaly detection
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Target className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Predictive Planning</h3>
            <p className="text-sm text-gray-600">
              AI-driven maintenance scheduling and resource optimization
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6 text-center">
            <Zap className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
            <h3 className="font-semibold mb-2">Automated Healing</h3>
            <p className="text-sm text-gray-600">
              Autonomous system recovery and emergency response capabilities
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>System Performance Targets</CardTitle>
          <CardDescription>
            Performance benchmarks achieved by the predictive maintenance system
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Anomaly Detection Accuracy</span>
                <span className="text-sm font-medium">95%+</span>
              </div>
              <Progress value={95} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">System Availability</span>
                <span className="text-sm font-medium">99.9%</span>
              </div>
              <Progress value={99.9} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Response Time</span>
                <span className="text-sm font-medium">&lt;100ms</span>
              </div>
              <Progress value={90} className="h-2" />
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm">Maintenance Efficiency</span>
                <span className="text-sm font-medium">85%+</span>
              </div>
              <Progress value={85} className="h-2" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PredictiveMaintenanceDemoPage;