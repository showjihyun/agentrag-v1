"use client";

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { WebhookConfig } from './WebhookConfig';
import { ScheduleConfig } from './ScheduleConfig';
import { APIKeyConfig } from './APIKeyConfig';
import { ChatConfig } from './ChatConfig';

interface TriggerConfigPanelProps {
  workflowId: string;
  onTriggerCreated?: (trigger: any) => void;
}

export function TriggerConfigPanel({ workflowId, onTriggerCreated }: TriggerConfigPanelProps) {
  const [activeTab, setActiveTab] = useState<string>('webhook');

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Workflow Triggers</CardTitle>
        <CardDescription>
          Configure how this workflow can be triggered
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="webhook">Webhook</TabsTrigger>
            <TabsTrigger value="schedule">Schedule</TabsTrigger>
            <TabsTrigger value="api">API</TabsTrigger>
            <TabsTrigger value="chat">Chat</TabsTrigger>
          </TabsList>

          <TabsContent value="webhook" className="mt-4">
            <WebhookConfig
              workflowId={workflowId}
              onTriggerCreated={onTriggerCreated}
            />
          </TabsContent>

          <TabsContent value="schedule" className="mt-4">
            <ScheduleConfig
              workflowId={workflowId}
              onTriggerCreated={onTriggerCreated}
            />
          </TabsContent>

          <TabsContent value="api" className="mt-4">
            <APIKeyConfig
              workflowId={workflowId}
              onTriggerCreated={onTriggerCreated}
            />
          </TabsContent>

          <TabsContent value="chat" className="mt-4">
            <ChatConfig
              workflowId={workflowId}
              onTriggerCreated={onTriggerCreated}
            />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
