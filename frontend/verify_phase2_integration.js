const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Phase 2 Integration...\n');

const checks = [];

// Check 1: ConversationHistory component
const conversationHistoryPath = path.join(__dirname, 'components', 'ConversationHistory.tsx');
if (fs.existsSync(conversationHistoryPath)) {
  const content = fs.readFileSync(conversationHistoryPath, 'utf-8');
  
  checks.push({
    name: 'ConversationHistory file exists',
    pass: true,
    details: 'File found at components/ConversationHistory.tsx'
  });
  
  checks.push({
    name: 'ConversationHistory imports MessageSearch',
    pass: content.includes('import MessageSearch') || content.includes('from \'./MessageSearch\'') || content.includes('from "./MessageSearch"'),
    details: 'Should import MessageSearch component'
  });
  
  checks.push({
    name: 'ConversationHistory has search state',
    pass: content.includes('showSearch') || content.includes('searchOpen') || content.includes('isSearchOpen') || content.includes('showMessageSearch'),
    details: 'Should have state for search modal visibility'
  });
  
  checks.push({
    name: 'ConversationHistory has search button',
    pass: content.includes('🔍') || (content.includes('Search') && content.includes('button')),
    details: 'Should have search button in UI'
  });
  
  checks.push({
    name: 'ConversationHistory renders MessageSearch',
    pass: content.includes('<MessageSearch') || content.includes('MessageSearch'),
    details: 'Should render MessageSearch component'
  });
} else {
  checks.push({
    name: 'ConversationHistory file exists',
    pass: false,
    details: 'File not found at components/ConversationHistory.tsx'
  });
}

// Check 2: MessageSearch component
const messageSearchPath = path.join(__dirname, 'components', 'MessageSearch.tsx');
if (fs.existsSync(messageSearchPath)) {
  const content = fs.readFileSync(messageSearchPath, 'utf-8');
  
  checks.push({
    name: 'MessageSearch file exists',
    pass: true,
    details: 'File found at components/MessageSearch.tsx'
  });
  
  checks.push({
    name: 'MessageSearch has onClose prop',
    pass: content.includes('onClose'),
    details: 'Should accept onClose callback prop'
  });
  
  checks.push({
    name: 'MessageSearch has close button',
    pass: content.includes('✕') || content.includes('×') || (content.includes('Close') && content.includes('button')),
    details: 'Should have close button in UI'
  });
  
  checks.push({
    name: 'MessageSearch has search input',
    pass: content.includes('input') && (content.includes('search') || content.includes('Search')),
    details: 'Should have search input field'
  });
  
  checks.push({
    name: 'MessageSearch uses apiClient.searchMessages',
    pass: content.includes('searchMessages'),
    details: 'Should call apiClient.searchMessages()'
  });
  
  checks.push({
    name: 'MessageSearch handles navigation',
    pass: content.includes('useRouter') || content.includes('router.push'),
    details: 'Should navigate to conversation on result click'
  });
} else {
  checks.push({
    name: 'MessageSearch file exists',
    pass: false,
    details: 'File not found at components/MessageSearch.tsx'
  });
}

// Check 3: QueryComplexityIndicator component
const complexityIndicatorPath = path.join(__dirname, 'components', 'QueryComplexityIndicator.tsx');
if (fs.existsSync(complexityIndicatorPath)) {
  const content = fs.readFileSync(complexityIndicatorPath, 'utf-8');
  
  checks.push({
    name: 'QueryComplexityIndicator file exists',
    pass: true,
    details: 'File found at components/QueryComplexityIndicator.tsx'
  });
  
  checks.push({
    name: 'QueryComplexityIndicator uses apiClient',
    pass: content.includes('analyzeQueryComplexity'),
    details: 'Should call apiClient.analyzeQueryComplexity()'
  });
  
  checks.push({
    name: 'QueryComplexityIndicator has debouncing',
    pass: content.includes('useDebounce') || content.includes('setTimeout') || content.includes('debounce'),
    details: 'Should debounce API calls'
  });
  
  checks.push({
    name: 'QueryComplexityIndicator shows complexity',
    pass: content.includes('complexity') && (content.includes('simple') || content.includes('moderate') || content.includes('complex')),
    details: 'Should display complexity level'
  });
} else {
  checks.push({
    name: 'QueryComplexityIndicator file exists',
    pass: false,
    details: 'File not found at components/QueryComplexityIndicator.tsx'
  });
}

// Check 4: ChatInterface integration
const chatInterfacePath = path.join(__dirname, 'components', 'ChatInterface.tsx');
if (fs.existsSync(chatInterfacePath)) {
  const content = fs.readFileSync(chatInterfacePath, 'utf-8');
  
  checks.push({
    name: 'ChatInterface imports QueryComplexityIndicator',
    pass: content.includes('QueryComplexityIndicator'),
    details: 'Should import QueryComplexityIndicator'
  });
  
  checks.push({
    name: 'ChatInterface uses QueryComplexityIndicator',
    pass: content.includes('<QueryComplexityIndicator'),
    details: 'Should render QueryComplexityIndicator'
  });
} else {
  checks.push({
    name: 'ChatInterface file exists',
    pass: false,
    details: 'File not found at components/ChatInterface.tsx'
  });
}

// Check 5: API client has new methods
const apiClientPath = path.join(__dirname, 'lib', 'api-client.ts');
if (fs.existsSync(apiClientPath)) {
  const content = fs.readFileSync(apiClientPath, 'utf-8');
  
  checks.push({
    name: 'API client has searchMessages method',
    pass: content.includes('searchMessages'),
    details: 'Should have searchMessages() method'
  });
  
  checks.push({
    name: 'API client has analyzeQueryComplexity method',
    pass: content.includes('analyzeQueryComplexity'),
    details: 'Should have analyzeQueryComplexity() method'
  });
  
  checks.push({
    name: 'API client has queryAutoMode method',
    pass: content.includes('queryAutoMode'),
    details: 'Should have queryAutoMode() method'
  });
} else {
  checks.push({
    name: 'API client file exists',
    pass: false,
    details: 'File not found at lib/api-client.ts'
  });
}

// Print results
console.log('📋 Verification Results:\n');

let passCount = 0;
let failCount = 0;

checks.forEach((check, index) => {
  const icon = check.pass ? '✅' : '❌';
  const status = check.pass ? 'PASS' : 'FAIL';
  
  console.log(`${icon} ${check.name}`);
  if (!check.pass || process.env.VERBOSE) {
    console.log(`   ${check.details}`);
  }
  
  if (check.pass) passCount++;
  else failCount++;
});

console.log('\n' + '='.repeat(60));
console.log(`📊 Results: ${passCount} passed, ${failCount} failed`);
console.log('='.repeat(60));

if (failCount === 0) {
  console.log('\n✅ ALL CHECKS PASSED!');
  console.log('🎉 Phase 2 Integration Complete!');
  console.log('\n📝 Next Steps:');
  console.log('   1. Start backend: cd backend && uvicorn main:app --reload');
  console.log('   2. Start frontend: cd frontend && npm run dev');
  console.log('   3. Test in browser: http://localhost:3000');
  console.log('   4. Follow USER_TESTING_PHASE2_INTEGRATION_PLAN.md');
} else {
  console.log('\n❌ SOME CHECKS FAILED');
  console.log('Please review the failed checks above and fix the issues.');
  console.log('\n📝 Common Issues:');
  console.log('   - Missing component files');
  console.log('   - Missing imports');
  console.log('   - Missing integration in parent components');
  console.log('   - Missing API client methods');
}

console.log('\n' + '='.repeat(60));

process.exit(failCount === 0 ? 0 : 1);
