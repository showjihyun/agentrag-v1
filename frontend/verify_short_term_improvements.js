/**
 * Verification script for short-term frontend improvements:
 * 1. Performance hooks
 * 2. Accessibility hooks
 * 3. Error pages (loading, error, not-found)
 * 4. Accessibility improvements
 */

const fs = require('fs');
const path = require('path');

console.log('='.repeat(70));
console.log('VERIFICATION: Short-Term Frontend Improvements');
console.log('='.repeat(70));
console.log();

let allPassed = true;

// 1. Check Performance Hooks
console.log('1. Checking Performance Hooks...');
const perfHooksPath = path.join(__dirname, 'lib', 'hooks', 'usePerformance.ts');
if (fs.existsSync(perfHooksPath)) {
  const content = fs.readFileSync(perfHooksPath, 'utf8');
  
  const checks = [
    { name: 'useDebounce', pattern: /export function useDebounce/ },
    { name: 'useThrottle', pattern: /export function useThrottle/ },
    { name: 'useIntersectionObserver', pattern: /export function useIntersectionObserver/ },
    { name: 'usePrevious', pattern: /export function usePrevious/ },
    { name: 'useIsMounted', pattern: /export function useIsMounted/ },
  ];
  
  checks.forEach(check => {
    if (check.pattern.test(content)) {
      console.log(`   ✓ ${check.name}`);
    } else {
      console.log(`   ✗ ${check.name}`);
      allPassed = false;
    }
  });
} else {
  console.log('   ✗ usePerformance.ts not found');
  allPassed = false;
}
console.log();

// 2. Check Accessibility Hooks
console.log('2. Checking Accessibility Hooks...');
const a11yHooksPath = path.join(__dirname, 'lib', 'hooks', 'useAccessibility.ts');
if (fs.existsSync(a11yHooksPath)) {
  const content = fs.readFileSync(a11yHooksPath, 'utf8');
  
  const checks = [
    { name: 'useFocusTrap', pattern: /export function useFocusTrap/ },
    { name: 'useKeyboardNavigation', pattern: /export function useKeyboardNavigation/ },
    { name: 'useAnnounce', pattern: /export function useAnnounce/ },
    { name: 'useSkipToContent', pattern: /export function useSkipToContent/ },
    { name: 'usePrefersReducedMotion', pattern: /export function usePrefersReducedMotion/ },
  ];
  
  checks.forEach(check => {
    if (check.pattern.test(content)) {
      console.log(`   ✓ ${check.name}`);
    } else {
      console.log(`   ✗ ${check.name}`);
      allPassed = false;
    }
  });
} else {
  console.log('   ✗ useAccessibility.ts not found');
  allPassed = false;
}
console.log();

// 3. Check Error Pages
console.log('3. Checking Error Pages...');
const errorPages = [
  { name: 'loading.tsx', path: path.join(__dirname, 'app', 'loading.tsx') },
  { name: 'error.tsx', path: path.join(__dirname, 'app', 'error.tsx') },
  { name: 'not-found.tsx', path: path.join(__dirname, 'app', 'not-found.tsx') },
];

errorPages.forEach(page => {
  if (fs.existsSync(page.path)) {
    console.log(`   ✓ ${page.name}`);
  } else {
    console.log(`   ✗ ${page.name}`);
    allPassed = false;
  }
});
console.log();

// 4. Check SkipToContent Component
console.log('4. Checking SkipToContent Component...');
const skipToContentPath = path.join(__dirname, 'components', 'SkipToContent.tsx');
if (fs.existsSync(skipToContentPath)) {
  const content = fs.readFileSync(skipToContentPath, 'utf8');
  
  const checks = [
    { name: 'Component export', pattern: /export default function SkipToContent/ },
    { name: 'Skip link', pattern: /href="#main-content"/ },
    { name: 'SR-only class', pattern: /sr-only/ },
    { name: 'Focus styles', pattern: /focus:/ },
    { name: 'ARIA label', pattern: /aria-label/ },
  ];
  
  checks.forEach(check => {
    if (check.pattern.test(content)) {
      console.log(`   ✓ ${check.name}`);
    } else {
      console.log(`   ✗ ${check.name}`);
      allPassed = false;
    }
  });
} else {
  console.log('   ✗ SkipToContent.tsx not found');
  allPassed = false;
}
console.log();

