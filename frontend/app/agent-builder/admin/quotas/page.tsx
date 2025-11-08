"use client";

import React, { useState, useEffect } from "react";
import { Users, Activity, Zap, Database, TrendingUp, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface QuotaUsage {
  tier: string;
  limits: {
    executions_per_day: number;
    executions_per_month: number;
    tokens_per_day: number;
    tokens_per_month: number;
    max_agents: number;
    max_workflows: number;
    max_knowledgebases: number;
    max_concurrent_executions: number;
  };
  usage: {
    executions: {
      daily: { used: number; limit: number; remaining: number };
      monthly: { used: number; limit: number; remaining: number };
    };
    tokens: {
      daily: { used: number; limit: number; remaining: number };
      monthly: { used: number; limit: number; remaining: number };
    };
    resources: {
      agents: { used: number; limit: number };
      workflows: { used: number; limit: number };
      knowledgebases: { used: number; limit: number };
    };
    concurrent_executions: { running: number; limit: number };
  };
}

export default function AdminQuotasPage() {
  const [quotaUsage, setQuotaUsage] = useState<QuotaUsage | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQuotaUsage();
  }, []);

  const loadQuotaUsage = async () => {
    try {
      setLoading(true);
      // Fetch quota usage from API
      const response = await fetch("/api/agent-builder/quota/usage", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });
      const data = await response.json();
      setQuotaUsage(data);
    } catch (error) {
      console.error("Failed to load quota usage:", error);
    } finally {
      setLoading(false);
    }
  };

  const calculatePercentage = (used: number, limit: number): number => {
    if (limit <= 0) return 0;
    return Math.min(100, (used / limit) * 100);
  };

  const getUsageColor = (percentage: number): string => {
    if (percentage >= 90) return "text-red-500";
    if (percentage >= 75) return "text-yellow-500";
    return "text-green-500";
  };

  const getTierBadgeVariant = (tier: string) => {
    switch (tier) {
      case "free":
        return "secondary";
      case "basic":
        return "default";
      case "premium":
        return "default";
      case "enterprise":
        return "default";
      default:
        return "secondary";
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (!quotaUsage) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load quota information</AlertDescription>
        </Alert>
      </div>
    );
  }

  const { tier, limits, usage } = quotaUsage;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Quota Dashboard</h1>
          <p className="text-muted-foreground">Monitor resource usage and limits</p>
        </div>
        <Badge variant={getTierBadgeVariant(tier)} className="text-lg px-4 py-2">
          {tier.toUpperCase()} Tier
        </Badge>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Daily Executions</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usage.executions.daily.used}</div>
            <p className="text-xs text-muted-foreground">
              of {limits.executions_per_day > 0 ? limits.executions_per_day : "unlimited"}
            </p>
            {limits.executions_per_day > 0 && (
              <Progress
                value={calculatePercentage(usage.executions.daily.used, limits.executions_per_day)}
                className="mt-2"
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Daily Tokens</CardTitle>
            <Zap className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(usage.tokens.daily.used / 1000).toFixed(1)}K
            </div>
            <p className="text-xs text-muted-foreground">
              of {limits.tokens_per_day > 0 ? `${(limits.tokens_per_day / 1000).toFixed(0)}K` : "unlimited"}
            </p>
            {limits.tokens_per_day > 0 && (
              <Progress
                value={calculatePercentage(usage.tokens.daily.used, limits.tokens_per_day)}
                className="mt-2"
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usage.resources.agents.used}</div>
            <p className="text-xs text-muted-foreground">
              of {limits.max_agents > 0 ? limits.max_agents : "unlimited"}
            </p>
            {limits.max_agents > 0 && (
              <Progress
                value={calculatePercentage(usage.resources.agents.used, limits.max_agents)}
                className="mt-2"
              />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Running Executions</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usage.concurrent_executions.running}</div>
            <p className="text-xs text-muted-foreground">
              of {limits.max_concurrent_executions} concurrent
            </p>
            <Progress
              value={calculatePercentage(
                usage.concurrent_executions.running,
                limits.max_concurrent_executions
              )}
              className="mt-2"
            />
          </CardContent>
        </Card>
      </div>

      {/* Detailed Usage */}
      <Tabs defaultValue="executions" className="space-y-4">
        <TabsList>
          <TabsTrigger value="executions">Executions</TabsTrigger>
          <TabsTrigger value="tokens">Tokens</TabsTrigger>
          <TabsTrigger value="resources">Resources</TabsTrigger>
        </TabsList>

        <TabsContent value="executions" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Daily Executions</CardTitle>
                <CardDescription>Resets every 24 hours</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Used</span>
                  <span className="text-2xl font-bold">{usage.executions.daily.used}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Limit</span>
                  <span className="text-lg">
                    {limits.executions_per_day > 0 ? limits.executions_per_day : "Unlimited"}
                  </span>
                </div>
                {limits.executions_per_day > 0 && (
                  <>
                    <Progress
                      value={calculatePercentage(
                        usage.executions.daily.used,
                        limits.executions_per_day
                      )}
                    />
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Remaining</span>
                      <span className={getUsageColor(
                        calculatePercentage(usage.executions.daily.used, limits.executions_per_day)
                      )}>
                        {usage.executions.daily.remaining}
                      </span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Monthly Executions</CardTitle>
                <CardDescription>Resets every month</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Used</span>
                  <span className="text-2xl font-bold">{usage.executions.monthly.used}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Limit</span>
                  <span className="text-lg">
                    {limits.executions_per_month > 0 ? limits.executions_per_month : "Unlimited"}
                  </span>
                </div>
                {limits.executions_per_month > 0 && (
                  <>
                    <Progress
                      value={calculatePercentage(
                        usage.executions.monthly.used,
                        limits.executions_per_month
                      )}
                    />
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Remaining</span>
                      <span className={getUsageColor(
                        calculatePercentage(usage.executions.monthly.used, limits.executions_per_month)
                      )}>
                        {usage.executions.monthly.remaining}
                      </span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="tokens" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Daily Token Usage</CardTitle>
                <CardDescription>Resets every 24 hours</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Used</span>
                  <span className="text-2xl font-bold">
                    {(usage.tokens.daily.used / 1000).toFixed(1)}K
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Limit</span>
                  <span className="text-lg">
                    {limits.tokens_per_day > 0
                      ? `${(limits.tokens_per_day / 1000).toFixed(0)}K`
                      : "Unlimited"}
                  </span>
                </div>
                {limits.tokens_per_day > 0 && (
                  <>
                    <Progress
                      value={calculatePercentage(usage.tokens.daily.used, limits.tokens_per_day)}
                    />
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Remaining</span>
                      <span className={getUsageColor(
                        calculatePercentage(usage.tokens.daily.used, limits.tokens_per_day)
                      )}>
                        {(usage.tokens.daily.remaining / 1000).toFixed(1)}K
                      </span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Monthly Token Usage</CardTitle>
                <CardDescription>Resets every month</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Used</span>
                  <span className="text-2xl font-bold">
                    {(usage.tokens.monthly.used / 1000).toFixed(1)}K
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Limit</span>
                  <span className="text-lg">
                    {limits.tokens_per_month > 0
                      ? `${(limits.tokens_per_month / 1000).toFixed(0)}K`
                      : "Unlimited"}
                  </span>
                </div>
                {limits.tokens_per_month > 0 && (
                  <>
                    <Progress
                      value={calculatePercentage(usage.tokens.monthly.used, limits.tokens_per_month)}
                    />
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Remaining</span>
                      <span className={getUsageColor(
                        calculatePercentage(usage.tokens.monthly.used, limits.tokens_per_month)
                      )}>
                        {(usage.tokens.monthly.remaining / 1000).toFixed(1)}K
                      </span>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Agents</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Created</span>
                  <span className="text-2xl font-bold">{usage.resources.agents.used}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Limit</span>
                  <span className="text-lg">
                    {limits.max_agents > 0 ? limits.max_agents : "Unlimited"}
                  </span>
                </div>
                {limits.max_agents > 0 && (
                  <Progress
                    value={calculatePercentage(usage.resources.agents.used, limits.max_agents)}
                  />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Workflows</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Created</span>
                  <span className="text-2xl font-bold">{usage.resources.workflows.used}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Limit</span>
                  <span className="text-lg">
                    {limits.max_workflows > 0 ? limits.max_workflows : "Unlimited"}
                  </span>
                </div>
                {limits.max_workflows > 0 && (
                  <Progress
                    value={calculatePercentage(usage.resources.workflows.used, limits.max_workflows)}
                  />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Knowledgebases</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Created</span>
                  <span className="text-2xl font-bold">{usage.resources.knowledgebases.used}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Limit</span>
                  <span className="text-lg">
                    {limits.max_knowledgebases > 0 ? limits.max_knowledgebases : "Unlimited"}
                  </span>
                </div>
                {limits.max_knowledgebases > 0 && (
                  <Progress
                    value={calculatePercentage(
                      usage.resources.knowledgebases.used,
                      limits.max_knowledgebases
                    )}
                  />
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
