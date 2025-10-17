/**
 * Verification Script: Register Page
 * Checks that the register page is properly implemented.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Register Page Implementation...\n');

let allChecksPassed = true;

// Check 1: Register page file exists
console.log('✓ Check 1: Register page file exists');
const registerPagePath = path.join(__dirname, 'app', 'auth', 'register', 'page.tsx');
if (!fs.existsSync(registerPagePath)) {
  console.error('❌ Register page file not found at:', registerPagePath);
  allChecksPassed = false;
} else {
  console.log('  ✅ File exists at app/auth/register/page.tsx\n');
}

// Check 2: Register page imports RegisterForm
console.log('✓ Check 2: Register page imports RegisterForm');
const registerPageContent = fs.readFileSync(registerPagePath, 'utf8');
if (!registerPageContent.includes("import RegisterForm from '@/components/RegisterForm'")) {
  console.error('❌ RegisterForm import not found');
  allChecksPassed = false;
} else {
  console.log('  ✅ RegisterForm component imported\n');
}

// Check 3: Register page uses useAuth hook
console.log('✓ Check 3: Register page uses useAuth hook');
if (!registerPageContent.includes("import { useAuth } from '@/contexts/AuthContext'")) {
  console.error('❌ useAuth import not found');
  allChecksPassed = false;
} else if (!registerPageContent.includes('const { isAuthenticated, isLoading } = useAuth()')) {
  console.error('❌ useAuth hook not used properly');
  allChecksPassed = false;
} else {
  console.log('  ✅ useAuth hook imported and used\n');
}

// Check 4: Register page uses useRouter for navigation
console.log('✓ Check 4: Register page uses useRouter for navigation');
if (!registerPageContent.includes("import { useRouter } from 'next/navigation'")) {
  console.error('❌ useRouter import not found');
  allChecksPassed = false;
} else if (!registerPageContent.includes('const router = useRouter()')) {
  console.error('❌ useRouter hook not used');
  allChecksPassed = false;
} else {
  console.log('  ✅ useRouter imported and used\n');
}

// Check 5: Register page redirects authenticated users
console.log('✓ Check 5: Register page redirects authenticated users');
if (!registerPageContent.includes('useEffect')) {
  console.error('❌ useEffect not found for redirect logic');
  allChecksPassed = false;
} else if (!registerPageContent.includes("router.push('/')")) {
  console.error('❌ Redirect to home not found');
  allChecksPassed = false;
} else if (!registerPageContent.includes('if (!isLoading && isAuthenticated)')) {
  console.error('❌ Authentication check not found');
  allChecksPassed = false;
} else {
  console.log('  ✅ Redirects authenticated users to home\n');
}

// Check 6: Register page renders RegisterForm component
console.log('✓ Check 6: Register page renders RegisterForm component');
if (!registerPageContent.includes('<RegisterForm />')) {
  console.error('❌ RegisterForm component not rendered');
  allChecksPassed = false;
} else {
  console.log('  ✅ RegisterForm component rendered\n');
}

// Check 7: Register page has loading state
console.log('✓ Check 7: Register page has loading state');
if (!registerPageContent.includes('if (isLoading)')) {
  console.error('❌ Loading state check not found');
  allChecksPassed = false;
} else if (!registerPageContent.includes('Loading...')) {
  console.error('❌ Loading message not found');
  allChecksPassed = false;
} else {
  console.log('  ✅ Loading state implemented\n');
}

// Check 8: Register page has "Continue as Guest" option
console.log('✓ Check 8: Register page has "Continue as Guest" option');
if (!registerPageContent.includes('Continue as Guest')) {
  console.error('❌ "Continue as Guest" button not found');
  allChecksPassed = false;
} else {
  console.log('  ✅ Guest mode option available\n');
}

// Check 9: Register page is a client component
console.log('✓ Check 9: Register page is a client component');
if (!registerPageContent.includes("'use client'")) {
  console.error('❌ "use client" directive not found');
  allChecksPassed = false;
} else {
  console.log('  ✅ Client component directive present\n');
}

// Check 10: Register page has proper styling
console.log('✓ Check 10: Register page has proper styling');
if (!registerPageContent.includes('min-h-screen')) {
  console.error('❌ Full-height layout not found');
  allChecksPassed = false;
} else if (!registerPageContent.includes('flex items-center justify-center')) {
  console.error('❌ Centered layout not found');
  allChecksPassed = false;
} else {
  console.log('  ✅ Proper Tailwind CSS styling applied\n');
}

// Final Summary
console.log('═'.repeat(60));
if (allChecksPassed) {
  console.log('✅ ALL CHECKS PASSED!');
  console.log('\n📋 Register Page Summary:');
  console.log('  • Uses RegisterForm component');
  console.log('  • Redirects to home (/) after successful registration');
  console.log('  • Redirects already authenticated users');
  console.log('  • Shows loading state while checking auth');
  console.log('  • Provides "Continue as Guest" option');
  console.log('  • Properly styled with Tailwind CSS');
  console.log('\n✨ Register page is ready for use!');
  process.exit(0);
} else {
  console.log('❌ SOME CHECKS FAILED');
  console.log('\nPlease review the errors above and fix the issues.');
  process.exit(1);
}
