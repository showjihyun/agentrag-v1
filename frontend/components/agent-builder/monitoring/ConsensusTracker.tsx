'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Vote,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  AlertTriangle,
  MessageSquare,
  Target,
  BarChart3,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface ConsensusVote {
  id: string;
  voterId: string;
  voterName: string;
  decision: 'for' | 'against' | 'abstain';
  reasoning?: string;
  confidence: number; // 0-1
  timestamp: string;
  weight?: number; // 투표 가중치
}

interface ConsensusSession {
  id: string;
  topic: string;
  description: string;
  status: 'active' | 'completed' | 'failed' | 'timeout';
  startTime: string;
  endTime?: string;
  threshold: number; // 합의 임계값 (0-1)
  currentConsensus: number; // 현재 합의 수준 (0-1)
  totalVoters: number;
  votes: ConsensusVote[];
  deadline?: string;
  facilitator?: string;
  rules: {
    requireUnanimity: boolean;
    allowAbstention: boolean;
    weightedVoting: boolean;
    maxRounds: number;
    currentRound: number;
  };
}

interface ConsensusTrackerProps {
  sessions: ConsensusSession[];
  onVoteSubmit?: (sessionId: string, vote: Omit<ConsensusVote, 'id' | 'timestamp'>) => void;
  onSessionControl?: (sessionId: string, action: 'start' | 'pause' | 'end' | 'extend') => void;
  className?: string;
}

const VoteCard: React.FC<{
  vote: ConsensusVote;
  showDetails?: boolean;
}> = ({ vote, showDetails = false }) => {
  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case 'for':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'against':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'abstain':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getDecisionIcon = (decision: string) => {
    switch (decision) {
      case 'for':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'against':
        return <XCircle className="w-4 h-4" />;
      case 'abstain':
        return <Clock className="w-4 h-4" />;
      default:
        return <Vote className="w-4 h-4" />;
    }
  };

  return (
    <div className={cn('p-3 border rounded-lg', getDecisionColor(vote.decision))}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {getDecisionIcon(vote.decision)}
          <span className="font-medium">{vote.voterName}</span>
          <Badge variant="outline" className="text-xs">
            {vote.decision === 'for' ? '찬성' : 
             vote.decision === 'against' ? '반대' : '기권'}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          {vote.weight && vote.weight !== 1 && (
            <Badge variant="secondary" className="text-xs">
              가중치 {vote.weight}
            </Badge>
          )}
          <Badge variant="outline" className="text-xs">
            신뢰도 {(vote.confidence * 100).toFixed(0)}%
          </Badge>
        </div>
      </div>
      
      <div className="text-xs text-gray-500 mb-2">{vote.timestamp}</div>
      
      {showDetails && vote.reasoning && (
        <div className="mt-2 p-2 bg-white/50 rounded text-sm">
          <div className="font-medium mb-1">투표 이유:</div>
          <div className="text-gray-700">{vote.reasoning}</div>
        </div>
      )}
    </div>
  );
};

