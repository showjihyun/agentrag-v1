'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

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
  variant?: 'default' | 'gradient' | 'minimal';
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  links,
  illustration,
  variant = 'gradient',
}: EmptyStateProps) {
  const [isHovered, setIsHovered] = React.useState(false);

  return (
    <Card 
      className={cn(
        "border-dashed transition-all duration-300",
        variant === 'gradient' && "hover:border-solid hover:shadow-lg"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardContent className="flex flex-col items-center justify-center py-16 px-6 text-center">
        {/* Animated Icon Container */}
        <div className="relative mb-8">
          {/* Background gradient blur */}
          {variant === 'gradient' && (
            <div 
              className={cn(
                "absolute inset-0 bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900/20 dark:to-blue-900/20 rounded-full blur-3xl transition-all duration-500",
                isHovered ? "scale-150 opacity-100" : "scale-100 opacity-60"
              )}
            />
          )}
          
          {/* Icon */}
          {illustration ? (
            <div className={cn(
              "relative transition-transform duration-300",
              isHovered && "scale-110"
            )}>
              {illustration}
            </div>
          ) : (
            <div 
              className={cn(
                "relative p-8 bg-white dark:bg-gray-900 rounded-full shadow-lg transition-all duration-300",
                isHovered && "scale-110 shadow-xl"
              )}
            >
              <div className="text-purple-500 dark:text-purple-400">
                {icon}
              </div>
            </div>
          )}
        </div>
        
        {/* Title with gradient */}
        <h3 className={cn(
          "text-2xl font-bold mb-3 transition-all duration-300",
          variant === 'gradient' && "bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent"
        )}>
          {title}
        </h3>
        
        {/* Description */}
        <p className="text-base text-muted-foreground mb-8 max-w-md leading-relaxed">
          {description}
        </p>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          {action && (
            <Button 
              onClick={action.onClick} 
              size="lg"
              className={cn(
                variant === 'gradient' && "bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-md hover:shadow-lg transition-all"
              )}
            >
              {action.icon && <action.icon className="mr-2 h-5 w-5" />}
              {action.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              variant="outline"
              onClick={secondaryAction.onClick}
              size="lg"
              className="hover:bg-purple-50 dark:hover:bg-purple-950/20 hover:border-purple-300 dark:hover:border-purple-700 transition-all"
            >
              {secondaryAction.label}
            </Button>
          )}
        </div>

        {/* Help Links */}
        {links && links.length > 0 && (
          <div className="flex flex-wrap gap-6 justify-center text-sm">
            {links.map((link, index) => (
              <a
                key={index}
                href={link.href}
                className="text-muted-foreground hover:text-purple-600 dark:hover:text-purple-400 transition-colors flex items-center gap-1"
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
