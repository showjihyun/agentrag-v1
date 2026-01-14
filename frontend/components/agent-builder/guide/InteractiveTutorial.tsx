/**
 * Interactive Tutorial System
 * Interactive tutorial for learning orchestration patterns
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { 
  Play,
  Pause,
  SkipForward,
  SkipBack,
  CheckCircle,
  Circle,
  BookOpen,
  Lightbulb,
  Target,
  Users,
  MessageSquare,
  Route,
  Hexagon,
  Bell,
  RefreshCw,
  ArrowRight,
  ArrowLeft,
  X,
  HelpCircle,
  Star,
  Clock,
  Award
} from 'lucide-react';
import { OrchestrationTypeValue, ORCHESTRATION_TYPES } from '@/lib/constants/orchestration';

interface TutorialStep {
  id: string;
  title: string;
  description: string;
  content: React.ReactNode;
  action?: {
    type: 'click' | 'input' | 'select' | 'wait';
    target?: string;
    value?: any;
    validation?: (value: any) => boolean;
  };
  tips?: string[];
  duration?: number; // in seconds
}

interface Tutorial {
  id: string;
  title: string;
  description: string;
  category: 'beginner' | 'intermediate' | 'advanced';
  estimatedTime: number; // in minutes
  patternType?: OrchestrationTypeValue;
  prerequisites?: string[];
  steps: TutorialStep[];
}

interface InteractiveTutorialProps {
  tutorialId?: string;
  onComplete?: (tutorialId: string, score: number) => void;
  onClose?: () => void;
}

export const InteractiveTutorial: React.FC<InteractiveTutorialProps> = ({
  tutorialId,
  onComplete,
  onClose
}) => {
  const [selectedTutorial, setSelectedTutorial] = useState<Tutorial | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [isPlaying, setIsPlaying] = useState(false);
  const [userProgress, setUserProgress] = useState<Record<string, any>>({});
  const [startTime, setStartTime] = useState<Date | null>(null);

  // Tutorial definitions
  const tutorials: Tutorial[] = [
    {
      id: 'consensus_basics',
      title: 'Consensus Building Pattern Basics',
      description: 'Learn how multiple Agents collaborate to make optimal decisions.',
      category: 'beginner',
      estimatedTime: 15,
      patternType: 'consensus_building',
      steps: [
        {
          id: 'intro',
          title: 'Introduction to Consensus Building Pattern',
          description: 'Learn the basic concepts and use cases of the consensus building pattern.',
          content: (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <MessageSquare className="h-8 w-8 text-blue-600" />
                <h3 className="text-xl font-semibold">Consensus Building Pattern</h3>
              </div>
              
              <p className="text-gray-700">
                The consensus building pattern is a method where multiple Agents discuss and negotiate to reach consensus on the optimal solution.
              </p>
              
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Key Features:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>Agents with diverse perspectives participate</li>
                  <li>Decision-making through voting mechanisms</li>
                  <li>Round-based discussion progression</li>
                  <li>Configurable consensus threshold</li>
                </ul>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Use Cases:</h4>
                <ul className="list-disc list-inside space-y-1 text-sm">
                  <li>Strategy formulation and policy decisions</li>
                  <li>Complex problem solving</li>
                  <li>Quality evaluation and review</li>
                  <li>Risk analysis</li>
                </ul>
              </div>
            </div>
          ),
          duration: 120
        },
        {
          id: 'voting_mechanisms',
          title: 'Understanding Voting Mechanisms',
          description: 'Learn the characteristics and selection criteria of various voting methods.',
          content: (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">Types of Voting Mechanisms</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold text-blue-600 mb-2">Simple Majority</h4>
                  <p className="text-sm text-gray-600 mb-2">The option with the most votes wins</p>
                  <div className="text-xs text-gray-500">
                    <p>✅ Quick decisions</p>
                    <p>❌ May ignore minority opinions</p>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold text-green-600 mb-2">Weighted Voting</h4>
                  <p className="text-sm text-gray-600 mb-2">Weights applied based on Agent expertise</p>
                  <div className="text-xs text-gray-500">
                    <p>✅ Reflects expertise</p>
                    <p>❌ Complex weight configuration</p>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold text-purple-600 mb-2">Unanimous</h4>
                  <p className="text-sm text-gray-600 mb-2">Requires agreement from all Agents</p>
                  <div className="text-xs text-gray-500">
                    <p>✅ Strong consensus</p>
                    <p>❌ Time-consuming</p>
                  </div>
                </div>
                
                <div className="border rounded-lg p-4">
                  <h4 className="font-semibold text-orange-600 mb-2">Supermajority</h4>
                  <p className="text-sm text-gray-600 mb-2">Requires 2/3 or more agreement</p>
                  <div className="text-xs text-gray-500">
                    <p>✅ Stable consensus</p>
                    <p>❌ High threshold</p>
                  </div>
                </div>
              </div>
            </div>
          ),
          duration: 180
        },
        {
          id: 'configuration_practice',
          title: 'Configuration Practice',
          description: 'Let\'s configure the main settings of the consensus building pattern.',
          content: (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">Configuration Practice</h3>
              
              <Alert>
                <Lightbulb className="h-4 w-4" />
                <AlertDescription>
                  Select the appropriate settings for this scenario: "5 experts deciding on a new product launch strategy"
                </AlertDescription>
              </Alert>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Voting Mechanism</label>
                  <div className="grid grid-cols-2 gap-2">
                    {['majority', 'weighted', 'unanimous', 'supermajority'].map((mechanism) => (
                      <button
                        key={mechanism}
                        className={`p-2 border rounded text-sm ${
                          userProgress.voting_mechanism === mechanism 
                            ? 'bg-blue-100 border-blue-500' 
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => setUserProgress(prev => ({ ...prev, voting_mechanism: mechanism }))}
                      >
                        {mechanism === 'majority' ? 'Simple Majority' :
                         mechanism === 'weighted' ? 'Weighted Voting' :
                         mechanism === 'unanimous' ? 'Unanimous' : 'Supermajority'}
                      </button>
                    ))}
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Consensus Threshold: {userProgress.consensus_threshold || 0.7}
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="1.0"
                    step="0.05"
                    value={userProgress.consensus_threshold || 0.7}
                    onChange={(e) => setUserProgress(prev => ({ 
                      ...prev, 
                      consensus_threshold: parseFloat(e.target.value) 
                    }))}
                    className="w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium mb-2">Maximum Rounds</label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={userProgress.max_rounds || 5}
                    onChange={(e) => setUserProgress(prev => ({ 
                      ...prev, 
                      max_rounds: parseInt(e.target.value) 
                    }))}
                    className="w-full p-2 border rounded"
                  />
                </div>
              </div>
            </div>
          ),
          action: {
            type: 'select',
            validation: (progress) => 
              progress.voting_mechanism && 
              progress.consensus_threshold >= 0.5 && 
              progress.max_rounds > 0
          },
          duration: 300
        },
        {
          id: 'best_practices',
          title: 'Best Practices',
          description: 'Learn tips and considerations when using the consensus building pattern.',
          content: (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">Best Practices and Tips</h3>
              
              <div className="space-y-4">
                <div className="bg-green-50 border-l-4 border-green-500 p-4">
                  <h4 className="font-semibold text-green-800 mb-2">✅ Recommendations</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-green-700">
                    <li>Clearly define Agent roles</li>
                    <li>Set an appropriate consensus threshold (usually 60-80%)</li>
                    <li>Set discussion time limits to improve efficiency</li>
                    <li>Use a mediator Agent to prevent deadlocks</li>
                  </ul>
                </div>
                
                <div className="bg-red-50 border-l-4 border-red-500 p-4">
                  <h4 className="font-semibold text-red-800 mb-2">❌ Cautions</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-red-700">
                    <li>Too many Agents delay decision-making</li>
                    <li>100% consensus can take a long time</li>
                    <li>Be careful of bias when setting weights</li>
                    <li>Set maximum rounds to prevent infinite loops</li>
                  </ul>
                </div>
                
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
                  <h4 className="font-semibold text-blue-800 mb-2">💡 Performance Optimization</h4>
                  <ul className="list-disc list-inside space-y-1 text-sm text-blue-700">
                    <li>Identify clear preferences through initial voting</li>
                    <li>Group similar opinions to improve efficiency</li>
                    <li>Use previous consensus results as learning data</li>
                    <li>Track progress with real-time monitoring</li>
                  </ul>
                </div>
              </div>
            </div>
          ),
          duration: 240
        },
        {
          id: 'completion',
          title: 'Tutorial Complete',
          description: 'You have completed the consensus building pattern tutorial!',
          content: (
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <Award className="h-16 w-16 text-yellow-500" />
              </div>
              
              <h3 className="text-2xl font-bold text-green-600">Congratulations! 🎉</h3>
              <p className="text-gray-600">You have successfully completed the consensus building pattern tutorial.</p>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="font-semibold mb-2">Learning Summary</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Completion Time</p>
                    <p className="font-medium">
                      {startTime ? Math.round((Date.now() - startTime.getTime()) / 60000) : 0} min
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Completion Rate</p>
                    <p className="font-medium">100%</p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-2">
                <h4 className="font-semibold">Next Steps</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <Button variant="outline" size="sm">
                    Learn Dynamic Routing
                  </Button>
                  <Button variant="outline" size="sm">
                    Apply to Real Project
                  </Button>
                </div>
              </div>
            </div>
          ),
          duration: 60
        }
      ]
    },
    {
      id: 'swarm_intelligence_intro',
      title: 'Introduction to Swarm Intelligence Pattern',
      description: 'Learn optimization algorithms that mimic swarm behavior in nature.',
      category: 'intermediate',
      estimatedTime: 20,
      patternType: 'swarm_intelligence',
      prerequisites: ['consensus_basics'],
      steps: [
        {
          id: 'swarm_intro',
          title: 'Swarm Intelligence Concept',
          description: 'Learn about swarm behavior in nature and its application in AI.',
          content: (
            <div className="space-y-4">
              <div className="flex items-center space-x-2 mb-4">
                <Hexagon className="h-8 w-8 text-orange-600" />
                <h3 className="text-xl font-semibold">Swarm Intelligence Pattern</h3>
              </div>
              
              <p className="text-gray-700">
                Swarm intelligence is a method that mimics collective behavior of ants, bees, bird flocks, etc. in nature to solve complex problems.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-orange-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">🐜 Ant Colony Optimization (ACO)</h4>
                  <p className="text-sm text-gray-600">
                    Mimics how ants find optimal paths using pheromones
                  </p>
                </div>
                
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">🐦 Particle Swarm Optimization (PSO)</h4>
                  <p className="text-sm text-gray-600">
                    Optimization algorithm mimicking bird flock behavior
                  </p>
                </div>
              </div>
            </div>
          ),
          duration: 150
        }
        // Additional steps would be added here
      ]
    }
  ];

  // Initialize tutorial
  useEffect(() => {
    if (tutorialId) {
      const tutorial = tutorials.find(t => t.id === tutorialId);
      if (tutorial) {
        setSelectedTutorial(tutorial);
        setStartTime(new Date());
      }
    }
  }, [tutorialId]);

  // Auto-advance for timed steps
  useEffect(() => {
    if (!isPlaying || !selectedTutorial) return;

    const currentStep = selectedTutorial.steps[currentStepIndex];
    if (currentStep?.duration && !currentStep.action) {
      const timer = setTimeout(() => {
        nextStep();
      }, currentStep.duration * 1000);

      return () => clearTimeout(timer);
    }
  }, [currentStepIndex, isPlaying, selectedTutorial]);

  const nextStep = useCallback(() => {
    if (!selectedTutorial) return;

    if (currentStepIndex < selectedTutorial.steps.length - 1) {
      setCurrentStepIndex(prev => prev + 1);
      setCompletedSteps(prev => new Set([...prev, selectedTutorial.steps[currentStepIndex].id]));
    } else {
      // Tutorial completed
      const score = calculateScore();
      onComplete?.(selectedTutorial.id, score);
    }
  }, [currentStepIndex, selectedTutorial, onComplete]);

  const prevStep = useCallback(() => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(prev => prev - 1);
    }
  }, [currentStepIndex]);

  const calculateScore = () => {
    if (!selectedTutorial) return 0;
    
    const completionRate = completedSteps.size / selectedTutorial.steps.length;
    const timeBonus = startTime ? Math.max(0, 1 - (Date.now() - startTime.getTime()) / (selectedTutorial.estimatedTime * 60000)) : 0;
    
    return Math.round((completionRate * 70 + timeBonus * 30) * 100) / 100;
  };

  const validateCurrentStep = () => {
    if (!selectedTutorial) return false;
    
    const currentStep = selectedTutorial.steps[currentStepIndex];
    if (currentStep.action?.validation) {
      return currentStep.action.validation(userProgress);
    }
    
    return true;
  };

  if (!selectedTutorial) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center">
            <BookOpen className="h-6 w-6 mr-2" />
            Interactive Tutorial
          </CardTitle>
          <CardDescription>Learn orchestration patterns step by step</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tutorials.map((tutorial) => (
              <Card key={tutorial.id} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <Badge className={
                      tutorial.category === 'beginner' ? 'bg-green-100 text-green-800' :
                      tutorial.category === 'intermediate' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }>
                      {tutorial.category === 'beginner' ? 'Beginner' :
                       tutorial.category === 'intermediate' ? 'Intermediate' : 'Advanced'}
                    </Badge>
                    <div className="flex items-center text-sm text-gray-500">
                      <Clock className="h-4 w-4 mr-1" />
                      {tutorial.estimatedTime} min
                    </div>
                  </div>
                  
                  <h3 className="font-semibold text-lg mb-2">{tutorial.title}</h3>
                  <p className="text-gray-600 text-sm mb-3">{tutorial.description}</p>
                  
                  {tutorial.prerequisites && (
                    <div className="mb-3">
                      <p className="text-xs text-gray-500 mb-1">Prerequisites:</p>
                      <div className="flex flex-wrap gap-1">
                        {tutorial.prerequisites.map((prereq) => (
                          <Badge key={prereq} variant="outline" className="text-xs">
                            {prereq}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <Button 
                    className="w-full"
                    onClick={() => {
                      setSelectedTutorial(tutorial);
                      setStartTime(new Date());
                    }}
                  >
                    <Play className="h-4 w-4 mr-2" />
                    Start
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentStep = selectedTutorial.steps[currentStepIndex];
  const progress = ((currentStepIndex + 1) / selectedTutorial.steps.length) * 100;

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center">
              <BookOpen className="h-6 w-6 mr-2" />
              {selectedTutorial.title}
            </CardTitle>
            <CardDescription>
              Step {currentStepIndex + 1} / {selectedTutorial.steps.length}: {currentStep.title}
            </CardDescription>
          </div>
          
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-600">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="w-full" />
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Step Content */}
        <div className="min-h-[400px]">
          <h3 className="text-xl font-semibold mb-4">{currentStep.title}</h3>
          <p className="text-gray-600 mb-6">{currentStep.description}</p>
          
          {currentStep.content}
          
          {currentStep.tips && (
            <div className="mt-6 bg-blue-50 p-4 rounded-lg">
              <h4 className="font-semibold text-blue-800 mb-2 flex items-center">
                <Lightbulb className="h-4 w-4 mr-1" />
                Tips
              </h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-blue-700">
                {currentStep.tips.map((tip, index) => (
                  <li key={index}>{tip}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-4 border-t">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={prevStep}
              disabled={currentStepIndex === 0}
            >
              <ArrowLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPlaying(!isPlaying)}
            >
              {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
          </div>
          
          <div className="flex items-center space-x-2">
            {currentStep.action ? (
              <Button
                onClick={nextStep}
                disabled={!validateCurrentStep()}
              >
                {currentStepIndex === selectedTutorial.steps.length - 1 ? 'Complete' : 'Next'}
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={nextStep}
              >
                {currentStepIndex === selectedTutorial.steps.length - 1 ? 'Complete' : 'Next'}
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};