const ConsensusSessionCard: React.FC<{
  session: ConsensusSession;
  onVoteSubmit?: (vote: Omit<ConsensusVote, 'id' | 'timestamp'>) => void;
  onControl?: (action: 'start' | 'pause' | 'end' | 'extend') => void;
}> = ({ session, onVoteSubmit, onControl }) => {
  const [selectedTab, setSelectedTab] = useState('overview');
  
  const votesFor = session.votes.filter(v => v.decision === 'for').length;
  const votesAgainst = session.votes.filter(v => v.decision === 'against').length;
  const votesAbstain = session.votes.filter(v => v.decision === 'abstain').length;
  const totalVotes = session.votes.length;
  const votingProgress = session.totalVoters > 0 ? (totalVotes / session.totalVoters) * 100 : 0;
  const supportRate = totalVotes > 0 ? (votesFor / totalVotes) * 100 : 0;
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'text-blue-600 bg-blue-50';
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'failed':
        return 'text-red-600 bg-red-50';
      case 'timeout':
        return 'text-yellow-600 bg-yellow-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const isConsensusReached = session.currentConsensus >= session.threshold;
  const timeRemaining = session.deadline ? 
    Math.max(0, new Date(session.deadline).getTime() - new Date().getTime()) : null;

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{session.topic}</CardTitle>
            <CardDescription className="mt-1">{session.description}</CardDescription>
          </div>
          <Badge className={cn('text-xs', getStatusColor(session.status))}>
            {session.status === 'active' ? '진행 중' :
             session.status === 'completed' ? '완료' :
             session.status === 'failed' ? '실패' :
             session.status === 'timeout' ? '시간 초과' : '대기'}
          </Badge>
        </div>
        
        {/* 진행률 및 합의 수준 */}
        <div className="space-y-3 mt-4">
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span>투표 진행률</span>
              <span>{totalVotes}/{session.totalVoters} ({votingProgress.toFixed(0)}%)</span>
            </div>
            <Progress value={votingProgress} className="h-2" />
          </div>
          
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span>합의 수준</span>
              <span>{(session.currentConsensus * 100).toFixed(0)}% (목표: {(session.threshold * 100).toFixed(0)}%)</span>
            </div>
            <Progress 
              value={session.currentConsensus * 100} 
              className={cn('h-2', isConsensusReached && 'bg-green-100')}
            />
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">개요</TabsTrigger>
            <TabsTrigger value="votes">투표 ({totalVotes})</TabsTrigger>
            <TabsTrigger value="stats">통계</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            {/* 투표 현황 요약 */}
            <div className="grid grid-cols-3 gap-2">
              <div className="text-center p-2 bg-green-50 rounded">
                <div className="text-lg font-semibold text-green-600">{votesFor}</div>
                <div className="text-xs text-gray-600">찬성</div>
              </div>
              <div className="text-center p-2 bg-red-50 rounded">
                <div className="text-lg font-semibold text-red-600">{votesAgainst}</div>
                <div className="text-xs text-gray-600">반대</div>
              </div>
              <div className="text-center p-2 bg-gray-50 rounded">
                <div className="text-lg font-semibold text-gray-600">{votesAbstain}</div>
                <div className="text-xs text-gray-600">기권</div>
              </div>
            </div>
            
            {/* 세션 정보 */}
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">라운드:</span>
                <span>{session.rules.currentRound}/{session.rules.maxRounds}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">시작 시간:</span>
                <span>{session.startTime}</span>
              </div>
              {timeRemaining && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">남은 시간:</span>
                  <span className="text-orange-600">
                    {Math.floor(timeRemaining / 60000)}분 {Math.floor((timeRemaining % 60000) / 1000)}초
                  </span>
                </div>
              )}
              {session.facilitator && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">진행자:</span>
                  <span>{session.facilitator}</span>
                </div>
              )}
            </div>
            
            {/* 제어 버튼 */}
            {session.status === 'active' && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onControl?.('pause')}
                >
                  일시정지
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onControl?.('end')}
                >
                  종료
                </Button>
                {timeRemaining && timeRemaining < 300000 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onControl?.('extend')}
                  >
                    시간 연장
                  </Button>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="votes">
            <ScrollArea className="h-[300px]">
              <div className="space-y-2">
                {session.votes.map((vote) => (
                  <VoteCard key={vote.id} vote={vote} showDetails />
                ))}
                {session.votes.length === 0 && (
                  <div className="text-center text-gray-500 py-8">
                    아직 투표가 없습니다.
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="stats" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded">
                <div className="text-xl font-bold text-blue-600">{supportRate.toFixed(0)}%</div>
                <div className="text-sm text-gray-600">지지율</div>
              </div>
              <div className="text-center p-3 bg-purple-50 rounded">
                <div className="text-xl font-bold text-purple-600">
                  {session.votes.reduce((sum, v) => sum + v.confidence, 0) / session.votes.length || 0}
                </div>
                <div className="text-sm text-gray-600">평균 신뢰도</div>
              </div>
            </div>
            
            {/* 투표 규칙 */}
            <div className="space-y-2">
              <h4 className="font-medium">투표 규칙</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <div>• 만장일치 필요: {session.rules.requireUnanimity ? '예' : '아니오'}</div>
                <div>• 기권 허용: {session.rules.allowAbstention ? '예' : '아니오'}</div>
                <div>• 가중 투표: {session.rules.weightedVoting ? '예' : '아니오'}</div>
                <div>• 최대 라운드: {session.rules.maxRounds}회</div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export const ConsensusTracker: React.FC<ConsensusTrackerProps> = ({
  sessions,
  onVoteSubmit,
  onSessionControl,
  className,
}) => {
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  // 통계 계산
  const activeSessions = sessions.filter(s => s.status === 'active').length;
  const completedSessions = sessions.filter(s => s.status === 'completed').length;
  const totalVotes = sessions.reduce((sum, s) => sum + s.votes.length, 0);
  const avgConsensusLevel = sessions.length > 0 ? 
    sessions.reduce((sum, s) => sum + s.currentConsensus, 0) / sessions.length : 0;

  return (
    <div className={cn('space-y-6', className)}>
      {/* 헤더 */}
      <div>
        <h2 className="text-2xl font-bold">합의 추적기</h2>
        <p className="text-gray-600">Agent 간 합의 과정 실시간 모니터링</p>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Vote className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{activeSessions}</div>
                <div className="text-sm text-gray-600">진행 중인 합의</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{completedSessions}</div>
                <div className="text-sm text-gray-600">완료된 합의</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{totalVotes}</div>
                <div className="text-sm text-gray-600">총 투표 수</div>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{(avgConsensusLevel * 100).toFixed(0)}%</div>
                <div className="text-sm text-gray-600">평균 합의 수준</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 합의 세션 목록 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {sessions.map((session) => (
          <ConsensusSessionCard
            key={session.id}
            session={session}
            onVoteSubmit={(vote) => onVoteSubmit?.(session.id, vote)}
            onControl={(action) => onSessionControl?.(session.id, action)}
          />
        ))}
        
        {sessions.length === 0 && (
          <div className="col-span-full text-center text-gray-500 py-12">
            <Vote className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <div className="text-lg font-medium mb-2">진행 중인 합의가 없습니다</div>
            <div className="text-sm">Agent 간 합의가 시작되면 여기에 표시됩니다.</div>
          </div>
        )}
      </div>
    </div>
  );
};