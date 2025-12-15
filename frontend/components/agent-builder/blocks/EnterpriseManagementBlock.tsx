'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { 
  Building2, 
  Shield, 
  Users, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Settings, 
  TrendingUp,
  Lock,
  Key,
  Database,
  Cloud,
  Monitor,
  BarChart3,
  UserCheck,
  Globe,
  Zap,
  RefreshCw,
  Plus,
  Eye,
  Edit,
  Trash2
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

interface Tenant {
  tenant_id: string;
  name: string;
  tier: string;
  status: string;
  isolation_level: string;
  created_at: string;
  resource_usage: {
    workflows: number;
    agents: number;
    storage_gb: number;
    api_calls: number;
  };
  quota_status: {
    workflows: { current: number; limit: number; usage_percentage: number };
    agents: { current: number; limit: number; usage_percentage: number };
    storage: { current_gb: number; limit_gb: number; usage_percentage: number };
    api_calls: { current_per_minute: number; limit_per_minute: number; usage_percentage: number };
  };
}

interface SecurityPolicy {
  policy_id: string;
  name: string;
  security_level: string;
  tenant_id: string;
  created_at: string;
  policy_summary: {
    mfa_required: boolean;
    session_timeout: number;
    encryption_required: boolean;
    audit_level: string;
  };
}

interface SecurityAlert {
  alert_id: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
}

interface DashboardData {
  tenant_info: {
    tenant_id: string;
    name: string;
    tier: string;
    status: string;
    created_at: string;
  };
  resource_status: any;
  performance_summary: {
    total_metrics: number;
    avg_uptime: number;
    avg_success_rate: number;
    total_cost: number;
  };
  security_status: {
    active_alerts: number;
    critical_alerts: number;
    recent_events: number;
    failed_logins: number;
  };
}

interface EnterpriseManagementBlockProps {
  onConfigChange?: (config: any) => void;
  initialConfig?: any;
}

