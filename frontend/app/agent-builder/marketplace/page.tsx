'use client';

import React from 'react';
import { TemplateMarketplace } from '@/components/agent-builder/TemplateMarketplace';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Store,
  TrendingUp,
  Users,
  Star,
  Download,
  Plus,
  Sparkles,
} from 'lucide-react';

export default function MarketplacePage() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-lg bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white">
        <div className="absolute inset-0 bg-black/20" />
        <div className="relative px-6 py-12 sm:px-12 sm:py-16">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 mb-4">
              <Store className="w-8 h-8" />
              <Badge className="bg-white/20 text-white border-white/30">
                <Sparkles className="w-3 h-3 mr-1" />
                Enhanced
              </Badge>
            </div>
            <h1 className="text-4xl font-bold mb-4">
              템플릿 마켓플레이스
            </h1>
            <p className="text-xl text-white/90 mb-6">
              검증된 에이전트 팀 구성을 찾아보고 바로 사용해보세요. 
              전문가들이 만든 워크플로우 템플릿으로 빠르게 시작하세요.
            </p>
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                <span>1,000+ 활성 사용자</span>
              </div>
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                <span>10,000+ 다운로드</span>
              </div>
              <div className="flex items-center gap-2">
                <Star className="w-4 h-4" />
                <span>평균 4.8점</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              총 템플릿
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">156</div>
            <div className="flex items-center gap-1 text-xs text-green-600">
              <TrendingUp className="w-3 h-3" />
              <span>+12 이번 주</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              인기 카테고리
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">고객 서비스</div>
            <div className="text-xs text-muted-foreground">
              32개 템플릿
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              이번 주 인기
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">AI 리서치 팀</div>
            <div className="text-xs text-muted-foreground">
              245회 다운로드
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              평균 평점
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-1">
              4.8
              <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
            </div>
            <div className="text-xs text-muted-foreground">
              2,847개 리뷰
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Featured Templates Banner */}
      <Card className="border-2 border-yellow-200 bg-gradient-to-r from-yellow-50 to-orange-50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-600" />
                이번 주 추천 템플릿
              </CardTitle>
              <CardDescription>
                전문가가 선별한 고품질 템플릿을 확인해보세요
              </CardDescription>
            </div>
            <Badge className="bg-yellow-500 text-white">
              Featured
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-white rounded-lg border">
              <h4 className="font-medium mb-2">🎧 고객 서비스 자동화</h4>
              <p className="text-sm text-muted-foreground mb-3">
                문의 분류부터 답변 생성까지 완전 자동화
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 text-sm">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span>4.9</span>
                </div>
                <Button size="sm" variant="outline">
                  사용하기
                </Button>
              </div>
            </div>

            <div className="p-4 bg-white rounded-lg border">
              <h4 className="font-medium mb-2">📊 데이터 분석 팀</h4>
              <p className="text-sm text-muted-foreground mb-3">
                데이터 수집, 분석, 리포트 생성 자동화
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 text-sm">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span>4.8</span>
                </div>
                <Button size="sm" variant="outline">
                  사용하기
                </Button>
              </div>
            </div>

            <div className="p-4 bg-white rounded-lg border">
              <h4 className="font-medium mb-2">✍️ 콘텐츠 제작 워크플로우</h4>
              <p className="text-sm text-muted-foreground mb-3">
                아이디어부터 최종 콘텐츠까지 한 번에
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 text-sm">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span>4.7</span>
                </div>
                <Button size="sm" variant="outline">
                  사용하기
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Marketplace */}
      <TemplateMarketplace
        onTemplateSelect={(template) => {
          console.log('Selected template:', template);
        }}
        showCreateButton={true}
      />

      {/* Community Section */}
      <Card>
        <CardHeader>
          <CardTitle>커뮤니티에 기여하기</CardTitle>
          <CardDescription>
            당신만의 템플릿을 공유하고 다른 사용자들과 함께 성장하세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold">템플릿 제작자가 되어보세요</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• 검증된 워크플로우를 템플릿으로 공유</li>
                <li>• 커뮤니티 피드백을 통한 개선</li>
                <li>• 사용량에 따른 리워드 획득</li>
                <li>• 전문가 인증 배지 획득 기회</li>
              </ul>
              <Button className="w-full">
                <Plus className="w-4 h-4 mr-2" />
                템플릿 만들기
              </Button>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold">커뮤니티 통계</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">1,247</div>
                  <div className="text-xs text-muted-foreground">활성 제작자</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">15.2K</div>
                  <div className="text-xs text-muted-foreground">총 다운로드</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">4.8</div>
                  <div className="text-xs text-muted-foreground">평균 평점</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">98%</div>
                  <div className="text-xs text-muted-foreground">만족도</div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}