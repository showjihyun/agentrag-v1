'use client';

import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { ValidationResult, getValidationSummary } from '@/lib/workflow-validation';
import { cn } from '@/lib/utils';

interface ValidationPanelProps {
  validation: ValidationResult;
  onClose?: () => void;
  onNodeClick?: (nodeId: string) => void;
  className?: string;
}

export function ValidationPanel({
  validation,
  onClose,
  onNodeClick,
  className,
}: ValidationPanelProps) {
  const summary = getValidationSummary(validation);

  if (!summary.hasErrors && !summary.hasWarnings) {
    return null;
  }

  return (
    <Card className={cn('border-l-4', className, {
      'border-l-red-500': summary.hasErrors,
      'border-l-yellow-500': !summary.hasErrors && summary.hasWarnings,
    })}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {summary.hasErrors ? (
              <AlertCircle className="h-5 w-5 text-red-500" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
            )}
            <CardTitle className="text-base">
              Validation {summary.hasErrors ? 'Errors' : 'Warnings'}
            </CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {summary.errorCount > 0 && (
              <Badge variant="destructive">{summary.errorCount} errors</Badge>
            )}
            {summary.warningCount > 0 && (
              <Badge variant="outline" className="border-yellow-500 text-yellow-600">
                {summary.warningCount} warnings
              </Badge>
            )}
            {onClose && (
              <Button variant="ghost" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[200px]">
          <div className="space-y-2">
            {validation.errors.map((error, index) => (
              <div
                key={`error-${index}`}
                className={cn(
                  'flex items-start gap-2 p-2 rounded-md border border-red-200 bg-red-50 cursor-pointer hover:bg-red-100 transition-colors',
                  onNodeClick && 'cursor-pointer'
                )}
                onClick={() => error.nodeId && onNodeClick?.(error.nodeId)}
              >
                <AlertCircle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-red-900">
                    {error.nodeName}
                    {error.field && (
                      <span className="text-red-600 font-normal"> • {error.field}</span>
                    )}
                  </div>
                  <div className="text-sm text-red-700">{error.message}</div>
                </div>
              </div>
            ))}

            {validation.warnings.map((warning, index) => (
              <div
                key={`warning-${index}`}
                className={cn(
                  'flex items-start gap-2 p-2 rounded-md border border-yellow-200 bg-yellow-50 hover:bg-yellow-100 transition-colors',
                  onNodeClick && warning.nodeId && 'cursor-pointer'
                )}
                onClick={() => warning.nodeId && onNodeClick?.(warning.nodeId)}
              >
                <AlertTriangle className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-yellow-900">
                    {warning.nodeName}
                    {warning.field && (
                      <span className="text-yellow-700 font-normal"> • {warning.field}</span>
                    )}
                  </div>
                  <div className="text-sm text-yellow-700">{warning.message}</div>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

/**
 * Compact validation badge for toolbar
 */
export function ValidationBadge({ validation }: { validation: ValidationResult }) {
  const summary = getValidationSummary(validation);

  if (!summary.hasErrors && !summary.hasWarnings) {
    return (
      <Badge variant="outline" className="border-green-500 text-green-600">
        <CheckCircle className="h-3 w-3 mr-1" />
        Valid
      </Badge>
    );
  }

  return (
    <div className="flex gap-1">
      {summary.errorCount > 0 && (
        <Badge variant="destructive">
          <AlertCircle className="h-3 w-3 mr-1" />
          {summary.errorCount}
        </Badge>
      )}
      {summary.warningCount > 0 && (
        <Badge variant="outline" className="border-yellow-500 text-yellow-600">
          <AlertTriangle className="h-3 w-3 mr-1" />
          {summary.warningCount}
        </Badge>
      )}
    </div>
  );
}
