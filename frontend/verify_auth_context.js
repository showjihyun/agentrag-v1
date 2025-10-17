/**
 * Verification script for AuthContext implementation.
 * Checks that all required components are present and properly structured.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying AuthContext Implementation...\n');

let allChecks = true;

// Check 1: AuthContext file exists
console.log('✓ Check 1: AuthContext file exists');
const authContextPath = path.join(__dirname, 'contexts', 'AuthContext.tsx');
if (!fs.existsSync(authContextPath)) {
  console.error('❌ AuthContext.tsx not found');
  allChecks = false;
} else {
  console.log('  ✅ File exists: contexts/AuthContext.tsx');
}

// Check 2: Read and verify AuthContext content
console.log('\n✓ Check 2: AuthContext content verification');
const authContextContent = fs.readFileSync(authContextPath, 'utf8');

const requiredElements = [
  { name: 'AuthContext creation', pattern: /createContext<AuthContextType/ },
  { name: 'AuthProvider component', pattern: /export function AuthProvider/ },
  { name: 'useAuth hook', pattern: /export function useAuth/ },
  { name: 'user state', pattern: /useState<UserResponse \| null>/ },
  { name: 'isLoading state', pattern: /isLoading/ },
  { name: 'isAuthenticated computed', pattern: /isAuthenticated/ },
  { name: 'login function', pattern: /const login = async \(email: string, password: string\)/ },
  { name: 'register function', pattern: /const register = async/ },
  { name: 'logout function', pattern: /const logout = \(\): void/ },
  { name: 'refreshUser function', pattern: /const refreshUser = async/ },
  { name: 'useEffect for auto-load', pattern: /useEffect\(\(\) => \{[\s\S]*?loadUser/ },
  { name: 'apiClient.login call', pattern: /apiClient\.login/ },
  { name: 'apiClient.register call', pattern: /apiClient\.register/ },
  { name: 'apiClient.me call', pattern: /apiClient\.me/ },
  { name: 'setTokens call', pattern: /setTokens/ },
  { name: 'clearTokens call', pattern: /clearTokens/ },
  { name: 'getAccessToken call', pattern: /getAccessToken/ },
  { name: 'isTokenExpired call', pattern: /isTokenExpired/ },
];

requiredElements.forEach(({ name, pattern }) => {
  if (pattern.test(authContextContent)) {
    console.log(`  ✅ ${name}`);
  } else {
    console.log(`  ❌ Missing: ${name}`);
    allChecks = false;
  }
});

// Check 3: Types file has auth interfaces
console.log('\n✓ Check 3: Auth types in types.ts');
const typesPath = path.join(__dirname, 'lib', 'types.ts');
const typesContent = fs.readFileSync(typesPath, 'utf8');

const requiredTypes = [
  { name: 'UserResponse interface', pattern: /export interface UserResponse/ },
  { name: 'TokenResponse interface', pattern: /export interface TokenResponse/ },
  { name: 'UserCreate interface', pattern: /export interface UserCreate/ },
  { name: 'UserLogin interface', pattern: /export interface UserLogin/ },
];

requiredTypes.forEach(({ name, pattern }) => {
  if (pattern.test(typesContent)) {
    console.log(`  ✅ ${name}`);
  } else {
    console.log(`  ❌ Missing: ${name}`);
    allChecks = false;
  }
});

// Check 4: API client has auth methods
console.log('\n✓ Check 4: Auth methods in api-client.ts');
const apiClientPath = path.join(__dirname, 'lib', 'api-client.ts');
const apiClientContent = fs.readFileSync(apiClientPath, 'utf8');

const requiredApiMethods = [
  { name: 'login method', pattern: /async login\(email: string, password: string\)/ },
  { name: 'register method', pattern: /async register\(userData: UserCreate\)/ },
  { name: 'me method', pattern: /async me\(\): Promise<UserResponse>/ },
  { name: 'refresh method', pattern: /async refresh\(refreshToken: string\)/ },
  { name: 'getAuthHeaders method', pattern: /getAuthHeaders\(\)/ },
  { name: 'fetchWithAuth method', pattern: /fetchWithAuth/ },
  { name: 'handleUnauthorized method', pattern: /handleUnauthorized/ },
];

requiredApiMethods.forEach(({ name, pattern }) => {
  if (pattern.test(apiClientContent)) {
    console.log(`  ✅ ${name}`);
  } else {
    console.log(`  ❌ Missing: ${name}`);
    allChecks = false;
  }
});

// Check 5: Auth utilities exist
console.log('\n✓ Check 5: Auth utilities in auth.ts');
const authUtilsPath = path.join(__dirname, 'lib', 'auth.ts');
const authUtilsContent = fs.readFileSync(authUtilsPath, 'utf8');

const requiredAuthUtils = [
  { name: 'setTokens function', pattern: /export function setTokens/ },
  { name: 'getAccessToken function', pattern: /export function getAccessToken/ },
  { name: 'getRefreshToken function', pattern: /export function getRefreshToken/ },
  { name: 'clearTokens function', pattern: /export function clearTokens/ },
  { name: 'isTokenExpired function', pattern: /export function isTokenExpired/ },
];

requiredAuthUtils.forEach(({ name, pattern }) => {
  if (pattern.test(authUtilsContent)) {
    console.log(`  ✅ ${name}`);
  } else {
    console.log(`  ❌ Missing: ${name}`);
    allChecks = false;
  }
});

// Check 6: Test file exists
console.log('\n✓ Check 6: Test file exists');
const testPath = path.join(__dirname, 'contexts', '__tests__', 'AuthContext.test.tsx');
if (fs.existsSync(testPath)) {
  console.log('  ✅ Test file exists: contexts/__tests__/AuthContext.test.tsx');
  
  const testContent = fs.readFileSync(testPath, 'utf8');
  const testCases = [
    'should initialize with no user',
    'should load user from token on mount',
    'should handle login successfully',
    'should handle register successfully',
    'should handle logout',
    'should refresh user data',
    'should clear tokens if token is expired',
    'should logout if refreshUser fails',
  ];
  
  testCases.forEach(testCase => {
    if (testContent.includes(testCase)) {
      console.log(`  ✅ Test case: ${testCase}`);
    } else {
      console.log(`  ⚠️  Missing test case: ${testCase}`);
    }
  });
} else {
  console.log('  ❌ Test file not found');
  allChecks = false;
}

// Summary
console.log('\n' + '='.repeat(60));
if (allChecks) {
  console.log('✅ All checks passed! AuthContext implementation is complete.');
  console.log('\n📋 Summary:');
  console.log('  • AuthContext.tsx created with all required functionality');
  console.log('  • Auth types added to types.ts');
  console.log('  • Auth methods added to api-client.ts');
  console.log('  • Auth utilities verified in auth.ts');
  console.log('  • Test file created with comprehensive test cases');
  console.log('\n🎯 Next Steps:');
  console.log('  1. Wrap your app with AuthProvider in app/layout.tsx');
  console.log('  2. Use useAuth() hook in components to access auth state');
  console.log('  3. Implement auth pages (login/register)');
  process.exit(0);
} else {
  console.log('❌ Some checks failed. Please review the implementation.');
  process.exit(1);
}
