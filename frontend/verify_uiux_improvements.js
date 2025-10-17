/**
 * Verification script for UI/UX improvements
 */

const fs = require('fs');
const path = require('path');

console.log('='.repeat(70));
console.log('UI/UX IMPROVEMENTS VERIFICATION');
console.log('='.repeat(70));

let allPassed = true;

// Check 1: Tabs component
console.log('\n=== Checking Tabs Component ===');
const tabsPath = path.join(__dirname, 'components/ui/Tabs.tsx');
if (fs.existsSync(tabsPath)) {
  const content = fs.readFileSync(tabsPath, 'utf8');
  if (content.includes('TabsList') && content.includes('TabsTrigger') && content.includes('TabsContent')) {
    console.log('✅ Tabs component created with all sub-components');
  } else {
    console.log('❌ Tabs component incomplete');
    allPassed = false;
  }
} else {
  console.log('❌ Tabs component not found');
  allPassed = false;
}

// Check 2: EmptyState component
console.log('\n=== Checking EmptyState Component ===');
const emptyStatePath = path.join(__dirname, 'components/ui/EmptyState.tsx');
if (fs.existsSync(emptyStatePath)) {
  const content = fs.readFileSync(emptyStatePath, 'utf8');
  if (content.includes('EmptyState') && content.includes('actions') && content.includes('examples')) {
    console.log('✅ EmptyState component created with actions and examples');
  } else {
    console.log('❌ EmptyState component incomplete');
    allPassed = false;
  }
} else {
  console.log('❌ EmptyState component not found');
  allPassed = false;
}

// Check 3: LoadingState component
console.log('\n=== Checking LoadingState Component ===');
const loadingStatePath = path.join(__dirname, 'components/ui/LoadingState.tsx');
if (fs.existsSync(loadingStatePath)) {
  const content = fs.readFileSync(loadingStatePath, 'utf8');
  if (content.includes('spinner') && content.includes('dots') && content.includes('pulse')) {
    console.log('✅ LoadingState component created with multiple variants');
  } else {
    console.log('❌ LoadingState component incomplete');
    allPassed = false;
  }
} else {
  console.log('❌ LoadingState component not found');
  allPassed = false;
}

// Check 4: ErrorState component
console.log('\n=== Checking ErrorState Component ===');
const errorStatePath = path.join(__dirname, 'components/ui/ErrorState.tsx');
if (fs.existsSync(errorStatePath)) {
  const content = fs.readFileSync(errorStatePath, 'utf8');
  if (content.includes('ErrorState') && content.includes('actions') && content.includes('details')) {
    console.log('✅ ErrorState component created with actions and details');
  } else {
    console.log('❌ ErrorState component incomplete');
    allPassed = false;
  }
} else {
  console.log('❌ ErrorState component not found');
  allPassed = false;
}

// Check 5: Drawer component
console.log('\n=== Checking Drawer Component ===');
const drawerPath = path.join(__dirname, 'components/ui/Drawer.tsx');
if (fs.existsSync(drawerPath)) {
  const content = fs.readFileSync(drawerPath, 'utf8');
  if (content.includes('Drawer') && content.includes('Backdrop') && content.includes('Escape')) {
    console.log('✅ Drawer component created with backdrop and keyboard support');
  } else {
    console.log('❌ Drawer component incomplete');
    allPassed = false;
  }
} else {
  console.log('❌ Drawer component not found');
  allPassed = false;
}

// Check 6: Page.tsx integration
console.log('\n=== Checking Page Integration ===');
const pagePath = path.join(__dirname, 'app/page.tsx');
if (fs.existsSync(pagePath)) {
  const content = fs.readFileSync(pagePath, 'utf8');
  
  const checks = [
    { name: 'Tabs import', pattern: /import.*Tabs.*from/ },
    { name: 'Drawer import', pattern: /import.*Drawer.*from/ },
    { name: 'Mobile tabs', pattern: /TabsList|TabsTrigger|TabsContent/ },
    { name: 'Desktop layout', pattern: /hidden lg:grid/ },
    { name: 'Mobile menu button', pattern: /setShowSidebar/ }
  ];
  
  checks.forEach(check => {
    if (check.pattern.test(content)) {
      console.log(`✅ ${check.name} integrated`);
    } else {
      console.log(`❌ ${check.name} not found`);
      allPassed = false;
    }
  });
} else {
  console.log('❌ Page.tsx not found');
  allPassed = false;
}

// Check 7: MessageList integration
console.log('\n=== Checking MessageList Integration ===');
const messageListPath = path.join(__dirname, 'components/MessageList.tsx');
if (fs.existsSync(messageListPath)) {
  const content = fs.readFileSync(messageListPath, 'utf8');
  if (content.includes('EmptyState') && content.includes('examples')) {
    console.log('✅ EmptyState integrated in MessageList');
  } else {
    console.log('❌ EmptyState not integrated in MessageList');
    allPassed = false;
  }
} else {
  console.log('❌ MessageList.tsx not found');
  allPassed = false;
}

// Check 8: DocumentUpload search feature
console.log('\n=== Checking DocumentUpload Search Feature ===');
const docUploadPath = path.join(__dirname, 'components/DocumentUpload.tsx');
if (fs.existsSync(docUploadPath)) {
  const content = fs.readFileSync(docUploadPath, 'utf8');
  
  const checks = [
    { name: 'Search state', pattern: /searchQuery/ },
    { name: 'Status filter', pattern: /statusFilter/ },
    { name: 'Search input', pattern: /Search documents/ },
    { name: 'Filter buttons', pattern: /completed.*processing.*failed/ }
  ];
  
  checks.forEach(check => {
    if (check.pattern.test(content)) {
      console.log(`✅ ${check.name} implemented`);
    } else {
      console.log(`❌ ${check.name} not found`);
      allPassed = false;
    }
  });
} else {
  console.log('❌ DocumentUpload.tsx not found');
  allPassed = false;
}

// Summary
console.log('\n' + '='.repeat(70));
console.log('VERIFICATION SUMMARY');
console.log('='.repeat(70));

if (allPassed) {
  console.log('✅ ALL CHECKS PASSED');
  console.log('='.repeat(70));
  process.exit(0);
} else {
  console.log('❌ SOME CHECKS FAILED');
  console.log('='.repeat(70));
  process.exit(1);
}
