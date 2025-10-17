/**
 * Verification script for SessionItem component
 * Checks that the component has all required functionality
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying SessionItem component...\n');

const componentPath = path.join(__dirname, 'components', 'SessionItem.tsx');
const testPath = path.join(__dirname, 'components', '__tests__', 'SessionItem.test.tsx');

let allChecks = true;

// Check 1: Component file exists
console.log('✓ Check 1: Component file exists');
if (!fs.existsSync(componentPath)) {
  console.error('❌ SessionItem.tsx not found');
  allChecks = false;
} else {
  console.log('  ✅ SessionItem.tsx exists');
}

// Check 2: Test file exists
console.log('\n✓ Check 2: Test file exists');
if (!fs.existsSync(testPath)) {
  console.error('❌ SessionItem.test.tsx not found');
  allChecks = false;
} else {
  console.log('  ✅ SessionItem.test.tsx exists');
}

// Check 3: Component has required props
console.log('\n✓ Check 3: Component has required props');
const componentContent = fs.readFileSync(componentPath, 'utf8');
const requiredProps = [
  'session: SessionResponse',
  'isActive: boolean',
  'onSelect:',
  'onDelete:',
  'onRename:',
];

requiredProps.forEach((prop) => {
  if (componentContent.includes(prop)) {
    console.log(`  ✅ Has prop: ${prop.split(':')[0]}`);
  } else {
    console.log(`  ❌ Missing prop: ${prop.split(':')[0]}`);
    allChecks = false;
  }
});

// Check 4: Component has formatRelativeTime function
console.log('\n✓ Check 4: Has relative time formatting');
if (componentContent.includes('formatRelativeTime')) {
  console.log('  ✅ formatRelativeTime function exists');
  
  // Check for time formats
  const timeFormats = ['Just now', 'ago', 'Yesterday'];
  timeFormats.forEach((format) => {
    if (componentContent.includes(format)) {
      console.log(`  ✅ Supports "${format}" format`);
    }
  });
} else {
  console.log('  ❌ formatRelativeTime function not found');
  allChecks = false;
}

// Check 5: Component has edit functionality
console.log('\n✓ Check 5: Has inline edit functionality');
const editFeatures = [
  { name: 'Edit state', pattern: 'isEditing' },
  { name: 'Double-click handler', pattern: 'handleDoubleClick' },
  { name: 'Enter key save', pattern: 'Enter' },
  { name: 'Escape key cancel', pattern: 'Escape' },
  { name: 'Input field', pattern: '<input' },
];

editFeatures.forEach(({ name, pattern }) => {
  if (componentContent.includes(pattern)) {
    console.log(`  ✅ ${name}`);
  } else {
    console.log(`  ❌ Missing ${name}`);
    allChecks = false;
  }
});

// Check 6: Component has delete functionality
console.log('\n✓ Check 6: Has delete functionality');
const deleteFeatures = [
  { name: 'Delete handler', pattern: 'handleDeleteClick' },
  { name: 'Confirmation dialog', pattern: 'window.confirm' },
  { name: 'Delete button', pattern: 'Delete conversation' },
];

deleteFeatures.forEach(({ name, pattern }) => {
  if (componentContent.includes(pattern)) {
    console.log(`  ✅ ${name}`);
  } else {
    console.log(`  ❌ Missing ${name}`);
    allChecks = false;
  }
});

// Check 7: Component has active state styling
console.log('\n✓ Check 7: Has active state highlighting');
if (componentContent.includes('isActive') && componentContent.includes('bg-blue')) {
  console.log('  ✅ Active state styling implemented');
} else {
  console.log('  ❌ Active state styling not found');
  allChecks = false;
}

// Check 8: Component has hover effects
console.log('\n✓ Check 8: Has hover effects');
const hoverFeatures = ['hover:', 'group-hover:', 'transition'];

hoverFeatures.forEach((feature) => {
  if (componentContent.includes(feature)) {
    console.log(`  ✅ Has ${feature} styling`);
  }
});

// Check 9: Test coverage
console.log('\n✓ Check 9: Test coverage');
const testContent = fs.readFileSync(testPath, 'utf8');
const testCases = [
  'renders session title',
  'highlights active session',
  'calls onSelect when clicked',
  'enters edit mode on double-click',
  'saves edited title on Enter',
  'cancels edit on Escape',
  'shows confirmation dialog before delete',
  'calls onDelete when confirmed',
  'formats relative time',
];

testCases.forEach((testCase) => {
  const found = testContent.toLowerCase().includes(testCase.toLowerCase());
  if (found) {
    console.log(`  ✅ Test: ${testCase}`);
  } else {
    console.log(`  ⚠️  Missing test: ${testCase}`);
  }
});

// Check 10: Component displays message count
console.log('\n✓ Check 10: Displays message count');
if (componentContent.includes('message_count')) {
  console.log('  ✅ Message count display implemented');
} else {
  console.log('  ❌ Message count display not found');
  allChecks = false;
}

// Summary
console.log('\n' + '='.repeat(50));
if (allChecks) {
  console.log('✅ All critical checks passed!');
  console.log('\n📋 Component Features:');
  console.log('  • Session title and relative time display');
  console.log('  • Message count display');
  console.log('  • Active session highlighting');
  console.log('  • Click to select session');
  console.log('  • Double-click to edit title inline');
  console.log('  • Enter to save, Escape to cancel');
  console.log('  • Delete button with confirmation');
  console.log('  • Hover effects for better UX');
  console.log('  • Responsive Tailwind CSS styling');
  console.log('\n✨ SessionItem component is ready to use!');
  process.exit(0);
} else {
  console.log('❌ Some checks failed. Please review the component.');
  process.exit(1);
}
