'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Video, 
  Play, 
  Upload,
  Zap,
  Eye,
  Mic,
  Film,
  BarChart3,
  Clock,
  FileVideo,
  CheckCircle,
  ArrowRight,
  Star,
  TrendingUp,
  Users,
  Award,
  Rocket
} from 'lucide-react';
import { GeminiVideoBlock } from '@/components/agent-builder/blocks';

export default function GeminiVideoDemo() {
  const [activeDemo, setActiveDemo] = useState('overview');

  const videoCapabilities = [
    {
      title: 'Comprehensive Analysis',
      description: 'Complete video analysis',
      icon: BarChart3,
      color: 'text-purple-600',
      features: ['Full Summary', 'Visual Elements', 'Audio Analysis', 'Structure Analysis', 'Quality Assessment'],
      accuracy: '96%',
      speed: '30-60s'
    },
    {
      title: 'Smart Summary',
      description: 'Key content summary',
      icon: FileVideo,
      color: 'text-blue-600',
      features: ['Main Content', 'Key Points', 'Target Audience', 'Viewing Value'],
      accuracy: '94%',
      speed: '15-30s'
    },
    {
      title: 'Audio Transcription',
      description: 'Speech to text conversion',
      icon: Mic,
      color: 'text-green-600',
      features: ['Speaker Identification', 'Timeline Organization', 'Keyword Extraction', 'Content Summary'],
      accuracy: '93%',
      speed: '20-40s'
    },
    {
      title: 'Object Detection',
      description: 'Object and person analysis',
      icon: Eye,
      color: 'text-orange-600',
      features: ['Object List', 'Person Analysis', 'Background Environment', 'Brand/Logo'],
      accuracy: '95%',
      speed: '25-45s'
    },
    {
      title: 'Scene Analysis',
      description: 'Scene composition analysis',
      icon: Film,
      color: 'text-red-600',
      features: ['Scene Segmentation', 'Transition Methods', 'Time Structure', 'Storytelling'],
      accuracy: '92%',
      speed: '35-55s'
    }
  ];

  const useCases = [
    {
      category: 'Education & Training',
      icon: '🎓',
      examples: [
        { name: 'Online Course Analysis', roi: '80% Time Saved', complexity: 'Medium' },
        { name: 'Educational Material Summary', roi: '90% Efficiency Improvement', complexity: 'Simple' },
        { name: 'Learning Progress Tracking', roi: '75% Improvement Effect', complexity: 'Complex' }
      ]
    },
    {
      category: 'Business & Marketing',
      icon: '💼',
      examples: [
        { name: 'Product Demo Analysis', roi: '85% Insight Improvement', complexity: 'Medium' },
        { name: 'Ad Effectiveness Measurement', roi: '70% Accuracy Improvement', complexity: 'Complex' },
        { name: 'Brand Monitoring', roi: '95% Automation', complexity: 'Simple' }
      ]
    },
    {
      category: 'Media & Entertainment',
      icon: '🎬',
      examples: [
        { name: 'Content Curation', roi: '90% Time Reduction', complexity: 'Simple' },
        { name: 'Storyboard Generation', roi: '75% Cost Reduction', complexity: 'Medium' },
        { name: 'Auto Subtitle Generation', roi: '95% Automation', complexity: 'Simple' }
      ]
    },
    {
      category: 'Security & Monitoring',
      icon: '🔒',
      examples: [
        { name: 'Security Video Analysis', roi: '85% Accuracy', complexity: 'Complex' },
        { name: 'Quality Control', roi: '80% Efficiency', complexity: 'Medium' },
        { name: 'Anomaly Detection', roi: '90% Auto Detection', complexity: 'Complex' }
      ]
    }
  ];

  const stats = [
    { label: 'Analysis Accuracy', value: '94.2%', trend: '+2.8%', icon: Eye },
    { label: 'Avg Processing Time', value: '32s', trend: '-18%', icon: Clock },
    { label: 'Supported Formats', value: '9', trend: '+3', icon: FileVideo },
    { label: 'Success Rate', value: '97.8%', trend: '+1.5%', icon: CheckCircle }
  ];

  const roadmapItems = [
    {
      phase: 'Phase 1',
      title: 'Core Video Analysis',
      status: 'completed',
      items: ['Basic Analysis', 'Object Detection', 'Audio Transcription', 'Scene Recognition']
    },
    {
      phase: 'Phase 2',
      title: 'Advanced Features',
      status: 'completed',
      items: ['Multi-format Support', 'Batch Processing', 'Real-time Analysis', 'Quality Assessment']
    },
    {
      phase: 'Phase 3',
      title: 'AI-Native Processing',
      status: 'in-progress',
      items: ['Auto-optimization', 'Predictive Analysis', 'Content Generation', 'Smart Editing']
    },
    {
      phase: 'Phase 4',
      title: 'Enterprise Platform',
      status: 'planned',
      items: ['Team Collaboration', 'Custom Models', 'API Marketplace', 'Advanced Analytics']
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-purple-50 to-blue-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="p-4 rounded-full bg-gradient-to-r from-red-500 via-purple-500 to-blue-500">
              <Video className="h-10 w-10 text-white" />
            </div>
            <Badge variant="secondary" className="text-xl px-6 py-3">
              🎬 VIDEO AI REVOLUTION
            </Badge>
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold bg-gradient-to-r from-red-600 via-purple-600 to-blue-600 bg-clip-text text-transparent mb-6">
            Gemini Video AI
          </h1>
          
          <p className="text-2xl text-muted-foreground mb-8 max-w-4xl mx-auto">
            World&apos;s First Fully Automated Video Analysis Platform Based on Gemini 3.0
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg" className="bg-gradient-to-r from-red-600 to-purple-600 hover:from-red-700 hover:to-purple-700 text-lg px-8 py-4">
              <Play className="h-6 w-6 mr-2" />
              Start Live Demo
            </Button>
            <Button size="lg" variant="outline" className="text-lg px-8 py-4">
              <Upload className="h-6 w-6 mr-2" />
              Test Video Upload
            </Button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto">
            {stats.map((stat, index) => {
              const Icon = stat.icon;
              return (
                <Card key={index} className="text-center hover:shadow-lg transition-all">
                  <CardContent className="p-6">
                    <Icon className="h-8 w-8 mx-auto mb-3 text-red-600" />
                    <div className="text-3xl font-bold text-red-600 mb-1">{stat.value}</div>
                    <div className="text-sm text-muted-foreground mb-2">{stat.label}</div>
                    <div className="text-xs text-green-600 font-medium">{stat.trend}</div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Main Content */}
        <Tabs value={activeDemo} onValueChange={setActiveDemo} className="w-full">
          <TabsList className="grid w-full grid-cols-5 mb-8">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="capabilities">Core Features</TabsTrigger>
            <TabsTrigger value="demo">Live Demo</TabsTrigger>
            <TabsTrigger value="usecases">Use Cases</TabsTrigger>
            <TabsTrigger value="roadmap">Roadmap</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-8">
            {/* Video Capabilities Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {videoCapabilities.map((capability, index) => {
                const Icon = capability.icon;
                return (
                  <Card key={index} className="hover:shadow-lg transition-all">
                    <CardHeader className="pb-3">
                      <div className={`p-3 rounded-lg bg-gray-100 dark:bg-gray-800 w-fit ${capability.color}`}>
                        <Icon className="h-8 w-8" />
                      </div>
                      <CardTitle className="text-xl">{capability.title}</CardTitle>
                      <CardDescription>{capability.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div className="text-center p-2 bg-green-50 dark:bg-green-900/20 rounded">
                            <div className="font-semibold text-green-600">{capability.accuracy}</div>
                            <div className="text-xs text-green-600">Accuracy</div>
                          </div>
                          <div className="text-center p-2 bg-blue-50 dark:bg-blue-900/20 rounded">
                            <div className="font-semibold text-blue-600">{capability.speed}</div>
                            <div className="text-xs text-blue-600">Processing Time</div>
                          </div>
                        </div>
                        <div className="space-y-1">
                          {capability.features.map((feature, featureIndex) => (
                            <div key={featureIndex} className="flex items-center gap-2 text-xs">
                              <CheckCircle className="h-3 w-3 text-green-500" />
                              <span>{feature}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Technology Highlights */}
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl">Technical Innovation</CardTitle>
                <CardDescription>
                  Next-generation analysis platform utilizing Gemini 3.0&apos;s latest video processing technology
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Zap className="h-5 w-5 text-yellow-500" />
                      Core Technology
                    </h3>
                    <div className="space-y-3">
                      <div className="p-3 border rounded-lg">
                        <h4 className="font-medium mb-1">🧠 Gemini 3.0 Native Processing</h4>
                        <p className="text-sm text-muted-foreground">
                          Complete analysis of long videos with 2M token context
                        </p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <h4 className="font-medium mb-1">⚡ Real-time Frame Analysis</h4>
                        <p className="text-sm text-muted-foreground">
                          Real-time frame-by-frame object and scene recognition
                        </p>
                      </div>
                      <div className="p-3 border rounded-lg">
                        <h4 className="font-medium mb-1">🎵 Advanced Audio Processing</h4>
                        <p className="text-sm text-muted-foreground">
                          Multi-speaker identification and emotion analysis
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                      <Award className="h-5 w-5 text-purple-500" />
                      Competitive Advantage
                    </h3>
                    <div className="space-y-3">
                      <div className="p-3 border rounded-lg bg-purple-50 dark:bg-purple-900/20">
                        <h4 className="font-medium mb-1 text-purple-700">🏆 Industry First</h4>
                        <p className="text-sm text-purple-600">
                          Fully integrated Gemini 3.0 video analysis platform
                        </p>
                      </div>
                      <div className="p-3 border rounded-lg bg-blue-50 dark:bg-blue-900/20">
                        <h4 className="font-medium mb-1 text-blue-700">🚀 5x Performance</h4>
                        <p className="text-sm text-blue-600">
                          5x faster video processing compared to existing solutions
                        </p>
                      </div>
                      <div className="p-3 border rounded-lg bg-green-50 dark:bg-green-900/20">
                        <h4 className="font-medium mb-1 text-green-700">🎯 94% Accuracy</h4>
                        <p className="text-sm text-green-600">
                          Industry-leading analysis accuracy
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="capabilities" className="space-y-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Video className="h-6 w-6 text-red-600" />
                    Supported Formats & Features
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="font-semibold mb-2">📹 Supported Formats</h4>
                      <div className="space-y-1 text-sm">
                        <Badge variant="outline">MP4</Badge>
                        <Badge variant="outline">MOV</Badge>
                        <Badge variant="outline">AVI</Badge>
                        <Badge variant="outline">WebM</Badge>
                        <Badge variant="outline">MPEG</Badge>
                        <Badge variant="outline">WMV</Badge>
                        <Badge variant="outline">3GPP</Badge>
                        <Badge variant="outline">FLV</Badge>
                      </div>
                    </div>
                    <div>
                      <h4 className="font-semibold mb-2">⚙️ Processing Options</h4>
                      <div className="space-y-1 text-sm">
                        <div>• Max 100MB file size</div>
                        <div>• 30 min length limit</div>
                        <div>• Auto frame sampling</div>
                        <div>• Audio include/exclude</div>
                        <div>• Real-time progress</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-6 w-6 text-purple-600" />
                    Analysis Type Features
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {videoCapabilities.slice(0, 3).map((capability, index) => (
                    <div key={index} className="p-3 border rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <capability.icon className={`h-4 w-4 ${capability.color}`} />
                        <span className="font-medium">{capability.title}</span>
                        <Badge variant="outline" className="text-xs">{capability.speed}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{capability.description}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="demo" className="space-y-8">
            <Card>
              <CardHeader>
                <CardTitle>🎮 Interactive Video Analysis Demo</CardTitle>
                <CardDescription>
                  Experience the actual Gemini Video Block firsthand
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="max-h-[800px] overflow-y-auto">
                  <GeminiVideoBlock
                    blockId="demo-video"
                    config={{
                      analysis_type: 'comprehensive',
                      model: 'gemini-1.5-pro',
                      temperature: 0.7,
                      frame_sampling: 'auto',
                      max_frames: 30,
                      include_audio: true
                    }}
                    onExecute={(result) => console.log('Video analysis result:', result)}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="usecases" className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {useCases.map((category, index) => (
                <Card key={index}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <span className="text-2xl">{category.icon}</span>
                      {category.category}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {category.examples.map((example, exampleIndex) => (
                        <div key={exampleIndex} className="p-3 border rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium">{example.name}</h4>
                            <Badge variant={
                              example.complexity === 'Simple' ? 'secondary' :
                              example.complexity === 'Medium' ? 'default' : 'destructive'
                            }>
                              {example.complexity}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <TrendingUp className="h-4 w-4 text-green-500" />
                            <span className="text-green-600 font-medium">{example.roi}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="roadmap" className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {roadmapItems.map((item, index) => (
                <Card key={index} className={`${
                  item.status === 'completed' ? 'border-green-500 bg-green-50 dark:bg-green-900/20' :
                  item.status === 'in-progress' ? 'border-red-500 bg-red-50 dark:bg-red-900/20' :
                  'border-gray-300'
                }`}>
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <Badge variant={
                        item.status === 'completed' ? 'default' :
                        item.status === 'in-progress' ? 'secondary' : 'outline'
                      }>
                        {item.phase}
                      </Badge>
                      {item.status === 'completed' && <CheckCircle className="h-5 w-5 text-green-500" />}
                      {item.status === 'in-progress' && <Video className="h-5 w-5 text-red-500" />}
                    </div>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {item.items.map((feature, featureIndex) => (
                        <div key={featureIndex} className="flex items-center gap-2 text-sm">
                          {item.status === 'completed' ? (
                            <CheckCircle className="h-3 w-3 text-green-500" />
                          ) : item.status === 'in-progress' ? (
                            <Video className="h-3 w-3 text-red-500" />
                          ) : (
                            <div className="h-3 w-3 border border-gray-300 rounded-full" />
                          )}
                          <span>{feature}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>

        {/* CTA Section */}
        <Card className="mt-12 bg-gradient-to-r from-red-600 via-purple-600 to-blue-600 text-white">
          <CardContent className="p-12 text-center">
            <Video className="h-16 w-16 mx-auto mb-6" />
            <h2 className="text-4xl font-bold mb-4">
              Open a New Era of Video AI
            </h2>
            <p className="text-xl mb-8 opacity-90 max-w-3xl mx-auto">
              Revolutionize content creation and analysis with Gemini 3.0-based video analysis 
              and boost work efficiency by 5x with this next-generation platform
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" variant="secondary" className="text-lg px-8 py-4">
                <Star className="h-6 w-6 mr-2" />
                Start Free Trial
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-red-600 text-lg px-8 py-4">
                <ArrowRight className="h-6 w-6 mr-2" />
                Go to Workflow Builder
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}