/**
 * Verification script for UserDashboard component
 * Checks that all required features are implemented
 */

const fs = require('fs');
const path = require('path');

const componentPath = path.join(__dirname, 'components', 'UserDashboard.tsx');

console.log('🔍 Verifying UserDashboard component...\n');

// Read the component file
const content = fs.readFileSync(componentPath, 'utf8');

const checks = [
  {
    name: 'Component exports UserDashboard',
    test: () => content.includes('export default function UserDashboard'),
  },
  {
    name: 'Uses useAuth hook',
    test: () => content.includes('useAuth()'),
  },
  {
    name: 'Displays user email',
    test: () => content.includes('user.email'),
  },
  {
    name: 'Displays user username',
    test: () => content.includes('user.username'),
  },
  {
    name: 'Displays user role',
    test: () => content.includes('user.role'),
  },
  {
    name: 'Displays created_at date',
    test: () => content.includes('user.created_at'),
  },
  {
    name: 'Displays query count',
    test: () => content.includes('user.query_count'),
  },
  {
    name: 'Displays storage used',
    test: () => content.includes('user.storage_used_bytes'),
  },
  {
    name: 'Shows storage quota (1GB)',
    test: () => content.includes('1024 * 1024 * 1024'),
  },
  {
    name: 'Has storage progress bar',
    test: () => content.includes('storagePercentage') && content.includes('rounded-full'),
  },
  {
    name: 'Formats bytes to MB/GB',
    test: () => content.includes('formatBytes'),
  },
  {
    name: 'Loads recent sessions',
    test: () => content.includes('getSessions') && content.includes('recentSessions'),
  },
  {
    name: 'Loads recent documents',
    test: () => content.includes('getDocuments') && content.includes('recentDocuments'),
  },
  {
    name: 'Has profile update form',
    test: () => content.includes('handleProfileUpdate') && content.includes('username') && content.includes('full_name'),
  },
  {
    name: 'Has password change form',
    test: () => content.includes('handlePasswordChange') && content.includes('current_password') && content.includes('new_password'),
  },
  {
    name: 'Validates password match',
    test: () => content.includes('passwords do not match') || content.includes('confirm_password'),
  },
  {
    name: 'Validates password length',
    test: () => content.includes('at least 8 characters') || content.includes('minLength={8}'),
  },
  {
    name: 'Has logout button',
    test: () => content.includes('logout') && content.includes('Logout'),
  },
  {
    name: 'Uses apiClient for updates',
    test: () => content.includes('apiClient.updateUser'),
  },
  {
    name: 'Calls refreshUser after profile update',
    test: () => content.includes('refreshUser()'),
  },
  {
    name: 'Shows loading states',
    test: () => content.includes('isLoading') && content.includes('Loading'),
  },
  {
    name: 'Shows error messages',
    test: () => content.includes('error') && content.includes('setError'),
  },
  {
    name: 'Shows success messages',
    test: () => content.includes('success') && content.includes('setSuccess'),
  },
  {
    name: 'Responsive design (grid layout)',
    test: () => content.includes('md:grid-cols-2') || content.includes('grid-cols-1'),
  },
];

let passed = 0;
let failed = 0;

checks.forEach((check) => {
  const result = check.test();
  if (result) {
    console.log(`✅ ${check.name}`);
    passed++;
  } else {
    console.log(`❌ ${check.name}`);
    failed++;
  }
});

console.log(`\n📊 Results: ${passed}/${checks.length} checks passed`);

if (failed === 0) {
  console.log('✅ All checks passed! UserDashboard component is complete.\n');
  process.exit(0);
} else {
  console.log(`❌ ${failed} check(s) failed.\n`);
  process.exit(1);
}
