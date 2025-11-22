import { memo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  Node,
  Edge,
  NodeTypes,
  EdgeTypes,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { WorkflowSearchBar } from './WorkflowSearchBar';

interface CanvasContentProps {
  nodes: Node[];
  edges: Edge[];
  nodeTypes: NodeTypes;
  edgeTypes: EdgeTypes;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  onSearchResults?: (results: Node[]) => void;
}

export const CanvasContent = memo(function CanvasContent({
  nodes,
  edges,
  nodeTypes,
  edgeTypes,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onSearchResults,
}: CanvasContentProps) {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      fitView
      className="bg-background"
    >
      <Background />
      <Controls />
      <MiniMap 
        nodeStrokeWidth={3}
        zoomable
        pannable
      />
      
      <Panel position="top-center" className="bg-background/95 backdrop-blur-sm rounded-lg shadow-lg p-2">
        <WorkflowSearchBar
          nodes={nodes}
          onSearchResults={onSearchResults}
        />
      </Panel>
    </ReactFlow>
  );
});
