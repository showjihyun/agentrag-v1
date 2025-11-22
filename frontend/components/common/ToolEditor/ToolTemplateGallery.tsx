"use client";

/**
 * Tool Template Gallery - 템플릿 선택 컴포넌트
 */

import React from "react";
import { Sparkles, Copy, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ToolTemplateGalleryProps } from "./types";

export function ToolTemplateGallery({ tool, onSelectTemplate }: ToolTemplateGalleryProps) {
  if (!tool.examples || tool.examples.length === 0) {
    return (
      <div className="text-center py-12">
        <Sparkles className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <p className="text-sm text-muted-foreground">
          No templates available for this tool
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold">Template Gallery</h3>
        <Badge variant="secondary">{tool.examples.length} templates</Badge>
      </div>

      <p className="text-sm text-muted-foreground">
        Start with a pre-configured template and customize it to your needs
      </p>

      <div className="grid gap-4 md:grid-cols-2">
        {tool.examples.map((example, index) => (
          <Card
            key={index}
            className="cursor-pointer transition-all hover:shadow-lg hover:border-primary"
            onClick={() => onSelectTemplate(example.config)}
          >
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                {example.name}
                <Badge variant="outline" className="text-xs">
                  Template
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs">
                {example.description}
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <div className="space-y-3">
                {/* Configuration Preview */}
                <div className="space-y-1">
                  <p className="text-xs font-medium text-muted-foreground">
                    Configured Parameters:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(example.config).slice(0, 5).map((key) => (
                      <Badge key={key} variant="secondary" className="text-xs">
                        {key}
                      </Badge>
                    ))}
                    {Object.keys(example.config).length > 5 && (
                      <Badge variant="secondary" className="text-xs">
                        +{Object.keys(example.config).length - 5} more
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-2">
                  <Button
                    size="sm"
                    className="flex-1 gap-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectTemplate(example.config);
                    }}
                  >
                    <Copy className="h-3 w-3" />
                    Use Template
                  </Button>
                  
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={(e) => {
                      e.stopPropagation();
                      console.log('Template config:', example.config);
                    }}
                  >
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Custom Template Hint */}
      <Card className="border-dashed">
        <CardContent className="pt-6">
          <div className="text-center space-y-2">
            <p className="text-sm font-medium">Need a custom template?</p>
            <p className="text-xs text-muted-foreground">
              Configure your tool and save it as a template for future use
            </p>
            <Button size="sm" variant="outline" className="gap-2">
              <Sparkles className="h-3 w-3" />
              Create Custom Template
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
