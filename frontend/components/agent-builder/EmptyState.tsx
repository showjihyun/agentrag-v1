'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

interface EmptyStateProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
    icon?: LucideIcon;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  links?: Array<{
    label: string;
    href: string;
  }>;
  illustration?: React.ReactNode;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  links,
  illustration,
}: EmptyStateProps) {
  return (
    <Card className="border-dashed">
      <CardContent className="flex flex-col items-center justify-center py-12 px-6 text-center">
        {illustration ? (
          <div className="mb-6">{illustration}</div>
        ) : (
          <div className="mb-6 text-muted-foreground opacity-50">
            {icon}
          </div>
        )}
        
        <h3 className="text-lg font-semibold mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground mb-6 max-w-md">
          {description}
        </p>

        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          {action && (
            <Button onClick={action.onClick} size="lg">
              {action.icon && <action.icon className="mr-2 h-4 w-4" />}
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              variant="outline"
              onClick={secondaryAction.onClick}
              size="lg"
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>

        {links && links.length > 0 && (
          <div className="flex flex-wrap gap-4 justify-center text-sm">
            {links.map((link, index) => (
              <a
                key={index}
                href={link.href}
                className="text-primary hover:underline"
                target="_blank"
                rel="noopener noreferrer"
              >
                {link.label}
              </a>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
