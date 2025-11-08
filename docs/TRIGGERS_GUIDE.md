# Triggers Guide - sim.ai Style

## 📌 Overview

Triggers are the entry points that automatically start your workflows based on specific events or conditions. Unlike the Start node which requires manual execution, Triggers enable automated workflow execution.

## 🎯 Trigger Types

### 1. ⚡ Manual Trigger
**Description**: Start workflow manually via UI or API

**Use Cases**:
- On-demand processing
- Testing workflows
- User-initiated actions

**Configuration**:
- Name: Display name for the trigger
- Description: What this trigger does

**Example**:
```
Manual Trigger → Agent (Process) → End
```

---

### 2. 🕐 Schedule Trigger
**Description**: Run workflow on a schedule using cron expressions

**Use Cases**:
- Daily reports
- Periodic data sync
- Scheduled maintenance tasks
- Batch processing

**Configuration**:
- **Cron Expression**: Define when to run
  - `0 0 * * *` - Every day at midnight
  - `0 */6 * * *` - Every 6 hours
  - `0 9 * * 1` - Every Monday at 9 AM
  - `*/15 * * * *` - Every 15 minutes

**Example**:
```
Schedule Trigger (daily at 9 AM)
  → Agent (Fetch Data)
  → Agent (Generate Report)
  → Tool (Send Email)
  → End
```

---

### 3. 🔗 Webhook Trigger
**Description**: Trigger workflow via HTTP POST request

**Use Cases**:
- GitHub webhooks
- Payment notifications
- Third-party integrations
- API callbacks

**Configuration**:
- **Webhook URL**: Auto-generated endpoint
- **Authentication**: Optional API key

**Example Webhook URL**:
```
POST https://your-domain.com/api/webhooks/wf_abc123
```

**Example Payload**:
```json
{
  "event": "user.created",
  "data": {
    "userId": "123",
    "email": "user@example.com"
  }
}
```

**Workflow Example**:
```
Webhook Trigger
  → Condition (event type)
    ├─ user.created → Agent (Welcome Email) → End
    └─ user.deleted → Agent (Cleanup) → End
```

---

### 4. 📧 Email Trigger
**Description**: Trigger when email is received at specific address

**Use Cases**:
- Support ticket creation
- Email-to-task conversion
- Automated email processing
- Invoice processing

**Configuration**:
- **Email Address**: workflow@yourdomain.com
- **Subject Filter**: Optional regex pattern
- **Sender Filter**: Optional email whitelist

**Example**:
```
Email Trigger (support@company.com)
  → Agent (Extract Info)
  → Tool (Create Ticket)
  → Agent (Send Confirmation)
  → End
```

---

### 5. 📅 Event Trigger
**Description**: Trigger on system or application events

**Use Cases**:
- User signup events
- Order completion
- File upload events
- Status changes

**Configuration**:
- **Event Type**: Select from available events
- **Event Filter**: Optional conditions

**Available Events**:
- `user.created`
- `user.updated`
- `order.completed`
- `file.uploaded`
- `status.changed`

**Example**:
```
Event Trigger (order.completed)
  → Agent (Process Order)
  → Tool (Update Inventory)
  → Agent (Send Confirmation)
  → End
```

---

### 6. 💾 Database Trigger
**Description**: Trigger on database changes (INSERT, UPDATE, DELETE)

**Use Cases**:
- Data synchronization
- Audit logging
- Real-time notifications
- Cache invalidation

**Configuration**:
- **Table Name**: Which table to monitor
- **Event Type**: INSERT, UPDATE, or DELETE
- **Condition**: Optional WHERE clause

**Example**:
```
Database Trigger (users table, INSERT)
  → Agent (Validate Data)
  → Tool (Send Welcome Email)
  → Tool (Update Analytics)
  → End
```

---

## 🏗️ Building Workflows with Triggers

### Basic Pattern
```
Trigger → Processing → End
```

### With Conditions
```
Trigger → Condition
           ├─ True → Process A → End
           └─ False → Process B → End
```

### Multi-Step Processing
```
Trigger
  → Agent (Extract)
  → Agent (Transform)
  → Agent (Validate)
  → Tool (Store)
  → End
```

### Error Handling
```
Trigger
  → Agent (Process)
  → Condition (success?)
    ├─ True → End
    └─ False → Agent (Retry) → End
```

---

## 📋 Configuration Examples

### 1. Daily Report Generation
```yaml
Trigger Type: Schedule
Cron: 0 9 * * 1-5  # Weekdays at 9 AM
Name: Daily Sales Report

Workflow:
  Schedule Trigger
    → Tool (Fetch Sales Data)
    → Agent (Analyze Trends)
    → Agent (Generate Report)
    → Tool (Send Email)
    → End
```

### 2. GitHub Webhook Integration
```yaml
Trigger Type: Webhook
Name: GitHub PR Webhook

Workflow:
  Webhook Trigger
    → Condition (action === "opened")
      ├─ True → Agent (Review Code) → Tool (Comment) → End
      └─ False → End
```

### 3. Support Email Automation
```yaml
Trigger Type: Email
Email: support@company.com
Name: Support Ticket Creator

Workflow:
  Email Trigger
    → Agent (Extract Issue)
    → Tool (Create Ticket)
    → Agent (Categorize)
    → Tool (Assign Team)
    → Agent (Send Confirmation)
    → End
```

