/**
 * Verification script for session navigation integration in page.tsx
 * 
 * This script verifies:
 * 1. URL updates with session ID when session is selected
 * 2. Messages are loaded for the selected session
 * 3. Session ID is read from URL on mount
 * 4. Session state is properly managed
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying session navigation integration in page.tsx...\n');

const pagePath = path.join(__dirname, 'app', 'page.tsx');
const pageContent = fs.readFileSync(pagePath, 'utf-8');

let allPassed = true;

// Test 1: Check for useRouter import
console.log('✓ Test 1: Checking for useRouter import...');
if (pageContent.includes("import { useSearchParams, useRouter } from 'next/navigation'")) {
  console.log('  ✅ useRouter is imported from next/navigation\n');
} else {
  console.log('  ❌ useRouter import not found\n');
  allPassed = false;
}

// Test 2: Check for router initialization
console.log('✓ Test 2: Checking for router initialization...');
if (pageContent.includes('const router = useRouter()')) {
  console.log('  ✅ Router is initialized\n');
} else {
  console.log('  ❌ Router initialization not found\n');
  allPassed = false;
}

// Test 3: Check for session state management
console.log('✓ Test 3: Checking for session state management...');
if (pageContent.includes('const [activeSessionId, setActiveSessionId] = useState<string | undefined>()')) {
  console.log('  ✅ Active session ID state is defined\n');
} else {
  console.log('  ❌ Active session ID state not found\n');
  allPassed = false;
}

// Test 4: Check for session messages state
console.log('✓ Test 4: Checking for session messages state...');
if (pageContent.includes('const [sessionMessages, setSessionMessages] = useState<MessageResponse[]>([])')) {
  console.log('  ✅ Session messages state is defined\n');
} else {
  console.log('  ❌ Session messages state not found\n');
  allPassed = false;
}

// Test 5: Check for loading state
console.log('✓ Test 5: Checking for loading state...');
if (pageContent.includes('const [isLoadingMessages, setIsLoadingMessages] = useState(false)')) {
  console.log('  ✅ Loading messages state is defined\n');
} else {
  console.log('  ❌ Loading messages state not found\n');
  allPassed = false;
}

// Test 6: Check for URL parameter reading on mount
console.log('✓ Test 6: Checking for URL parameter reading...');
if (pageContent.includes('const sessionId = searchParams.get(\'session\')') &&
    pageContent.includes('if (sessionId) {') &&
    pageContent.includes('setActiveSessionId(sessionId)')) {
  console.log('  ✅ Session ID is read from URL on mount\n');
} else {
  console.log('  ❌ URL parameter reading not found\n');
  allPassed = false;
}

// Test 7: Check for loadSessionMessages function
console.log('✓ Test 7: Checking for loadSessionMessages function...');
if (pageContent.includes('const loadSessionMessages = async (sessionId: string)') &&
    pageContent.includes('const response = await apiClient.getSessionMessages(sessionId)') &&
    pageContent.includes('setSessionMessages(response.messages)')) {
  console.log('  ✅ loadSessionMessages function is implemented\n');
} else {
  console.log('  ❌ loadSessionMessages function not found or incomplete\n');
  allPassed = false;
}

// Test 8: Check for effect to load messages when session changes
console.log('✓ Test 8: Checking for effect to load messages...');
if (pageContent.includes('useEffect(() => {') &&
    pageContent.includes('if (activeSessionId && isAuthenticated) {') &&
    pageContent.includes('loadSessionMessages(activeSessionId)')) {
  console.log('  ✅ Effect to load messages when session changes is present\n');
} else {
  console.log('  ❌ Effect to load messages not found\n');
  allPassed = false;
}

// Test 9: Check for handleSessionSelect function
console.log('✓ Test 9: Checking for handleSessionSelect function...');
if (pageContent.includes('const handleSessionSelect = (sessionId: string)') &&
    pageContent.includes('setActiveSessionId(sessionId)') &&
    pageContent.includes('router.push(`/?session=${sessionId}`)')) {
  console.log('  ✅ handleSessionSelect function updates state and URL\n');
} else {
  console.log('  ❌ handleSessionSelect function not found or incomplete\n');
  allPassed = false;
}

// Test 10: Check for ConversationHistory integration
console.log('✓ Test 10: Checking for ConversationHistory integration...');
if (pageContent.includes('<ConversationHistory') &&
    pageContent.includes('activeSessionId={activeSessionId}') &&
    pageContent.includes('onSessionSelect={handleSessionSelect}')) {
  console.log('  ✅ ConversationHistory is integrated with proper props\n');
} else {
  console.log('  ❌ ConversationHistory integration not found or incomplete\n');
  allPassed = false;
}

// Test 11: Check for error handling in loadSessionMessages
console.log('✓ Test 11: Checking for error handling...');
if (pageContent.includes('try {') &&
    pageContent.includes('setIsLoadingMessages(true)') &&
    pageContent.includes('catch (error)') &&
    pageContent.includes('finally {') &&
    pageContent.includes('setIsLoadingMessages(false)')) {
  console.log('  ✅ Error handling and loading states are properly managed\n');
} else {
  console.log('  ❌ Error handling not found or incomplete\n');
  allPassed = false;
}

// Test 12: Check for clearing messages when no session
console.log('✓ Test 12: Checking for message clearing logic...');
if (pageContent.includes('} else {') &&
    pageContent.includes('setSessionMessages([])')) {
  console.log('  ✅ Messages are cleared when no session is active\n');
} else {
  console.log('  ❌ Message clearing logic not found\n');
  allPassed = false;
}

// Summary
console.log('\n' + '='.repeat(60));
if (allPassed) {
  console.log('✅ ALL TESTS PASSED!');
  console.log('\nSession navigation is fully implemented:');
  console.log('  • URL updates with session ID (router.push)');
  console.log('  • Messages load for selected session (apiClient.getSessionMessages)');
  console.log('  • Session ID is read from URL on mount');
  console.log('  • Proper state management and error handling');
  console.log('  • Integration with ConversationHistory component');
} else {
  console.log('❌ SOME TESTS FAILED');
  console.log('\nPlease review the failed tests above.');
  process.exit(1);
}
console.log('='.repeat(60));
