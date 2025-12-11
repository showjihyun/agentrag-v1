-- Fix workflow_executions status constraint to include 'waiting_approval'

-- Drop old constraint
ALTER TABLE workflow_executions DROP CONSTRAINT IF EXISTS check_workflow_execution_status_valid;

-- Create new constraint with waiting_approval
ALTER TABLE workflow_executions ADD CONSTRAINT check_workflow_execution_status_valid 
CHECK (status IN ('running', 'completed', 'failed', 'timeout', 'cancelled', 'waiting_approval'));