const EnterpriseManagementBlock: React.FC<EnterpriseManagementBlockProps> = ({
  onConfigChange,
  initialConfig = {}
}) => {
  // State
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [securityPolicies, setSecurityPolicies] = useState<SecurityPolicy[]>([]);
  const [securityAlerts, setSecurityAlerts] = useState<SecurityAlert[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<string>('');
  
  // Form states
  const [newTenantForm, setNewTenantForm] = useState({
    name: '',
    tier: 'professional',
    isolation_level: 'shared',
    admin_email: ''
  });
  
  const [newPolicyForm, setNewPolicyForm] = useState({
    name: '',
    security_level: 'medium',
    mfa_required: false,
    session_timeout: 480,
    encryption_required: true
  });

  // Status colors
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'suspended': return 'text-yellow-600 bg-yellow-100';
      case 'terminated': return 'text-red-600 bg-red-100';
      case 'provisioning': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier.toLowerCase()) {
      case 'starter': return 'text-blue-600 bg-blue-100';
      case 'professional': return 'text-purple-600 bg-purple-100';
      case 'enterprise': return 'text-gold-600 bg-gold-100';
      case 'custom': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'low': return 'text-blue-600 bg-blue-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  // API calls
  const fetchTenants = async () => {
    try {
      const response = await fetch('/api/agent-builder/enterprise/tenants');
      if (response.ok) {
        const data = await response.json();
        setTenants(data);
      }
    } catch (error) {
      console.error('Failed to fetch tenants:', error);
    }
  };

  const fetchSecurityPolicies = async () => {
    try {
      const response = await fetch('/api/agent-builder/enterprise/security/policies');
      if (response.ok) {
        const data = await response.json();
        setSecurityPolicies(data);
      }
    } catch (error) {
      console.error('Failed to fetch security policies:', error);
    }
  };

  const fetchSecurityAlerts = async () => {
    try {
      const response = await fetch('/api/agent-builder/enterprise/security/alerts');
      if (response.ok) {
        const data = await response.json();
        setSecurityAlerts(data.active_alerts || []);
      }
    } catch (error) {
      console.error('Failed to fetch security alerts:', error);
    }
  };

  const fetchDashboard = async () => {
    try {
      const response = await fetch('/api/agent-builder/enterprise/dashboard');
      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };

  const createTenant = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/agent-builder/enterprise/tenants', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newTenantForm)
      });
      
      if (response.ok) {
        await fetchTenants();
        setNewTenantForm({
          name: '',
          tier: 'professional',
          isolation_level: 'shared',
          admin_email: ''
        });
      }
    } catch (error) {
      console.error('Failed to create tenant:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const createSecurityPolicy = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/agent-builder/enterprise/security/policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newPolicyForm.name,
          security_level: newPolicyForm.security_level,
          policy_config: {
            mfa_required: newPolicyForm.mfa_required,
            session_timeout_minutes: newPolicyForm.session_timeout,
            encryption_required: newPolicyForm.encryption_required
          }
        })
      });
      
      if (response.ok) {
        await fetchSecurityPolicies();
        setNewPolicyForm({
          name: '',
          security_level: 'medium',
          mfa_required: false,
          session_timeout: 480,
          encryption_required: true
        });
      }
    } catch (error) {
      console.error('Failed to create security policy:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Effects
  useEffect(() => {
    const fetchAllData = async () => {
      setIsLoading(true);
      await Promise.all([
        fetchTenants(),
        fetchSecurityPolicies(),
        fetchSecurityAlerts(),
        fetchDashboard()
      ]);
      setIsLoading(false);
    };

    fetchAllData();

    // Set up polling
    const interval = setInterval(fetchAllData, 30000); // 30초마다 새로고침
    return () => clearInterval(interval);
  }, []);

  // Chart data
  const resourceUsageData = tenants.map(tenant => ({
    name: tenant.name,
    workflows: tenant.quota_status.workflows?.usage_percentage || 0,
    agents: tenant.quota_status.agents?.usage_percentage || 0,
    storage: tenant.quota_status.storage?.usage_percentage || 0
  }));

  const securityStatusData = [
    { name: 'Active Alerts', value: securityAlerts.length, color: '#ef4444' },
    { name: 'Resolved', value: Math.max(0, 20 - securityAlerts.length), color: '#22c55e' }
  ];

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Building2 className="h-6 w-6 text-blue-600" />
            Enterprise Management
          </h2>
          <p className="text-gray-600 mt-1">
            Multi-tenant architecture with enterprise-grade security and governance
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchTenants();
              fetchSecurityPolicies();
              fetchSecurityAlerts();
              fetchDashboard();
            }}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Dashboard Overview */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">System Uptime</p>
                  <p className="text-2xl font-bold">{dashboardData.performance_summary.avg_uptime.toFixed(1)}%</p>
                </div>
                <div className="p-2 rounded-full bg-green-100 text-green-600">
                  <Activity className="h-4 w-4" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold">{(dashboardData.performance_summary.avg_success_rate * 100).toFixed(1)}%</p>
                </div>
                <div className="p-2 rounded-full bg-blue-100 text-blue-600">
                  <CheckCircle className="h-4 w-4" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Security Alerts</p>
                  <p className="text-2xl font-bold">{dashboardData.security_status.active_alerts}</p>
                </div>
                <div className="p-2 rounded-full bg-red-100 text-red-600">
                  <AlertTriangle className="h-4 w-4" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Cost</p>
                  <p className="text-2xl font-bold">${dashboardData.performance_summary.total_cost.toFixed(0)}</p>
                </div>
                <div className="p-2 rounded-full bg-purple-100 text-purple-600">
                  <TrendingUp className="h-4 w-4" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="tenants" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="tenants">Tenants</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="monitoring">Monitoring</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* Tenants Tab */}
        <TabsContent value="tenants" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Tenant Management</h3>
            <Button onClick={() => setSelectedTenant('new')}>
              <Plus className="h-4 w-4 mr-2" />
              Create Tenant
            </Button>
          </div>

          {selectedTenant === 'new' && (
            <Card>
              <CardHeader>
                <CardTitle>Create New Tenant</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="tenant-name">Tenant Name</Label>
                    <Input
                      id="tenant-name"
                      value={newTenantForm.name}
                      onChange={(e) => setNewTenantForm(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter tenant name"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="admin-email">Admin Email</Label>
                    <Input
                      id="admin-email"
                      type="email"
                      value={newTenantForm.admin_email}
                      onChange={(e) => setNewTenantForm(prev => ({ ...prev, admin_email: e.target.value }))}
                      placeholder="admin@company.com"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="tier">Tier</Label>
                    <Select value={newTenantForm.tier} onValueChange={(value) => setNewTenantForm(prev => ({ ...prev, tier: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="starter">Starter</SelectItem>
                        <SelectItem value="professional">Professional</SelectItem>
                        <SelectItem value="enterprise">Enterprise</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="isolation">Isolation Level</Label>
                    <Select value={newTenantForm.isolation_level} onValueChange={(value) => setNewTenantForm(prev => ({ ...prev, isolation_level: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="shared">Shared</SelectItem>
                        <SelectItem value="dedicated">Dedicated</SelectItem>
                        <SelectItem value="hybrid">Hybrid</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Button onClick={createTenant} disabled={isLoading}>
                    Create Tenant
                  </Button>
                  <Button variant="outline" onClick={() => setSelectedTenant('')}>
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 gap-4">
            {tenants.map((tenant) => (
              <Card key={tenant.tenant_id}>
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h4 className="text-lg font-semibold">{tenant.name}</h4>
                        <Badge className={getTierColor(tenant.tier)}>
                          {tenant.tier}
                        </Badge>
                        <Badge className={getStatusColor(tenant.status)}>
                          {tenant.status}
                        </Badge>
                        <Badge variant="outline">
                          {tenant.isolation_level}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-gray-600">Workflows</p>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">
                              {tenant.quota_status.workflows?.current || 0}/{tenant.quota_status.workflows?.limit || 0}
                            </span>
                            <Progress value={tenant.quota_status.workflows?.usage_percentage || 0} className="h-2 flex-1" />
                          </div>
                        </div>
                        
                        <div>
                          <p className="text-sm text-gray-600">Agents</p>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">
                              {tenant.quota_status.agents?.current || 0}/{tenant.quota_status.agents?.limit || 0}
                            </span>
                            <Progress value={tenant.quota_status.agents?.usage_percentage || 0} className="h-2 flex-1" />
                          </div>
                        </div>
                        
                        <div>
                          <p className="text-sm text-gray-600">Storage</p>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">
                              {tenant.quota_status.storage?.current_gb?.toFixed(1) || 0}GB/{tenant.quota_status.storage?.limit_gb || 0}GB
                            </span>
                            <Progress value={tenant.quota_status.storage?.usage_percentage || 0} className="h-2 flex-1" />
                          </div>
                        </div>
                        
                        <div>
                          <p className="text-sm text-gray-600">API Calls/min</p>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">
                              {tenant.quota_status.api_calls?.current_per_minute || 0}/{tenant.quota_status.api_calls?.limit_per_minute || 0}
                            </span>
                            <Progress value={tenant.quota_status.api_calls?.usage_percentage || 0} className="h-2 flex-1" />
                          </div>
                        </div>
                      </div>
                      
                      <p className="text-sm text-gray-500">
                        Created: {new Date(tenant.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="outline" size="sm">
                        <Settings className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Security Policies */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Security Policies
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {securityPolicies.map((policy) => (
                    <div key={policy.policy_id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-medium">{policy.name}</h4>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className={getSeverityColor(policy.security_level)}>
                              {policy.security_level}
                            </Badge>
                            {policy.policy_summary.mfa_required && (
                              <Badge variant="outline">MFA Required</Badge>
                            )}
                            {policy.policy_summary.encryption_required && (
                              <Badge variant="outline">Encrypted</Badge>
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mt-2">
                            Session timeout: {policy.policy_summary.session_timeout} minutes
                          </p>
                        </div>
                        <Button variant="outline" size="sm">
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => setSelectedTenant('new-policy')}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create Policy
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Security Alerts */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5" />
                  Security Alerts ({securityAlerts.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {securityAlerts.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                    <p className="text-gray-600">No active security alerts</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {securityAlerts.map((alert) => (
                      <Alert key={alert.alert_id}>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                          <div className="flex items-start justify-between">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <Badge className={getSeverityColor(alert.severity)}>
                                  {alert.severity}
                                </Badge>
                                <span className="text-sm text-gray-600">
                                  {new Date(alert.created_at).toLocaleString()}
                                </span>
                              </div>
                              <p className="font-medium">{alert.title}</p>
                              <p className="text-sm text-gray-600">{alert.description}</p>
                            </div>
                          </div>
                        </AlertDescription>
                      </Alert>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Create Security Policy Form */}
          {selectedTenant === 'new-policy' && (
            <Card>
              <CardHeader>
                <CardTitle>Create Security Policy</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="policy-name">Policy Name</Label>
                    <Input
                      id="policy-name"
                      value={newPolicyForm.name}
                      onChange={(e) => setNewPolicyForm(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Enter policy name"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="security-level">Security Level</Label>
                    <Select value={newPolicyForm.security_level} onValueChange={(value) => setNewPolicyForm(prev => ({ ...prev, security_level: value }))}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="critical">Critical</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <Button onClick={createSecurityPolicy} disabled={isLoading}>
                    Create Policy
                  </Button>
                  <Button variant="outline" onClick={() => setSelectedTenant('')}>
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Monitoring Tab */}
        <TabsContent value="monitoring" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Resource Usage Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Resource Usage by Tenant
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={resourceUsageData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Area type="monotone" dataKey="workflows" stackId="1" stroke="#8884d8" fill="#8884d8" />
                      <Area type="monotone" dataKey="agents" stackId="1" stroke="#82ca9d" fill="#82ca9d" />
                      <Area type="monotone" dataKey="storage" stackId="1" stroke="#ffc658" fill="#ffc658" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Security Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Security Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={securityStatusData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {securityStatusData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* System Health Metrics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                System Health Metrics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Overall Uptime</span>
                    <span className="text-sm font-medium">99.9%</span>
                  </div>
                  <Progress value={99.9} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Security Score</span>
                    <span className="text-sm font-medium">95%</span>
                  </div>
                  <Progress value={95} className="h-2" />
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Compliance Status</span>
                    <span className="text-sm font-medium">100%</span>
                  </div>
                  <Progress value={100} className="h-2" />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Enterprise Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="font-medium">Global Security Settings</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Enforce MFA for all tenants</span>
                      <input type="checkbox" className="rounded" />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Enable audit logging</span>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Require data encryption</span>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                  </div>
                </div>
                
                <div className="space-y-4">
                  <h4 className="font-medium">Resource Management</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Auto-scaling enabled</span>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Resource monitoring</span>
                      <input type="checkbox" className="rounded" defaultChecked />
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">Cost optimization</span>
                      <input type="checkbox" className="rounded" />
                    </div>
                  </div>
                </div>
              </div>
              
              <Button className="w-full">
                Save Configuration
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnterpriseManagementBlock;