'use client';

import React from 'react';
import { NodeProps } from 'reactflow';
import { NodeExecutionOverlay } from './NodeExecutionOverlay';
import { NodeStatus } from './ExecutionStatusBadge';

/**
 * Higher Order Component to add execution overlay to any node
 */
export function withExecutionOverlay<T extends NodeProps>(
  WrappedComponent: React.ComponentType<T>
) {
  return function NodeWithExecutionOverlay(props: T) {
    const { data } = props;
    
    // Extract execution data from node data
    const executionStatus = data?.executionStatus as NodeStatus | undefined;
    const executionError = data?.executionError as string | undefined;
    const executionOutput = data?.executionOutput;
    const startTime = data?.startTime as number | undefined;
    const endTime = data?.endTime as number | undefined;
    const progress = data?.progress as number | undefined;

    return (
      <div className="relative">
        <WrappedComponent {...props} />
        <NodeExecutionOverlay
          status={executionStatus}
          startTime={startTime}
          endTime={endTime}
          error={executionError}
          progress={progress}
          showDetails={true}
        />
      </div>
    );
  };
}
