'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Package,
  Search,
  Plus,
  Trash2,
  Check,
  AlertTriangle,
  Shield,
  Download,
  ExternalLink,
  Loader2,
  Info,
} from 'lucide-react';
import { toast } from 'sonner';

interface InstalledPackage {
  name: string;
  version: string;
  description?: string;
  isBuiltin?: boolean;
}

interface AvailablePackage {
  name: string;
  version: string;
  description: string;
  downloads?: number;
  isSecure: boolean;
}

interface PackageManagerProps {
  language: string;
  onPackagesChange?: (packages: string[]) => void;
}

// 언어별 기본 패키지
const BUILTIN_PACKAGES: Record<string, InstalledPackage[]> = {
  python: [
    { name: 'json', version: 'builtin', description: 'JSON 인코딩/디코딩', isBuiltin: true },
    { name: 'datetime', version: 'builtin', description: '날짜/시간 처리', isBuiltin: true },
    { name: 'math', version: 'builtin', description: '수학 함수', isBuiltin: true },
    { name: 'random', version: 'builtin', description: '난수 생성', isBuiltin: true },
    { name: 're', version: 'builtin', description: '정규표현식', isBuiltin: true },
    { name: 'csv', version: 'builtin', description: 'CSV 파일 처리', isBuiltin: true },
    { name: 'io', version: 'builtin', description: 'I/O 스트림', isBuiltin: true },
    { name: 'base64', version: 'builtin', description: 'Base64 인코딩', isBuiltin: true },
  ],
  javascript: [
    { name: 'JSON', version: 'builtin', description: 'JSON 처리', isBuiltin: true },
    { name: 'Math', version: 'builtin', description: '수학 함수', isBuiltin: true },
    { name: 'Date', version: 'builtin', description: '날짜/시간', isBuiltin: true },
    { name: 'fetch', version: 'builtin', description: 'HTTP 요청', isBuiltin: true },
    { name: 'Promise', version: 'builtin', description: '비동기 처리', isBuiltin: true },
  ],
};

// 설치 가능한 패키지 (화이트리스트)
const AVAILABLE_PACKAGES: Record<string, AvailablePackage[]> = {
  python: [
    { name: 'requests', version: '2.31.0', description: 'HTTP 라이브러리', downloads: 1000000, isSecure: true },
    { name: 'pandas', version: '2.0.3', description: '데이터 분석', downloads: 800000, isSecure: true },
    { name: 'numpy', version: '1.24.0', description: '수치 계산', downloads: 900000, isSecure: true },
    { name: 'beautifulsoup4', version: '4.12.0', description: 'HTML 파싱', downloads: 500000, isSecure: true },
    { name: 'httpx', version: '0.24.0', description: '비동기 HTTP', downloads: 300000, isSecure: true },
    { name: 'pydantic', version: '2.0.0', description: '데이터 검증', downloads: 400000, isSecure: true },
  ],
  javascript: [
    { name: 'lodash', version: '4.17.21', description: '유틸리티 함수', downloads: 2000000, isSecure: true },
    { name: 'axios', version: '1.4.0', description: 'HTTP 클라이언트', downloads: 1500000, isSecure: true },
    { name: 'dayjs', version: '1.11.0', description: '날짜 처리', downloads: 800000, isSecure: true },
  ],
};

