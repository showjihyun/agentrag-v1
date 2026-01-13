/**
 * Plugin Installation Wizard
 * 단계별 플러그인 설치 프로세스 UI
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Stepper,
  StepperItem,
  StepperSeparator,
} from '@/components/ui/stepper';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  Package,
  Download,
  CheckCircle,
  AlertCircle,
  XCircle,
  Loader2,
  ChevronRight,
  ChevronDown,
  Github,
  Globe,
  FileText,
  Settings,
  Shield,
  Zap,
  RefreshCw,
  Eye,
  Terminal,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import { toast } from 'sonner';

export interface PluginSource {
  type: 'github' | 'url' | 'local' | 'marketplace';
  url?: string;
  repository?: string;
  branch?: string;
  tag?: string;
  localPath?: string;
  marketplaceId?: string;
}

export interface PluginDependency {
  name: string;
  version: string;
  required: boolean;
  installed: boolean;
  compatible: boolean;
  description?: string;
}

export interface PluginManifest {
  name: string;
  version: string;
  description: string;
  author: string;
  license: string;
  homepage?: string;
  repository?: string;
  keywords: string[];
  dependencies: PluginDependency[];
  permissions: string[];
  configSchema?: any;
  minSystemVersion?: string;
}

export interface InstallationStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  canSkip?: boolean;
  canRetry?: boolean;
  progress?: number;
  logs?: string[];
  error?: string;
}

interface PluginInstallationWizardProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (pluginId: string) => void;
  onError: (error: string) => void;
}

export function PluginInstallationWizard({
  isOpen,
  onClose,
  onComplete,
  onError,
}: PluginInstallationWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [source, setSource] = useState<PluginSource>({ type: 'github' });
  const [manifest, setManifest] = useState<PluginManifest | null>(null);
  const [dependencies, setDependencies] = useState<PluginDependency[]>([]);
  const [installationSteps, setInstallationSteps] = useState<InstallationStep[]>([]);
  const [isInstalling, setIsInstalling] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [autoRetry, setAutoRetry] = useState(true);
  const [installationId, setInstallationId] = useState<string>('');
  
  const logScrollRef = useRef<HTMLDivElement>(null);

  const steps = [
    { id: 'source', title: 'Source', description: 'Select plugin source' },
    { id: 'validation', title: 'Validation', description: 'Validate plugin manifest' },
    { id: 'dependencies', title: 'Dependencies', description: 'Check dependencies' },
    { id: 'configuration', title: 'Configuration', description: 'Configure plugin settings' },
    { id: 'installation', title: 'Installation', description: 'Install plugin' },
    { id: 'confirmation', title: 'Complete', description: 'Installation complete' },
  ];

  // 로그 자동 스크롤
  useEffect(() => {
    if (logScrollRef.current) {
      logScrollRef.current.scrollTop = logScrollRef.current.scrollHeight;
    }
  }, [installationSteps]);

  // 소스 검증
  const validateSource = async (): Promise<boolean> => {
    try {
      const response = await fetch('/api/agent-builder/plugins/validate-source', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(source),
      });

      if (!response.ok) {
        throw new Error('Failed to validate source');
      }

      const data = await response.json();
      setManifest(data.manifest);
      return true;
    } catch (error) {
      toast.error('Failed to validate plugin source');
      return false;
    }
  };

  // 의존성 검사
  const checkDependencies = async (): Promise<boolean> => {
    if (!manifest) return false;

    try {
      const response = await fetch('/api/agent-builder/plugins/check-dependencies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dependencies: manifest.dependencies }),
      });

      const data = await response.json();
      setDependencies(data.dependencies);
      
      // 필수 의존성이 모두 만족되는지 확인
      const missingRequired = data.dependencies.filter(
        (dep: PluginDependency) => dep.required && (!dep.installed || !dep.compatible)
      );
      
      return missingRequired.length === 0;
    } catch (error) {
      toast.error('Failed to check dependencies');
      return false;
    }
  };

  // 플러그인 설치
  const installPlugin = async (): Promise<void> => {
    setIsInstalling(true);
    
    const steps: InstallationStep[] = [
      {
        id: 'download',
        title: 'Downloading Plugin',
        description: 'Downloading plugin files...',
        status: 'pending',
        progress: 0,
        logs: [],
      },
      {
        id: 'extract',
        title: 'Extracting Files',
        description: 'Extracting plugin files...',
        status: 'pending',
        progress: 0,
        logs: [],
      },
      {
        id: 'validate',
        title: 'Validating Plugin',
        description: 'Validating plugin structure...',
        status: 'pending',
        progress: 0,
        logs: [],
      },
      {
        id: 'dependencies',
        title: 'Installing Dependencies',
        description: 'Installing required dependencies...',
        status: 'pending',
        progress: 0,
        logs: [],
        canSkip: true,
      },
      {
        id: 'register',
        title: 'Registering Plugin',
        description: 'Registering plugin in system...',
        status: 'pending',
        progress: 0,
        logs: [],
      },
      {
        id: 'activate',
        title: 'Activating Plugin',
        description: 'Activating plugin...',
        status: 'pending',
        progress: 0,
        logs: [],
      },
    ];

    setInstallationSteps(steps);

    try {
      const response = await fetch('/api/agent-builder/plugins/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source,
          manifest,
          autoRetry,
        }),
      });

      if (!response.ok) {
        throw new Error('Installation failed');
      }

      const data = await response.json();
      setInstallationId(data.installationId);

      // WebSocket으로 실시간 진행 상황 수신
      const ws = new WebSocket(`/api/agent-builder/plugins/install-progress/${data.installationId}`);
      
      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        updateInstallationStep(update);
      };

      ws.onclose = () => {
        setIsInstalling(false);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsInstalling(false);
      };

    } catch (error) {
      setIsInstalling(false);
      onError('Installation failed');
    }
  };

  // 설치 단계 업데이트
  const updateInstallationStep = (update: any) => {
    setInstallationSteps(prev => prev.map(step => {
      if (step.id === update.stepId) {
        return {
          ...step,
          status: update.status,
          progress: update.progress,
          logs: [...(step.logs || []), ...(update.logs || [])],
          error: update.error,
        };
      }
      return step;
    }));

    if (update.status === 'completed' && update.stepId === 'activate') {
      toast.success('Plugin installed successfully!');
      onComplete(update.pluginId);
    }
  };

  // 단계 재시도
  const retryStep = async (stepId: string) => {
    try {
      await fetch(`/api/agent-builder/plugins/retry-step/${installationId}/${stepId}`, {
        method: 'POST',
      });
    } catch (error) {
      toast.error('Failed to retry step');
    }
  };

  // 다음 단계로
  const nextStep = async () => {
    if (currentStep === 1) {
      const isValid = await validateSource();
      if (!isValid) return;
    } else if (currentStep === 2) {
      const depsOk = await checkDependencies();
      if (!depsOk) {
        toast.error('Please resolve dependency issues before continuing');
        return;
      }
    } else if (currentStep === 4) {
      await installPlugin();
      setCurrentStep(currentStep + 1);
      return;
    }

    setCurrentStep(currentStep + 1);
  };

  // 이전 단계로
  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  // 소스 입력 렌더링
  const renderSourceStep = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-4 gap-2">
        {(['github', 'url', 'local', 'marketplace'] as const).map((type) => (
          <Button
            key={type}
            variant={source.type === type ? 'default' : 'outline'}
            onClick={() => setSource({ type })}
            className="flex flex-col items-center gap-2 h-20"
          >
            {type === 'github' && <Github className="h-6 w-6" />}
            {type === 'url' && <Globe className="h-6 w-6" />}
            {type === 'local' && <FileText className="h-6 w-6" />}
            {type === 'marketplace' && <Package className="h-6 w-6" />}
            <span className="capitalize">{type}</span>
          </Button>
        ))}
      </div>

      {source.type === 'github' && (
        <div className="space-y-3">
          <div>
            <Label htmlFor="repository">Repository</Label>
            <Input
              id="repository"
              placeholder="owner/repository"
              value={source.repository || ''}
              onChange={(e) => setSource({ ...source, repository: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="branch">Branch (optional)</Label>
              <Input
                id="branch"
                placeholder="main"
                value={source.branch || ''}
                onChange={(e) => setSource({ ...source, branch: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="tag">Tag (optional)</Label>
              <Input
                id="tag"
                placeholder="v1.0.0"
                value={source.tag || ''}
                onChange={(e) => setSource({ ...source, tag: e.target.value })}
              />
            </div>
          </div>
        </div>
      )}

      {source.type === 'url' && (
        <div>
          <Label htmlFor="url">Plugin URL</Label>
          <Input
            id="url"
            placeholder="https://example.com/plugin.zip"
            value={source.url || ''}
            onChange={(e) => setSource({ ...source, url: e.target.value })}
          />
        </div>
      )}

      {source.type === 'local' && (
        <div>
          <Label htmlFor="localPath">Local Path</Label>
          <Input
            id="localPath"
            placeholder="/path/to/plugin"
            value={source.localPath || ''}
            onChange={(e) => setSource({ ...source, localPath: e.target.value })}
          />
        </div>
      )}
    </div>
  );

  // 매니페스트 검증 렌더링
  const renderValidationStep = () => (
    <div className="space-y-4">
      {manifest ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              {manifest.name}
            </CardTitle>
            <CardDescription>{manifest.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Version:</span> {manifest.version}
              </div>
              <div>
                <span className="font-medium">Author:</span> {manifest.author}
              </div>
              <div>
                <span className="font-medium">License:</span> {manifest.license}
              </div>
              <div>
                <span className="font-medium">Dependencies:</span> {manifest.dependencies.length}
              </div>
            </div>
            
            {manifest.keywords.length > 0 && (
              <div>
                <span className="font-medium text-sm">Keywords:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {manifest.keywords.map((keyword) => (
                    <Badge key={keyword} variant="secondary" className="text-xs">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {manifest.permissions.length > 0 && (
              <div>
                <span className="font-medium text-sm">Permissions:</span>
                <div className="mt-1 space-y-1">
                  {manifest.permissions.map((permission) => (
                    <div key={permission} className="flex items-center gap-2 text-sm">
                      <Shield className="h-4 w-4 text-yellow-500" />
                      {permission}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Click "Next" to validate the plugin source.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );

  // 의존성 확인 렌더링
  const renderDependenciesStep = () => (
    <div className="space-y-4">
      {dependencies.length > 0 ? (
        <div className="space-y-2">
          {dependencies.map((dep) => (
            <Card key={dep.name} className="p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {dep.installed && dep.compatible ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : dep.installed && !dep.compatible ? (
                    <AlertTriangle className="h-5 w-5 text-yellow-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-500" />
                  )}
                  <div>
                    <div className="font-medium">{dep.name}</div>
                    <div className="text-sm text-muted-foreground">
                      Required: {dep.version}
                      {dep.description && ` - ${dep.description}`}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {dep.required && (
                    <Badge variant="destructive" className="text-xs">
                      Required
                    </Badge>
                  )}
                  <Badge
                    variant={
                      dep.installed && dep.compatible
                        ? 'default'
                        : dep.installed
                        ? 'secondary'
                        : 'outline'
                    }
                    className="text-xs"
                  >
                    {dep.installed && dep.compatible
                      ? 'Compatible'
                      : dep.installed
                      ? 'Incompatible'
                      : 'Missing'}
                  </Badge>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <Alert>
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>
            No dependencies required for this plugin.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );

  // 설치 진행 상황 렌더링
  const renderInstallationStep = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Installation Progress</h3>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowLogs(!showLogs)}
          >
            <Terminal className="h-4 w-4 mr-1" />
            {showLogs ? 'Hide' : 'Show'} Logs
          </Button>
          {isInstalling && (
            <Badge variant="secondary" className="animate-pulse">
              <Loader2 className="h-3 w-3 mr-1 animate-spin" />
              Installing...
            </Badge>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {installationSteps.map((step, index) => (
          <Card key={step.id} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                {step.status === 'completed' ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : step.status === 'failed' ? (
                  <XCircle className="h-5 w-5 text-red-500" />
                ) : step.status === 'running' ? (
                  <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                ) : (
                  <Clock className="h-5 w-5 text-muted-foreground" />
                )}
                <div>
                  <div className="font-medium">{step.title}</div>
                  <div className="text-sm text-muted-foreground">
                    {step.description}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {step.status === 'failed' && step.canRetry && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => retryStep(step.id)}
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Retry
                  </Button>
                )}
                {step.progress !== undefined && (
                  <div className="w-20">
                    <Progress value={step.progress} className="h-2" />
                  </div>
                )}
              </div>
            </div>

            {step.error && (
              <Alert variant="destructive" className="mt-2">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{step.error}</AlertDescription>
              </Alert>
            )}

            {showLogs && step.logs && step.logs.length > 0 && (
              <Collapsible>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" size="sm" className="mt-2">
                    <ChevronDown className="h-4 w-4 mr-1" />
                    View Logs ({step.logs.length})
                  </Button>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <ScrollArea className="h-32 mt-2">
                    <div
                      ref={logScrollRef}
                      className="bg-muted p-3 rounded text-xs font-mono space-y-1"
                    >
                      {step.logs.map((log, logIndex) => (
                        <div key={logIndex}>{log}</div>
                      ))}
                    </div>
                  </ScrollArea>
                </CollapsibleContent>
              </Collapsible>
            )}
          </Card>
        ))}
      </div>
    </div>
  );

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Install Plugin
          </DialogTitle>
          <DialogDescription>
            Follow the steps to install a new plugin
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col h-full">
          {/* Progress Stepper */}
          <div className="mb-6">
            <div className="flex items-center justify-between">
              {steps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        index < currentStep
                          ? 'bg-green-500 text-white'
                          : index === currentStep
                          ? 'bg-blue-500 text-white'
                          : 'bg-muted text-muted-foreground'
                      }`}
                    >
                      {index < currentStep ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : (
                        index + 1
                      )}
                    </div>
                    <div className="text-xs mt-1 text-center">
                      <div className="font-medium">{step.title}</div>
                      <div className="text-muted-foreground">{step.description}</div>
                    </div>
                  </div>
                  {index < steps.length - 1 && (
                    <div
                      className={`flex-1 h-0.5 mx-2 ${
                        index < currentStep ? 'bg-green-500' : 'bg-muted'
                      }`}
                    />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Step Content */}
          <ScrollArea className="flex-1 pr-4">
            {currentStep === 0 && renderSourceStep()}
            {currentStep === 1 && renderValidationStep()}
            {currentStep === 2 && renderDependenciesStep()}
            {currentStep === 3 && manifest?.configSchema && (
              <div>Configuration step would go here</div>
            )}
            {currentStep === 4 && renderInstallationStep()}
            {currentStep === 5 && (
              <div className="text-center py-8">
                <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">Installation Complete!</h3>
                <p className="text-muted-foreground">
                  The plugin has been successfully installed and activated.
                </p>
              </div>
            )}
          </ScrollArea>

          {/* Navigation */}
          <Separator className="my-4" />
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              onClick={prevStep}
              disabled={currentStep === 0 || isInstalling}
            >
              Previous
            </Button>

            <div className="flex items-center gap-2">
              {currentStep < steps.length - 1 ? (
                <Button
                  onClick={nextStep}
                  disabled={
                    isInstalling ||
                    (currentStep === 0 && !source.repository && !source.url && !source.localPath)
                  }
                >
                  {currentStep === 4 ? 'Install' : 'Next'}
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              ) : (
                <Button onClick={onClose}>
                  Close
                </Button>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}