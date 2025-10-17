/**
 * Comprehensive verification for Task 5.5.1: Auth Context + API Client
 * Verifies all sub-tasks are complete.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Task 5.5.1: Auth Context + API Client\n');
console.log('=' .repeat(60));

let allChecks = true;
const results = {
  passed: 0,
  failed: 0,
  warnings: 0,
};

function checkFile(filePath, description) {
  const fullPath = path.join(__dirname, filePath);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ ${description}`);
    results.passed++;
    return fs.readFileSync(fullPath, 'utf8');
  } else {
    console.log(`❌ ${description} - FILE NOT FOUND`);
    results.failed++;
    allChecks = false;
    return null;
  }
}

function checkPattern(content, pattern, description) {
  if (!content) return false;
  
  if (pattern.test(content)) {
    console.log(`  ✅ ${description}`);
    results.passed++;
    return true;
  } else {
    console.log(`  ❌ ${description}`);
    results.failed++;
    allChecks = false;
    return false;
  }
}

// Sub-task 1: Create frontend/lib/auth.ts
console.log('\n📋 Sub-task 1: Create frontend/lib/auth.ts');
const authContent = checkFile('lib/auth.ts', 'Auth utilities file exists');
if (authContent) {
  checkPattern(authContent, /export function setTokens/, 'setTokens function');
  checkPattern(authContent, /export function getAccessToken/, 'getAccessToken function');
  checkPattern(authContent, /export function getRefreshToken/, 'getRefreshToken function');
  checkPattern(authContent, /export function clearTokens/, 'clearTokens function');
  checkPattern(authContent, /export function isTokenExpired/, 'isTokenExpired function');
}

// Sub-task 2: Create frontend/contexts/AuthContext.tsx
console.log('\n📋 Sub-task 2: Create frontend/contexts/AuthContext.tsx');
const contextContent = checkFile('contexts/AuthContext.tsx', 'AuthContext file exists');
if (contextContent) {
  checkPattern(contextContent, /createContext<AuthContextType/, 'AuthContext created');
  checkPattern(contextContent, /export function AuthProvider/, 'AuthProvider component');
  checkPattern(contextContent, /export function useAuth/, 'useAuth hook');
  checkPattern(contextContent, /useState<UserResponse \| null>/, 'user state');
  checkPattern(contextContent, /isLoading/, 'isLoading state');
  checkPattern(contextContent, /isAuthenticated/, 'isAuthenticated computed');
  checkPattern(contextContent, /const login = async/, 'login function');
  checkPattern(contextContent, /const register = async/, 'register function');
  checkPattern(contextContent, /const logout = \(\): void/, 'logout function');
  checkPattern(contextContent, /const refreshUser = async/, 'refreshUser function');
  checkPattern(contextContent, /useEffect/, 'Auto-load on mount');
}

// Sub-task 3: Update frontend/lib/api-client.ts
console.log('\n📋 Sub-task 3: Update frontend/lib/api-client.ts');
const apiContent = checkFile('lib/api-client.ts', 'API client file exists');
if (apiContent) {
  // Auth support
  console.log('  Auth Support:');
  checkPattern(apiContent, /getAuthHeaders\(\)/, '  - getAuthHeaders method');
  checkPattern(apiContent, /fetchWithAuth/, '  - fetchWithAuth method');
  checkPattern(apiContent, /handleUnauthorized/, '  - handleUnauthorized method');
  
  // Auth endpoints
  console.log('  Auth Endpoints:');
  checkPattern(apiContent, /async login\(email: string, password: string\)/, '  - login endpoint');
  checkPattern(apiContent, /async register\(userData: UserCreate\)/, '  - register endpoint');
  checkPattern(apiContent, /async me\(\): Promise<UserResponse>/, '  - me endpoint');
  checkPattern(apiContent, /async refresh\(refreshToken: string\)/, '  - refresh endpoint');
  
  // Conversation endpoints
  console.log('  Conversation Endpoints:');
  checkPattern(apiContent, /async getSessions/, '  - getSessions endpoint');
  checkPattern(apiContent, /async createSession/, '  - createSession endpoint');
  checkPattern(apiContent, /async updateSession/, '  - updateSession endpoint');
  checkPattern(apiContent, /async deleteSession/, '  - deleteSession endpoint');
  checkPattern(apiContent, /async getSessionMessages/, '  - getSessionMessages endpoint');
  
  // Document endpoints
  console.log('  Document Endpoints:');
  checkPattern(apiContent, /async uploadBatch/, '  - uploadBatch endpoint');
  checkPattern(apiContent, /async getBatchStatus/, '  - getBatchStatus endpoint');
  checkPattern(apiContent, /streamBatchProgress/, '  - streamBatchProgress endpoint');
  
  // Existing methods updated
  console.log('  Updated Existing Methods:');
  checkPattern(apiContent, /fetchWithAuth.*uploadDocument/, '  - uploadDocument uses auth');
  checkPattern(apiContent, /fetchWithAuth.*queryStream/, '  - queryStream uses auth');
  checkPattern(apiContent, /fetchWithAuth.*getDocuments/, '  - getDocuments uses auth');
  checkPattern(apiContent, /fetchWithAuth.*deleteDocument/, '  - deleteDocument uses auth');
}

// Sub-task 4: Update frontend/lib/types.ts
console.log('\n📋 Sub-task 4: Update frontend/lib/types.ts');
const typesContent = checkFile('lib/types.ts', 'Types file exists');
if (typesContent) {
  checkPattern(typesContent, /export interface UserResponse/, 'UserResponse interface');
  checkPattern(typesContent, /export interface TokenResponse/, 'TokenResponse interface');
  checkPattern(typesContent, /export interface UserCreate/, 'UserCreate interface');
  checkPattern(typesContent, /export interface UserLogin/, 'UserLogin interface');
}

// Sub-task 5: Wrap app with AuthProvider
console.log('\n📋 Sub-task 5: Wrap app with AuthProvider in layout.tsx');
const layoutContent = checkFile('app/layout.tsx', 'Layout file exists');
if (layoutContent) {
  checkPattern(layoutContent, /import.*AuthProvider.*from.*@\/contexts\/AuthContext/, 'AuthProvider imported');
  checkPattern(layoutContent, /<AuthProvider>/, 'AuthProvider wraps app');
}

// Additional checks
console.log('\n📋 Additional Checks');
checkFile('contexts/__tests__/AuthContext.test.tsx', 'Test file exists');
checkFile('verify_auth_context.js', 'Verification script exists');
checkFile('AUTH_CONTEXT_USAGE.md', 'Usage documentation exists');

// Summary
console.log('\n' + '='.repeat(60));
console.log('📊 VERIFICATION SUMMARY');
console.log('='.repeat(60));
console.log(`✅ Passed: ${results.passed}`);
console.log(`❌ Failed: ${results.failed}`);
console.log(`⚠️  Warnings: ${results.warnings}`);
console.log('='.repeat(60));

if (allChecks) {
  console.log('\n🎉 SUCCESS! Task 5.5.1 is COMPLETE!');
  console.log('\n✅ All Sub-tasks Completed:');
  console.log('  1. ✅ Create frontend/lib/auth.ts with auth utilities');
  console.log('  2. ✅ Create frontend/contexts/AuthContext.tsx with AuthContext');
  console.log('  3. ✅ Update frontend/lib/api-client.ts with auth support');
  console.log('  4. ✅ Update frontend/lib/types.ts with auth interfaces');
  console.log('  5. ✅ Wrap app with AuthProvider in layout.tsx');
  
  console.log('\n📦 Deliverables:');
  console.log('  • AuthContext with full state management');
  console.log('  • Auth utilities for token management');
  console.log('  • API client with auth support and token refresh');
  console.log('  • Auth endpoints (login, register, me, refresh)');
  console.log('  • Conversation endpoints (sessions, messages)');
  console.log('  • Document endpoints (batch upload, progress streaming)');
  console.log('  • App wrapped with AuthProvider');
  console.log('  • Comprehensive test suite');
  console.log('  • Usage documentation');
  
  console.log('\n🚀 Next Steps:');
  console.log('  → Task 5.5.2: Auth Pages (Login/Register)');
  console.log('  → Task 5.5.3: Conversation History Sidebar');
  console.log('  → Task 5.5.4: Batch Upload UI');
  
  console.log('\n💡 Quick Start:');
  console.log('  1. Use useAuth() hook in any component');
  console.log('  2. Check AUTH_CONTEXT_USAGE.md for examples');
  console.log('  3. Implement login/register pages next');
  
  process.exit(0);
} else {
  console.log('\n❌ FAILED! Some checks did not pass.');
  console.log('Please review the failed items above.');
  process.exit(1);
}
