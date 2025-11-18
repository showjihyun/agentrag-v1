# Slack & Gmail Tools - Quick Reference

## 🚀 Quick Start

### Slack Setup

1. Create Slack App: https://api.slack.com/apps
2. Add Bot Token Scopes:
   - `chat:write`
   - `chat:write.public`
   - `channels:read`
   - `channels:manage`
   - `users:read`
   - `files:write`
3. Install to workspace
4. Copy Bot Token (xoxb-...)
5. Set environment variable: `SLACK_BOT_TOKEN=xoxb-...`

### Gmail Setup

1. Create Google Cloud Project: https://console.cloud.google.com
2. Enable Gmail API
3. Create OAuth2 credentials
4. Get access token via OAuth2 flow
5. Set credentials in workflow

## 📝 Slack Operations

### Send Message
```json
{
  "operation": "Send Message",
  "token": "xoxb-your-token",
  "channel": "#general",
  "text": "Hello World!"
}
```

### Send Rich Message (Block Kit)
```json
{
  "operation": "Send Message",
  "token": "xoxb-your-token",
  "channel": "#notifications",
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Bold* and _italic_ text"
      }
    }
  ]
}
```

### Send Direct Message
```json
{
  "operation": "Send Direct Message",
  "token": "xoxb-your-token",
  "user": "U1234567890",
  "text": "Private message"
}
```

### Update Message
```json
{
  "operation": "Update Message",
  "token": "xoxb-your-token",
  "channel": "C1234567890",
  "message_ts": "1234567890.123456",
  "text": "Updated text"
}
```

### Create Channel
```json
{
  "operation": "Create Channel",
  "token": "xoxb-your-token",
  "channel_name": "new-channel",
  "is_private": false
}
```

### Get User Info
```json
{
  "operation": "Get User",
  "token": "xoxb-your-token",
  "user": "U1234567890"
}
```

## 📧 Gmail Operations

### Send Email
```json
{
  "operation": "Send Email",
  "credentials": {"access_token": "your-token"},
  "to": "user@example.com",
  "subject": "Hello",
  "body": "Email body",
  "body_type": "Plain Text"
}
```

### Send HTML Email
```json
{
  "operation": "Send Email",
  "credentials": {"access_token": "your-token"},
  "to": "user@example.com",
  "subject": "HTML Email",
  "body": "<h1>Hello</h1><p>HTML content</p>",
  "body_type": "HTML"
}
```

### Send with CC/BCC
```json
{
  "operation": "Send Email",
  "credentials": {"access_token": "your-token"},
  "to": "user@example.com",
  "cc": "cc@example.com",
  "bcc": "bcc@example.com",
  "subject": "Email with CC/BCC",
  "body": "Content"
}
```

### Search Emails
```json
{
  "operation": "Search Emails",
  "credentials": {"access_token": "your-token"},
  "query": "from:boss@example.com is:unread",
  "max_results": 10
}
```

### Get Email
```json
{
  "operation": "Get Email",
  "credentials": {"access_token": "your-token"},
  "message_id": "1234567890abcdef"
}
```

### Create Draft
```json
{
  "operation": "Create Draft",
  "credentials": {"access_token": "your-token"},
  "to": "user@example.com",
  "subject": "Draft",
  "body": "Draft content"
}
```

### Add Label
```json
{
  "operation": "Add Label",
  "credentials": {"access_token": "your-token"},
  "message_id": "1234567890abcdef",
  "label_ids": ["INBOX", "IMPORTANT"]
}
```

## 🎨 Slack Block Kit Examples

### Header + Section
```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🚀 Deployment Complete"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "Version 1.2.3 deployed successfully"
      }
    }
  ]
}
```

### Fields (2 columns)
```json
{
  "blocks": [
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Status:*\nSuccess"
        },
        {
          "type": "mrkdwn",
          "text": "*Duration:*\n2m 30s"
        }
      ]
    }
  ]
}
```

