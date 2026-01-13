/**
 * Accessibility Provider
 * 접근성 표준 준수 및 다국어 지원을 위한 프로바이더
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { 
  Accessibility, 
  Eye, 
  EyeOff, 
  Volume2, 
  VolumeX, 
  Type, 
  Contrast, 
  MousePointer,
  Keyboard,
  Languages,
  Settings,
  Monitor,
  Smartphone,
  Tablet
} from 'lucide-react';

interface AccessibilitySettings {
  // Visual
  highContrast: boolean;
  fontSize: number; // 0.8 to 1.5
  reducedMotion: boolean;
  focusIndicators: boolean;
  
  // Audio
  soundEnabled: boolean;
  screenReaderSupport: boolean;
  audioDescriptions: boolean;
  
  // Motor
  keyboardNavigation: boolean;
  clickDelay: number; // ms
  largerClickTargets: boolean;
  
  // Cognitive
  simplifiedUI: boolean;
  autoplayDisabled: boolean;
  timeoutExtended: boolean;
  
  // Language & Localization
  language: 'ko' | 'en';
  dateFormat: 'ko' | 'en' | 'iso';
  numberFormat: 'ko' | 'en';
  
  // Device
  deviceType: 'desktop' | 'tablet' | 'mobile';
  touchOptimized: boolean;
}

interface AccessibilityContextType {
  settings: AccessibilitySettings;
  updateSettings: (updates: Partial<AccessibilitySettings>) => void;
  announceToScreenReader: (message: string) => void;
  t: (key: string, params?: Record<string, any>) => string;
}

const defaultSettings: AccessibilitySettings = {
  highContrast: false,
  fontSize: 1.0,
  reducedMotion: false,
  focusIndicators: true,
  soundEnabled: true,
  screenReaderSupport: false,
  audioDescriptions: false,
  keyboardNavigation: true,
  clickDelay: 0,
  largerClickTargets: false,
  simplifiedUI: false,
  autoplayDisabled: false,
  timeoutExtended: false,
  language: 'ko',
  dateFormat: 'ko',
  numberFormat: 'ko',
  deviceType: 'desktop',
  touchOptimized: false
};

// Translations
const translations = {
  ko: {
    // Navigation
    'nav.home': '홈',
    'nav.patterns': '패턴',
    'nav.monitoring': '모니터링',
    'nav.settings': '설정',
    'nav.help': '도움말',
    
    // Orchestration Patterns
    'pattern.consensus_building': '합의 구축',
    'pattern.dynamic_routing': '동적 라우팅',
    'pattern.swarm_intelligence': '군집 지능',
    'pattern.event_driven': '이벤트 기반',
    'pattern.reflection': '자기 성찰',
    
    // Common Actions
    'action.save': '저장',
    'action.cancel': '취소',
    'action.delete': '삭제',
    'action.edit': '편집',
    'action.create': '생성',
    'action.start': '시작',
    'action.stop': '중지',
    'action.pause': '일시정지',
    'action.resume': '재개',
    'action.reset': '초기화',
    
    // Status
    'status.completed': '완료',
    'status.failed': '실패',
    'status.running': '실행 중',
    'status.pending': '대기 중',
    'status.timeout': '시간 초과',
    
    // Accessibility
    'a11y.high_contrast': '고대비 모드',
    'a11y.font_size': '글자 크기',
    'a11y.reduced_motion': '애니메이션 줄이기',
    'a11y.screen_reader': '스크린 리더 지원',
    'a11y.keyboard_nav': '키보드 탐색',
    'a11y.language': '언어',
    
    // Messages
    'msg.loading': '로딩 중...',
    'msg.error': '오류가 발생했습니다',
    'msg.success': '성공적으로 완료되었습니다',
    'msg.no_data': '데이터가 없습니다',
    
    // Validation
    'validation.required': '필수 항목입니다',
    'validation.invalid': '유효하지 않은 값입니다',
    'validation.min_length': '최소 {min}자 이상 입력해주세요',
    'validation.max_length': '최대 {max}자까지 입력 가능합니다'
  },
  en: {
    // Navigation
    'nav.home': 'Home',
    'nav.patterns': 'Patterns',
    'nav.monitoring': 'Monitoring',
    'nav.settings': 'Settings',
    'nav.help': 'Help',
    
    // Orchestration Patterns
    'pattern.consensus_building': 'Consensus Building',
    'pattern.dynamic_routing': 'Dynamic Routing',
    'pattern.swarm_intelligence': 'Swarm Intelligence',
    'pattern.event_driven': 'Event Driven',
    'pattern.reflection': 'Reflection',
    
    // Common Actions
    'action.save': 'Save',
    'action.cancel': 'Cancel',
    'action.delete': 'Delete',
    'action.edit': 'Edit',
    'action.create': 'Create',
    'action.start': 'Start',
    'action.stop': 'Stop',
    'action.pause': 'Pause',
    'action.resume': 'Resume',
    'action.reset': 'Reset',
    
    // Status
    'status.completed': 'Completed',
    'status.failed': 'Failed',
    'status.running': 'Running',
    'status.pending': 'Pending',
    'status.timeout': 'Timeout',
    
    // Accessibility
    'a11y.high_contrast': 'High Contrast',
    'a11y.font_size': 'Font Size',
    'a11y.reduced_motion': 'Reduce Motion',
    'a11y.screen_reader': 'Screen Reader Support',
    'a11y.keyboard_nav': 'Keyboard Navigation',
    'a11y.language': 'Language',
    
    // Messages
    'msg.loading': 'Loading...',
    'msg.error': 'An error occurred',
    'msg.success': 'Successfully completed',
    'msg.no_data': 'No data available',
    
    // Validation
    'validation.required': 'This field is required',
    'validation.invalid': 'Invalid value',
    'validation.min_length': 'Minimum {min} characters required',
    'validation.max_length': 'Maximum {max} characters allowed'
  }
};

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityProvider');
  }
  return context;
};

interface AccessibilityProviderProps {
  children: React.ReactNode;
}

export const AccessibilityProvider: React.FC<AccessibilityProviderProps> = ({ children }) => {
  const [settings, setSettings] = useState<AccessibilitySettings>(() => {
    // Load from localStorage
    const saved = localStorage.getItem('accessibility-settings');
    return saved ? { ...defaultSettings, ...JSON.parse(saved) } : defaultSettings;
  });

  // Save settings to localStorage
  useEffect(() => {
    localStorage.setItem('accessibility-settings', JSON.stringify(settings));
  }, [settings]);

  // Apply CSS custom properties for accessibility
  useEffect(() => {
    const root = document.documentElement;
    
    // Font size
    root.style.setProperty('--font-size-scale', settings.fontSize.toString());
    
    // High contrast
    if (settings.highContrast) {
      root.classList.add('high-contrast');
    } else {
      root.classList.remove('high-contrast');
    }
    
    // Reduced motion
    if (settings.reducedMotion) {
      root.classList.add('reduced-motion');
    } else {
      root.classList.remove('reduced-motion');
    }
    
    // Focus indicators
    if (settings.focusIndicators) {
      root.classList.add('enhanced-focus');
    } else {
      root.classList.remove('enhanced-focus');
    }
    
    // Larger click targets
    if (settings.largerClickTargets) {
      root.classList.add('large-targets');
    } else {
      root.classList.remove('large-targets');
    }
    
    // Touch optimized
    if (settings.touchOptimized) {
      root.classList.add('touch-optimized');
    } else {
      root.classList.remove('touch-optimized');
    }
  }, [settings]);

  // Detect device type
  useEffect(() => {
    const detectDeviceType = () => {
      const width = window.innerWidth;
      const isTouchDevice = 'ontouchstart' in window;
      
      let deviceType: AccessibilitySettings['deviceType'] = 'desktop';
      if (width < 768) {
        deviceType = 'mobile';
      } else if (width < 1024) {
        deviceType = 'tablet';
      }
      
      setSettings(prev => ({
        ...prev,
        deviceType,
        touchOptimized: isTouchDevice
      }));
    };

    detectDeviceType();
    window.addEventListener('resize', detectDeviceType);
    return () => window.removeEventListener('resize', detectDeviceType);
  }, []);

  // Screen reader announcements
  const announceToScreenReader = (message: string) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  };

  // Translation function
  const t = (key: string, params?: Record<string, any>): string => {
    const translation = translations[settings.language][key] || key;
    
    if (params) {
      return Object.entries(params).reduce((str, [param, value]) => {
        return str.replace(`{${param}}`, String(value));
      }, translation);
    }
    
    return translation;
  };

  const updateSettings = (updates: Partial<AccessibilitySettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  };

  const contextValue: AccessibilityContextType = {
    settings,
    updateSettings,
    announceToScreenReader,
    t
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
    </AccessibilityContext.Provider>
  );
};

// Accessibility Settings Panel Component
export const AccessibilitySettingsPanel: React.FC = () => {
  const { settings, updateSettings, t } = useAccessibility();

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Accessibility className="h-6 w-6 mr-2" />
          {t('a11y.settings')} / Accessibility Settings
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Visual Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold flex items-center">
            <Eye className="h-5 w-5 mr-2" />
            Visual / 시각적 설정
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="high-contrast">{t('a11y.high_contrast')}</Label>
              <Switch
                id="high-contrast"
                checked={settings.highContrast}
                onCheckedChange={(checked) => updateSettings({ highContrast: checked })}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label htmlFor="reduced-motion">{t('a11y.reduced_motion')}</Label>
              <Switch
                id="reduced-motion"
                checked={settings.reducedMotion}
                onCheckedChange={(checked) => updateSettings({ reducedMotion: checked })}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="font-size">{t('a11y.font_size')}: {Math.round(settings.fontSize * 100)}%</Label>
            <Slider
              id="font-size"
              value={[settings.fontSize]}
              onValueChange={([value]) => updateSettings({ fontSize: value })}
              min={0.8}
              max={1.5}
              step={0.1}
              className="w-full"
            />
          </div>
        </div>

        {/* Audio Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold flex items-center">
            <Volume2 className="h-5 w-5 mr-2" />
            Audio / 오디오 설정
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="sound-enabled">Sound Effects / 효과음</Label>
              <Switch
                id="sound-enabled"
                checked={settings.soundEnabled}
                onCheckedChange={(checked) => updateSettings({ soundEnabled: checked })}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label htmlFor="screen-reader">{t('a11y.screen_reader')}</Label>
              <Switch
                id="screen-reader"
                checked={settings.screenReaderSupport}
                onCheckedChange={(checked) => updateSettings({ screenReaderSupport: checked })}
              />
            </div>
          </div>
        </div>

        {/* Motor Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold flex items-center">
            <MousePointer className="h-5 w-5 mr-2" />
            Motor / 조작 설정
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="keyboard-nav">{t('a11y.keyboard_nav')}</Label>
              <Switch
                id="keyboard-nav"
                checked={settings.keyboardNavigation}
                onCheckedChange={(checked) => updateSettings({ keyboardNavigation: checked })}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <Label htmlFor="large-targets">Large Click Targets / 큰 클릭 영역</Label>
              <Switch
                id="large-targets"
                checked={settings.largerClickTargets}
                onCheckedChange={(checked) => updateSettings({ largerClickTargets: checked })}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="click-delay">Click Delay / 클릭 지연: {settings.clickDelay}ms</Label>
            <Slider
              id="click-delay"
              value={[settings.clickDelay]}
              onValueChange={([value]) => updateSettings({ clickDelay: value })}
              min={0}
              max={1000}
              step={100}
              className="w-full"
            />
          </div>
        </div>

        {/* Language Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold flex items-center">
            <Languages className="h-5 w-5 mr-2" />
            Language / 언어 설정
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="language">{t('a11y.language')}</Label>
              <Select
                value={settings.language}
                onValueChange={(value: 'ko' | 'en') => updateSettings({ language: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ko">한국어</SelectItem>
                  <SelectItem value="en">English</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="date-format">Date Format / 날짜 형식</Label>
              <Select
                value={settings.dateFormat}
                onValueChange={(value: 'ko' | 'en' | 'iso') => updateSettings({ dateFormat: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ko">2026년 1월 9일</SelectItem>
                  <SelectItem value="en">January 9, 2026</SelectItem>
                  <SelectItem value="iso">2026-01-09</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Device Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold flex items-center">
            <Monitor className="h-5 w-5 mr-2" />
            Device / 기기 설정
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Device Type / 기기 유형</Label>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                {settings.deviceType === 'desktop' && <Monitor className="h-4 w-4" />}
                {settings.deviceType === 'tablet' && <Tablet className="h-4 w-4" />}
                {settings.deviceType === 'mobile' && <Smartphone className="h-4 w-4" />}
                <span>{settings.deviceType} (자동 감지)</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <Label htmlFor="touch-optimized">Touch Optimized / 터치 최적화</Label>
              <Switch
                id="touch-optimized"
                checked={settings.touchOptimized}
                onCheckedChange={(checked) => updateSettings({ touchOptimized: checked })}
              />
            </div>
          </div>
        </div>

        {/* Reset Button */}
        <div className="pt-4 border-t">
          <Button
            variant="outline"
            onClick={() => setSettings(defaultSettings)}
            className="w-full"
          >
            Reset to Defaults / 기본값으로 초기화
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};