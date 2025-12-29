"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Play, 
  Pause, 
  Square, 
  Settings, 
  Users, 
  Clock, 
  DollarSign,
  Activity,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus,
  Trash2,
  Eye,
  BarChart3,
  Network,
  Zap
} from 'lucide-react';
import { toast } from 'sonner';

interface Task {
  task_id: string;
  task_type: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  requirements: Record<string, any>;
  input_data: Record<string, any>;
  deadline?: string;
  estimated_duration?: number;
}