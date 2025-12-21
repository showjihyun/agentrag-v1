'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { 
  Plus, 
  Sparkles, 
  Search, 
  Filter,
  LayoutGrid,
  List,
  Zap
} from 'lucide-react';

interface QuickActionBarProps {
  type: 'agentflow' | 'chatflow';
  onNewFlow: () => void;
  onToggleTemplates: () => void;
  showTemplates: boolean;
  viewMode: 'grid' | 'list';
  onViewModeChange: (mode: 'grid' | 'list') => void;
}

export function QuickActionBar({ 
  type, 
  onNewFlow, 
  onToggleTemplates, 
  showTemplates,
  viewMode,
  onViewModeChange 
}: QuickActionBarProps) {
  const isAgentflow = type === 'agentflow';
  const primaryColor = isAgentflow ? 'purple' : 'blue';

  return (
    <Card className="p-4 mb-6 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 border-0">
      <div className="flex items-center justify-between">
        {/* 왼쪽: 빠른 액션 */}
        <div className="flex items-center gap-3">
          <Button 
            size="lg"
            onClick={onNewFlow}
            className={`bg-gradient-to-r from-${primaryColor}-600 to-${primaryColor}-700 hover:from-${primaryColor}-700 hover:to-${primaryColor}-800 shadow-lg hover:shadow-xl transition-all`}
          >
            <Plus className="mr-2 h-5 w-5" />
            새 {isAgentflow ? 'Agentflow' : 'Chatflow'}
          </Button>
          
          <Button 
            variant="outline" 
            onClick={onToggleTemplates}
            className="border-2"
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {showTemplates ? '템플릿 숨기기' : '템플릿으로 시작'}
          </Button>

          <Button variant="ghost" size="sm">
            <Zap className="mr-2 h-4 w-4" />
            빠른 설정
          </Button>
        </div>

        {/* 오른쪽: 뷰 옵션 */}
        <div className="flex items-center gap-2">
          <div className="flex items-center border rounded-lg p-1 bg-white dark:bg-gray-800">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => onViewModeChange('grid')}
              className="h-8 w-8 p-0"
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => onViewModeChange('list')}
              className="h-8 w-8 p-0"
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}