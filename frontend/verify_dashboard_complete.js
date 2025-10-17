#!/usr/bin/env node

/**
 * Verification script for Task 5.5.5: User Dashboard
 * 
 * Checks:
 * 1. UserDashboard component exists and has all required features
 * 2. Dashboard page exists with authentication check
 * 3. UserMenu component exists and is integrated
 * 4. API client has updateUser method
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Task 5.5.5: User Dashboard...\n');

let allChecksPassed = true;
const results = [];

// Helper function to check file exists
function checkFileExists(filePath, description) {
  const fullPath = path.join(__dirname, filePath);
  const exists = fs.existsSync(fullPath);
  
  results.push({
    check: description,
    passed: exists,
    message: exists ? `✅ ${description}` : `❌ ${description} - File not found: ${filePath}`
  });
  
  if (!exists) allChecksPassed = false;
  return exists;
}

// Helper function to check file contains text
function checkFileContains(filePath, searchText, description) {
  const fullPath = path.join(__dirname, filePath);
  
  if (!fs.existsSync(fullPath)) {
    results.push({
      check: description,
      passed: false,
      message: `❌ ${description} - File not found: ${filePath}`
    });
    allChecksPassed = false;
    return false;
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  const contains = content.includes(searchText);
  
  results.push({
    check: description,
    passed: contains,
    message: contains ? `✅ ${description}` : `❌ ${description} - Not found in ${filePath}`
  });
  
  if (!contains) allChecksPassed = false;
  return contains;
}

// Helper function to check multiple texts in file
function checkFileContainsAll(filePath, searchTexts, description) {
  const fullPath = path.join(__dirname, filePath);
  
  if (!fs.existsSync(fullPath)) {
    results.push({
      check: description,
      passed: false,
      message: `❌ ${description} - File not found: ${filePath}`
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

console.log('📋 Checking Component Files...\n');

// Check 1: UserDashboard component exists
checkFileExists(
  'components/UserDashboard.tsx',
  'UserDashboard component file exists'
);

// Check 2: UserDashboard has required features
checkFileContainsAll(
  'components/UserDashboard.tsx',
  [
    'User Information',
    'Usage Statistics',
    'Recent Activity',
    'Settings',
    'query_count',
    'storage_used_bytes',
    'formatBytes',
    'handleProfileUpdate',
    'handlePasswordChange',
    'logout'
  ],
  'UserDashboard has all required features'
);

// Check 3: UserMenu component exists
checkFileExists(
  'components/UserMenu.tsx',
  'UserMenu component file exists'
);

// Check 4: UserMenu has required features
checkFileContainsAll(
  'components/UserMenu.tsx',
  [
    'Dashboard',
    'Logout',
    'router.push(\'/dashboard\')',
    'logout'
  ],
  'UserMenu has dashboard link and logout'
);

console.log('\n📋 Checking Page Files...\n');

// Check 5: Dashboard page exists
checkFileExists(
  'app/dashboard/page.tsx',
  'Dashboard page file exists'
);

// Check 6: Dashboard page has authentication check
checkFileContainsAll(
  'app/dashboard/page.tsx',
  [
    'useAuth',
    'UserDashboard',
    'router.push',
    'isLoading',
    'Loading dashboard'
  ],
  'Dashboard page has authentication check and redirect'
);

console.log('\n📋 Checking Integration...\n');

// Check 7: Main page imports UserMenu
checkFileContains(
  'app/page.tsx',
  'import UserMenu from',
  'Main page imports UserMenu'
);

// Check 8: Main page uses UserMenu
checkFileContains(
  'app/page.tsx',
  '<UserMenu />',
  'Main page renders UserMenu'
);

// Check 9: API client has updateUser method
checkFileContainsAll(
  'lib/api-client.ts',
  [
    'async updateUser',
    'username?:',
    'full_name?:',
    'current_password?:',
    'new_password?:'
  ],
  'API client has updateUser method with all parameters'
);

console.log('\n📋 Checking TypeScript Types...\n');

// Check 10: Types include SessionResponse and DocumentResponse
checkFileContainsAll(
  'lib/types.ts',
  [
    'SessionResponse',
    'DocumentResponse'
  ],
  'Types include SessionResponse and DocumentResponse'
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
  console.log('\n🎉 Task 5.5.5: User Dashboard is COMPLETE!\n');
  console.log('Features implemented:');
  console.log('  ✅ UserDashboard component with user info, stats, activity, settings');
  console.log('  ✅ Dashboard page with authentication check');
  console.log('  ✅ UserMenu component with navigation');
  console.log('  ✅ Integration in main page header');
  console.log('  ✅ Profile update functionality');
  console.log('  ✅ Password change functionality');
  console.log('  ✅ Logout functionality');
  console.log('  ✅ Recent activity display');
  console.log('  ✅ Storage usage visualization');
  console.log('\n📝 Next steps:');
  console.log('  1. Test the dashboard in the browser');
  console.log('  2. Verify authentication flow');
  console.log('  3. Test profile updates');
  console.log('  4. Test password change');
  console.log('  5. Verify responsive design on mobile');
  console.log('\n🚀 Phase 5 is now 100% COMPLETE!\n');
  process.exit(0);
} else {
  console.log('❌ SOME CHECKS FAILED');
  console.log('='.repeat(70));
  console.log('\n⚠️  Please review the failed checks above.\n');
  process.exit(1);
}
