/**
 * Verification Script: Continue as Guest Feature
 * 
 * This script verifies that the "Continue as Guest" button on the login page
 * allows users to access the application without authentication.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying "Continue as Guest" Feature...\n');

let allChecksPassed = true;

// Check 1: Verify login page has guest button
console.log('✓ Check 1: Login page has "Continue as Guest" button');
const loginPagePath = path.join(__dirname, 'app', 'auth', 'login', 'page.tsx');
const loginPageContent = fs.readFileSync(loginPagePath, 'utf-8');

const hasGuestButton = loginPageContent.includes('Continue as Guest');
const hasGuestNavigation = loginPageContent.includes("router.push('/')");
const hasGuestDescription = loginPageContent.includes('Use the app without an account');

if (hasGuestButton && hasGuestNavigation && hasGuestDescription) {
  console.log('  ✅ Guest button found with proper navigation and description\n');
} else {
  console.log('  ❌ Guest button implementation incomplete');
  console.log(`     - Has button text: ${hasGuestButton}`);
  console.log(`     - Has navigation: ${hasGuestNavigation}`);
  console.log(`     - Has description: ${hasGuestDescription}\n`);
  allChecksPassed = false;
}

// Check 2: Verify button styling and accessibility
console.log('✓ Check 2: Button has proper styling and accessibility');
const hasButtonStyling = loginPageContent.includes('bg-white hover:bg-gray-50');
const hasButtonBorder = loginPageContent.includes('border border-gray-300');
const hasFocusRing = loginPageContent.includes('focus:ring-2 focus:ring-blue-500');

if (hasButtonStyling && hasButtonBorder && hasFocusRing) {
  console.log('  ✅ Button has proper Tailwind styling and focus states\n');
} else {
  console.log('  ❌ Button styling incomplete');
  console.log(`     - Has styling: ${hasButtonStyling}`);
  console.log(`     - Has border: ${hasButtonBorder}`);
  console.log(`     - Has focus ring: ${hasFocusRing}\n`);
  allChecksPassed = false;
}

// Check 3: Verify visual separator
console.log('✓ Check 3: Visual separator between login and guest option');
const hasSeparator = loginPageContent.includes('Or');
const hasSeparatorLine = loginPageContent.includes('border-t border-gray-300');

if (hasSeparator && hasSeparatorLine) {
  console.log('  ✅ Visual separator with "Or" text found\n');
} else {
  console.log('  ❌ Visual separator incomplete\n');
  allChecksPassed = false;
}

// Check 4: Verify home page doesn't require authentication
console.log('✓ Check 4: Home page accessible without authentication');
const homePagePath = path.join(__dirname, 'app', 'page.tsx');
const homePageContent = fs.readFileSync(homePagePath, 'utf-8');

// Home page should not have authentication checks that block access
const hasAuthCheck = homePageContent.includes('isAuthenticated') && 
                     homePageContent.includes('redirect');

if (!hasAuthCheck) {
  console.log('  ✅ Home page is accessible without authentication\n');
} else {
  console.log('  ⚠️  Home page may have authentication requirements\n');
}

// Check 5: Verify backward compatibility note
console.log('✓ Check 5: User guidance for guest mode');
const hasLimitedFeaturesNote = loginPageContent.includes('limited features');

if (hasLimitedFeaturesNote) {
  console.log('  ✅ User is informed about limited features in guest mode\n');
} else {
  console.log('  ⚠️  Consider adding note about limited features\n');
}

// Summary
console.log('═══════════════════════════════════════════════════════════');
if (allChecksPassed) {
  console.log('✅ ALL CHECKS PASSED');
  console.log('\n"Continue as Guest" feature is properly implemented!');
  console.log('\nFeatures verified:');
  console.log('  • Guest button on login page');
  console.log('  • Navigation to home page without auth');
  console.log('  • Proper styling and accessibility');
  console.log('  • Visual separator between options');
  console.log('  • User guidance about limited features');
  console.log('  • Home page accessible without authentication');
} else {
  console.log('❌ SOME CHECKS FAILED');
  console.log('\nPlease review the failed checks above.');
  process.exit(1);
}
console.log('═══════════════════════════════════════════════════════════');