### 4. User Signup Flow
```yaml
Trigger Type: Event
Event: user.created
Name: New User Onboarding

Workflow:
  Event Trigger
    → Agent (Validate User)
    → Tool (Send Welcome Email)
    → Tool (Create Profile)
    → Agent (Recommend Content)
    → End
```

### 5. Database Sync
```yaml
Trigger Type: Database
Table: orders
Event: INSERT
Name: Order Processing

Workflow:
  Database Trigger
    → Agent (Validate Order)
    → Tool (Update Inventory)
    → Tool (Send Notification)
    → Agent (Calculate Shipping)
    → End
```

---

## 🎨 Visual Design

### Trigger Node Appearance
- **Gradient Background**: Each trigger type has unique colors
- **Icon**: Distinctive icon for each type
- **No Input Handle**: Triggers are entry points
- **Output Handle**: Connects to workflow

### Color Scheme
- Manual: Yellow-Orange gradient
- Schedule: Blue-Cyan gradient
- Webhook: Purple-Pink gradient
- Email: Green-Emerald gradient
- Event: Red-Rose gradient
- Database: Indigo-Violet gradient

---

## 🔧 Advanced Features

### Multiple Triggers
You can have multiple triggers in one workflow:
```
Trigger A (Manual) ─┐
                    ├→ Agent → End
Trigger B (Webhook)─┘
```

### Trigger Chaining
One workflow can trigger another:
```
Workflow 1:
  Trigger → Process → Tool (Trigger Workflow 2) → End

Workflow 2:
  Webhook Trigger → Process → End
```

### Conditional Triggers
```
Trigger
  → Condition (time of day)
    ├─ Morning → Agent (Morning Process) → End
    └─ Evening → Agent (Evening Process) → End
```

---

## 📊 Monitoring & Logs

### Trigger Execution Logs
- Timestamp
- Trigger type
- Input data
- Execution status
- Duration

### Metrics
- Trigger count
- Success rate
- Average execution time
- Error rate

---

## 🐛 Troubleshooting

### Trigger Not Firing

**Schedule Trigger**:
- Check cron expression syntax
- Verify timezone settings
- Ensure workflow is active

**Webhook Trigger**:
- Verify webhook URL
- Check authentication
- Validate payload format

**Email Trigger**:
- Confirm email address is configured
- Check spam filters
- Verify email forwarding rules

**Database Trigger**:
- Ensure database connection
- Check table permissions
- Verify trigger conditions

---

## 🎯 Best Practices

### 1. Use Descriptive Names
```
✅ "Daily Sales Report - 9 AM"
❌ "Trigger 1"
```

### 2. Add Clear Descriptions
```
✅ "Generates and emails daily sales report to management team"
❌ "Report trigger"
```

### 3. Test Before Production
- Use Manual Trigger for testing
- Validate with sample data
- Monitor first few executions

### 4. Handle Errors Gracefully
```
Trigger
  → Try: Process
  → Catch: Log Error → Notify Admin → End
```

### 5. Set Appropriate Schedules
- Avoid peak hours for heavy processing
- Consider timezone differences
- Use rate limiting for high-frequency triggers

### 6. Secure Webhooks
- Use authentication tokens
- Validate payload signatures
- Implement rate limiting

---

## 🚀 Quick Start

### 1. Add Trigger to Workflow
1. Open workflow editor
2. Click **Triggers** tab in palette
3. Drag desired trigger to canvas

### 2. Configure Trigger
1. Click trigger node
2. Set name and description
3. Configure trigger-specific settings
4. Click **Apply Changes**

### 3. Connect to Workflow
1. Drag from trigger's output handle
2. Connect to first processing node
3. Build rest of workflow

### 4. Save and Activate
1. Click **Save Workflow**
2. Activate workflow
3. Monitor execution logs

---

## 📚 Examples Library

### E-commerce Order Processing
```
Database Trigger (orders, INSERT)
  → Agent (Validate Order)
  → Condition (payment_status)
    ├─ paid → Agent (Process) → Tool (Ship) → End
    └─ pending → Agent (Send Reminder) → End
```

### Content Moderation
```
Event Trigger (content.submitted)
  → Agent (Analyze Content)
  → Condition (is_appropriate)
    ├─ True → Tool (Publish) → End
    └─ False → Tool (Flag) → Agent (Notify) → End
```

### Backup Automation
```
Schedule Trigger (0 2 * * *)  # 2 AM daily
  → Tool (Backup Database)
  → Tool (Upload to S3)
  → Agent (Verify Backup)
  → Tool (Send Report)
  → End
```

### Customer Support
```
Email Trigger (support@company.com)
  → Agent (Extract Issue)
  → Agent (Classify Priority)
  → Condition (priority)
    ├─ high → Tool (Alert Team) → End
    └─ normal → Tool (Create Ticket) → End
```

---

## 🎉 Summary

Triggers enable powerful automation by:
- ✅ Starting workflows automatically
- ✅ Responding to events in real-time
- ✅ Scheduling recurring tasks
- ✅ Integrating with external systems
- ✅ Processing data as it arrives

**6 Trigger Types Available**:
1. ⚡ Manual - On-demand execution
2. 🕐 Schedule - Time-based automation
3. 🔗 Webhook - HTTP-triggered workflows
4. 📧 Email - Email-triggered processing
5. 📅 Event - Event-driven automation
6. 💾 Database - Data-change triggers

Start building automated workflows today!

---

**Documentation Version**: 1.0
**Last Updated**: 2025-11-09
