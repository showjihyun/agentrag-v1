/**
 * Workflow Components Index
 * 
 * Centralized exports for all workflow components
 */

// Core editor
export { WorkflowEditor } from './WorkflowEditor';

// Block palette
export { ImprovedBlockPalette } from './ImprovedBlockPalette';
export { BlockPalette } from './BlockPalette'; // Deprecated

// Drag and drop
export { DraggableBlock, DropZoneIndicator, useDragAndDrop } from './DraggableBlock';

// Configuration panels
export { NodeConfigPanel } from './NodeConfigPanel';
export { NodeConfigurationPanel } from './NodeConfigurationPanel';

// Execution
export { EnhancedExecutionPanel } from './EnhancedExecutionPanel';
export { ExecutionControlPanel } from './ExecutionControlPanel';
export { ExecutionDetailsPanel } from './ExecutionDetailsPanel';
export { ExecutionStatusBadge } from './ExecutionStatusBadge';

// Minimap and navigation
export { ExecutionMiniMap, ZoomControls } from './ExecutionMiniMap';

// Context menu
export { WorkflowContextMenu, useContextMenu } from './WorkflowContextMenu';

// Onboarding
export { OnboardingTour, useOnboardingTour } from './OnboardingTour';

// Search
export { NodeSearch } from './NodeSearch';

// Validation
export { ValidationPanel } from './ValidationPanel';

// Skeleton loaders
export { 
  WorkflowEditorSkeleton, 
  WorkflowCanvasSkeleton, 
  PaletteSkeleton, 
  PropertiesPanelSkeleton,
  WorkflowCardSkeleton,
  Skeleton,
} from './WorkflowSkeletonLoader';

// Template gallery
export { TemplateGallery } from './TemplateGallery';
export type { WorkflowTemplate } from './TemplateGallery';

// Analytics
export { WorkflowAnalytics } from './WorkflowAnalytics';

// Monitoring
export { MonitoringDashboard } from './MonitoringDashboard';
export { CostTrackingDashboard } from './CostTrackingDashboard';

// Multi-Agent Team
export { AgentTeamBuilder } from './AgentTeamBuilder';

// NLP Workflow Generation
export { NLPWorkflowGenerator } from './NLPWorkflowGenerator';

// Visual Debugger
export { VisualDebugger } from './VisualDebugger';
export type { DebugNode, DebugState, DebugSnapshot, WatchExpression } from './VisualDebugger';

// Smart Error Recovery
export { SmartErrorRecovery } from './SmartErrorRecovery';
export type { WorkflowError, RecoveryOption, AIAnalysis } from './SmartErrorRecovery';

// Conversational Builder
export { ConversationalBuilder } from './ConversationalBuilder';
export type { Message, GeneratedWorkflow } from './ConversationalBuilder';

// AI Optimizer
export { AIOptimizer } from './AIOptimizer';
export type { OptimizationSuggestion, WorkflowMetrics } from './AIOptimizer';

// Collaboration
export { CollaborationPanel } from './CollaborationPanel';
export type { Collaborator, Comment, ActivityItem } from './CollaborationPanel';

// Version Control
export { VersionControlPanel } from './VersionControlPanel';
export type { Branch, Commit, Change, Environment } from './VersionControlPanel';

// Nodes (re-export from nodes folder)
export * from './nodes';
