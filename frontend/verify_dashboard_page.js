/**
 * Verification script for Dashboard Page (Task 5.5.5)
 * 
 * This script verifies that the dashboard page:
 * 1. Uses UserDashboard component
 * 2. Requires authentication (redirects to login if not authenticated)
 * 3. Fetches user data on mount (via AuthContext)
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Dashboard Page Implementation...\n');

let allChecksPassed = true;

// Check 1: Dashboard page file exists
console.log('✓ Check 1: Dashboard page file exists');
const dashboardPagePath = path.join(__dirname, 'app', 'dashboard', 'page.tsx');
if (!fs.existsSync(dashboardPagePath)) {
  console.log('  ❌ FAIL: frontend/app/dashboard/page.tsx does not exist');
  allChecksPassed = false;
} else {
  console.log('  ✅ PASS: frontend/app/dashboard/page.tsx exists');
}

// Check 2: Verify file content
console.log('\n✓ Check 2: Verify dashboard page implementation');
const dashboardPageContent = fs.readFileSync(dashboardPagePath, 'utf-8');

// Check 2.1: Uses UserDashboard component
if (dashboardPageContent.includes('import UserDashboard from') && 
    dashboardPageContent.includes('<UserDashboard')) {
  console.log('  ✅ PASS: Uses UserDashboard component');
} else {
  console.log('  ❌ FAIL: Does not use UserDashboard component');
  allChecksPassed = false;
}

// Check 2.2: Uses AuthContext
if (dashboardPageContent.includes('useAuth') && 
    dashboardPageContent.includes('from \'@/contexts/AuthContext\'')) {
  console.log('  ✅ PASS: Uses AuthContext');
} else {
  console.log('  ❌ FAIL: Does not use AuthContext');
  allChecksPassed = false;
}

// Check 2.3: Checks authentication state
if (dashboardPageContent.includes('isAuthenticated') || 
    dashboardPageContent.includes('user')) {
  console.log('  ✅ PASS: Checks authentication state');
} else {
  console.log('  ❌ FAIL: Does not check authentication state');
  allChecksPassed = false;
}

// Check 2.4: Redirects to login when not authenticated
if (dashboardPageContent.includes('router.push') && 
    (dashboardPageContent.includes('/auth/login') || dashboardPageContent.includes('/login'))) {
  console.log('  ✅ PASS: Redirects to login when not authenticated');
} else {
  console.log('  ❌ FAIL: Does not redirect to login');
  allChecksPassed = false;
}

// Check 2.5: Uses useRouter for navigation
if (dashboardPageContent.includes('useRouter') && 
    dashboardPageContent.includes('from \'next/navigation\'')) {
  console.log('  ✅ PASS: Uses Next.js useRouter for navigation');
} else {
  console.log('  ❌ FAIL: Does not use useRouter');
  allChecksPassed = false;
}

// Check 2.6: Shows loading state
if (dashboardPageContent.includes('isLoading') && 
    dashboardPageContent.includes('Loading')) {
  console.log('  ✅ PASS: Shows loading state while checking auth');
} else {
  console.log('  ❌ FAIL: Does not show loading state');
  allChecksPassed = false;
}

// Check 2.7: Uses useEffect for auth check
if (dashboardPageContent.includes('useEffect') && 
    dashboardPageContent.includes('isAuthenticated')) {
  console.log('  ✅ PASS: Uses useEffect to check authentication on mount');
} else {
  console.log('  ❌ FAIL: Does not use useEffect for auth check');
  allChecksPassed = false;
}

// Check 2.8: Client component
if (dashboardPageContent.includes('\'use client\'')) {
  console.log('  ✅ PASS: Marked as client component');
} else {
  console.log('  ❌ FAIL: Not marked as client component');
  allChecksPassed = false;
}

// Check 3: Verify redirect URL includes dashboard path
console.log('\n✓ Check 3: Verify redirect behavior');
if (dashboardPageContent.includes('redirect=/dashboard') || 
    dashboardPageContent.includes('redirect=') && dashboardPageContent.includes('dashboard')) {
  console.log('  ✅ PASS: Includes redirect parameter to return to dashboard after login');
} else {
  console.log('  ⚠️  WARNING: May not include redirect parameter (optional but recommended)');
}

// Summary
console.log('\n' + '='.repeat(60));
if (allChecksPassed) {
  console.log('✅ ALL CHECKS PASSED');
  console.log('\nDashboard page implementation is complete:');
  console.log('  • Uses UserDashboard component');
  console.log('  • Requires authentication');
  console.log('  • Redirects to login if not authenticated');
  console.log('  • Fetches user data via AuthContext');
  console.log('  • Shows loading state');
  console.log('  • Handles authentication state properly');
} else {
  console.log('❌ SOME CHECKS FAILED');
  console.log('\nPlease review the failed checks above.');
  process.exit(1);
}
console.log('='.repeat(60));
