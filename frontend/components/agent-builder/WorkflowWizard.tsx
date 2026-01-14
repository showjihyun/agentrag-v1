'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { getAvailableProviders, getModelsForProvider } from '@/lib/llm-models';
import {
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Users,
  MessageSquare,
  Sparkles,
  Settings,
  Rocket,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface WizardStep {
  id: number;
  name: string;
  description: string;
  icon: React.ReactNode;
}

const steps: WizardStep[] = [
  {
    id: 1,
    name: 'Select Type',
    description: 'Choose the type of workflow you want to create',
    icon: <Sparkles className="h-5 w-5" />,
  },
  {
    id: 2,
    name: 'Basic Info',
    description: 'Enter name and description',
    icon: <Settings className="h-5 w-5" />,
  },
  {
    id: 3,
    name: 'Configuration',
    description: 'Configure your workflow',
    icon: <Users className="h-5 w-5" />,
  },
  {
    id: 4,
    name: 'Complete',
    description: 'Review settings and create',
    icon: <Rocket className="h-5 w-5" />,
  },
];

interface WorkflowWizardProps {
  onComplete?: (data: any) => void;
  onCancel?: () => void;
}

export function WorkflowWizard({ onComplete, onCancel }: WorkflowWizardProps) {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    type: '',
    name: '',
    description: '',
    orchestration: 'sequential',
    llmProvider: 'ollama',
    llmModel: 'llama3.1',
  });

  const progress = ((currentStep + 1) / steps.length) * 100;

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    if (formData.type === 'agentflow') {
      router.push(`/agent-builder/agentflows/new?name=${encodeURIComponent(formData.name)}&description=${encodeURIComponent(formData.description)}&orchestration=${formData.orchestration}`);
    } else if (formData.type === 'chatflow') {
      router.push(`/agent-builder/chatflows/new?name=${encodeURIComponent(formData.name)}&description=${encodeURIComponent(formData.description)}&provider=${formData.llmProvider}&model=${formData.llmModel}`);
    }
    onComplete?.(formData);
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 0:
        return formData.type !== '';
      case 1:
        return formData.name.trim() !== '';
      case 2:
        return true;
      case 3:
        return true;
      default:
        return false;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card
                className={cn(
                  'cursor-pointer transition-all duration-300 hover:shadow-lg',
                  formData.type === 'agentflow'
                    ? 'border-purple-500 bg-purple-50 dark:bg-purple-950/20 ring-2 ring-purple-500'
                    : 'hover:border-purple-300'
                )}
                onClick={() => setFormData({ ...formData, type: 'agentflow' })}
              >
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-lg bg-purple-100 dark:bg-purple-900">
                      <Users className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">Agentflow</CardTitle>
                      <CardDescription>Multi-Agent System</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Create workflows where multiple AI agents collaborate to perform complex tasks.
                  </p>
                  <div className="flex gap-2 mt-4">
                    <Badge variant="secondary">Sequential</Badge>
                    <Badge variant="secondary">Parallel</Badge>
                    <Badge variant="secondary">Hierarchical</Badge>
                  </div>
                </CardContent>
              </Card>

              <Card
                className={cn(
                  'cursor-pointer transition-all duration-300 hover:shadow-lg',
                  formData.type === 'chatflow'
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-950/20 ring-2 ring-blue-500'
                    : 'hover:border-blue-300'
                )}
                onClick={() => setFormData({ ...formData, type: 'chatflow' })}
              >
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-lg bg-blue-100 dark:bg-blue-900">
                      <MessageSquare className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">Chatflow</CardTitle>
                      <CardDescription>Conversational AI Chatbot</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Create RAG-based chatbots and AI assistants to interact with users.
                  </p>
                  <div className="flex gap-2 mt-4">
                    <Badge variant="secondary">RAG</Badge>
                    <Badge variant="secondary">Memory</Badge>
                    <Badge variant="secondary">Tool Integration</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input
                id="name"
                placeholder="e.g., Customer Support Chatbot"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="text-lg"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe what this workflow does..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
              />
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            {formData.type === 'agentflow' ? (
              <div className="space-y-2">
                <Label htmlFor="orchestration">Orchestration Method</Label>
                <Select
                  value={formData.orchestration}
                  onValueChange={(value) => setFormData({ ...formData, orchestration: value })}
                >
                  <SelectTrigger id="orchestration">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sequential">Sequential Execution</SelectItem>
                    <SelectItem value="parallel">Parallel Execution</SelectItem>
                    <SelectItem value="hierarchical">Hierarchical Execution</SelectItem>
                    <SelectItem value="adaptive">Adaptive Execution</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-sm text-muted-foreground">
                  Choose how agents will collaborate
                </p>
              </div>
            ) : (
              <>
                <div className="space-y-2">
                  <Label htmlFor="llmProvider">LLM Provider</Label>
                  <Select
                    value={formData.llmProvider}
                    onValueChange={(value) => setFormData({ ...formData, llmProvider: value })}
                  >
                    <SelectTrigger id="llmProvider">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {getAvailableProviders().map((provider) => (
                        <SelectItem key={provider.id} value={provider.id}>
                          {provider.name} {provider.type === 'local' ? '(Local)' : ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="llmModel">Model</Label>
                  <Select
                    value={formData.llmModel}
                    onValueChange={(value) => setFormData({ ...formData, llmModel: value })}
                  >
                    <SelectTrigger id="llmModel">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {getModelsForProvider(formData.llmProvider).map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          {model.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </>
            )}
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900 mb-4">
                <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-2xl font-bold mb-2">Ready to Go!</h3>
              <p className="text-muted-foreground">
                Review your settings and create the workflow
              </p>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Settings Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Type</p>
                    <p className="font-medium">
                      {formData.type === 'agentflow' ? 'Agentflow' : 'Chatflow'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Name</p>
                    <p className="font-medium">{formData.name}</p>
                  </div>
                  {formData.description && (
                    <div className="col-span-2">
                      <p className="text-sm text-muted-foreground">Description</p>
                      <p className="font-medium">{formData.description}</p>
                    </div>
                  )}
                  {formData.type === 'agentflow' ? (
                    <div>
                      <p className="text-sm text-muted-foreground">Orchestration</p>
                      <p className="font-medium capitalize">{formData.orchestration}</p>
                    </div>
                  ) : (
                    <>
                      <div>
                        <p className="text-sm text-muted-foreground">LLM Provider</p>
                        <p className="font-medium capitalize">{formData.llmProvider}</p>
                      </div>
                      <div>
                        <p className="text-sm text-muted-foreground">Model</p>
                        <p className="font-medium">{formData.llmModel}</p>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">
            Step {currentStep + 1} / {steps.length}
          </span>
          <span className="text-sm text-muted-foreground">{Math.round(progress)}%</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Step Indicators */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center">
                <div
                  className={cn(
                    'flex items-center justify-center w-12 h-12 rounded-full transition-all duration-300',
                    currentStep >= index
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                  )}
                >
                  {currentStep > index ? (
                    <CheckCircle className="h-6 w-6" />
                  ) : (
                    step.icon
                  )}
                </div>
                <div className="mt-2 text-center">
                  <p className={cn(
                    'text-sm font-medium',
                    currentStep >= index ? 'text-foreground' : 'text-muted-foreground'
                  )}>
                    {step.name}
                  </p>
                  <p className="text-xs text-muted-foreground hidden md:block max-w-[120px]">
                    {step.description}
                  </p>
                </div>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'flex-1 h-0.5 mx-2 transition-all duration-300',
                    currentStep > index
                      ? 'bg-gradient-to-r from-purple-600 to-blue-600'
                      : 'bg-gray-200 dark:bg-gray-700'
                  )}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-2xl">{steps[currentStep].name}</CardTitle>
          <CardDescription className="text-base">
            {steps[currentStep].description}
          </CardDescription>
        </CardHeader>
        <CardContent className="min-h-[300px]">
          {renderStepContent()}
        </CardContent>
      </Card>

      {/* Navigation Buttons */}
      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={currentStep === 0 ? onCancel : handlePrevious}
          size="lg"
        >
          <ChevronLeft className="mr-2 h-5 w-5" />
          {currentStep === 0 ? 'Cancel' : 'Previous'}
        </Button>
        <Button
          onClick={handleNext}
          disabled={!isStepValid()}
          size="lg"
          className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
        >
          {currentStep === steps.length - 1 ? (
            <>
              <Rocket className="mr-2 h-5 w-5" />
              Create
            </>
          ) : (
            <>
              Next
              <ChevronRight className="ml-2 h-5 w-5" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
