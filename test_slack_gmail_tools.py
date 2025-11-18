"""
Test Slack and Gmail tools with n8n-level functionality.
"""

import asyncio
import os
from backend.core.tools.integrations.slack_tool import execute_slack_tool
from backend.core.tools.integrations.gmail_tool import execute_gmail_tool


async def test_slack_send_message():
    """Test Slack send message."""
    print("\n=== Testing Slack Send Message ===")
    
    result = await execute_slack_tool({
        "operation": "Send Message",
        "token": os.getenv("SLACK_BOT_TOKEN", "xoxb-test-token"),
        "channel": "#general",
        "text": "Hello from AgenticRAG! 🚀"
    })
    
    print(f"Result: {result}")
    return result


async def test_slack_send_rich_message():
    """Test Slack send rich message with blocks."""
    print("\n=== Testing Slack Rich Message ===")
    
    result = await execute_slack_tool({
        "operation": "Send Message",
        "token": os.getenv("SLACK_BOT_TOKEN", "xoxb-test-token"),
        "channel": "#notifications",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Complete* :white_check_mark:"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": "*Version:*\n1.2.3"
                    },
                    {
                        "type": "mrkdwn",
                        "text": "*Status:*\nSuccess"
                    }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Deployed by AgenticRAG Bot"
                }
            }
        ]
    })
    
    print(f"Result: {result}")
    return result


async def test_slack_direct_message():
    """Test Slack direct message."""
    print("\n=== Testing Slack Direct Message ===")
    
    result = await execute_slack_tool({
        "operation": "Send Direct Message",
        "token": os.getenv("SLACK_BOT_TOKEN", "xoxb-test-token"),
        "user": "U1234567890",
        "text": "Hi! This is a private message from AgenticRAG."
    })
    
    print(f"Result: {result}")
    return result


async def test_slack_get_channel():
    """Test Slack get channel info."""
    print("\n=== Testing Slack Get Channel ===")
    
    result = await execute_slack_tool({
        "operation": "Get Channel",
        "token": os.getenv("SLACK_BOT_TOKEN", "xoxb-test-token"),
        "channel": "C1234567890"
    })
    
    print(f"Result: {result}")
    return result


async def test_gmail_send_email():
    """Test Gmail send email."""
    print("\n=== Testing Gmail Send Email ===")
    
    result = await execute_gmail_tool({
        "operation": "Send Email",
        "credentials": {
            "access_token": os.getenv("GMAIL_ACCESS_TOKEN", "test-token")
        },
        "to": "user@example.com",
        "subject": "Hello from AgenticRAG",
        "body": "This is a test email sent via AgenticRAG's Gmail integration.",
        "body_type": "Plain Text"
    })
    
    print(f"Result: {result}")
    return result


async def test_gmail_send_html_email():
    """Test Gmail send HTML email."""
    print("\n=== Testing Gmail HTML Email ===")
    
    html_body = """
    <html>
        <body>
            <h1>Weekly Report</h1>
            <p>Here is your weekly report from AgenticRAG:</p>
            <ul>
                <li>Total queries: 1,234</li>
                <li>Average response time: 2.3s</li>
                <li>User satisfaction: 95%</li>
            </ul>
            <p>Best regards,<br>AgenticRAG Team</p>
        </body>
    </html>
    """
    
    result = await execute_gmail_tool({
        "operation": "Send Email",
        "credentials": {
            "access_token": os.getenv("GMAIL_ACCESS_TOKEN", "test-token")
        },
        "to": "user@example.com",
        "cc": "manager@example.com",
        "subject": "Weekly Report - AgenticRAG",
        "body": html_body,
        "body_type": "HTML"
    })
    
    print(f"Result: {result}")
    return result


async def test_gmail_search_emails():
    """Test Gmail search emails."""
    print("\n=== Testing Gmail Search Emails ===")
    
    result = await execute_gmail_tool({
        "operation": "Search Emails",
        "credentials": {
            "access_token": os.getenv("GMAIL_ACCESS_TOKEN", "test-token")
        },
        "query": "from:boss@example.com is:unread",
        "max_results": 5
    })
    
    print(f"Result: {result}")
    return result


async def test_gmail_create_draft():
    """Test Gmail create draft."""
    print("\n=== Testing Gmail Create Draft ===")
    
    result = await execute_gmail_tool({
        "operation": "Create Draft",
        "credentials": {
            "access_token": os.getenv("GMAIL_ACCESS_TOKEN", "test-token")
        },
        "to": "user@example.com",
        "subject": "Draft: Important Update",
        "body": "This is a draft email that will be reviewed before sending.",
        "body_type": "Plain Text"
    })
    
    print(f"Result: {result}")
    return result


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Slack and Gmail Tools (n8n-level functionality)")
    print("=" * 60)
    
    # Slack tests
    print("\n" + "=" * 60)
    print("SLACK TESTS")
    print("=" * 60)
    
    try:
        await test_slack_send_message()
    except Exception as e:
        print(f"Error: {e}")
    
    try:
        await test_slack_send_rich_message()
    except Exception as e:
        print(f"Error: {e}")
    
    try:
        await test_slack_direct_message()
    except Exception as e:
        print(f"Error: {e}")
    
    try:
        await test_slack_get_channel()
    except Exception as e:
        print(f"Error: {e}")
    
    # Gmail tests
    print("\n" + "=" * 60)
    print("GMAIL TESTS")
    print("=" * 60)
    
    try:
        await test_gmail_send_email()
    except Exception as e:
        print(f"Error: {e}")
    
    try:
        await test_gmail_send_html_email()
    except Exception as e:
        print(f"Error: {e}")
    
    try:
        await test_gmail_search_emails()
    except Exception as e:
        print(f"Error: {e}")
    
    try:
        await test_gmail_create_draft()
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\nNote: To run these tests with real credentials:")
    print("1. Set SLACK_BOT_TOKEN environment variable")
    print("2. Set GMAIL_ACCESS_TOKEN environment variable")
    print("3. Update channel IDs and email addresses")


if __name__ == "__main__":
    asyncio.run(main())
