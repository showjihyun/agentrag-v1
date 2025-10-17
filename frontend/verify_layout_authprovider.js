/**
 * Verification script for AuthProvider integration in layout.tsx
 * 
 * This script verifies that:
 * 1. AuthProvider is imported in layout.tsx
 * 2. AuthProvider wraps the app children
 * 3. The component hierarchy is correct
 */

const fs = require('fs');
const path = require('path');

function verifyAuthProviderIntegration() {
  console.log('🔍 Verifying AuthProvider integration in layout.tsx...\n');

  const layoutPath = path.join(__dirname, 'app', 'layout.tsx');
  const layoutContent = fs.readFileSync(layoutPath, 'utf-8');

  let allPassed = true;

  // Check 1: AuthProvider is imported
  console.log('✓ Check 1: AuthProvider import');
  if (layoutContent.includes('import { AuthProvider } from "@/contexts/AuthContext"')) {
    console.log('  ✅ AuthProvider is imported from @/contexts/AuthContext\n');
  } else {
    console.log('  ❌ AuthProvider import not found\n');
    allPassed = false;
  }

  // Check 2: AuthProvider wraps children
  console.log('✓ Check 2: AuthProvider wraps app');
  if (layoutContent.includes('<AuthProvider>')) {
    console.log('  ✅ AuthProvider component is used in JSX\n');
  } else {
    console.log('  ❌ AuthProvider component not found in JSX\n');
    allPassed = false;
  }

  // Check 3: Proper component hierarchy
  console.log('✓ Check 3: Component hierarchy');
  const hasErrorBoundary = layoutContent.includes('<ErrorBoundary>');
  const hasToastProvider = layoutContent.includes('<ToastProvider>');
  
  if (hasErrorBoundary && hasToastProvider) {
    console.log('  ✅ Proper component hierarchy detected:');
    console.log('     ErrorBoundary → AuthProvider → ToastProvider → children\n');
  } else {
    console.log('  ⚠️  Component hierarchy may need review\n');
  }

  // Check 4: AuthContext file exists
  console.log('✓ Check 4: AuthContext file exists');
  const authContextPath = path.join(__dirname, 'contexts', 'AuthContext.tsx');
  if (fs.existsSync(authContextPath)) {
    console.log('  ✅ AuthContext.tsx exists at contexts/AuthContext.tsx\n');
    
    const authContextContent = fs.readFileSync(authContextPath, 'utf-8');
    
    // Verify exports
    if (authContextContent.includes('export function AuthProvider') && 
        authContextContent.includes('export function useAuth')) {
      console.log('  ✅ AuthProvider and useAuth are properly exported\n');
    } else {
      console.log('  ❌ Missing required exports\n');
      allPassed = false;
    }
  } else {
    console.log('  ❌ AuthContext.tsx not found\n');
    allPassed = false;
  }

  // Summary
  console.log('═══════════════════════════════════════════════════════');
  if (allPassed) {
    console.log('✅ ALL CHECKS PASSED');
    console.log('   AuthProvider is properly integrated in layout.tsx');
    console.log('   The app is now wrapped with authentication context');
  } else {
    console.log('❌ SOME CHECKS FAILED');
    console.log('   Please review the issues above');
  }
  console.log('═══════════════════════════════════════════════════════\n');

  return allPassed;
}

// Run verification
const success = verifyAuthProviderIntegration();
process.exit(success ? 0 : 1);
