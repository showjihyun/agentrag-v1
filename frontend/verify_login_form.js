/**
 * Verification script for LoginForm component
 * Checks that all required features are implemented
 */

const fs = require('fs');
const path = require('path');

const componentPath = path.join(__dirname, 'components', 'LoginForm.tsx');

console.log('🔍 Verifying LoginForm Component...\n');

// Read the component file
const content = fs.readFileSync(componentPath, 'utf-8');

const checks = [
  {
    name: 'Email input with useState',
    test: () => content.includes('useState') && content.includes('email') && content.includes('setEmail'),
  },
  {
    name: 'Password input with useState',
    test: () => content.includes('password') && content.includes('setPassword'),
  },
  {
    name: 'Email validation (regex)',
    test: () => content.includes('emailRegex') || content.includes('/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/'),
  },
  {
    name: 'Required fields validation',
    test: () => content.includes('required') || content.includes('!email') || content.includes('!password'),
  },
  {
    name: 'useAuth hook usage',
    test: () => content.includes('useAuth()') && content.includes('login'),
  },
  {
    name: 'Submit handler calls login',
    test: () => content.includes('handleSubmit') && content.includes('await login('),
  },
  {
    name: 'Loading state',
    test: () => content.includes('isLoading') && content.includes('setIsLoading'),
  },
  {
    name: 'Disabled button during loading',
    test: () => content.includes('disabled={isLoading}'),
  },
  {
    name: 'Loading spinner',
    test: () => content.includes('animate-spin') || content.includes('Logging in'),
  },
  {
    name: 'Error display',
    test: () => content.includes('error') && content.includes('setError') && content.includes('text-red'),
  },
  {
    name: 'Link to register page',
    test: () => content.includes('/auth/register') && content.includes('Sign up'),
  },
  {
    name: 'Router redirect after login',
    test: () => content.includes('useRouter') && content.includes('router.push'),
  },
  {
    name: 'Form element with onSubmit',
    test: () => content.includes('<form') && content.includes('onSubmit={handleSubmit}'),
  },
  {
    name: 'Controlled inputs (value + onChange)',
    test: () => content.includes('value={email}') && content.includes('onChange='),
  },
  {
    name: 'Tailwind CSS styling',
    test: () => content.includes('className=') && content.includes('bg-'),
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
  console.log('\n✅ LoginForm component verification PASSED!');
  console.log('\n📋 Component Features:');
  console.log('  • Email and password inputs (controlled components)');
  console.log('  • Client-side validation (email format, required fields)');
  console.log('  • Submit handler calls useAuth().login()');
  console.log('  • Loading state with disabled button and spinner');
  console.log('  • Error display in red text');
  console.log('  • Link to register page');
  console.log('  • Router redirect after successful login');
  process.exit(0);
} else {
  console.log(`\n❌ LoginForm component verification FAILED (${failed} issues)`);
  process.exit(1);
}