export default function PackageManager({ language, onPackagesChange }: PackageManagerProps) {
  const [installedPackages, setInstalledPackages] = useState<InstalledPackage[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isInstalling, setIsInstalling] = useState<string | null>(null);

  // 초기 패키지 로드
  useEffect(() => {
    const builtins = BUILTIN_PACKAGES[language] || [];
    setInstalledPackages(builtins);
  }, [language]);

  // 패키지 설치
  const installPackage = useCallback(async (pkg: AvailablePackage) => {
    setIsInstalling(pkg.name);
    
    // 시뮬레이션 딜레이
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setInstalledPackages(prev => {
      if (prev.some(p => p.name === pkg.name)) {
        toast.error(`${pkg.name}은(는) 이미 설치되어 있습니다.`);
        return prev;
      }
      const updated = [...prev, { name: pkg.name, version: pkg.version, description: pkg.description }];
      onPackagesChange?.(updated.filter(p => !p.isBuiltin).map(p => p.name));
      toast.success(`${pkg.name} 설치 완료`);
      return updated;
    });
    
    setIsInstalling(null);
  }, [onPackagesChange]);

  // 패키지 제거
  const removePackage = useCallback((pkgName: string) => {
    setInstalledPackages(prev => {
      const pkg = prev.find(p => p.name === pkgName);
      if (pkg?.isBuiltin) {
        toast.error('기본 패키지는 제거할 수 없습니다.');
        return prev;
      }
      const updated = prev.filter(p => p.name !== pkgName);
      onPackagesChange?.(updated.filter(p => !p.isBuiltin).map(p => p.name));
      toast.success(`${pkgName} 제거 완료`);
      return updated;
    });
  }, [onPackagesChange]);

  // 검색 필터링
  const availablePackages = (AVAILABLE_PACKAGES[language] || []).filter(
    pkg => !installedPackages.some(ip => ip.name === pkg.name) &&
           (searchQuery === '' || pkg.name.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/30 dark:to-orange-950/30 rounded-lg border border-amber-200 dark:border-amber-800">
        <Package className="h-5 w-5 text-amber-600" />
        <span className="font-medium flex-1">Package Manager</span>
        <Badge variant="secondary" className="text-xs">Phase 3</Badge>
      </div>

      {/* Security Notice */}
      <div className="flex items-start gap-2 p-2 bg-blue-50 dark:bg-blue-950/30 rounded-lg text-xs">
        <Shield className="h-4 w-4 text-blue-600 mt-0.5" />
        <p className="text-blue-700 dark:text-blue-300">
          모든 패키지는 보안 검증된 샌드박스 환경에서 실행됩니다.
        </p>
      </div>

      {/* Installed Packages */}
      <div className="space-y-2">
        <p className="text-sm font-medium">설치된 패키지</p>
        <ScrollArea className="h-32 border rounded-lg p-2">
          <div className="space-y-1">
            {installedPackages.map((pkg) => (
              <div
                key={pkg.name}
                className="flex items-center gap-2 p-2 hover:bg-muted rounded"
              >
                <Check className="h-4 w-4 text-green-500" />
                <span className="text-sm font-mono flex-1">{pkg.name}</span>
                <Badge variant="outline" className="text-xs">{pkg.version}</Badge>
                {pkg.isBuiltin ? (
                  <Badge variant="secondary" className="text-xs">내장</Badge>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0"
                    onClick={() => removePackage(pkg.name)}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Search & Available Packages */}
      <div className="space-y-2">
        <p className="text-sm font-medium">패키지 추가</p>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="패키지 검색..."
            className="pl-9"
          />
        </div>
        <ScrollArea className="h-40 border rounded-lg p-2">
          <div className="space-y-1">
            {availablePackages.map((pkg) => (
              <div
                key={pkg.name}
                className="flex items-center gap-2 p-2 hover:bg-muted rounded"
              >
                <Package className="h-4 w-4 text-muted-foreground" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono">{pkg.name}</span>
                    <Badge variant="outline" className="text-xs">{pkg.version}</Badge>
                    {pkg.isSecure && (
                      <Shield className="h-3 w-3 text-green-500" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">{pkg.description}</p>
                </div>
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1"
                  onClick={() => installPackage(pkg)}
                  disabled={isInstalling === pkg.name}
                >
                  {isInstalling === pkg.name ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Download className="h-3 w-3" />
                  )}
                  설치
                </Button>
              </div>
            ))}
            {availablePackages.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">
                {searchQuery ? '검색 결과가 없습니다.' : '모든 패키지가 설치되어 있습니다.'}
              </p>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Info */}
      <div className="flex items-start gap-2 p-2 bg-muted rounded-lg text-xs">
        <Info className="h-4 w-4 mt-0.5" />
        <p className="text-muted-foreground">
          코드에서 <code className="bg-black/10 dark:bg-white/10 px-1 rounded">import {'{package}'}</code>로 사용하세요.
        </p>
      </div>
    </div>
  );
}
