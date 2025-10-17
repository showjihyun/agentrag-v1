#!/usr/bin/env node

/**
 * UI Enhancements Verification Script
 * 
 * Verifies Phase 1 UI enhancements:
 * 1. QueryComplexityIndicator component
 * 2. ChatInterface integration
 * 3. MessageSearch component
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying UI Enhancements (Phase 1)...\n');

let allChecksPassed = true;
const results = [];

// Helper function to check file exists
function checkFileExists(filePath, description) {
  const fullPath = path.join(__dirname, filePath);
  const exists = fs.existsSync(fullPath);
  
  results.push({
    check: description,
    passed: exists,
    message: exists ? `✅ ${description}` : `❌ ${description} - File not found`
  });
  
  if (!exists) allChecksPassed = false;
  return exists;
}

// Helper function to check file contains text
function checkFileContains(filePath, searchTexts, description) {
  const fullPath = path.join(__dirname, filePath);
  
  if (!fs.existsSync(fullPath)) {
    results.push({
      check: description,
      passed: false,
      message: `❌ ${description} - File not found`
    });
    allChecksPassed = false;
    return false;
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  const missingTexts = searchTexts.filter(text => !content.includes(text));
  
  if (missingTexts.length === 0) {
    results.push({
      check: description,
      passed: true,
      message: `✅ ${description}`
    });
    return true;
  } else {
    results.push({
      check: description,
      passed: false,
      message: `❌ ${description} - Missing: ${missingTexts.join(', ')}`
    });
    allChecksPassed = false;
    return false;
  }
}

console.log('📋 Phase 1: High Priority UI Enhancements\n');

// Check 1: QueryComplexityIndicator component
console.log('1️⃣ Query Complexity Indicator\n');

checkFileExists(
  'components/QueryComplexityIndicator.tsx',
  'QueryComplexityIndicator component exists'
);

checkFileContains(
  'components/QueryComplexityIndicator.tsx',
  [
    'analyzeQueryComplexity',
    'complexity',
    'estimated_time',
    'recommended_mode',
    'simple',
    'moderate',
    'complex'
  ],
  'QueryComplexityIndicator has all required features'
);

// Check 2: ChatInterface integration
console.log('\n2️⃣ ChatInterface Integration\n');

checkFileContains(
  'components/ChatInterface.tsx',
  [
    'QueryComplexityIndicator',
    'import QueryComplexityIndicator'
  ],
  'ChatInterface imports QueryComplexityIndicator'
);

checkFileContains(
  'components/ChatInterface.tsx',
  [
    '<QueryComplexityIndicator',
    'query={input}',
    'onAnalysisComplete'
  ],
  'ChatInterface uses QueryComplexityIndicator'
);

// Check 3: MessageSearch component
console.log('\n3️⃣ Message Search Component\n');

checkFileExists(
  'components/MessageSearch.tsx',
  'MessageSearch component exists'
);

checkFileContains(
  'components/MessageSearch.tsx',
  [
    'searchMessages',
    'Search Messages',
    'handleResultClick',
    'router.push',
    'session_id'
  ],
  'MessageSearch has all required features'
);

// Print results
console.log('\n' + '='.repeat(70));
console.log('📊 VERIFICATION RESULTS');
console.log('='.repeat(70) + '\n');

results.forEach(result => {
  console.log(result.message);
});

console.log('\n' + '='.repeat(70));

if (allChecksPassed) {
  console.log('✅ ALL CHECKS PASSED!');
  console.log('='.repeat(70));
  console.log('\n🎉 Phase 1 UI Enhancements Complete!\n');
  console.log('Components created:');
  console.log('  ✅ QueryComplexityIndicator - Shows query complexity analysis');
  console.log('  ✅ ChatInterface - Integrated with complexity indicator');
  console.log('  ✅ MessageSearch - Global message search');
  console.log('\n📝 Next steps:');
  console.log('  1. Test QueryComplexityIndicator in browser');
  console.log('  2. Verify complexity analysis works');
  console.log('  3. Test MessageSearch functionality');
  console.log('  4. Integrate MessageSearch in ConversationHistory');
  console.log('  5. User testing and feedback');
  console.log('\n🚀 Ready for Phase 2 implementation!\n');
  process.exit(0);
} else {
  console.log('❌ SOME CHECKS FAILED');
  console.log('='.repeat(70));
  console.log('\n⚠️  Please review the failed checks above.\n');
  process.exit(1);
}
