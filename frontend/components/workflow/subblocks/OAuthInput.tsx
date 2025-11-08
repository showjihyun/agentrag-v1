'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, ExternalLink } from 'lucide-react';

export interface OAuthInputProps {
  id: string;
  title: string;
  provider: string;
  isConnected?: boolean;
  accountInfo?: string;
  required?: boolean;
  disabled?: boolean;
  onConnect?: () => void;
  onDisconnect?: () => void;
  error?: string;
}

export function OAuthInput({
  id,
  title,
  provider,
  isConnected = false,
  accountInfo,
  required,
  disabled,
  onConnect,
  onDisconnect,
  error,
}: OAuthInputProps) {
  const [connecting, setConnecting] = useState(false);

  const handleConnect = async () => {
    setConnecting(true);
    try {
      await onConnect?.();
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {title}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      
      <div className="border rounded-lg p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-medium text-sm">{provider}</span>
            {isConnected ? (
              <Badge variant="default" className="gap-1">
                <CheckCircle className="h-3 w-3" />
                Connected
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1">
                <XCircle className="h-3 w-3" />
                Not Connected
              </Badge>
            )}
          </div>
        </div>

        {isConnected && accountInfo && (
          <p className="text-sm text-muted-foreground">{accountInfo}</p>
        )}

        <div className="flex gap-2">
          {!isConnected ? (
            <Button
              size="sm"
              onClick={handleConnect}
              disabled={disabled || connecting}
              className="gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              {connecting ? 'Connecting...' : `Connect ${provider}`}
            </Button>
          ) : (
            <Button
              size="sm"
              variant="outline"
              onClick={onDisconnect}
              disabled={disabled}
            >
              Disconnect
            </Button>
          )}
        </div>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
