/**
 * Verify production features are properly integrated in UI
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Checking Production Features Integration in UI...\n');

let passed = 0;
let failed = 0;
let warnings = 0;

function checkFile(filepath, description) {
  if (fs.existsSync(filepath)) {
    console.log(`✓ ${description}`);
    passed++;
    return true;
  } else {
    console.log(`✗ ${description}`);
    console.log(`  Missing: ${filepath}`);
    failed++;
    return false;
  }
}

function checkFileContent(filepath, searchStrings, description) {
  if (!fs.existsSync(filepath)) {
    console.log(`✗ ${description} - File not found`);
    failed++;
    return false;
  }
  
  const content = fs.readFileSync(filepath, 'utf8');
  const missing = searchStrings.filter(str => !content.includes(str));
  
  if (missing.length === 0) {
    console.log(`✓ ${description}`);
    passed++;
    return true;
  } else {
    console.log(`✗ ${description}`);
    console.log(`  Missing: ${missing.join(', ')}`);
    failed++;
    return false;
  }
}

function warn(message) {
  console.log(`⚠ ${message}`);
  warnings++;
}

// 1. Health Check & Monitoring UI
console.log('\n=== 1. Health Check & Monitoring UI ===\n');

checkFile(
  'components/monitoring/SystemHealth.tsx',
  'System Health Component'
) || warn('Create SystemHealth component to display /health/detailed data');

checkFile(
  'components/monitoring/PerformanceMetrics.tsx',
  'Performance Metrics Component'
) || warn('Create PerformanceMetrics component to display /health/metrics data');

checkFile(
  'components/monitoring/ErrorSummary.tsx',
  'Error Summary Component'
) || warn('Create ErrorSummary component to display /health/errors data');

// 2. Security Features UI
console.log('\n=== 2. Security Features UI ===\n');

checkFile(
  'components/auth/PasswordStrengthIndicator.tsx',
  'Password Strength Indicator'
) || warn('Create PasswordStrengthIndicator for registration/password change');

checkFile(
  'components/auth/RateLimitWarning.tsx',
  'Rate Limit Warning Component'
) || warn('Create RateLimitWarning to show rate limit status');

// Check if RegisterForm uses validation
if (fs.existsSync('components/RegisterForm.tsx')) {
  checkFileContent(
    'components/RegisterForm.tsx',
    ['password', 'validation', 'error'],
    'RegisterForm has validation'
  );
}

// 3. Performance Indicators
console.log('\n=== 3. Performance Indicators ===\n');

checkFile(
  'components/ui/ResponseTimeIndicator.tsx',
  'Response Time Indicator'
) || warn('Create ResponseTimeIndicator to show X-Response-Time header');

checkFile(
  'components/ui/LoadingSpinner.tsx',
  'Loading Spinner with timeout'
) || warn('Create LoadingSpinner with performance tracking');

// 4. User Feedback Integration
console.log('\n=== 4. User Feedback Integration ===\n');

if (fs.existsSync('components/AnswerFeedback.tsx')) {
  checkFileContent(
    'components/AnswerFeedback.tsx',
    ['rating', 'feedback', 'submit'],
    'AnswerFeedback component functional'
  );
} else {
  warn('AnswerFeedback component should be integrated in MessageList');
}

// 5. Document Upload Security
console.log('\n=== 5. Document Upload Security ===\n');

if (fs.existsSync('components/DocumentUpload.tsx')) {
  checkFileContent(
    'components/DocumentUpload.tsx',
    ['accept', 'maxSize', 'validation'],
    'DocumentUpload has file validation'
  ) || warn('Add file type and size validation to DocumentUpload');
}

// 6. API Client Integration
console.log('\n=== 6. API Client Integration ===\n');

if (fs.existsSync('lib/api-client.ts')) {
  const apiClient = fs.readFileSync('lib/api-client.ts', 'utf8');
  
  // Check for health endpoints
  if (apiClient.includes('/health')) {
    console.log('✓ API Client has health check methods');
    passed++;
  } else {
    console.log('✗ API Client missing health check methods');
    failed++;
  }
  
  // Check for error handling
  if (apiClient.includes('catch') || apiClient.includes('error')) {
    console.log('✓ API Client has error handling');
    passed++;
  } else {
    console.log('✗ API Client missing error handling');
    failed++;
  }
  
  // Check for retry logic
  if (apiClient.includes('retry')) {
    console.log('✓ API Client has retry logic');
    passed++;
  } else {
    warn('Consider adding retry logic to API Client');
  }
}

// 7. User Dashboard Integration
console.log('\n=== 7. User Dashboard Integration ===\n');

if (fs.existsSync('components/UserDashboard.tsx')) {
  checkFileContent(
    'components/UserDashboard.tsx',
    ['usage', 'stats', 'documents'],
    'UserDashboard shows user statistics'
  );
}

if (fs.existsSync('app/dashboard/page.tsx')) {
  console.log('✓ Dashboard page exists');
  passed++;
} else {
  warn('Create dashboard page to show user metrics');
}

// 8. Error Boundaries
console.log('\n=== 8. Error Boundaries ===\n');

checkFile(
  'app/error.tsx',
  'Global Error Boundary'
);

checkFile(
  'components/ui/ErrorState.tsx',
  'Error State Component'
);

// 9. Loading States
console.log('\n=== 9. Loading States ===\n');

checkFile(
  'components/ui/LoadingState.tsx',
  'Loading State Component'
);

if (fs.existsSync('components/DocumentUploadProgress.tsx')) {
  console.log('✓ Document Upload Progress Component');
  passed++;
}

// 10. Notifications
console.log('\n=== 10. Notifications ===\n');

checkFile(
  'components/notifications/NotificationCenter.tsx',
  'Notification Center'
);

// Check if notifications are used for security events
if (fs.existsSync('components/notifications/NotificationCenter.tsx')) {
  const content = fs.readFileSync('components/notifications/NotificationCenter.tsx', 'utf8');
  if (content.includes('security') || content.includes('warning')) {
    console.log('✓ Notifications support security alerts');
    passed++;
  } else {
    warn('Add security alert support to NotificationCenter');
  }
}

// 11. Responsive Design
console.log('\n=== 11. Responsive Design ===\n');

if (fs.existsSync('lib/design-tokens.ts')) {
  console.log('✓ Design tokens defined');
  passed++;
}

// 12. Accessibility
console.log('\n=== 12. Accessibility ===\n');

if (fs.existsSync('lib/hooks/useAccessibility.ts')) {
  console.log('✓ Accessibility hook exists');
  passed++;
}

// Check for ARIA labels in key components
const componentsToCheck = [
  'components/Button.tsx',
  'components/DocumentUpload.tsx',
  'components/MessageList.tsx'
];

let ariaCount = 0;
componentsToCheck.forEach(comp => {
  if (fs.existsSync(comp)) {
    const content = fs.readFileSync(comp, 'utf8');
    if (content.includes('aria-') || content.includes('role=')) {
      ariaCount++;
    }
  }
});

if (ariaCount > 0) {
  console.log(`✓ ${ariaCount} components have ARIA attributes`);
  passed++;
} else {
  warn('Add ARIA attributes to components for accessibility');
}

// Summary
console.log('\n' + '='.repeat(60));
console.log('Summary');
console.log('='.repeat(60));
console.log(`Total Checks: ${passed + failed}`);
console.log(`✓ Passed: ${passed}`);
console.log(`✗ Failed: ${failed}`);
console.log(`⚠ Warnings: ${warnings}`);

const passRate = ((passed / (passed + failed)) * 100).toFixed(1);
console.log(`\nPass Rate: ${passRate}%`);

if (failed === 0 && warnings === 0) {
  console.log('\n✅ All production features are properly integrated!');
  process.exit(0);
} else if (failed === 0) {
  console.log('\n⚠️  All checks passed but there are recommendations');
  process.exit(0);
} else {
  console.log('\n❌ Some production features need integration');
  process.exit(1);
}