### Divider
```json
{
  "blocks": [
    {"type": "divider"}
  ]
}
```

### Context (footer)
```json
{
  "blocks": [
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "Deployed by John Doe at 2:30 PM"
        }
      ]
    }
  ]
}
```

## 🔍 Gmail Search Queries

### Common Queries
- `from:user@example.com` - From specific sender
- `to:user@example.com` - To specific recipient
- `subject:report` - Subject contains "report"
- `is:unread` - Unread emails
- `is:starred` - Starred emails
- `has:attachment` - Has attachments
- `after:2024/01/01` - After date
- `before:2024/12/31` - Before date
- `label:important` - Has label

### Combined Queries
- `from:boss@example.com is:unread` - Unread from boss
- `subject:invoice has:attachment` - Invoices with attachments
- `from:team@example.com after:2024/01/01` - From team this year

## 🎯 Common Use Cases

### 1. Deployment Notification
```python
# Slack
await execute_slack_tool({
    "operation": "Send Message",
    "channel": "#deployments",
    "blocks": [
        {"type": "header", "text": {"type": "plain_text", "text": "🚀 Deployed"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "Version 1.2.3"}}
    ]
})
```

### 2. Error Alert
```python
# Gmail
await execute_gmail_tool({
    "operation": "Send Email",
    "to": "oncall@example.com",
    "subject": "🚨 Error Alert",
    "body": "<h1>Error Detected</h1><p>Details...</p>",
    "body_type": "HTML"
})
```

### 3. Daily Report
```python
# Both
await execute_slack_tool({...})  # Post to Slack
await execute_gmail_tool({...})  # Email to team
```

### 4. Customer Onboarding
```python
# Slack DM
await execute_slack_tool({
    "operation": "Send Direct Message",
    "user": "U123",
    "text": "Welcome!"
})

# Welcome Email
await execute_gmail_tool({
    "operation": "Send Email",
    "to": "customer@example.com",
    "subject": "Welcome!",
    "body": "..."
})
```

## 🔐 Security Best Practices

1. **Never hardcode tokens** - Use environment variables
2. **Use OAuth2** - For Gmail, use OAuth2 instead of passwords
3. **Limit scopes** - Only request necessary permissions
4. **Rotate tokens** - Regularly rotate API tokens
5. **Monitor usage** - Track API usage and errors
6. **Validate inputs** - Always validate user inputs
7. **Use HTTPS** - Always use secure connections

## 🐛 Troubleshooting

### Slack Errors

| Error | Solution |
|-------|----------|
| `invalid_auth` | Check token is correct and starts with `xoxb-` |
| `channel_not_found` | Verify channel ID or name |
| `not_in_channel` | Invite bot to channel first |
| `missing_scope` | Add required scope to bot |

### Gmail Errors

| Error | Solution |
|-------|----------|
| `401 Unauthorized` | Refresh OAuth2 token |
| `403 Forbidden` | Check API is enabled and scopes are correct |
| `404 Not Found` | Verify message ID exists |
| `429 Too Many Requests` | Implement rate limiting |

## 📚 Resources

- [Slack API Docs](https://api.slack.com/)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)
- [Gmail API Docs](https://developers.google.com/gmail/api)
- [Gmail Query Syntax](https://support.google.com/mail/answer/7190)
- [OAuth2 Guide](https://developers.google.com/identity/protocols/oauth2)

## 💡 Tips

1. **Use Block Kit** - Slack Block Kit provides much richer formatting than plain text
2. **Test with webhooks** - Use webhook triggers to test workflows
3. **Handle errors** - Always implement error handling
4. **Use templates** - Create reusable message templates
5. **Monitor rate limits** - Both APIs have rate limits
6. **Cache tokens** - Cache OAuth2 tokens to avoid repeated auth flows
7. **Use batch operations** - For multiple operations, use batch APIs when available

---

**Need help?** Check the full documentation at `SLACK_GMAIL_TOOLS_COMPLETE.md`
