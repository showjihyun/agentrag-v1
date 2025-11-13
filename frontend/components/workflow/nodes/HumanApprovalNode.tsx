'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { UserCheck } from 'lucide-react';

interface HumanApprovalNodeData {
  label: string;
  approvers?: string[];
  timeout?: number;
  requireAll?: boolean;
}

export default function HumanApprovalNode({ data, selected }: NodeProps<HumanApprovalNodeData>) {
  const approverCount = data.approvers?.length || 0;
  const requireAll = data.requireAll !== false;

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <UserCheck className="w-5 h-5 text-amber-600" />
          <span className="font-semibold text-gray-800">Human Approval</span>
        </div>
        
        <div className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded font-medium">
          {requireAll ? 'All must approve' : 'Any can approve'}
        </div>

        {approverCount > 0 && (
          <div className="text-xs text-gray-500 mt-2">
            {approverCount} approver{approverCount > 1 ? 's' : ''}
          </div>
        )}

        {data.timeout && (
          <div className="text-xs text-gray-400 mt-1">
            Timeout: {data.timeout}h
          </div>
        )}
      </div>

      {/* Approved output */}
      <Handle
        type="source"
        position={Position.Right}
        id="approved"
        style={{ top: '40%', background: '#10b981' }}
        className="w-3 h-3"
      />
      
      {/* Rejected output */}
      <Handle
        type="source"
        position={Position.Right}
        id="rejected"
        style={{ top: '60%', background: '#ef4444' }}
        className="w-3 h-3"
      />
    </div>
  );
}
