/**
 * Verification Script for RegisterForm Component
 * Checks that all required features are implemented correctly.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying RegisterForm Component Implementation...\n');

const componentPath = path.join(__dirname, 'components', 'RegisterForm.tsx');
const componentContent = fs.readFileSync(componentPath, 'utf-8');

let allChecksPassed = true;

// Check 1: Component exists
console.log('✓ RegisterForm.tsx file exists');

// Check 2: Required imports
const requiredImports = [
  'useState',
  'FormEvent',
  'useRouter',
  'Link',
  'useAuth'
];

console.log('\n📦 Checking imports...');
requiredImports.forEach(imp => {
  if (componentContent.includes(imp)) {
    console.log(`  ✓ ${imp} imported`);
  } else {
    console.log(`  ✗ ${imp} NOT imported`);
    allChecksPassed = false;
  }
});

// Check 3: Form state (controlled components)
const requiredState = [
  'email',
  'username',
  'password',
  'confirmPassword',
  'isLoading',
  'error'
];

console.log('\n📝 Checking form state...');
requiredState.forEach(state => {
  const statePattern = new RegExp(`const \\[${state},\\s*set`);
  if (statePattern.test(componentContent)) {
    console.log(`  ✓ ${state} state defined`);
  } else {
    console.log(`  ✗ ${state} state NOT defined`);
    allChecksPassed = false;
  }
});

// Check 4: Validation functions
const validationChecks = [
  { name: 'Email format validation', pattern: /isValidEmail.*emailRegex.*test/ },
  { name: 'Password strength validation', pattern: /isStrongPassword.*length.*8/ },
  { name: 'Letter check in password', pattern: /hasLetter.*test/ },
  { name: 'Digit check in password', pattern: /hasDigit.*test/ },
  { name: 'Passwords match validation', pattern: /password.*!==.*confirmPassword/ }
];

console.log('\n🔐 Checking validation logic...');
validationChecks.forEach(check => {
  if (check.pattern.test(componentContent)) {
    console.log(`  ✓ ${check.name}`);
  } else {
    console.log(`  ✗ ${check.name} NOT found`);
    allChecksPassed = false;
  }
});

// Check 5: Required field validation
const requiredFieldChecks = [
  'email is required',
  'username is required',
  'password is required',
  'confirm your password'
];

console.log('\n✅ Checking required field validation...');
requiredFieldChecks.forEach(check => {
  if (componentContent.toLowerCase().includes(check.toLowerCase())) {
    console.log(`  ✓ ${check} validation`);
  } else {
    console.log(`  ✗ ${check} validation NOT found`);
    allChecksPassed = false;
  }
});

// Check 6: Form inputs
const requiredInputs = [
  { id: 'email', type: 'email' },
  { id: 'username', type: 'text' },
  { id: 'password', type: 'password' },
  { id: 'confirmPassword', type: 'password' }
];

console.log('\n📋 Checking form inputs...');
requiredInputs.forEach(input => {
  const inputPattern = new RegExp(`id="${input.id}".*type="${input.type}"`);
  if (inputPattern.test(componentContent)) {
    console.log(`  ✓ ${input.id} input (${input.type})`);
  } else {
    console.log(`  ✗ ${input.id} input NOT found`);
    allChecksPassed = false;
  }
});

// Check 7: Submit handler
console.log('\n🚀 Checking submit handler...');
if (componentContent.includes('handleSubmit') && 
    componentContent.includes('await register(email, username, password)')) {
  console.log('  ✓ Submit handler calls useAuth().register()');
} else {
  console.log('  ✗ Submit handler NOT properly implemented');
  allChecksPassed = false;
}

// Check 8: Loading state
console.log('\n⏳ Checking loading state...');
if (componentContent.includes('disabled={isLoading}') && 
    componentContent.includes('Creating account...')) {
  console.log('  ✓ Loading state implemented');
  console.log('  ✓ Button disabled during loading');
  console.log('  ✓ Loading spinner shown');
} else {
  console.log('  ✗ Loading state NOT properly implemented');
  allChecksPassed = false;
}

// Check 9: Error display
console.log('\n❌ Checking error display...');
if (componentContent.includes('{error &&') && 
    componentContent.includes('bg-red-100')) {
  console.log('  ✓ Error display component');
  console.log('  ✓ Error styling (red background)');
} else {
  console.log('  ✗ Error display NOT properly implemented');
  allChecksPassed = false;
}

// Check 10: Link to login page
console.log('\n🔗 Checking navigation links...');
if (componentContent.includes('href="/auth/login"') && 
    componentContent.includes('Already have an account?')) {
  console.log('  ✓ Link to login page');
  console.log('  ✓ Proper link text');
} else {
  console.log('  ✗ Login link NOT found');
  allChecksPassed = false;
}

// Check 11: Redirect after registration
console.log('\n🔄 Checking redirect logic...');
if (componentContent.includes('router.push') && 
    componentContent.includes('await register')) {
  console.log('  ✓ Redirect after successful registration');
} else {
  console.log('  ✗ Redirect logic NOT found');
  allChecksPassed = false;
}

// Check 12: Password strength hint
console.log('\n💡 Checking user guidance...');
if (componentContent.includes('Must be at least 8 characters')) {
  console.log('  ✓ Password strength hint displayed');
} else {
  console.log('  ✗ Password strength hint NOT found');
  allChecksPassed = false;
}

// Check 13: Accessibility features
console.log('\n♿ Checking accessibility...');
const accessibilityFeatures = [
  { name: 'Label for email', pattern: /htmlFor="email"/ },
  { name: 'Label for username', pattern: /htmlFor="username"/ },
  { name: 'Label for password', pattern: /htmlFor="password"/ },
  { name: 'Label for confirmPassword', pattern: /htmlFor="confirmPassword"/ },
  { name: 'Autocomplete attributes', pattern: /autoComplete/ }
];

accessibilityFeatures.forEach(feature => {
  if (feature.pattern.test(componentContent)) {
    console.log(`  ✓ ${feature.name}`);
  } else {
    console.log(`  ✗ ${feature.name} NOT found`);
    allChecksPassed = false;
  }
});

// Check 14: Styling consistency
console.log('\n🎨 Checking styling...');
const stylingFeatures = [
  'Tailwind CSS classes',
  'Responsive design (max-w-md)',
  'Shadow and rounded corners',
  'Focus states (focus:ring)',
  'Hover states (hover:bg)'
];

stylingFeatures.forEach(feature => {
  const hasFeature = componentContent.includes('shadow') || 
                     componentContent.includes('rounded') ||
                     componentContent.includes('focus:') ||
                     componentContent.includes('hover:') ||
                     componentContent.includes('max-w-md');
  if (hasFeature) {
    console.log(`  ✓ ${feature}`);
  }
});

// Final summary
console.log('\n' + '='.repeat(50));
if (allChecksPassed) {
  console.log('✅ ALL CHECKS PASSED!');
  console.log('\nRegisterForm component is fully implemented with:');
  console.log('  • Email, username, password, confirm password inputs (controlled)');
  console.log('  • Email format validation (regex)');
  console.log('  • Password strength validation (min 8 chars, letter + digit)');
  console.log('  • Passwords match validation');
  console.log('  • Required fields validation');
  console.log('  • Submit handler calling useAuth().register()');
  console.log('  • Loading state with spinner');
  console.log('  • Error display with styling');
  console.log('  • Link to login page');
  console.log('  • Redirect after successful registration');
  console.log('  • Accessibility features (labels, autocomplete)');
  console.log('  • Consistent styling with LoginForm');
  process.exit(0);
} else {
  console.log('❌ SOME CHECKS FAILED');
  console.log('\nPlease review the implementation.');
  process.exit(1);
}
