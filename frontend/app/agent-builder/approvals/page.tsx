'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

interface Approval {
  id: string;
  workflow_id: string;
  message: string;
  status: 'pending' | 'approved' | 'rejected' | 'timeout';
  approvers: string[];
  require_all: boolean;
  created_at: string;
  timeout_at: string;
  data_for_review: any;
  approved_by: string[];
  rejected_by: string[];
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('pending');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadApprovals();
  }, [filter]);

  const loadApprovals = async () => {
    setLoading(true);
    try {
      const statusFilter = filter === 'all' ? '' : filter;
      const response = await fetch(`/api/approvals?status=${statusFilter}`);
      const data = await response.json();
      setApprovals(data.approvals || []);
    } catch (error) {
      console.error('Failed to load approvals:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approvalId: string, approver: string) => {
    try {
      const response = await fetch(`/api/approvals/${approvalId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approver }),
      });

      if (response.ok) {
        loadApprovals();
      }
    } catch (error) {
      console.error('Failed to approve:', error);
    }
  };

  const handleReject = async (approvalId: string, approver: string) => {
    try {
      const response = await fetch(`/api/approvals/${approvalId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approver }),
      });

      if (response.ok) {
        loadApprovals();
      }
    } catch (error) {
      console.error('Failed to reject:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'rejected':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'timeout':
        return <AlertCircle className="w-5 h-5 text-orange-600" />;
      default:
        return <Clock className="w-5 h-5 text-blue-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'timeout':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Approval Requests
          </h1>
          <p className="text-gray-600">
            Review and approve workflow execution requests
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {(['all', 'pending', 'approved', 'rejected'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${
                filter === f
                  ? 'bg-blue-500 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Approvals List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading approvals...</p>
          </div>
        ) : approvals.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No approval requests
            </h3>
            <p className="text-gray-600">
              {filter === 'pending'
                ? 'No pending approvals at the moment'
                : `No ${filter} approvals found`}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {approvals.map((approval) => (
              <div
                key={approval.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(approval.status)}
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {approval.message || 'Approval Required'}
                      </h3>
                      <p className="text-sm text-gray-500">
                        Workflow ID: {approval.workflow_id}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(
                      approval.status
                    )}`}
                  >
                    {approval.status}
                  </span>
                </div>

                {/* Data for Review */}
                {approval.data_for_review && (
                  <div className="mb-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">
                      Data for Review:
                    </h4>
                    <pre className="text-xs text-gray-600 overflow-x-auto">
                      {JSON.stringify(approval.data_for_review, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Approvers Info */}
                <div className="mb-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <span>Approvers:</span>
                    <span className="font-medium">
                      {approval.approvers.join(', ')}
                    </span>
                    {approval.require_all && (
                      <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                        All required
                      </span>
                    )}
                  </div>
                  {approval.approved_by.length > 0 && (
                    <div className="text-sm text-green-600 mt-1">
                      ✓ Approved by: {approval.approved_by.join(', ')}
                    </div>
                  )}
                  {approval.rejected_by.length > 0 && (
                    <div className="text-sm text-red-600 mt-1">
                      ✗ Rejected by: {approval.rejected_by.join(', ')}
                    </div>
                  )}
                </div>

                {/* Timestamps */}
                <div className="flex gap-4 text-xs text-gray-500 mb-4">
                  <span>Created: {new Date(approval.created_at).toLocaleString()}</span>
                  {approval.timeout_at && (
                    <span>
                      Timeout: {new Date(approval.timeout_at).toLocaleString()}
                    </span>
                  )}
                </div>

                {/* Actions */}
                {approval.status === 'pending' && (
                  <div className="flex gap-2">
                    <Button
                      onClick={() => handleApprove(approval.id, 'current-user@example.com')}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      onClick={() => handleReject(approval.id, 'current-user@example.com')}
                      variant="destructive"
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
