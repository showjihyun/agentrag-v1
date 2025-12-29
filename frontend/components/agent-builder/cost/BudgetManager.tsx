'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { AlertTriangle, Bell, Save, DollarSign } from 'lucide-react';

interface BudgetManagerProps {
  agentId?: string;
  currentCost: number;
  budgetLimit?: number;
  onUpdate?: () => void;
}

export function BudgetManager({
  agentId,
  currentCost,
  budgetLimit,
  onUpdate,
}: BudgetManagerProps) {
  const { toast } = useToast();
  const [budget, setBudget] = useState(budgetLimit?.toString() || '');
  const [alertThreshold, setAlertThreshold] = useState('80');
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [autoStop, setAutoStop] = useState(false);
  const [saving, setSaving] = useState(false);

  const budgetValue = parseFloat(budget) || 0;
  const usedPercentage = budgetValue > 0 ? (currentCost / budgetValue) * 100 : 0;
  const remaining = Math.max(0, budgetValue - currentCost);

  const handleSave = async () => {
    if (!agentId) {
      toast({
        title: 'Error',
        description: 'Agent ID is required',
        variant: 'destructive',
      });
      return;
    }

    setSaving(true);
    try {
      await agentBuilderAPI.updateBudgetSettings(agentId, {
        budget_limit: budgetValue,
        alert_threshold: parseFloat(alertThreshold),
        email_alerts: emailAlerts,
        auto_stop: autoStop,
      });

      toast({
        title: 'Budget Settings Saved',
        description: 'Your budget settings have been updated',
      });

      if (onUpdate) onUpdate();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to save budget settings',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  return (
    <div className="space-y-6">
      {/* Current Budget Status */}
      {budgetValue > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Budget Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Usage</span>
                <span className="text-sm font-bold">
                  {formatCurrency(currentCost)} / {formatCurrency(budgetValue)}
                </span>
              </div>
              <Progress value={usedPercentage} className="h-3" />
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-muted-foreground">
                  {usedPercentage.toFixed(1)}% used
                </span>
                <span className="text-xs text-muted-foreground">
                  {formatCurrency(remaining)} remaining
                </span>
              </div>
            </div>

            {usedPercentage >= parseFloat(alertThreshold) && (
              <div className="flex items-center gap-2 p-3 bg-yellow-50 dark:bg-yellow-950/50 border border-yellow-200 dark:border-yellow-900 rounded-md">
                <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  You've reached {usedPercentage.toFixed(0)}% of your budget limit
                </p>
              </div>
            )}

            {usedPercentage >= 100 && (
              <div className="flex items-center gap-2 p-3 bg-red-50 dark:bg-red-950/50 border border-red-200 dark:border-red-900 rounded-md">
                <AlertTriangle className="h-4 w-4 text-red-600 dark:text-red-400" />
                <p className="text-sm text-red-800 dark:text-red-200">
                  Budget limit exceeded!
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Budget Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Budget Settings</CardTitle>
          <CardDescription>Set spending limits and alerts</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="budget">Monthly Budget Limit</Label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                id="budget"
                type="number"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="0.00"
                className="pl-9"
                step="0.01"
                min="0"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Set a monthly spending limit for AI costs
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="threshold">Alert Threshold (%)</Label>
            <Input
              id="threshold"
              type="number"
              value={alertThreshold}
              onChange={(e) => setAlertThreshold(e.target.value)}
              placeholder="80"
              min="0"
              max="100"
            />
            <p className="text-xs text-muted-foreground">
              Get notified when you reach this percentage of your budget
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="flex items-center gap-2">
                <Bell className="h-4 w-4" />
                Email Alerts
              </Label>
              <p className="text-xs text-muted-foreground">
                Receive email notifications when threshold is reached
              </p>
            </div>
            <Switch checked={emailAlerts} onCheckedChange={setEmailAlerts} />
          </div>

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Auto-Stop at Limit
              </Label>
              <p className="text-xs text-muted-foreground">
                Automatically stop executions when budget is exceeded
              </p>
            </div>
            <Switch checked={autoStop} onCheckedChange={setAutoStop} />
          </div>

          <Button onClick={handleSave} disabled={saving} className="w-full">
            <Save className="mr-2 h-4 w-4" />
            {saving ? 'Saving...' : 'Save Budget Settings'}
          </Button>
        </CardContent>
      </Card>

      {/* Budget Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recommendations</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start gap-2">
              <Badge variant="outline" className="mt-0.5">
                Tip
              </Badge>
              <p className="text-sm">
                Based on your current usage, we recommend a monthly budget of{' '}
                <strong>{formatCurrency(currentCost * 1.2)}</strong> to account for growth
              </p>
            </div>
            <div className="flex items-start gap-2">
              <Badge variant="outline" className="mt-0.5">
                Tip
              </Badge>
              <p className="text-sm">
                Enable auto-stop to prevent unexpected costs when testing new agents
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
