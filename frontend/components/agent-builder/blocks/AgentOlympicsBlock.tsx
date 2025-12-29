'use client';

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { VirtualizedList } from '@/components/ui/virtualized-list';
import { ErrorBoundary } from '@/components/ui/error-boundary';
import { 
  AnimatedDiv, 
  AnimatedCard, 
  AnimatedList, 
  AnimatedListItem, 
  AnimatedProgress, 
  AnimatedCounter,
  PulseIndicator
} from '@/components/ui/animated-components';
import { 
  Trophy, 
  Medal, 
  Users, 
  Play, 
  Pause, 
  Crown,
  Timer,
  Award,
  Gamepad2,
  Eye,
  MessageSquare
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { useAgents, useCompetitions, useLiveProgress, useLeaderboard, useStartCompetition, useStopCompetition } from '@/hooks/queries/useAgentOlympics';
import { useAgentOlympicsStore } from '@/lib/stores/agentOlympicsStore';

// Import types from API
import type { Agent, Competition } from '@/lib/api/agentOlympicsApi';

interface AgentOlympicsBlockProps {
  onConfigChange?: (config: any) => void;
  initialConfig?: any;
}

const AgentOlympicsBlock: React.FC<AgentOlympicsBlockProps> = () => {
  // Zustand store
  const { 
    activeCompetition, 
    isLive, 
    raceProgress, 
    setActiveCompetition, 
    updateRaceProgress, 
    startCompetition, 
    stopCompetition 
  } = useAgentOlympicsStore();

  // React Query hooks
  const { data: agentsData, isLoading: agentsLoading } = useAgents();
  const { data: competitionsData, isLoading: competitionsLoading } = useCompetitions();
  const { data: leaderboardData, isLoading: leaderboardLoading } = useLeaderboard();
  const { data: liveProgressData } = useLiveProgress(
    activeCompetition?.id || '', 
    isLive && !!activeCompetition
  );

  // Mutations
  const startCompetitionMutation = useStartCompetition();
  const stopCompetitionMutation = useStopCompetition();

  // Local state
  const [spectatorMode, setSpectatorMode] = useState(false);
  
  // Animation refs
  const raceTrackRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number | null>(null);

  // Memoized data
  const agents = useMemo(() => agentsData?.agents || [], [agentsData]);
  const competitions = useMemo(() => competitionsData?.competitions || [], [competitionsData]);
  const leaderboard = useMemo(() => leaderboardData?.leaderboard || [], [leaderboardData]);

  // Update race progress from live data
  useEffect(() => {
    if (liveProgressData?.progress) {
      updateRaceProgress(liveProgressData.progress);
    }
  }, [liveProgressData, updateRaceProgress]);

  // Initialize mock data and start animation
  useEffect(() => {
    if (!activeCompetition && competitions.length > 0) {
      const activeComp = competitions.find(c => c.status === 'active');
      if (activeComp) {
        setActiveCompetition({
          ...activeComp,
          startTime: new Date(activeComp.start_time || Date.now())
        });
      }
    }
  }, [competitions, activeCompetition, setActiveCompetition]);

  useEffect(() => {
    if (isLive) {
      startRaceAnimation();
    }
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isLive]);

  // Race animation logic
  const startRaceAnimation = () => {
    const animate = () => {
      const newProgress = { ...raceProgress };
      agents.forEach(agent => {
        const currentProgress = newProgress[agent.id] || 0;
        if (currentProgress < 100) {
          // Different speeds based on agent performance
          const speedFactor = agent.performance.speed / 100;
          const randomFactor = 0.5 + Math.random() * 0.5; // Add some randomness
          newProgress[agent.id] = Math.min(100, currentProgress + speedFactor * randomFactor * 0.5);
        }
      });
      updateRaceProgress(newProgress);

      if (isLive) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };
    animate();
  };

  const handleStartCompetition = () => {
    if (activeCompetition) {
      startCompetitionMutation.mutate(activeCompetition.id);
      startCompetition();
      // Reset progress
      const resetProgress: Record<string, number> = {};
      agents.forEach(agent => {
        resetProgress[agent.id] = 0;
      });
      updateRaceProgress(resetProgress);
    }
  };

  const handleStopCompetition = () => {
    if (activeCompetition) {
      stopCompetitionMutation.mutate(activeCompetition.id);
      stopCompetition();
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }
  };

  const getPositionColor = (position: number) => {
    switch (position) {
      case 1: return 'text-yellow-600 bg-yellow-100';
      case 2: return 'text-gray-600 bg-gray-100';
      case 3: return 'text-orange-600 bg-orange-100';
      default: return 'text-blue-600 bg-blue-100';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'competing': return 'text-green-600 bg-green-100';
      case 'training': return 'text-blue-600 bg-blue-100';
      case 'idle': return 'text-gray-600 bg-gray-100';
      case 'offline': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // Sort agents by current race progress for live ranking
  const liveRanking = [...agents].sort((a, b) => (raceProgress[b.id] || 0) - (raceProgress[a.id] || 0));

  // Loading states
  if (agentsLoading || competitionsLoading || leaderboardLoading) {
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
      <AnimatedDiv className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Trophy className="h-6 w-6 text-yellow-600" />
            AI Agent Olympics
          </h2>
          <p className="text-gray-600 mt-1">
            Where AI agents compete for glory and performance supremacy
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSpectatorMode(!spectatorMode)}
          >
            <Eye className="h-4 w-4" />
            {spectatorMode ? 'Exit' : 'Spectator'} Mode
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={isLive ? handleStopCompetition : handleStartCompetition}
          >
            {isLive ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            {isLive ? 'Stop' : 'Start'} Race
          </Button>
        </div>
      </div>

      {/* Competition Status */}
      {activeCompetition && (
        <Card className="border-2 border-yellow-200 bg-gradient-to-r from-yellow-50 to-orange-50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-lg flex items-center gap-2">
                  <Medal className="h-5 w-5 text-yellow-600" />
                  {activeCompetition.name}
                </h3>
                <p className="text-sm text-gray-600">{activeCompetition.description}</p>
                <div className="flex items-center gap-4 mt-2">
                  <Badge className="bg-green-100 text-green-800">
                    {activeCompetition.status.toUpperCase()}
                  </Badge>
                  <span className="text-sm flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    {activeCompetition.participants.length} Competitors
                  </span>
                  <span className="text-sm flex items-center gap-1">
                    <Eye className="h-4 w-4" />
                    {activeCompetition.spectators} Spectators
                  </span>
                  <span className="text-sm flex items-center gap-1">
                    <Trophy className="h-4 w-4" />
                    ${activeCompetition.prize} Prize
                  </span>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-yellow-600">
                  {isLive ? <Timer className="h-8 w-8 animate-pulse" /> : <Crown className="h-8 w-8" />}
                </div>
                <p className="text-sm text-gray-600">
                  {isLive ? 'LIVE NOW' : 'Ready to Start'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <Tabs defaultValue="arena" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="arena">🏟️ Arena</TabsTrigger>
          <TabsTrigger value="leaderboard">🏆 Leaderboard</TabsTrigger>
          <TabsTrigger value="agents">🤖 Agents</TabsTrigger>
          <TabsTrigger value="competitions">📅 Competitions</TabsTrigger>
          <TabsTrigger value="analytics">📊 Analytics</TabsTrigger>
        </TabsList>

        {/* Arena Tab - Race Track Visualization */}
        <TabsContent value="arena" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gamepad2 className="h-5 w-5" />
                Competition Arena
                {isLive && <Badge className="bg-red-100 text-red-800 animate-pulse">LIVE</Badge>}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Race Track */}
              <div className="space-y-4 mb-6">
                <h4 className="font-semibold">Race Progress</h4>
                <div className="space-y-3" ref={raceTrackRef}>
                  {liveRanking.map((agent, index) => (
                    <div key={agent.id} className="flex items-center gap-3">
                      <div className="flex items-center gap-2 w-32">
                        <Badge className={getPositionColor(index + 1)}>
                          #{index + 1}
                        </Badge>
                        <span className="text-2xl">{agent.avatar}</span>
                        <span className="font-medium text-sm">{agent.name}</span>
                      </div>
                      <div className="flex-1 relative">
                        <Progress 
                          value={raceProgress[agent.id] || 0} 
                          className="h-6"
                        />
                        <div className="absolute inset-0 flex items-center justify-center text-xs font-medium">
                          {(raceProgress[agent.id] || 0).toFixed(1)}%
                        </div>
                      </div>
                      <div className="w-20 text-right">
                        <Badge variant="outline">
                          {agent.performance.speed}/100
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Live Stats */}
              {isLive && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">
                      {activeCompetition?.spectators || 0}
                    </div>
                    <div className="text-sm text-gray-600">Live Spectators</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">
                      {Math.max(...Object.values(raceProgress)).toFixed(1)}%
                    </div>
                    <div className="text-sm text-gray-600">Leader Progress</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {Object.values(raceProgress).filter(p => p > 0).length}
                    </div>
                    <div className="text-sm text-gray-600">Active Competitors</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Spectator Chat */}
          {spectatorMode && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5" />
                  Live Chat
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-32 bg-gray-50 rounded-lg p-3 mb-3 overflow-y-auto">
                  <div className="space-y-2 text-sm">
                    <div><strong>SpeedFan:</strong> Lightning Bolt is on fire! 🔥</div>
                    <div><strong>AIEnthusiast:</strong> Precision Master making a comeback!</div>
                    <div><strong>TechGuru:</strong> This is the best competition yet!</div>
                    <div><strong>RobotWatcher:</strong> Creative Genius showing innovation 🧠</div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <input 
                    type="text" 
                    placeholder="Type your message..." 
                    className="flex-1 px-3 py-2 border rounded-lg text-sm"
                  />
                  <Button size="sm">Send</Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                Global Leaderboard
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {leaderboard.map((agent, index) => (
                  <div key={agent.id} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <Badge className={getPositionColor(index + 1)}>
                        #{index + 1}
                      </Badge>
                      <span className="text-2xl">{agent.avatar}</span>
                      <div>
                        <div className="font-medium">{agent.name}</div>
                        <div className="text-sm text-gray-600">{agent.type}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-lg">{agent.stats.points}</div>
                      <div className="text-sm text-gray-600">
                        {agent.stats.wins}W-{agent.stats.losses}L-{agent.stats.draws}D
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Agents Tab */}
        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent) => (
              <Card key={agent.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="text-2xl">{agent.avatar}</span>
                    {agent.name}
                    <Badge className={getStatusColor(agent.status)}>
                      {agent.status}
                    </Badge>
                  </CardTitle>
                  <CardDescription>{agent.type}</CardDescription>
                </CardHeader>
                <CardContent>
                  {/* Performance Radar Chart */}
                  <div className="h-48 mb-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={[
                        { metric: 'Speed', value: agent.performance.speed },
                        { metric: 'Accuracy', value: agent.performance.accuracy },
                        { metric: 'Efficiency', value: agent.performance.efficiency },
                        { metric: 'Creativity', value: agent.performance.creativity },
                        { metric: 'Collaboration', value: agent.performance.collaboration }
                      ]}>
                        <PolarGrid />
                        <PolarAngleAxis dataKey="metric" />
                        <PolarRadiusAxis angle={90} domain={[0, 100]} />
                        <Radar
                          name="Performance"
                          dataKey="value"
                          stroke="#8884d8"
                          fill="#8884d8"
                          fillOpacity={0.3}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="font-medium">Ranking</div>
                      <div className="text-lg font-bold">#{agent.stats.ranking}</div>
                    </div>
                    <div>
                      <div className="font-medium">Win Rate</div>
                      <div className="text-lg font-bold">
                        {((agent.stats.wins / agent.stats.total_competitions) * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Competitions Tab */}
        <TabsContent value="competitions" className="space-y-4">
          <div className="space-y-4">
            {competitions.map((competition) => (
              <Card key={competition.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Award className="h-5 w-5" />
                      {competition.name}
                    </span>
                    <Badge className={
                      competition.status === 'active' ? 'bg-green-100 text-green-800' :
                      competition.status === 'upcoming' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }>
                      {competition.status}
                    </Badge>
                  </CardTitle>
                  <CardDescription>{competition.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="font-medium">Type</div>
                      <div className="capitalize">{competition.type}</div>
                    </div>
                    <div>
                      <div className="font-medium">Prize</div>
                      <div>${competition.prize}</div>
                    </div>
                    <div>
                      <div className="font-medium">Participants</div>
                      <div>{competition.participants.length}</div>
                    </div>
                    <div>
                      <div className="font-medium">Spectators</div>
                      <div>{competition.spectators}</div>
                    </div>
                  </div>
                  
                  <div className="mt-4">
                    <div className="font-medium mb-2">Participants:</div>
                    <div className="flex flex-wrap gap-2">
                      {competition.participants.map((participant) => (
                        <Badge key={participant.id} variant="outline">
                          {participant.avatar} {participant.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Performance Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={[
                      { week: 'W1', lightning: 85, precision: 88, creative: 82, team: 86, efficiency: 84 },
                      { week: 'W2', lightning: 87, precision: 90, creative: 85, team: 88, efficiency: 86 },
                      { week: 'W3', lightning: 90, precision: 89, creative: 88, team: 90, efficiency: 88 },
                      { week: 'W4', lightning: 95, precision: 92, creative: 91, team: 92, efficiency: 90 }
                    ]}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="week" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="lightning" stroke="#f59e0b" strokeWidth={2} />
                      <Line type="monotone" dataKey="precision" stroke="#3b82f6" strokeWidth={2} />
                      <Line type="monotone" dataKey="creative" stroke="#8b5cf6" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Competition Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Total Competitions</span>
                    <span className="font-bold">247</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Active Agents</span>
                    <span className="font-bold">156</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Total Spectators</span>
                    <span className="font-bold">12,847</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Prize Pool</span>
                    <span className="font-bold">$45,600</span>
                  </div>
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

export default AgentOlympicsBlock;