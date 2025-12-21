'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { 
  AnimatedDiv, 
  AnimatedCard, 
  AnimatedList, 
  AnimatedListItem, 
  AnimatedProgress, 
  PulseIndicator
} from '@/components/ui/animated-components';
import { 
  Heart, 
  Brain, 
  Zap, 
  TrendingUp,
  Activity,
  Users,
  Lightbulb,
  Shield,
  Target,
  Thermometer,
  Eye,
  Palette,
  RefreshCw
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { useUserMood, useTeamDynamics, useEmotionHistory, useWellnessInsights, useAnalyzeEmotion, useStartEmotionMonitoring, useStopEmotionMonitoring } from '@/hooks/queries/useEmotionalAI';
import { useEmotionalAIStore } from '@/lib/stores/emotionalAIStore';
import type { EmotionState, UserMood, TeamEmotionalDynamics } from '@/lib/api/emotionalAIApi';

// Types are now imported from API

interface EmotionalAIBlockProps {
  onConfigChange?: (config: any) => void;
  initialConfig?: any;
}

const EmotionalAIBlock: React.FC<EmotionalAIBlockProps> = ({
  onConfigChange
}) => {
  // Zustand store
  const { 
    currentUser, 
    teamDynamics, 
    emotionHistory, 
    adaptiveMode, 
    emotionalTheme,
    setCurrentUser,
    setTeamDynamics,
    setAdaptiveMode,
    setEmotionalTheme,
    updateUserEmotion
  } = useEmotionalAIStore();

  // React Query hooks
  const userId = 'user-1'; // Mock user ID
  const teamId = 'team-1'; // Mock team ID
  
  const { data: userMoodData, isLoading: userMoodLoading } = useUserMood(userId);
  const { data: teamDynamicsData, isLoading: teamDynamicsLoading } = useTeamDynamics(teamId);
  const { data: emotionHistoryData } = useEmotionHistory(userId, 24);
  const { data: wellnessInsightsData } = useWellnessInsights(userId);

  // Mutations
  const analyzeEmotionMutation = useAnalyzeEmotion();
  const startMonitoringMutation = useStartEmotionMonitoring();
  const stopMonitoringMutation = useStopEmotionMonitoring();

  // Local state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [monitoringSessionId, setMonitoringSessionId] = useState<string | null>(null);

  // Memoized data
  const emotionWheelData = useMemo(() => [
    { name: 'Joy', value: 25, color: '#fbbf24', icon: '😊' },
    { name: 'Trust', value: 20, color: '#34d399', icon: '🤝' },
    { name: 'Fear', value: 10, color: '#f87171', icon: '😰' },
    { name: 'Surprise', value: 15, color: '#a78bfa', icon: '😲' },
    { name: 'Sadness', value: 8, color: '#60a5fa', icon: '😢' },
    { name: 'Disgust', value: 5, color: '#fb7185', icon: '🤢' },
    { name: 'Anger', value: 7, color: '#ef4444', icon: '😠' },
    { name: 'Anticipation', value: 10, color: '#f59e0b', icon: '🤔' }
  ], []);

  const wellnessInsights = useMemo(() => wellnessInsightsData?.insights || [], [wellnessInsightsData]);

  // Update store when data changes
  useEffect(() => {
    if (userMoodData?.user_mood) {
      setCurrentUser({
        ...userMoodData.user_mood,
        userId: userMoodData.user_mood.user_id,
        currentEmotion: {
          ...userMoodData.user_mood.current_emotion,
          timestamp: new Date(userMoodData.user_mood.current_emotion.timestamp)
        }
      });
    }
  }, [userMoodData, setCurrentUser]);

  useEffect(() => {
    if (teamDynamicsData?.team_dynamics) {
      setTeamDynamics({
        ...teamDynamicsData.team_dynamics,
        teamId: teamDynamicsData.team_dynamics.team_id,
        teamName: teamDynamicsData.team_dynamics.team_name,
        overallMood: teamDynamicsData.team_dynamics.overall_mood,
        cohesionScore: teamDynamicsData.team_dynamics.cohesion_score,
        stressIndicators: teamDynamicsData.team_dynamics.stress_indicators,
        productivityCorrelation: teamDynamicsData.team_dynamics.productivity_correlation,
        conflictRisk: teamDynamicsData.team_dynamics.conflict_risk,
        burnoutRisk: teamDynamicsData.team_dynamics.burnout_risk
      });
    }
  }, [teamDynamicsData, setTeamDynamics]);

  // Emotion analysis function
  const handleEmotionAnalysis = () => {
    setIsAnalyzing(true);
    analyzeEmotionMutation.mutate({
      user_id: userId,
      input_type: 'text',
      data: { context: 'UI interaction' }
    }, {
      onSettled: () => setIsAnalyzing(false)
    });
  };

  // Start/stop monitoring functions
  const handleStartMonitoring = () => {
    startMonitoringMutation.mutate(userId, {
      onSuccess: (data) => {
        setMonitoringSessionId(data.session_id);
      }
    });
  };

  const handleStopMonitoring = () => {
    if (monitoringSessionId) {
      stopMonitoringMutation.mutate(monitoringSessionId, {
        onSuccess: () => {
          setMonitoringSessionId(null);
        }
      });
    }
  };

  const getEmotionColor = (emotion: string) => {
    const colorMap: Record<string, string> = {
      happy: 'text-yellow-600 bg-yellow-100',
      sad: 'text-blue-600 bg-blue-100',
      angry: 'text-red-600 bg-red-100',
      excited: 'text-orange-600 bg-orange-100',
      calm: 'text-green-600 bg-green-100',
      stressed: 'text-purple-600 bg-purple-100',
      focused: 'text-indigo-600 bg-indigo-100',
      frustrated: 'text-pink-600 bg-pink-100'
    };
    return colorMap[emotion] || 'text-gray-600 bg-gray-100';
  };

  const getEmotionIcon = (emotion: string) => {
    const iconMap: Record<string, string> = {
      happy: '😊',
      sad: '😢',
      angry: '😠',
      excited: '🤩',
      calm: '😌',
      stressed: '😰',
      focused: '🧐',
      frustrated: '😤'
    };
    return iconMap[emotion] || '😐';
  };

  const getWellnessLevel = (score: number) => {
    if (score >= 80) return { level: 'Excellent', color: 'text-green-600' };
    if (score >= 60) return { level: 'Good', color: 'text-blue-600' };
    if (score >= 40) return { level: 'Fair', color: 'text-yellow-600' };
    return { level: 'Needs Attention', color: 'text-red-600' };
  };

  const adaptThemeToEmotion = (emotion: string) => {
    const themeMap: Record<string, string> = {
      happy: 'warm',
      calm: 'cool',
      focused: 'minimal',
      stressed: 'soothing',
      excited: 'vibrant'
    };
    const newTheme = themeMap[emotion] || 'default';
    setEmotionalTheme(newTheme);
    onConfigChange?.({ emotionalTheme: newTheme });
  };

  // Loading states
  if (userMoodLoading || teamDynamicsLoading) {
    return (
      <div className="w-full space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-32 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="h-64 bg-gray-200 rounded"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <AnimatedDiv className={`w-full space-y-6 transition-all duration-500 ${
      emotionalTheme === 'warm' ? 'bg-gradient-to-br from-orange-50 to-yellow-50' :
      emotionalTheme === 'cool' ? 'bg-gradient-to-br from-blue-50 to-green-50' :
      emotionalTheme === 'soothing' ? 'bg-gradient-to-br from-purple-50 to-pink-50' :
      emotionalTheme === 'vibrant' ? 'bg-gradient-to-br from-red-50 to-orange-50' :
      'bg-white'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Heart className="h-6 w-6 text-pink-600" />
            Emotional AI Integration
          </h2>
          <p className="text-gray-600 mt-1">
            AI that understands and adapts to human emotions for better collaboration
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <Label htmlFor="adaptive-mode">Adaptive Mode</Label>
            <Switch
              id="adaptive-mode"
              checked={adaptiveMode}
              onCheckedChange={setAdaptiveMode}
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleEmotionAnalysis}
            disabled={isAnalyzing}
          >
            {isAnalyzing ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
            {isAnalyzing ? 'Analyzing...' : 'Analyze Emotion'}
          </Button>
        </div>
      </div>

      {/* Current Emotion Status */}
      {currentUser && (
        <AnimatedCard className="border-2 border-pink-200 bg-gradient-to-r from-pink-50 to-purple-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-4xl">
                  {getEmotionIcon(currentUser.currentEmotion.primary)}
                </div>
                <div>
                  <h3 className="font-semibold text-lg">Current Emotional State</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className={getEmotionColor(currentUser.currentEmotion.primary)}>
                      {currentUser.currentEmotion.primary.toUpperCase()}
                    </Badge>
                    <span className="text-sm text-gray-600">
                      Intensity: {(currentUser.currentEmotion.intensity * 100).toFixed(0)}%
                    </span>
                    <span className="text-sm text-gray-600">
                      Confidence: {(currentUser.currentEmotion.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    {currentUser.currentEmotion.context}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-2xl font-bold ${getWellnessLevel(currentUser.wellnessScore).color}`}>
                  {currentUser.wellnessScore}
                </div>
                <div className="text-sm text-gray-600">
                  Wellness Score
                </div>
                <div className={`text-sm ${getWellnessLevel(currentUser.wellnessScore).color}`}>
                  {getWellnessLevel(currentUser.wellnessScore).level}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Tabs defaultValue="emotion-wheel" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="emotion-wheel">🎭 Emotion Wheel</TabsTrigger>
          <TabsTrigger value="wellness">💚 Wellness</TabsTrigger>
          <TabsTrigger value="team-dynamics">👥 Team Dynamics</TabsTrigger>
          <TabsTrigger value="adaptive-ui">🎨 Adaptive UI</TabsTrigger>
          <TabsTrigger value="insights">💡 Insights</TabsTrigger>
        </TabsList>

        {/* Emotion Wheel Tab */}
        <TabsContent value="emotion-wheel" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Emotion Wheel Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Palette className="h-5 w-5" />
                  Emotion Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={emotionWheelData}
                        cx="50%"
                        cy="50%"
                        outerRadius={120}
                        innerRadius={60}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {emotionWheelData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        formatter={(value, name, props) => [
                          `${value}%`, 
                          `${props.payload.icon} ${name}`
                        ]}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Emotion Legend */}
                <div className="grid grid-cols-2 gap-2 mt-4">
                  {emotionWheelData.map((emotion) => (
                    <div key={emotion.name} className="flex items-center gap-2 text-sm">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: emotion.color }}
                      />
                      <span>{emotion.icon}</span>
                      <span>{emotion.name}</span>
                      <span className="text-gray-500">({emotion.value}%)</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Emotion Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  Emotion Timeline (24h)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={emotionHistory.map((emotion, index) => ({
                      time: index,
                      intensity: emotion.intensity * 100,
                      confidence: emotion.confidence * 100
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="time" />
                      <YAxis />
                      <Tooltip />
                      <Area 
                        type="monotone" 
                        dataKey="intensity" 
                        stackId="1"
                        stroke="#8884d8" 
                        fill="#8884d8" 
                        fillOpacity={0.6}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="confidence" 
                        stackId="2"
                        stroke="#82ca9d" 
                        fill="#82ca9d" 
                        fillOpacity={0.6}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                {/* Recent Emotions */}
                <div className="mt-4">
                  <h4 className="font-medium mb-2">Recent Emotions</h4>
                  <div className="flex flex-wrap gap-2">
                    {emotionHistory.slice(-6).map((emotion, index) => (
                      <Badge key={index} className={getEmotionColor(emotion.primary)}>
                        {getEmotionIcon(emotion.primary)} {emotion.primary}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Wellness Tab */}
        <TabsContent value="wellness" className="space-y-4">
          {currentUser && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Stress Level */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Thermometer className="h-8 w-8 text-red-600" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-600">Stress Level</p>
                      <p className="text-xl font-bold">{currentUser.stressLevel}%</p>
                      <Progress value={currentUser.stressLevel} className="h-2 mt-1" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Energy Level */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Zap className="h-8 w-8 text-yellow-600" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-600">Energy Level</p>
                      <p className="text-xl font-bold">{currentUser.energyLevel}%</p>
                      <Progress value={currentUser.energyLevel} className="h-2 mt-1" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Focus Level */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Target className="h-8 w-8 text-blue-600" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-600">Focus Level</p>
                      <p className="text-xl font-bold">{currentUser.focusLevel}%</p>
                      <Progress value={currentUser.focusLevel} className="h-2 mt-1" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Wellness Score */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Heart className="h-8 w-8 text-pink-600" />
                    <div className="flex-1">
                      <p className="text-sm text-gray-600">Wellness Score</p>
                      <p className="text-xl font-bold">{currentUser.wellnessScore}%</p>
                      <Progress value={currentUser.wellnessScore} className="h-2 mt-1" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Wellness Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5" />
                Wellness Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Stress Management:</strong> Consider taking a 10-minute break. 
                    Your stress level is slightly elevated.
                  </AlertDescription>
                </Alert>
                <Alert>
                  <TrendingUp className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Energy Boost:</strong> Great energy levels! 
                    This is an optimal time for challenging tasks.
                  </AlertDescription>
                </Alert>
                <Alert>
                  <Eye className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Focus Enhancement:</strong> Excellent focus detected. 
                    Consider tackling your most important work now.
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Team Dynamics Tab */}
        <TabsContent value="team-dynamics" className="space-y-4">
          {teamDynamics && (
            <>
              {/* Team Overview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5" />
                    {teamDynamics.teamName}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">
                        {teamDynamics.cohesionScore}%
                      </div>
                      <div className="text-sm text-gray-600">Team Cohesion</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {(teamDynamics.productivityCorrelation * 100).toFixed(0)}%
                      </div>
                      <div className="text-sm text-gray-600">Productivity Correlation</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-yellow-600">
                        {teamDynamics.conflictRisk}%
                      </div>
                      <div className="text-sm text-gray-600">Conflict Risk</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">
                        {teamDynamics.burnoutRisk}%
                      </div>
                      <div className="text-sm text-gray-600">Burnout Risk</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Team Recommendations */}
              <Card>
                <CardHeader>
                  <CardTitle>Team Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {teamDynamics.recommendations.map((recommendation, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 bg-blue-50 rounded-lg">
                        <Lightbulb className="h-4 w-4 text-blue-600" />
                        <span className="text-sm">{recommendation}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Adaptive UI Tab */}
        <TabsContent value="adaptive-ui" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5" />
                Emotion-Based Theme Adaptation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label>Current Theme: {emotionalTheme}</Label>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mt-2">
                    {['default', 'warm', 'cool', 'soothing', 'vibrant'].map((theme) => (
                      <Button
                        key={theme}
                        variant={emotionalTheme === theme ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setEmotionalTheme(theme)}
                        className="capitalize"
                      >
                        {theme}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Auto-adapt to emotions</Label>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={adaptiveMode}
                      onCheckedChange={setAdaptiveMode}
                    />
                    <span className="text-sm text-gray-600">
                      Automatically change theme based on detected emotions
                    </span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Accessibility Features */}
          <Card>
            <CardHeader>
              <CardTitle>Emotional Accessibility Features</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Stress Reduction Mode</Label>
                  <Switch />
                  <p className="text-sm text-gray-600">
                    Reduces visual complexity when stress is detected
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Focus Enhancement</Label>
                  <Switch />
                  <p className="text-sm text-gray-600">
                    Minimizes distractions during high focus periods
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Energy-Based Brightness</Label>
                  <Switch />
                  <p className="text-sm text-gray-600">
                    Adjusts interface brightness based on energy levels
                  </p>
                </div>
                <div className="space-y-2">
                  <Label>Mood-Based Notifications</Label>
                  <Switch />
                  <p className="text-sm text-gray-600">
                    Filters notifications based on current emotional state
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Emotional Patterns</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span>Most Common Emotion</span>
                    <Badge className="bg-yellow-100 text-yellow-800">😊 Happy</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Peak Energy Time</span>
                    <span className="font-medium">10:00 AM - 12:00 PM</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Stress Triggers</span>
                    <span className="font-medium">Meetings, Deadlines</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Productivity Correlation</span>
                    <span className="font-medium text-green-600">+0.78</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>AI Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <Alert>
                    <Brain className="h-4 w-4" />
                    <AlertDescription>
                      Schedule important tasks during your peak energy hours (10 AM - 12 PM)
                    </AlertDescription>
                  </Alert>
                  <Alert>
                    <Heart className="h-4 w-4" />
                    <AlertDescription>
                      Consider meditation breaks when stress levels exceed 60%
                    </AlertDescription>
                  </Alert>
                  <Alert>
                    <Users className="h-4 w-4" />
                    <AlertDescription>
                      Team collaboration is most effective when overall mood is positive
                    </AlertDescription>
                  </Alert>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
      </AnimatedDiv>
    </ErrorBoundary>
  );
};

export default EmotionalAIBlock;