// 5. Check Layout Integration
console.log('5. Checking Layout Integration...');
const layoutPath = path.join(__dirname, 'app', 'layout.tsx');
if (fs.existsSync(layoutPath)) {
  const content = fs.readFileSync(layoutPath, 'utf8');
  
  const checks = [
    { name: 'SkipToContent import', pattern: /import SkipToContent/ },
    { name: 'SkipToContent usage', pattern: /<SkipToContent \/>/ },
  ];
  
  checks.forEach(check => {
    if (check.pattern.test(content)) {
      console.log(`   ✓ ${check.name}`);
    } else {
      console.log(`   ✗ ${check.name}`);
      allPassed = false;
    }
  });
} else {
  console.log('   ✗ layout.tsx not found');
  allPassed = false;
}
console.log();

// 6. Check Main Content ID
console.log('6. Checking Main Content Accessibility...');
const pagePath = path.join(__dirname, 'app', 'page.tsx');
if (fs.existsSync(pagePath)) {
  const content = fs.readFileSync(pagePath, 'utf8');
  
  const checks = [
    { name: 'main-content ID', pattern: /id="main-content"/ },
    { name: 'tabIndex', pattern: /tabIndex={-1}/ },
  ];
  
  checks.forEach(check => {
    if (check.pattern.test(content)) {
      console.log(`   ✓ ${check.name}`);
    } else {
      console.log(`   ✗ ${check.name}`);
      allPassed = false;
    }
  });
} else {
  console.log('   ✗ page.tsx not found');
  allPassed = false;
}
console.log();

// Summary
console.log('='.repeat(70));
console.log('VERIFICATION SUMMARY');
console.log('='.repeat(70));
console.log();

if (allPassed) {
  console.log('✓ ALL CHECKS PASSED');
  console.log();
  console.log('Short-Term Frontend Improvements Complete!');
  console.log();
  console.log('✅ 1. Performance Hooks');
  console.log('   • useDebounce - Debounce expensive operations');
  console.log('   • useThrottle - Rate-limit operations');
  console.log('   • useIntersectionObserver - Lazy loading');
  console.log('   • usePrevious - Compare with previous value');
  console.log('   • useIsMounted - Check mount status');
  console.log();
  console.log('✅ 2. Accessibility Hooks');
  console.log('   • useFocusTrap - Trap focus in modals');
  console.log('   • useKeyboardNavigation - Keyboard shortcuts');
  console.log('   • useAnnounce - Screen reader announcements');
  console.log('   • useSkipToContent - Skip navigation');
  console.log('   • usePrefersReducedMotion - Respect user preferences');
  console.log();
  console.log('✅ 3. Error Pages');
  console.log('   • loading.tsx - Loading state');
  console.log('   • error.tsx - Error boundary');
  console.log('   • not-found.tsx - 404 page');
  console.log();
  console.log('✅ 4. Accessibility Improvements');
  console.log('   • Skip to content link');
  console.log('   • Main content landmark');
  console.log('   • Keyboard focus management');
  console.log('   • ARIA labels');
  console.log();
  console.log('Features Now Available:');
  console.log('  • Performance optimization hooks ready to use');
  console.log('  • Accessibility hooks for better UX');
  console.log('  • Proper error handling pages');
  console.log('  • Keyboard navigation support');
  console.log('  • Screen reader support');
  console.log();
  console.log('Usage Examples:');
  console.log();
  console.log('// Performance');
  console.log('const debouncedSearch = useDebounce(handleSearch, 300);');
  console.log('const throttledScroll = useThrottle(handleScroll, 100);');
  console.log();
  console.log('// Accessibility');
  console.log('const containerRef = useFocusTrap(isModalOpen);');
  console.log('const announce = useAnnounce();');
  console.log('announce("Message sent successfully");');
  console.log();
  console.log('Next Steps:');
  console.log('  1. Apply React.memo to components');
  console.log('  2. Add useMemo/useCallback where needed');
  console.log('  3. Test keyboard navigation');
  console.log('  4. Test with screen reader');
  console.log('  5. Proceed to medium-term improvements');
  console.log();
  process.exit(0);
} else {
  console.log('✗ SOME CHECKS FAILED');
  console.log();
  console.log('Please review the failed checks above and fix any issues.');
  console.log();
  process.exit(1);
}
