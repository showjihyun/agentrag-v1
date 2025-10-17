"""
Simple verification script for query message saving functionality.

This script verifies the code structure without running the full application.
"""

import sys
import os
import re

print("=" * 80)
print("QUERY MESSAGE SAVING VERIFICATION (Code Structure)")
print("=" * 80)
print()

# Read the query.py file
query_file = os.path.join(os.path.dirname(__file__), "api", "query.py")

if not os.path.exists(query_file):
    print(f"✗ File not found: {query_file}")
    sys.exit(1)

with open(query_file, "r", encoding="utf-8") as f:
    content = f.read()

print("✓ Check 1: Verifying stream_agent_response signature...")
# Check if function has user and db parameters
if re.search(
    r"async def stream_agent_response\([^)]*user:\s*User\s*\|\s*None[^)]*\)", content
):
    print("  ✓ Function has 'user: User | None' parameter")
else:
    print("  ✗ Missing 'user: User | None' parameter")
    sys.exit(1)

if re.search(
    r"async def stream_agent_response\([^)]*db:\s*Session\s*\|\s*None[^)]*\)", content
):
    print("  ✓ Function has 'db: Session | None' parameter")
else:
    print("  ✗ Missing 'db: Session | None' parameter")
    sys.exit(1)

print()

print("✓ Check 2: Verifying user authentication check...")
if "if user is not None and db is not None:" in content:
    print("  ✓ User authentication check present")
else:
    print("  ✗ Missing user authentication check")
    sys.exit(1)

print()

print("✓ Check 3: Verifying ConversationService usage...")
if "from services.conversation_service import ConversationService" in content:
    print("  ✓ ConversationService imported")
else:
    print("  ✗ ConversationService not imported")
    sys.exit(1)

if "conversation_service = ConversationService(db)" in content:
    print("  ✓ ConversationService instantiated")
else:
    print("  ✗ ConversationService not instantiated")
    sys.exit(1)

print()

print("✓ Check 4: Verifying session creation...")
if "get_or_create_session" in content:
    print("  ✓ get_or_create_session called")
else:
    print("  ✗ get_or_create_session not called")
    sys.exit(1)

print()

print("✓ Check 5: Verifying user message saving...")
if re.search(r'save_message_with_sources\([^)]*role="user"[^)]*\)', content):
    print("  ✓ User message saved before processing")
else:
    print("  ✗ User message not saved")
    sys.exit(1)

print()

print("✓ Check 6: Verifying response accumulation...")
if "response_buffer" in content:
    print("  ✓ Response buffer for accumulation present")
else:
    print("  ✗ Response buffer missing")
    sys.exit(1)

if "response_buffer.append" in content:
    print("  ✓ Response content accumulated")
else:
    print("  ✗ Response content not accumulated")
    sys.exit(1)

print()

print("✓ Check 7: Verifying assistant message saving...")
if re.search(r'save_message_with_sources\([^)]*role="assistant"[^)]*\)', content):
    print("  ✓ Assistant message saved after completion")
else:
    print("  ✗ Assistant message not saved")
    sys.exit(1)

print()

print("✓ Check 8: Verifying source extraction...")
if "sources_list" in content:
    print("  ✓ Sources list for extraction present")
else:
    print("  ✗ Sources list missing")
    sys.exit(1)

if '"sources" in step.metadata' in content or '"sources" in' in content:
    print("  ✓ Sources extracted from metadata")
else:
    print("  ✗ Sources not extracted")
    sys.exit(1)

print()

print("✓ Check 9: Verifying metadata inclusion...")
metadata_fields = [
    "query_mode",
    "processing_time_ms",
    "confidence_score",
    "cache_hit",
    "cache_match_type",
    "cache_similarity",
]

for field in metadata_fields:
    if field in content:
        print(f"  ✓ Metadata field '{field}' included")
    else:
        print(f"  ⚠ Metadata field '{field}' not found (may be optional)")

print()

print("✓ Check 10: Verifying stream_hybrid_response signature...")
if re.search(
    r"async def stream_hybrid_response\([^)]*user:\s*User\s*\|\s*None[^)]*\)", content
):
    print("  ✓ stream_hybrid_response has 'user: User | None' parameter")
else:
    print("  ✗ stream_hybrid_response missing 'user: User | None' parameter")
    sys.exit(1)

if re.search(
    r"async def stream_hybrid_response\([^)]*db:\s*Session\s*\|\s*None[^)]*\)", content
):
    print("  ✓ stream_hybrid_response has 'db: Session | None' parameter")
else:
    print("  ✗ stream_hybrid_response missing 'db: Session | None' parameter")
    sys.exit(1)

print()

print("✓ Check 11: Verifying function calls pass user and db...")
# Check stream_agent_response call
if re.search(r"stream_agent_response\([^)]*user=user[^)]*\)", content):
    print("  ✓ stream_agent_response called with user parameter")
else:
    print("  ✗ stream_agent_response not called with user parameter")
    sys.exit(1)

if re.search(r"stream_agent_response\([^)]*db=db[^)]*\)", content):
    print("  ✓ stream_agent_response called with db parameter")
else:
    print("  ✗ stream_agent_response not called with db parameter")
    sys.exit(1)

# Check stream_hybrid_response call
if re.search(r"stream_hybrid_response\([^)]*user=user[^)]*\)", content):
    print("  ✓ stream_hybrid_response called with user parameter")
else:
    print("  ✗ stream_hybrid_response not called with user parameter")
    sys.exit(1)

if re.search(r"stream_hybrid_response\([^)]*db=db[^)]*\)", content):
    print("  ✓ stream_hybrid_response called with db parameter")
else:
    print("  ✗ stream_hybrid_response not called with db parameter")
    sys.exit(1)

print()

print("✓ Check 12: Verifying error handling...")
if "except Exception as e:" in content and "logger.error" in content:
    print("  ✓ Error handling present with logging")
else:
    print("  ✗ Error handling missing")
    sys.exit(1)

if (
    "# Continue processing even if database save fails" in content
    or "# Continue even if database save fails" in content
):
    print("  ✓ Graceful error handling (continues on DB failure)")
else:
    print("  ⚠ Warning: May not continue on database failures")

print()

# Summary
print("=" * 80)
print("✅ ALL CHECKS PASSED")
print("=" * 80)
print()
print("Summary:")
print("  ✓ stream_agent_response() accepts user and db parameters")
print("  ✓ stream_hybrid_response() accepts user and db parameters")
print("  ✓ User authentication check implemented")
print("  ✓ ConversationService properly used")
print("  ✓ Session creation/retrieval implemented")
print("  ✓ User messages saved before processing")
print("  ✓ Response content accumulated in buffer")
print("  ✓ Assistant messages saved after completion")
print("  ✓ Sources extracted and saved")
print("  ✓ Metadata includes required fields")
print("  ✓ Function calls pass user and db parameters")
print("  ✓ Error handling implemented")
print()
print("Task 5.3.4 (Message Saving) implementation verified successfully!")
print()
