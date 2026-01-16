'use client';

import React from 'react';
import { TemplateMarketplace } from '@/components/agent-builder/TemplateMarketplace';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Store,
  TrendingUp,
  Users,
  Star,
  Download,
  Plus,
  Sparkles,
} from 'lucide-react';

export default function MarketplacePage() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-lg bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 text-white">
        <div className="absolute inset-0 bg-black/20" />
        <div className="relative px-6 py-12 sm:px-12 sm:py-16">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 mb-4">
              <Store className="w-8 h-8" />
              <Badge className="bg-white/20 text-white border-white/30">
                <Sparkles className="w-3 h-3 mr-1" />
                Enhanced
              </Badge>
            </div>
            <h1 className="text-4xl font-bold mb-4">
              Template Marketplace
            </h1>
            <p className="text-xl text-white/90 mb-6">
              Discover and deploy verified agent team configurations instantly. 
              Get started quickly with workflow templates created by experts.
            </p>
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                <span>1,000+ Active Users</span>
              </div>
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                <span>10,000+ Downloads</span>
              </div>
              <div className="flex items-center gap-2">
                <Star className="w-4 h-4" />
                <span>4.8 Avg Rating</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Templates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">156</div>
            <div className="flex items-center gap-1 text-xs text-green-600">
              <TrendingUp className="w-3 h-3" />
              <span>+12 this week</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Popular Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">Customer Service</div>
            <div className="text-xs text-muted-foreground">
              32 templates
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Trending This Week
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">AI Research Team</div>
            <div className="text-xs text-muted-foreground">
              245 downloads
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Average Rating
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold flex items-center gap-1">
              4.8
              <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
            </div>
            <div className="text-xs text-muted-foreground">
              2,847 reviews
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Featured Templates Banner */}
      <Card className="border-2 border-yellow-200 bg-gradient-to-r from-yellow-50 to-orange-50">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-yellow-600" />
                Featured Templates This Week
              </CardTitle>
              <CardDescription>
                Check out high-quality templates curated by experts
              </CardDescription>
            </div>
            <Badge className="bg-yellow-500 text-white">
              Featured
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-white rounded-lg border">
              <h4 className="font-medium mb-2">🎧 Customer Service Automation</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Fully automated from inquiry classification to response generation
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 text-sm">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span>4.9</span>
                </div>
                <Button size="sm" variant="outline">
                  Use Template
                </Button>
              </div>
            </div>

            <div className="p-4 bg-white rounded-lg border">
              <h4 className="font-medium mb-2">📊 Data Analysis Team</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Automate data collection, analysis, and report generation
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 text-sm">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span>4.8</span>
                </div>
                <Button size="sm" variant="outline">
                  Use Template
                </Button>
              </div>
            </div>

            <div className="p-4 bg-white rounded-lg border">
              <h4 className="font-medium mb-2">✍️ Content Creation Workflow</h4>
              <p className="text-sm text-muted-foreground mb-3">
                From idea to final content in one seamless flow
              </p>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1 text-sm">
                  <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  <span>4.7</span>
                </div>
                <Button size="sm" variant="outline">
                  Use Template
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Marketplace */}
      <TemplateMarketplace
        onTemplateSelect={(template) => {
          console.log('Selected template:', template);
        }}
        showCreateButton={true}
      />

      {/* Community Section */}
      <Card>
        <CardHeader>
          <CardTitle>Contribute to the Community</CardTitle>
          <CardDescription>
            Share your templates and grow together with other users
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h3 className="font-semibold">Become a Template Creator</h3>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>• Share verified workflows as templates</li>
                <li>• Improve through community feedback</li>
                <li>• Earn rewards based on usage</li>
                <li>• Opportunity to earn expert verification badge</li>
              </ul>
              <Button className="w-full">
                <Plus className="w-4 h-4 mr-2" />
                Create Template
              </Button>
            </div>

            <div className="space-y-4">
              <h3 className="font-semibold">Community Statistics</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">1,247</div>
                  <div className="text-xs text-muted-foreground">Active Creators</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">15.2K</div>
                  <div className="text-xs text-muted-foreground">Total Downloads</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">4.8</div>
                  <div className="text-xs text-muted-foreground">Avg Rating</div>
                </div>
                <div className="text-center p-3 bg-muted rounded-lg">
                  <div className="text-2xl font-bold">98%</div>
                  <div className="text-xs text-muted-foreground">Satisfaction</div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}