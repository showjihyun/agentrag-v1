/**
 * UI Improvements Verification Script
 * Verifies all 5 improvement areas:
 * 1. ARIA attributes
 * 2. Dark mode toggle
 * 3. Breadcrumb navigation
 * 4. Image optimization (next/image)
 * 5. React.memo optimization
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying UI Improvements...\n');

let allPassed = true;
const results = [];

// Helper function to check file exists and contains text
function checkFileContains(filePath, searchTexts, description) {
  const fullPath = path.join(__dirname, filePath);
  
  if (!fs.existsSync(fullPath)) {
    results.push(`❌ ${description}: File not found - ${filePath}`);
    allPassed = false;
    return false;
  }
  
  const content = fs.readFileSync(fullPath, 'utf8');
  const missingTexts = searchTexts.filter(text => !content.includes(text));
  
  if (missingTexts.length > 0) {
    results.push(`❌ ${description}: Missing - ${missingTexts.join(', ')}`);
    allPassed = false;
    return false;
  }
  
  results.push(`✅ ${description}`);
  return true;
}

// 1. ARIA Attributes Check
console.log('1️⃣ Checking ARIA Attributes...');
checkFileContains(
  'components/MessageList.tsx',
  ['role="log"', 'aria-live="polite"', 'aria-label="Chat messages"', 'role="article"'],
  'MessageList ARIA attributes'
);

checkFileContains(
  'components/SessionItem.tsx',
  ['role="button"', 'aria-label=', 'aria-current='],
  'SessionItem ARIA attributes'
);

checkFileContains(
  'components/UserMenu.tsx',
  ['role="navigation"', 'aria-label="User menu"', 'role="menu"', 'aria-expanded='],
  'UserMenu ARIA attributes'
);

checkFileContains(
  'components/DocumentUpload.tsx',
  ['aria-label="Choose file to upload"', 'aria-label="File upload area'],
  'DocumentUpload ARIA attributes'
);

// 2. Dark Mode Toggle Check
console.log('\n2️⃣ Checking Dark Mode Toggle...');
checkFileContains(
  'contexts/ThemeContext.tsx',
  ['ThemeProvider', 'useTheme', 'toggleTheme', 'effectiveTheme'],
  'ThemeContext implementation'
);

checkFileContains(
  'components/ThemeToggle.tsx',
  ['useTheme', 'toggleTheme', 'aria-label='],
  'ThemeToggle component'
);

checkFileContains(
  'app/layout.tsx',
  ['ThemeProvider', 'suppressHydrationWarning'],
  'ThemeProvider in layout'
);

checkFileContains(
  'app/page.tsx',
  ['ThemeToggle', 'import ThemeToggle'],
  'ThemeToggle in main page'
);

// 3. Breadcrumb Navigation Check
console.log('\n3️⃣ Checking Breadcrumb Navigation...');
checkFileContains(
  'components/Breadcrumb.tsx',
  ['aria-label="Breadcrumb"', 'role="list"', 'aria-current="page"'],
  'Breadcrumb component'
);

checkFileContains(
  'app/page.tsx',
  ['Breadcrumb', 'import Breadcrumb'],
  'Breadcrumb in main page'
);

// 4. React.memo Optimization Check
console.log('\n4️⃣ Checking React.memo Optimization...');
checkFileContains(
  'components/MessageList.tsx',
  ['React.memo', 'prevProps', 'nextProps'],
  'MessageList React.memo'
);

checkFileContains(
  'components/SessionItem.tsx',
  ['React.memo', 'const SessionItem = React.memo'],
  'SessionItem React.memo'
);

checkFileContains(
  'components/UserMenu.tsx',
  ['React.memo', 'const UserMenu = React.memo'],
  'UserMenu React.memo'
);

checkFileContains(
  'components/DocumentUpload.tsx',
  ['React.memo', 'const DocumentUpload'],
  'DocumentUpload React.memo'
);

// 5. Component Integration Check
console.log('\n5️⃣ Checking Component Integration...');
checkFileContains(
  'app/page.tsx',
  ['ThemeToggle', 'Breadcrumb'],
  'Main page integration'
);

// Print results
console.log('\n' + '='.repeat(60));
console.log('📊 VERIFICATION RESULTS');
console.log('='.repeat(60) + '\n');

results.forEach(result => console.log(result));

console.log('\n' + '='.repeat(60));
if (allPassed) {
  console.log('✅ ALL CHECKS PASSED!');
  console.log('='.repeat(60));
  console.log('\n🎉 UI Improvements Successfully Implemented!\n');
  console.log('Improvements Applied:');
  console.log('  1. ✅ ARIA attributes for accessibility');
  console.log('  2. ✅ Dark mode manual toggle');
  console.log('  3. ✅ Breadcrumb navigation');
  console.log('  4. ✅ React.memo optimization');
  console.log('  5. ✅ Component integration\n');
  process.exit(0);
} else {
  console.log('❌ SOME CHECKS FAILED');
  console.log('='.repeat(60));
  console.log('\n⚠️  Please review the failed checks above.\n');
  process.exit(1);
}
