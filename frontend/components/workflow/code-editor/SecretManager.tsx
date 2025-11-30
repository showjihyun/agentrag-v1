'use client';

import { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Key,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  Shield,
  Clock,
  Copy,
  Check,
  Loader2,
  AlertTriangle,
  Lock,
} from 'lucide-react';
import { toast } from 'sonner';

type SecretType = 'string' | 'password' | 'json' | 'api_key';
type SecretEnv = 'dev' | 'staging' | 'prod' | 'all';

interface Secret {
  id: string;
  name: string;
  type: SecretType;
  environment: SecretEnv;
  lastUsed?: string;
  createdAt: string;
  maskedValue: string;
}

interface SecretManagerProps {
  onSecretSelect?: (secretName: string) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function SecretManager({ onSecretSelect }: SecretManagerProps) {
  const [secrets, setSecrets] = useState<Secret[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSecret, setNewSecret] = useState<{ name: string; value: string; type: SecretType; environment: SecretEnv }>({ name: '', value: '', type: 'string', environment: 'all' });
  const [visibleSecrets, setVisibleSecrets] = useState<Set<string>>(new Set());
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // 시크릿 목록 로드
  useEffect(() => {
    loadSecrets();
  }, []);

  const loadSecrets = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/secrets`, {
        headers: { ...(token && { Authorization: `Bearer ${token}` }) },
      });
      const data = await response.json();
      setSecrets(data.secrets || []);
    } catch (error) {
      // 데모 데이터
      setSecrets([
        { id: '1', name: 'API_KEY', type: 'api_key', environment: 'all', maskedValue: '****abc123', createdAt: new Date().toISOString() },
        { id: '2', name: 'DB_PASSWORD', type: 'password', environment: 'prod', maskedValue: '********', createdAt: new Date().toISOString() },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // 시크릿 추가
  const addSecret = async () => {
    if (!newSecret.name.trim() || !newSecret.value.trim()) {
      toast.error('이름과 값을 입력해주세요.');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_BASE}/api/workflow/secrets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify(newSecret),
      });

      const maskedValue = newSecret.type === 'password' ? '********' : `****${newSecret.value.slice(-4)}`;
      setSecrets(prev => [...prev, {
        id: `${Date.now()}`,
        name: newSecret.name,
        type: newSecret.type,
        environment: newSecret.environment,
        maskedValue,
        createdAt: new Date().toISOString(),
      }]);

      setNewSecret({ name: '', value: '', type: 'string', environment: 'all' });
      setShowAddForm(false);
      toast.success('시크릿이 추가되었습니다.');
    } catch (error) {
      toast.error('시크릿 추가 실패');
    }
  };

  // 시크릿 삭제
  const deleteSecret = async (id: string) => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${API_BASE}/api/workflow/secrets/${id}`, {
        method: 'DELETE',
        headers: { ...(token && { Authorization: `Bearer ${token}` }) },
      });
      setSecrets(prev => prev.filter(s => s.id !== id));
      toast.success('시크릿이 삭제되었습니다.');
    } catch (error) {
      setSecrets(prev => prev.filter(s => s.id !== id));
      toast.success('시크릿이 삭제되었습니다.');
    }
  };

  // 시크릿 복사 (사용법)
  const copyUsage = (name: string) => {
    const usage = `secrets.get("${name}")`;
    navigator.clipboard.writeText(usage);
    setCopiedId(name);
    setTimeout(() => setCopiedId(null), 2000);
    toast.success('사용법이 복사되었습니다.');
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'api_key': return <Key className="h-4 w-4 text-yellow-500" />;
      case 'password': return <Lock className="h-4 w-4 text-red-500" />;
      default: return <Shield className="h-4 w-4 text-blue-500" />;
    }
  };

  const getEnvBadge = (env: string) => {
    const colors: Record<string, string> = {
      dev: 'bg-green-100 text-green-800',
      staging: 'bg-yellow-100 text-yellow-800',
      prod: 'bg-red-100 text-red-800',
      all: 'bg-blue-100 text-blue-800',
    };
    return <Badge className={`text-xs ${colors[env] || colors.all}`}>{env}</Badge>;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-red-50 to-pink-50 dark:from-red-950/30 dark:to-pink-950/30 rounded-lg border border-red-200 dark:border-red-800">
        <Key className="h-5 w-5 text-red-600" />
        <span className="font-medium flex-1">Secrets Manager</span>
        <Badge variant="secondary" className="text-xs">Phase 4</Badge>
      </div>

      {/* Security Notice */}
      <div className="flex items-start gap-2 p-2 bg-yellow-50 dark:bg-yellow-950/30 rounded-lg text-xs">
        <Shield className="h-4 w-4 text-yellow-600 mt-0.5" />
        <p className="text-yellow-700 dark:text-yellow-300">
          시크릿은 암호화되어 저장되며, 코드에서 안전하게 접근할 수 있습니다.
        </p>
      </div>

      {/* Add Button */}
      <Button
        onClick={() => setShowAddForm(!showAddForm)}
        variant="outline"
        size="sm"
        className="w-full gap-2"
      >
        <Plus className="h-4 w-4" />
        시크릿 추가
      </Button>

      {/* Add Form */}
      {showAddForm && (
        <div className="p-3 border rounded-lg space-y-3 bg-muted/50">
          <div className="grid grid-cols-2 gap-2">
            <div>
              <Label className="text-xs">이름</Label>
              <Input
                value={newSecret.name}
                onChange={(e) => setNewSecret(prev => ({ ...prev, name: e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, '_') }))}
                placeholder="API_KEY"
                className="h-8 text-sm font-mono"
              />
            </div>
            <div>
              <Label className="text-xs">타입</Label>
              <Select value={newSecret.type} onValueChange={(v: any) => setNewSecret(prev => ({ ...prev, type: v }))}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="string">String</SelectItem>
                  <SelectItem value="password">Password</SelectItem>
                  <SelectItem value="api_key">API Key</SelectItem>
                  <SelectItem value="json">JSON</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div>
            <Label className="text-xs">값</Label>
            <Input
              type={newSecret.type === 'password' ? 'password' : 'text'}
              value={newSecret.value}
              onChange={(e) => setNewSecret(prev => ({ ...prev, value: e.target.value }))}
              placeholder="시크릿 값 입력"
              className="h-8 text-sm font-mono"
            />
          </div>
          <div>
            <Label className="text-xs">환경</Label>
            <Select value={newSecret.environment} onValueChange={(v: any) => setNewSecret(prev => ({ ...prev, environment: v }))}>
              <SelectTrigger className="h-8 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="dev">Development</SelectItem>
                <SelectItem value="staging">Staging</SelectItem>
                <SelectItem value="prod">Production</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={addSecret} className="flex-1">저장</Button>
            <Button size="sm" variant="ghost" onClick={() => setShowAddForm(false)}>취소</Button>
          </div>
        </div>
      )}

      {/* Secrets List */}
      <ScrollArea className="h-48">
        <div className="space-y-2">
          {secrets.map((secret) => (
            <div
              key={secret.id}
              className="flex items-center gap-2 p-2 border rounded-lg hover:bg-muted/50"
            >
              {getTypeIcon(secret.type)}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-mono font-medium">{secret.name}</span>
                  {getEnvBadge(secret.environment)}
                </div>
                <p className="text-xs text-muted-foreground font-mono">{secret.maskedValue}</p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0"
                onClick={() => copyUsage(secret.name)}
              >
                {copiedId === secret.name ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0 text-red-500"
                onClick={() => deleteSecret(secret.id)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}
          {secrets.length === 0 && !isLoading && (
            <p className="text-sm text-muted-foreground text-center py-4">
              등록된 시크릿이 없습니다.
            </p>
          )}
        </div>
      </ScrollArea>

      {/* Usage Info */}
      <div className="p-2 bg-muted rounded-lg text-xs">
        <p className="font-medium mb-1">코드에서 사용:</p>
        <code className="bg-black/10 dark:bg-white/10 px-1 rounded">
          api_key = secrets.get("API_KEY")
        </code>
      </div>
    </div>
  );
}
