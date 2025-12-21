"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Download, Search, Filter, RefreshCw } from "lucide-react";
import { agentBuilderAPI } from "@/lib/api/agent-builder";

interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>("all");
  const [userFilter, setUserFilter] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    loadAuditLogs();
  }, [page, actionFilter, resourceTypeFilter, userFilter]);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      
      const params: Record<string, any> = {
        page,
        page_size: 50
      };
      
      if (actionFilter !== "all") {
        params.action = actionFilter;
      }
      
      if (resourceTypeFilter !== "all") {
        params.resource_type = resourceTypeFilter;
      }
      
      if (userFilter) {
        params.user_id = userFilter;
      }
      
      const response = await agentBuilderApi.getAuditLogs(params);
      
      setLogs(response.logs);
      setTotalPages(response.total_pages);
    } catch (error) {
      console.error("Failed to load audit logs:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(1);
    loadAuditLogs();
  };

  const handleExport = async (format: "csv" | "json") => {
    try {
      const params: Record<string, any> = {};
      
      if (actionFilter !== "all") {
        params.action = actionFilter;
      }
      
      if (resourceTypeFilter !== "all") {
        params.resource_type = resourceTypeFilter;
      }
      
      if (userFilter) {
        params.user_id = userFilter;
      }
      
      const blob = await agentBuilderApi.exportAuditLogs(format, params);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString()}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Failed to export audit logs:", error);
    }
  };

  const getActionBadgeVariant = (action: string) => {
    if (action.startsWith("create")) return "default";
    if (action.startsWith("update")) return "secondary";
    if (action.startsWith("delete")) return "destructive";
    if (action.startsWith("execute")) return "outline";
    if (action.startsWith("security")) return "destructive";
    return "default";
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Audit Logs</h1>
          <p className="text-muted-foreground">
            View and export system audit logs for compliance and debugging
          </p>
        </div>
        
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => handleExport("csv")}
          >
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button
            variant="outline"
            onClick={() => handleExport("json")}
          >
            <Download className="w-4 h-4 mr-2" />
            Export JSON
          </Button>
          <Button
            variant="outline"
            onClick={loadAuditLogs}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter audit logs by action, resource type, or user</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Action</label>
              <Select value={actionFilter} onValueChange={setActionFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All actions" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All actions</SelectItem>
                  <SelectItem value="create_agent">Create Agent</SelectItem>
                  <SelectItem value="update_agent">Update Agent</SelectItem>
                  <SelectItem value="delete_agent">Delete Agent</SelectItem>
                  <SelectItem value="execute_agent">Execute Agent</SelectItem>
                  <SelectItem value="create_workflow">Create Workflow</SelectItem>
                  <SelectItem value="execute_workflow">Execute Workflow</SelectItem>
                  <SelectItem value="grant_permission">Grant Permission</SelectItem>
                  <SelectItem value="security_">Security Events</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Resource Type</label>
              <Select value={resourceTypeFilter} onValueChange={setResourceTypeFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All resources" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All resources</SelectItem>
                  <SelectItem value="agent">Agent</SelectItem>
                  <SelectItem value="workflow">Workflow</SelectItem>
                  <SelectItem value="block">Block</SelectItem>
                  <SelectItem value="knowledgebase">Knowledgebase</SelectItem>
                  <SelectItem value="variable">Variable</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">User ID</label>
              <Input
                placeholder="Filter by user ID"
                value={userFilter}
                onChange={(e) => setUserFilter(e.target.value)}
              />
            </div>

            <div className="flex items-end">
              <Button onClick={handleSearch} className="w-full">
                <Search className="w-4 h-4 mr-2" />
                Search
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Audit Log Entries</CardTitle>
          <CardDescription>
            Showing {logs.length} entries (Page {page} of {totalPages})
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px]">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>IP Address</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      Loading audit logs...
                    </TableCell>
                  </TableRow>
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      No audit logs found
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="font-mono text-xs">
                        {formatTimestamp(log.timestamp)}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.user_id.substring(0, 8)}...
                      </TableCell>
                      <TableCell>
                        <Badge variant={getActionBadgeVariant(log.action)}>
                          {log.action}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {log.resource_type && log.resource_id ? (
                          <div className="text-sm">
                            <div className="font-medium">{log.resource_type}</div>
                            <div className="font-mono text-xs text-muted-foreground">
                              {log.resource_id.substring(0, 8)}...
                            </div>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.ip_address || "-"}
                      </TableCell>
                      <TableCell>
                        <Badge variant={log.details.success ? "default" : "destructive"}>
                          {log.details.success ? "Success" : "Failed"}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <details className="cursor-pointer">
                          <summary className="text-sm text-blue-600 hover:underline">
                            View
                          </summary>
                          <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto max-w-md">
                            {JSON.stringify(log.details, null, 2)}
                          </pre>
                        </details>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </ScrollArea>

          {!loading && logs.length > 0 && (
            <div className="flex justify-between items-center mt-4">
              <Button
                variant="outline"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="outline"
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
