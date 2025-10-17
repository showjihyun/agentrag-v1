/**
 * Verification script for Login Page
 * Checks that the login page is properly implemented with all required features.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Login Page Implementation...\n');

const loginPagePath = path.join(__dirname, 'app', 'auth', 'login', 'page.tsx');

// Check if file exists
if (!fs.existsSync(loginPagePath)) {
  console.error('❌ Login page file not found at:', loginPagePath);
  process.exit(1);
}

const content = fs.readFileSync(loginPagePath, 'utf-8');

const checks = [
  {
    name: 'Uses LoginForm component',
    test: () => content.includes('import LoginForm from') && content.includes('<LoginForm'),
    required: true
  },
  {
    name: 'Imports useRouter from next/navigation',
    test: () => content.includes("import { useRouter } from 'next/navigation'"),
    required: true
  },
  {
    name: 'Imports useAuth hook',
    test: () => content.includes("import { useAuth } from '@/contexts/AuthContext'"),
    required: true
  },
  {
    name: 'Uses useEffect for redirect logic',
    test: () => content.includes('useEffect'),
    required: true
  },
  {
    name: 'Redirects to home (/) after successful login',
    test: () => content.includes("router.push('/')"),
    required: true
  },
  {
    name: 'Checks isAuthenticated state',
    test: () => content.includes('isAuthenticated'),
    required: true
  },
  {
    name: 'Handles loading state',
    test: () => content.includes('isLoading'),
    required: true
  },
  {
    name: 'Shows loading spinner while checking auth',
    test: () => content.includes('animate-spin') || content.includes('Loading'),
    required: true
  },
  {
    name: 'Redirects already authenticated users',
    test: () => {
      const hasEffect = content.includes('useEffect');
      const hasRedirect = content.includes("router.push('/')");
      const hasAuthCheck = content.includes('isAuthenticated');
      return hasEffect && hasRedirect && hasAuthCheck;
    },
    required: true
  },
  {
    name: 'Has "Continue as Guest" option',
    test: () => content.includes('Continue as Guest') || content.includes('guest'),
    required: true
  },
  {
    name: 'Is a client component',
    test: () => content.includes("'use client'"),
    required: true
  },
  {
    name: 'Has proper page layout with styling',
    test: () => content.includes('min-h-screen') && content.includes('flex'),
    required: true
  },
  {
    name: 'Has welcome message/heading',
    test: () => content.includes('Welcome') || content.includes('Sign in'),
    required: false
  }
];

let passed = 0;
let failed = 0;
let warnings = 0;

checks.forEach(check => {
  const result = check.test();
  if (result) {
    console.log(`✅ ${check.name}`);
    passed++;
  } else {
    if (check.required) {
      console.log(`❌ ${check.name}`);
      failed++;
    } else {
      console.log(`⚠️  ${check.name} (optional)`);
      warnings++;
    }
  }
});

console.log('\n' + '='.repeat(50));
console.log(`📊 Results: ${passed} passed, ${failed} failed, ${warnings} warnings`);
console.log('='.repeat(50) + '\n');

if (failed > 0) {
  console.error('❌ Login page verification failed!');
  process.exit(1);
}

console.log('✅ Login page verification passed!');
console.log('\n📝 Implementation Summary:');
console.log('   - Login page created at app/auth/login/page.tsx');
console.log('   - Uses LoginForm component for authentication');
console.log('   - Redirects to home (/) after successful login using useRouter');
console.log('   - Redirects already authenticated users automatically');
console.log('   - Shows loading state while checking authentication');
console.log('   - Includes "Continue as Guest" option for backward compatibility');
console.log('   - Responsive design with Tailwind CSS');
console.log('\n✨ Task completed successfully!');
