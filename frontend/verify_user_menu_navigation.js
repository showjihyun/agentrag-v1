/**
 * Verification script for User Menu Navigation
 * 
 * This script verifies that:
 * 1. UserMenu component exists and has dashboard navigation
 * 2. UserMenu is integrated in the main page header
 * 3. Dashboard page exists and is accessible
 * 4. User avatar/email is displayed when authenticated
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying User Menu Navigation Implementation...\n');

let allChecksPassed = true;

// Check 1: Verify UserMenu component exists
console.log('✓ Check 1: UserMenu component exists');
const userMenuPath = path.join(__dirname, 'components', 'UserMenu.tsx');
if (!fs.existsSync(userMenuPath)) {
  console.error('❌ UserMenu.tsx not found');
  allChecksPassed = false;
} else {
  const userMenuContent = fs.readFileSync(userMenuPath, 'utf8');
  
  // Check for dashboard navigation
  if (!userMenuContent.includes('router.push(\'/dashboard\')')) {
    console.error('❌ Dashboard navigation not found in UserMenu');
    allChecksPassed = false;
  } else {
    console.log('  ✓ Dashboard navigation implemented');
  }
  
  // Check for user avatar
  if (!userMenuContent.includes('getInitials')) {
    console.error('❌ User avatar/initials not found');
    allChecksPassed = false;
  } else {
    console.log('  ✓ User avatar with initials implemented');
  }
  
  // Check for user email display
  if (!userMenuContent.includes('user.email')) {
    console.error('❌ User email display not found');
    allChecksPassed = false;
  } else {
    console.log('  ✓ User email display implemented');
  }
  
  // Check for dropdown menu
  if (!userMenuContent.includes('isOpen')) {
    console.error('❌ Dropdown menu state not found');
    allChecksPassed = false;
  } else {
    console.log('  ✓ Dropdown menu functionality implemented');
  }
  
  // Check for logout functionality
  if (!userMenuContent.includes('logout')) {
    console.error('❌ Logout functionality not found');
    allChecksPassed = false;
  } else {
    console.log('  ✓ Logout functionality implemented');
  }
}

// Check 2: Verify UserMenu is integrated in main page
console.log('\n✓ Check 2: UserMenu integrated in main page header');
const mainPagePath = path.join(__dirname, 'app', 'page.tsx');
if (!fs.existsSync(mainPagePath)) {
  console.error('❌ Main page not found');
  allChecksPassed = false;
} else {
  const mainPageContent = fs.readFileSync(mainPagePath, 'utf8');
  
  // Check for UserMenu import
  if (!mainPageContent.includes('import UserMenu from')) {
    console.error('❌ UserMenu not imported in main page');
    allChecksPassed = false;
  } else {
    console.log('  ✓ UserMenu imported');
  }
  
  // Check for UserMenu in header
  if (!mainPageContent.includes('<UserMenu />')) {
    console.error('❌ UserMenu not rendered in header');
    allChecksPassed = false;
  } else {
    console.log('  ✓ UserMenu rendered in header');
  }
  
  // Check for conditional rendering based on authentication
  if (!mainPageContent.includes('isAuthenticated && <UserMenu />')) {
    console.error('❌ UserMenu not conditionally rendered based on auth');
    allChecksPassed = false;
  } else {
    console.log('  ✓ UserMenu conditionally rendered when authenticated');
  }
}

// Check 3: Verify dashboard page exists
console.log('\n✓ Check 3: Dashboard page exists');
const dashboardPagePath = path.join(__dirname, 'app', 'dashboard', 'page.tsx');
if (!fs.existsSync(dashboardPagePath)) {
  console.error('❌ Dashboard page not found');
  allChecksPassed = false;
} else {
  const dashboardContent = fs.readFileSync(dashboardPagePath, 'utf8');
  
  // Check for authentication requirement
  if (!dashboardContent.includes('useAuth')) {
    console.error('❌ Dashboard page does not check authentication');
    allChecksPassed = false;
  } else {
    console.log('  ✓ Dashboard page checks authentication');
  }
  
  // Check for redirect to login
  if (!dashboardContent.includes('router.push(\'/auth/login')) {
    console.error('❌ Dashboard page does not redirect unauthenticated users');
    allChecksPassed = false;
  } else {
    console.log('  ✓ Dashboard redirects unauthenticated users to login');
  }
  
  // Check for UserDashboard component
  if (!dashboardContent.includes('UserDashboard')) {
    console.error('❌ UserDashboard component not used');
    allChecksPassed = false;
  } else {
    console.log('  ✓ UserDashboard component integrated');
  }
}

// Check 4: Verify UserDashboard component exists
console.log('\n✓ Check 4: UserDashboard component exists');
const userDashboardPath = path.join(__dirname, 'components', 'UserDashboard.tsx');
if (!fs.existsSync(userDashboardPath)) {
  console.error('❌ UserDashboard.tsx not found');
  allChecksPassed = false;
} else {
  console.log('  ✓ UserDashboard component exists');
}

// Final result
console.log('\n' + '='.repeat(50));
if (allChecksPassed) {
  console.log('✅ All checks passed! User menu navigation is properly implemented.');
  console.log('\nImplemented features:');
  console.log('  • User avatar with initials in header');
  console.log('  • User email display in dropdown');
  console.log('  • Dashboard navigation link');
  console.log('  • Logout functionality');
  console.log('  • Conditional rendering based on authentication');
  console.log('  • Dashboard page with auth protection');
  process.exit(0);
} else {
  console.log('❌ Some checks failed. Please review the errors above.');
  process.exit(1);
}
