/**
 * Collaboration Panel Component
 * 
 * 협업 중인 사용자들을 표시하는 패널
 */
import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Users, Wifi, WifiOff } from 'lucide-react';
import { CollaborativeUser } from '@/hooks/useCollaboration';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface CollaborationPanelProps {
  users: CollaborativeUser[];
  isConnected: boolean;
  onClose: () => void;
}

export const CollaborationPanel: React.FC<CollaborationPanelProps> = ({
  users,
  isConnected,
  onClose
}) => {
  const onlineUsers = users.filter(user => user.isOnline);
  const offlineUsers = users.filter(user => !user.isOnline);

  const formatLastSeen = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    
    if (diffMins < 1) return '방금 전';
    if (diffMins < 60) return `${diffMins}분 전`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}시간 전`;
    
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}일 전`;
  };

  const getUserInitials = (name: string) => {
    return name
      .split(' ')
      .map(word => word[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <motion.div
      initial={{ x: 300, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 300, opacity: 0 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="absolute top-4 right-4 z-40"
    >
      <Card className="w-80 shadow-lg">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              <CardTitle className="text-sm">협업 중</CardTitle>
            </div>
            
            <div className="flex items-center gap-2">
              {/* 연결 상태 */}
              <div className="flex items-center gap-1">
                {isConnected ? (
                  <Wifi className="w-4 h-4 text-green-500" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500" />
                )}
                <span className={`text-xs ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
                  {isConnected ? '연결됨' : '연결 끊김'}
                </span>
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="h-6 w-6 p-0"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* 온라인 사용자 */}
          {onlineUsers.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-2">
                온라인 ({onlineUsers.length})
              </h4>
              <div className="space-y-2">
                <AnimatePresence>
                  {onlineUsers.map(user => (
                    <motion.div
                      key={user.id}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50"
                    >
                      <div className="relative">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={user.avatar} alt={user.name} />
                          <AvatarFallback 
                            className="text-xs text-white"
                            style={{ backgroundColor: user.color }}
                          >
                            {getUserInitials(user.name)}
                          </AvatarFallback>
                        </Avatar>
                        
                        {/* 온라인 상태 표시 */}
                        <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 border-2 border-white rounded-full" />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {user.name}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {user.email}
                        </p>
                      </div>
                      
                      <Badge 
                        variant="secondary" 
                        className="text-xs"
                        style={{ 
                          backgroundColor: `${user.color}20`,
                          color: user.color,
                          borderColor: user.color
                        }}
                      >
                        활성
                      </Badge>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          )}

          {/* 오프라인 사용자 */}
          {offlineUsers.length > 0 && (
            <div>
              <h4 className="text-xs font-medium text-gray-700 mb-2">
                최근 참여 ({offlineUsers.length})
              </h4>
              <div className="space-y-2">
                {offlineUsers.slice(0, 5).map(user => (
                  <div
                    key={user.id}
                    className="flex items-center gap-3 p-2 rounded-lg opacity-60"
                  >
                    <div className="relative">
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={user.avatar} alt={user.name} />
                        <AvatarFallback 
                          className="text-xs text-white"
                          style={{ backgroundColor: user.color }}
                        >
                          {getUserInitials(user.name)}
                        </AvatarFallback>
                      </Avatar>
                      
                      {/* 오프라인 상태 표시 */}
                      <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-gray-400 border-2 border-white rounded-full" />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-700 truncate">
                        {user.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatLastSeen(user.lastSeen)}
                      </p>
                    </div>
                  </div>
                ))}
                
                {offlineUsers.length > 5 && (
                  <p className="text-xs text-gray-500 text-center py-1">
                    +{offlineUsers.length - 5}명 더
                  </p>
                )}
              </div>
            </div>
          )}

          {/* 사용자가 없는 경우 */}
          {users.length === 0 && (
            <div className="text-center py-4">
              <Users className="w-8 h-8 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">
                아직 협업 중인 사용자가 없습니다
              </p>
            </div>
          )}

          {/* 협업 팁 */}
          {onlineUsers.length > 1 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <h5 className="text-xs font-medium text-blue-800 mb-1">
                💡 협업 팁
              </h5>
              <p className="text-xs text-blue-700">
                다른 사용자가 편집 중인 블록은 색상으로 표시됩니다. 
                동시 편집을 피해 충돌을 방지하세요.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};