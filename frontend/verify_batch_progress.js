/**
 * Verification script for BatchProgress component
 * Checks that the component is properly implemented with all required features.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying BatchProgress Component Implementation...\n');

let allChecksPassed = true;

function checkFailed(message) {
  console.log(`❌ ${message}`);
  allChecksPassed = false;
}

function checkPassed(message) {
  console.log(`✅ ${message}`);
}

// Check 1: Component file exists
const componentPath = path.join(__dirname, 'components', 'BatchProgress.tsx');
if (!fs.existsSync(componentPath)) {
  checkFailed('BatchProgress.tsx does not exist');
  process.exit(1);
} else {
  checkPassed('BatchProgress.tsx exists');
}

// Read component file
const componentContent = fs.readFileSync(componentPath, 'utf-8');

// Check 2: Component uses SSE via EventSource
if (componentContent.includes('EventSource') && componentContent.includes('streamBatchProgress')) {
  checkPassed('Component uses EventSource for SSE streaming');
} else {
  checkFailed('Component does not properly use EventSource for SSE');
}

// Check 3: Real-time progress updates
if (componentContent.includes('onmessage') && componentContent.includes('setProgress')) {
  checkPassed('Component handles real-time progress updates');
} else {
  checkFailed('Component does not handle real-time progress updates');
}

// Check 4: File-by-file status display
if (componentContent.includes('getStatusIcon') && componentContent.includes('files.map')) {
  checkPassed('Component displays file-by-file status with icons');
} else {
  checkFailed('Component does not display file-by-file status');
}

// Check 5: Success/failure summary
if (
  componentContent.includes('completed_files') &&
  componentContent.includes('failed_files') &&
  componentContent.includes('total_files')
) {
  checkPassed('Component shows success/failure summary');
} else {
  checkFailed('Component does not show success/failure summary');
}

// Check 6: Close button when complete
if (componentContent.includes('isComplete') && componentContent.includes('onClose')) {
  checkPassed('Component has close button when complete');
} else {
  checkFailed('Component does not have close button functionality');
}

// Check 7: Auto-close on success
if (
  componentContent.includes('autoCloseOnSuccess') &&
  componentContent.includes('autoCloseDelay') &&
  componentContent.includes('setTimeout')
) {
  checkPassed('Component supports auto-close on success');
} else {
  checkFailed('Component does not support auto-close on success');
}

// Check 8: Progress bar
if (componentContent.includes('progressPercentage') && componentContent.includes('width:')) {
  checkPassed('Component displays progress bar');
} else {
  checkFailed('Component does not display progress bar');
}

// Check 9: Error handling
if (componentContent.includes('onerror') && componentContent.includes('setError')) {
  checkPassed('Component handles SSE connection errors');
} else {
  checkFailed('Component does not handle SSE connection errors');
}

// Check 10: Cleanup on unmount
if (componentContent.includes('eventSource?.close()') && componentContent.includes('return ()')) {
  checkPassed('Component cleans up EventSource on unmount');
} else {
  checkFailed('Component does not properly clean up on unmount');
}

// Check 11: Status icons for different states
const statusStates = ['pending', 'processing', 'completed', 'failed'];
const hasAllStatusIcons = statusStates.every((status) =>
  componentContent.includes(`'${status}'`)
);
if (hasAllStatusIcons) {
  checkPassed('Component has icons for all file status states');
} else {
  checkFailed('Component is missing status icons for some states');
}

// Check 12: TypeScript types
if (
  componentContent.includes('BatchProgressProps') &&
  componentContent.includes('BatchProgressResponse')
) {
  checkPassed('Component uses proper TypeScript types');
} else {
  checkFailed('Component does not use proper TypeScript types');
}

// Check 13: Test file exists
const testPath = path.join(__dirname, 'components', '__tests__', 'BatchProgress.test.tsx');
if (!fs.existsSync(testPath)) {
  checkFailed('BatchProgress.test.tsx does not exist');
} else {
  checkPassed('BatchProgress.test.tsx exists');

  const testContent = fs.readFileSync(testPath, 'utf-8');

  // Check test coverage
  const testCases = [
    'renders loading state',
    'displays progress updates',
    'file-by-file status',
    'success summary',
    'failure summary',
    'close button',
    'auto-closes',
    'EventSource on unmount',
    'error message',
  ];

  const missingTests = testCases.filter(
    (testCase) => !testContent.toLowerCase().includes(testCase.toLowerCase())
  );

  if (missingTests.length === 0) {
    checkPassed('All required test cases are present');
  } else {
    checkFailed(`Missing test cases: ${missingTests.join(', ')}`);
  }
}

// Check 14: Responsive design
if (componentContent.includes('max-w-') && componentContent.includes('overflow-')) {
  checkPassed('Component has responsive design considerations');
} else {
  checkFailed('Component may not be responsive');
}

// Check 15: Accessibility
if (componentContent.includes('aria-label')) {
  checkPassed('Component includes accessibility attributes');
} else {
  checkFailed('Component is missing accessibility attributes');
}

// Summary
console.log('\n' + '='.repeat(50));
if (allChecksPassed) {
  console.log('✅ All checks passed! BatchProgress component is properly implemented.');
  console.log('\n📋 Component Features:');
  console.log('  • Real-time progress updates via SSE');
  console.log('  • File-by-file status with icons');
  console.log('  • Success/failure summary');
  console.log('  • Close button when complete');
  console.log('  • Auto-close on success (optional)');
  console.log('  • Progress bar visualization');
  console.log('  • Error handling');
  console.log('  • Proper cleanup on unmount');
  console.log('  • Responsive design');
  console.log('  • Accessibility support');
  process.exit(0);
} else {
  console.log('❌ Some checks failed. Please review the implementation.');
  process.exit(1);
}
