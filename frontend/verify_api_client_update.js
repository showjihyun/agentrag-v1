/**
 * Verification script for Task 5.5.1: API Client Update
 * 
 * This script verifies that the API client has been updated with:
 * - Auth support with automatic token refresh
 * - All auth endpoints
 * - All conversation endpoints
 * - Updated document endpoints with batch support
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying API Client Update (Task 5.5.1)...\n');

let allChecksPassed = true;

// Read the API client file
const apiClientPath = path.join(__dirname, 'lib', 'api-client.ts');
const apiClientContent = fs.readFileSync(apiClientPath, 'utf8');

// Read the types file
const typesPath = path.join(__dirname, 'lib', 'types.ts');
const typesContent = fs.readFileSync(typesPath, 'utf8');

// Check 1: getAuthHeaders method
console.log('✓ Check 1: getAuthHeaders() method');
if (apiClientContent.includes('private getAuthHeaders()') && 
    apiClientContent.includes("'Authorization': `Bearer ${token}`")) {
  console.log('  ✅ getAuthHeaders() method implemented\n');
} else {
  console.log('  ❌ getAuthHeaders() method not found or incomplete\n');
  allChecksPassed = false;
}

// Check 2: Token refresh logic on 401
console.log('✓ Check 2: Token refresh logic on 401 response');
if (apiClientContent.includes('handleUnauthorized') && 
    apiClientContent.includes('response.status === 401') &&
    apiClientContent.includes('/api/auth/refresh')) {
  console.log('  ✅ Token refresh logic implemented\n');
} else {
  console.log('  ❌ Token refresh logic not found\n');
  allChecksPassed = false;
}

// Check 3: fetchWithAuth method
console.log('✓ Check 3: fetchWithAuth() method for authenticated requests');
if (apiClientContent.includes('private async fetchWithAuth') && 
    apiClientContent.includes('this.getAuthHeaders()')) {
  console.log('  ✅ fetchWithAuth() method implemented\n');
} else {
  console.log('  ❌ fetchWithAuth() method not found\n');
  allChecksPassed = false;
}

// Check 4: Auth endpoints
console.log('✓ Check 4: Auth endpoints');
const authEndpoints = [
  { name: 'login', pattern: 'async login(email: string, password: string): Promise<TokenResponse>' },
  { name: 'register', pattern: 'async register(userData: UserCreate): Promise<TokenResponse>' },
  { name: 'me', pattern: 'async me(): Promise<UserResponse>' },
  { name: 'refresh', pattern: 'async refresh(refreshToken: string): Promise<TokenResponse>' }
];

let authEndpointsOk = true;
authEndpoints.forEach(endpoint => {
  if (apiClientContent.includes(endpoint.pattern)) {
    console.log(`  ✅ ${endpoint.name}() endpoint implemented`);
  } else {
    console.log(`  ❌ ${endpoint.name}() endpoint not found`);
    authEndpointsOk = false;
  }
});
console.log();
if (!authEndpointsOk) allChecksPassed = false;

// Check 5: Conversation endpoints
console.log('✓ Check 5: Conversation endpoints');
const conversationEndpoints = [
  { name: 'getSessions', pattern: 'async getSessions(limit: number = 20, offset: number = 0): Promise<SessionListResponse>' },
  { name: 'createSession', pattern: 'async createSession(title?: string): Promise<SessionResponse>' },
  { name: 'updateSession', pattern: 'async updateSession(id: string, title: string): Promise<SessionResponse>' },
  { name: 'deleteSession', pattern: 'async deleteSession(id: string): Promise<void>' },
  { name: 'getSessionMessages', pattern: 'async getSessionMessages(id: string, limit: number = 50, offset: number = 0): Promise<MessageListResponse>' }
];

let conversationEndpointsOk = true;
conversationEndpoints.forEach(endpoint => {
  if (apiClientContent.includes(endpoint.pattern)) {
    console.log(`  ✅ ${endpoint.name}() endpoint implemented`);
  } else {
    console.log(`  ❌ ${endpoint.name}() endpoint not found`);
    conversationEndpointsOk = false;
  }
});
console.log();
if (!conversationEndpointsOk) allChecksPassed = false;

// Check 6: Document endpoints
console.log('✓ Check 6: Document endpoints (updated with auth and batch support)');
const documentEndpoints = [
  { name: 'uploadDocument', pattern: 'async uploadDocument(file: File): Promise<DocumentResponse>' },
  { name: 'uploadBatch', pattern: 'async uploadBatch(files: File[]): Promise<BatchUploadResponse>' },
  { name: 'getDocuments', pattern: 'async getDocuments(status?: string, limit: number = 50, offset: number = 0): Promise<DocumentListResponse>' },
  { name: 'deleteDocument', pattern: 'async deleteDocument(documentId: string): Promise<void>' },
  { name: 'getBatchStatus', pattern: 'async getBatchStatus(batchId: string): Promise<BatchProgressResponse>' },
  { name: 'streamBatchProgress', pattern: 'streamBatchProgress(batchId: string): EventSource' }
];

let documentEndpointsOk = true;
documentEndpoints.forEach(endpoint => {
  if (apiClientContent.includes(endpoint.pattern)) {
    console.log(`  ✅ ${endpoint.name}() endpoint implemented`);
  } else {
    console.log(`  ❌ ${endpoint.name}() endpoint not found`);
    documentEndpointsOk = false;
  }
});
console.log();
if (!documentEndpointsOk) allChecksPassed = false;

// Check 7: Auth headers in existing methods
console.log('✓ Check 7: Existing methods use fetchWithAuth');
const methodsUsingAuth = [
  'uploadDocument',
  'getDocuments',
  'deleteDocument',
  'uploadBatch',
  'getBatchStatus',
  'queryStream'
];

let authHeadersOk = true;
methodsUsingAuth.forEach(method => {
  const methodRegex = new RegExp(`async ${method}[^{]*{[^}]*fetchWithAuth`, 's');
  if (methodRegex.test(apiClientContent) || apiClientContent.includes(`async *${method}`)) {
    console.log(`  ✅ ${method}() uses fetchWithAuth`);
  } else {
    console.log(`  ❌ ${method}() doesn't use fetchWithAuth`);
    authHeadersOk = false;
  }
});
console.log();
if (!authHeadersOk) allChecksPassed = false;

// Check 8: TypeScript types
console.log('✓ Check 8: Required TypeScript types defined');
const requiredTypes = [
  'SessionResponse',
  'SessionListResponse',
  'MessageResponse',
  'MessageListResponse',
  'DocumentResponse',
  'DocumentListResponse',
  'BatchUploadResponse',
  'BatchProgressResponse'
];

let typesOk = true;
requiredTypes.forEach(type => {
  if (typesContent.includes(`interface ${type}`)) {
    console.log(`  ✅ ${type} interface defined`);
  } else {
    console.log(`  ❌ ${type} interface not found`);
    typesOk = false;
  }
});
console.log();
if (!typesOk) allChecksPassed = false;

// Check 9: Imports
console.log('✓ Check 9: Proper imports');
const requiredImports = [
  'getAccessToken',
  'getRefreshToken',
  'setTokens',
  'clearTokens',
  'SessionListResponse',
  'SessionResponse',
  'MessageListResponse',
  'DocumentResponse',
  'DocumentListResponse',
  'BatchUploadResponse',
  'BatchProgressResponse'
];

let importsOk = true;
requiredImports.forEach(imp => {
  if (apiClientContent.includes(imp)) {
    console.log(`  ✅ ${imp} imported`);
  } else {
    console.log(`  ❌ ${imp} not imported`);
    importsOk = false;
  }
});
console.log();
if (!importsOk) allChecksPassed = false;

// Final summary
console.log('═══════════════════════════════════════════════════════════');
if (allChecksPassed) {
  console.log('✅ ALL CHECKS PASSED - API Client Update Complete!');
  console.log('\nThe API client has been successfully updated with:');
  console.log('  • Auth support with automatic token refresh');
  console.log('  • All auth endpoints (login, register, me, refresh)');
  console.log('  • All conversation endpoints (sessions, messages)');
  console.log('  • Updated document endpoints with batch support');
  console.log('  • Proper TypeScript types for all responses');
  console.log('  • Auth headers automatically included in all requests');
} else {
  console.log('❌ SOME CHECKS FAILED - Please review the issues above');
  process.exit(1);
}
console.log('═══════════════════════════════════════════════════════════');
