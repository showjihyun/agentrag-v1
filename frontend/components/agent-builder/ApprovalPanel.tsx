"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  User,
  Calendar
} from "lucide-react";
import { useToast } from "@/components/ui/use-toast";

interface ApprovalRequest {
  request_id: string;
  agent_id: string;
  execution_id: string;
  action: string;
  context: Record<string, any>;
  priority: "low" | "medium" | "high" | "critical";
  status: "pending" | "approved" | "rejected" | "timeout" | "cancelled";
  created_at: string;
  expires_at: string;
  time_remaining_seconds?: number;
  is_requester: boolean;
  is_approver: boolean;
}

interface ApprovalPanelProps {
  userId: string;
}

export function ApprovalPanel({ userId }: ApprovalPanelProps) {
  const [pendingApprovals, setPendingApprovals] = useState<ApprovalRequest[]>([]);
  const [selectedRequest, setSelectedRequest] = useState<ApprovalRequest | null>(null);
  const [comment, setComment] = useState("");
  const [rejectionReason, setRejectionReason] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchPendingApprovals();
    
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchPendingApprovals, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchPendingApprovals = async () => {
    try {
      const response = await fetch("/api/agent-builder/approvals/pending", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        setPendingApprovals(data.pending_approvals || []);
      }
    } catch (error) {
      console.error("Failed to fetch pending approvals:", error);
    }
  };

  const handleApprove = async (requestId: string) => {
    setLoading(true);
    
    try {
      const response = await fetch(
        `/api/agent-builder/approvals/requests/${requestId}/approve`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("token")}`
          },
          body: JSON.stringify({
            comment: comment || undefined
          })
        }
      );
      
      if (response.ok) {
        toast({
          title: "Approved",
          description: "Request has been approved successfully"
        });
        
        setComment("");
        setSelectedRequest(null);
        fetchPendingApprovals();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Failed to approve");
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (requestId: string) => {
    if (!rejectionReason.trim()) {
      toast({
        title: "Error",
        description: "Please provide a rejection reason",
        variant: "destructive"
      });
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await fetch(
        `/api/agent-builder/approvals/requests/${requestId}/reject`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${localStorage.getItem("token")}`
          },
          body: JSON.stringify({
            reason: rejectionReason,
            comment: comment || undefined
          })
        }
      );
      
      if (response.ok) {
        toast({
          title: "Rejected",
          description: "Request has been rejected"
        });
        
        setComment("");
        setRejectionReason("");
        setSelectedRequest(null);
        fetchPendingApprovals();
      } else {
        const error = await response.json();
        throw new Error(error.detail || "Failed to reject");
      }
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "critical": return "destructive";
      case "high": return "destructive";
      case "medium": return "default";
      case "low": return "secondary";
      default: return "default";
    }
  };

  const formatTimeRemaining = (seconds: number) => {
    if (seconds < 0) return "Expired";
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h`;
    }
    
    return `${hours}h ${minutes}m`;
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Pending Approvals
          </CardTitle>
          <CardDescription>
            {pendingApprovals.length} request{pendingApprovals.length !== 1 ? "s" : ""} awaiting your approval
          </CardDescription>
        </CardHeader>
        <CardContent>
          {pendingApprovals.length === 0 ? (
            <Alert>
              <AlertDescription>
                No pending approvals at this time.
              </AlertDescription>
            </Alert>
          ) : (
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {pendingApprovals.map((request) => (
                  <Card 
                    key={request.request_id}
                    className={`cursor-pointer transition-colors ${
                      selectedRequest?.request_id === request.request_id
                        ? "border-primary"
                        : ""
                    }`}
                    onClick={() => setSelectedRequest(request)}
                  >
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2 flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold">{request.action}</h4>
                            <Badge variant={getPriorityColor(request.priority)}>
                              {request.priority}
                            </Badge>
                          </div>
                          
                          <div className="text-sm text-muted-foreground space-y-1">
                            <div className="flex items-center gap-2">
                              <User className="h-3 w-3" />
                              <span>Agent: {request.agent_id}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <Calendar className="h-3 w-3" />
                              <span>
                                Created: {new Date(request.created_at).toLocaleString()}
                              </span>
                            </div>
                            {request.time_remaining_seconds !== undefined && (
                              <div className="flex items-center gap-2">
                                <Clock className="h-3 w-3" />
                                <span>
                                  Time remaining: {formatTimeRemaining(request.time_remaining_seconds)}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {request.time_remaining_seconds !== undefined && 
                         request.time_remaining_seconds < 3600 && (
                          <AlertTriangle className="h-5 w-5 text-destructive" />
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {selectedRequest && (
        <Card>
          <CardHeader>
            <CardTitle>Approval Decision</CardTitle>
            <CardDescription>
              Review the request details and make your decision
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-semibold">Action</h4>
              <p className="text-sm">{selectedRequest.action}</p>
            </div>
            
            <div className="space-y-2">
              <h4 className="font-semibold">Context</h4>
              <pre className="text-xs bg-muted p-3 rounded-md overflow-auto max-h-[200px]">
                {JSON.stringify(selectedRequest.context, null, 2)}
              </pre>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Comment (Optional)</label>
              <Textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Add a comment..."
                rows={3}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Rejection Reason (Required for rejection)</label>
              <Textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Provide a reason if rejecting..."
                rows={2}
              />
            </div>
            
            <div className="flex gap-2">
              <Button
                onClick={() => handleApprove(selectedRequest.request_id)}
                disabled={loading}
                className="flex-1"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Approve
              </Button>
              
              <Button
                onClick={() => handleReject(selectedRequest.request_id)}
                disabled={loading || !rejectionReason.trim()}
                variant="destructive"
                className="flex-1"
              >
                <XCircle className="h-4 w-4 mr-2" />
                Reject
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
