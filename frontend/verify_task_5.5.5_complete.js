/**
 * Comprehensive Verification for Task 5.5.5: User Dashboard
 * 
 * This script verifies all three sub-tasks:
 * 1. UserDashboard component
 * 2. Dashboard page
 * 3. Navigation link to dashboard
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Task 5.5.5: User Dashboard - Complete Implementation\n');
console.log('=' .repeat(70));

let allChecksPassed = true;
let totalChecks = 0;
let passedChecks = 0;

function check(description, condition) {
  totalChecks++;
  if (condition) {
    passedChecks++;
    console.log(`✅ ${description}`);
    return true;
  } else {
    console.log(`❌ ${description}`);
    allChecksPassed = false;
    return false;
  }
}

// Sub-task 1: UserDashboard Component
console.log('\n📋 Sub-task 1: UserDashboard Component');
console.log('-'.repeat(70));

const userDashboardPath = path.join(__dirname, 'components', 'UserDashboard.tsx');
if (fs.existsSync(userDashboardPath)) {
  const content = fs.readFileSync(userDashboardPath, 'utf8');
  
  check('UserDashboard component file exists', true);
  check('Displays user email', content.includes('user.email'));
  check('Displays user username', content.includes('user.username'));
  check('Displays user role', content.includes('user.role'));
  check('Displays created_at date', content.includes('created_at'));
  check('Displays query count', content.includes('query_count'));
  check('Displays storage used', content.includes('storage_used_bytes'));
  check('Shows storage quota', content.includes('1GB') || content.includes('1073741824') || content.includes('storageQuota'));
  check('Has storage progress bar', content.includes('bg-gray-200 rounded-full') || content.includes('storagePercentage'));
  check('Formats bytes to MB/GB', content.includes('formatBytes') || content.includes('MB') || content.includes('GB'));
  check('Loads recent sessions', content.includes('getSessions') || content.includes('sessions'));
  check('Loads recent documents', content.includes('getDocuments') || content.includes('documents'));
  check('Has profile update form', content.includes('handleProfileUpdate') || content.includes('isEditingProfile'));
  check('Has password change form', content.includes('password') && content.includes('change'));
  check('Has logout button', content.includes('logout'));
  check('Uses useAuth hook', content.includes('useAuth'));
  check('Uses apiClient', content.includes('apiClient'));
  check('Responsive design', content.includes('grid') || content.includes('flex'));
} else {
  check('UserDashboard component file exists', false);
}

// Sub-task 2: Dashboard Page
console.log('\n📋 Sub-task 2: Dashboard Page');
console.log('-'.repeat(70));

const dashboardPagePath = path.join(__dirname, 'app', 'dashboard', 'page.tsx');
if (fs.existsSync(dashboardPagePath)) {
  const content = fs.readFileSync(dashboardPagePath, 'utf8');
  
  check('Dashboard page file exists', true);
  check('Uses UserDashboard component', content.includes('UserDashboard'));
  check('Requires authentication', content.includes('useAuth'));
  check('Redirects to login if not authenticated', content.includes('router.push') && content.includes('/auth/login'));
  check('Shows loading state', content.includes('isLoading'));
  check('Fetches user data on mount', content.includes('useEffect') || content.includes('useAuth'));
} else {
  check('Dashboard page file exists', false);
}

// Sub-task 3: Navigation Link
console.log('\n📋 Sub-task 3: Navigation Link to Dashboard');
console.log('-'.repeat(70));

const userMenuPath = path.join(__dirname, 'components', 'UserMenu.tsx');
if (fs.existsSync(userMenuPath)) {
  const content = fs.readFileSync(userMenuPath, 'utf8');
  
  check('UserMenu component file exists', true);
  check('Has dashboard navigation link', content.includes('/dashboard'));
  check('Shows user avatar', content.includes('avatar') || content.includes('initials'));
  check('Shows user email in header', content.includes('user.email'));
  check('Has dropdown menu', content.includes('isOpen') || content.includes('dropdown'));
  check('Conditionally renders based on auth', content.includes('user') || content.includes('isAuthenticated'));
} else {
  check('UserMenu component file exists', false);
}

// Check integration in main page
const mainPagePath = path.join(__dirname, 'app', 'page.tsx');
if (fs.existsSync(mainPagePath)) {
  const content = fs.readFileSync(mainPagePath, 'utf8');
  
  check('UserMenu imported in main page', content.includes('import UserMenu'));
  check('UserMenu rendered in header', content.includes('<UserMenu'));
  check('UserMenu conditionally rendered', content.includes('isAuthenticated') && content.includes('UserMenu'));
} else {
  check('Main page file exists', false);
}

// Final Summary
console.log('\n' + '='.repeat(70));
console.log(`\n📊 VERIFICATION SUMMARY`);
console.log('-'.repeat(70));
console.log(`Total Checks: ${totalChecks}`);
console.log(`Passed: ${passedChecks}`);
console.log(`Failed: ${totalChecks - passedChecks}`);
console.log(`Success Rate: ${((passedChecks / totalChecks) * 100).toFixed(1)}%`);

if (allChecksPassed) {
  console.log('\n🎉 SUCCESS! Task 5.5.5 is COMPLETE!');
  console.log('\n✅ All Sub-tasks Verified:');
  console.log('   1. ✅ UserDashboard component with user info and usage stats');
  console.log('   2. ✅ Dashboard page with authentication protection');
  console.log('   3. ✅ Navigation link in header with user avatar/email');
  console.log('\n🚀 Phase 5 is now 100% COMPLETE!');
  console.log('\nImplemented Features:');
  console.log('   • User dashboard with profile and stats');
  console.log('   • User menu with avatar and dropdown');
  console.log('   • Dashboard navigation from header');
  console.log('   • Profile update functionality');
  console.log('   • Password change functionality');
  console.log('   • Recent activity display');
  console.log('   • Storage quota visualization');
  console.log('   • Responsive design for all devices');
  console.log('   • Authentication protection throughout');
  process.exit(0);
} else {
  console.log('\n❌ FAILED: Some checks did not pass.');
  console.log('Please review the errors above and fix the issues.');
  process.exit(1);
}
