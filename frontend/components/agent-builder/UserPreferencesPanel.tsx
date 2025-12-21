'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { 
  Settings, 
  Grid, 
  List, 
  Eye, 
  Zap, 
  Volume2, 
  VolumeX,
  Palette,
  Type,
  RotateCcw,
  Pin,
  Star,
  Clock
} from 'lucide-react';
import { useUserPreferences } from '@/lib/stores/userPreferences';

interface UserPreferencesPanelProps {
  trigger?: React.ReactNode;
}

export function UserPreferencesPanel({ trigger }: UserPreferencesPanelProps) {
  const {
    // Current preferences
    defaultViewMode,
    cardDensity,
    defaultSortBy,
    defaultFilterStatus,
    showTemplatesByDefault,
    enableAnimations,
    enableSounds,
    enableVirtualization,
    itemsPerPage,
    highContrast,
    reducedMotion,
    fontSize,
    favoriteTemplates,
    pinnedFlows,
    
    // Actions
    setViewMode,
    setCardDensity,
    setSortBy,
    setFilterStatus,
    toggleTemplatesByDefault,
    toggleAnimations,
    toggleSounds,
    setVirtualization,
    setItemsPerPage,
    setHighContrast,
    setReducedMotion,
    setFontSize,
    resetToDefaults
  } = useUserPreferences();

  const defaultTrigger = (
    <Button variant="outline" size="icon">
      <Settings className="h-4 w-4" />
    </Button>
  );

  return (
    <Sheet>
      <SheetTrigger className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 w-10">
        <Settings className="h-4 w-4" />
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            사용자 설정
          </SheetTitle>
          <SheetDescription>
            워크플로우 플랫폼 사용 환경을 개인화하세요
          </SheetDescription>
        </SheetHeader>

        <div className="space-y-6 mt-6">
          {/* 보기 설정 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Eye className="h-4 w-4" />
                보기 설정
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>기본 보기 모드</Label>
                <Select value={defaultViewMode} onValueChange={setViewMode}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="grid">
                      <div className="flex items-center gap-2">
                        <Grid className="h-4 w-4" />
                        그리드 뷰
                      </div>
                    </SelectItem>
                    <SelectItem value="list">
                      <div className="flex items-center gap-2">
                        <List className="h-4 w-4" />
                        리스트 뷰
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>카드 밀도</Label>
                <Select value={cardDensity} onValueChange={setCardDensity}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="compact">컴팩트</SelectItem>
                    <SelectItem value="comfortable">편안함</SelectItem>
                    <SelectItem value="spacious">여유로움</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="templates-default">기본적으로 템플릿 표시</Label>
                <Switch
                  id="templates-default"
                  checked={showTemplatesByDefault}
                  onCheckedChange={toggleTemplatesByDefault}
                />
              </div>
            </CardContent>
          </Card>

          {/* 정렬 및 필터 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Clock className="h-4 w-4" />
                기본 정렬 및 필터
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>기본 정렬 방식</Label>
                <Select value={defaultSortBy} onValueChange={setSortBy}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="updated_at">최근 수정순</SelectItem>
                    <SelectItem value="created_at">생성일순</SelectItem>
                    <SelectItem value="name">이름순</SelectItem>
                    <SelectItem value="execution_count">실행 횟수순</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>기본 상태 필터</Label>
                <Select value={defaultFilterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">전체</SelectItem>
                    <SelectItem value="active">활성화</SelectItem>
                    <SelectItem value="inactive">비활성화</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* 성능 설정 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Zap className="h-4 w-4" />
                성능 설정
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label htmlFor="virtualization">가상화 스크롤링</Label>
                  <p className="text-xs text-muted-foreground">
                    대량의 항목에서 성능 향상
                  </p>
                </div>
                <Switch
                  id="virtualization"
                  checked={enableVirtualization}
                  onCheckedChange={setVirtualization}
                />
              </div>

              <div className="space-y-2">
                <Label>페이지당 항목 수</Label>
                <Select value={itemsPerPage.toString()} onValueChange={(v) => setItemsPerPage(parseInt(v))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="6">6개</SelectItem>
                    <SelectItem value="12">12개</SelectItem>
                    <SelectItem value="24">24개</SelectItem>
                    <SelectItem value="48">48개</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="animations">애니메이션 효과</Label>
                <Switch
                  id="animations"
                  checked={enableAnimations}
                  onCheckedChange={toggleAnimations}
                />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Label htmlFor="sounds">사운드 효과</Label>
                  {enableSounds ? <Volume2 className="h-3 w-3" /> : <VolumeX className="h-3 w-3" />}
                </div>
                <Switch
                  id="sounds"
                  checked={enableSounds}
                  onCheckedChange={toggleSounds}
                />
              </div>
            </CardContent>
          </Card>

          {/* 접근성 설정 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Palette className="h-4 w-4" />
                접근성 설정
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="high-contrast">고대비 모드</Label>
                <Switch
                  id="high-contrast"
                  checked={highContrast}
                  onCheckedChange={setHighContrast}
                />
              </div>

              <div className="flex items-center justify-between">
                <Label htmlFor="reduced-motion">모션 감소</Label>
                <Switch
                  id="reduced-motion"
                  checked={reducedMotion}
                  onCheckedChange={setReducedMotion}
                />
              </div>

              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Type className="h-4 w-4" />
                  글꼴 크기
                </Label>
                <Select value={fontSize} onValueChange={setFontSize}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="small">작게</SelectItem>
                    <SelectItem value="medium">보통</SelectItem>
                    <SelectItem value="large">크게</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* 사용자 데이터 */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">사용자 데이터</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Star className="h-4 w-4 text-yellow-500" />
                  <span>즐겨찾기: {favoriteTemplates.length}개</span>
                </div>
                <div className="flex items-center gap-2">
                  <Pin className="h-4 w-4 text-blue-500" />
                  <span>고정된 플로우: {pinnedFlows.length}개</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Separator />

          {/* 초기화 */}
          <div className="flex justify-center">
            <Button 
              variant="outline" 
              onClick={resetToDefaults}
              className="flex items-center gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              기본값으로 초기화
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}