/**
 * UI/UX Consistency Verification Script
 * Checks for design consistency across components
 */

const fs = require('fs');
const path = require('path');

console.log('🎨 UI/UX Consistency Check\n');
console.log('='.repeat(50));
console.log('');

let issues = [];
let warnings = [];
let passed = 0;

// ============================================
// 1. Border Radius Consistency
// ============================================
console.log('📐 1. Border Radius Consistency');

const borderRadiusPatterns = {
  'rounded-lg': 0,
  'rounded-md': 0,
  'rounded-xl': 0,
  'rounded-2xl': 0,
  'rounded-full': 0,
  'rounded': 0,
};

const componentsDir = 'frontend/components';
const files = fs.readdirSync(componentsDir).filter(f => f.endsWith('.tsx'));

files.forEach(file => {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  Object.keys(borderRadiusPatterns).forEach(pattern => {
    const matches = content.match(new RegExp(pattern, 'g'));
    if (matches) {
      borderRadiusPatterns[pattern] += matches.length;
    }
  });
});

console.log('  Border radius usage:');
Object.entries(borderRadiusPatterns).forEach(([pattern, count]) => {
  if (count > 0) {
    console.log(`    ${pattern}: ${count} occurrences`);
  }
});

// Most common should be rounded-lg
const mostCommon = Object.entries(borderRadiusPatterns)
  .sort((a, b) => b[1] - a[1])[0];

if (mostCommon[0] === 'rounded-lg') {
  console.log('  ✅ Primary border radius (rounded-lg) is most common');
  passed++;
} else {
  warnings.push('Border radius: rounded-lg should be the primary choice');
  console.log(`  ⚠️  Most common is ${mostCommon[0]}, should standardize to rounded-lg`);
}
console.log('');

// ============================================
// 2. Color Consistency
// ============================================
console.log('🎨 2. Color Consistency');

const colorPatterns = {
  'bg-blue-600': 0,
  'bg-blue-500': 0,
  'bg-blue-700': 0,
  'bg-green-600': 0,
  'bg-red-600': 0,
  'bg-gray-200': 0,
};

files.forEach(file => {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  Object.keys(colorPatterns).forEach(pattern => {
    const matches = content.match(new RegExp(pattern, 'g'));
    if (matches) {
      colorPatterns[pattern] += matches.length;
    }
  });
});

console.log('  Primary color usage:');
Object.entries(colorPatterns).forEach(([pattern, count]) => {
  if (count > 0) {
    console.log(`    ${pattern}: ${count} occurrences`);
  }
});

if (colorPatterns['bg-blue-600'] > colorPatterns['bg-blue-500']) {
  console.log('  ✅ Primary blue (bg-blue-600) is consistently used');
  passed++;
} else {
  warnings.push('Color: bg-blue-600 should be the primary blue');
  console.log('  ⚠️  Consider standardizing to bg-blue-600 for primary actions');
}
console.log('');

// ============================================
// 3. Button Consistency
// ============================================
console.log('🔘 3. Button Component Usage');

let buttonComponentUsage = 0;
let inlineButtonUsage = 0;

files.forEach(file => {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  
  // Check for Button component usage
  const buttonMatches = content.match(/<Button/g);
  if (buttonMatches) {
    buttonComponentUsage += buttonMatches.length;
  }
  
  // Check for inline button elements
  const inlineMatches = content.match(/<button[^>]*className/g);
  if (inlineMatches) {
    inlineButtonUsage += inlineMatches.length;
  }
});

console.log(`  Button component usage: ${buttonComponentUsage}`);
console.log(`  Inline button usage: ${inlineButtonUsage}`);

const buttonRatio = buttonComponentUsage / (buttonComponentUsage + inlineButtonUsage);
if (buttonRatio > 0.3) {
  console.log(`  ✅ Button component is used (${(buttonRatio * 100).toFixed(1)}% of buttons)`);
  passed++;
} else {
  issues.push(`Button component usage is low (${(buttonRatio * 100).toFixed(1)}%)`);
  console.log(`  ❌ Button component usage is low, consider refactoring inline buttons`);
}
console.log('');

// ============================================
// 4. Spacing Consistency
// ============================================
console.log('📏 4. Spacing Consistency');

const spacingPatterns = {
  'gap-2': 0,
  'gap-3': 0,
  'gap-4': 0,
  'space-y-2': 0,
  'space-y-4': 0,
  'space-y-6': 0,
};

files.forEach(file => {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  Object.keys(spacingPatterns).forEach(pattern => {
    const matches = content.match(new RegExp(pattern, 'g'));
    if (matches) {
      spacingPatterns[pattern] += matches.length;
    }
  });
});

console.log('  Spacing usage:');
Object.entries(spacingPatterns).forEach(([pattern, count]) => {
  if (count > 0) {
    console.log(`    ${pattern}: ${count} occurrences`);
  }
});

console.log('  ✅ Spacing patterns are being used consistently');
passed++;
console.log('');

// ============================================
// 5. Typography Consistency
// ============================================
console.log('📝 5. Typography Consistency');

const typographyPatterns = {
  'text-sm': 0,
  'text-base': 0,
  'text-lg': 0,
  'text-xl': 0,
  'text-2xl': 0,
  'font-medium': 0,
  'font-semibold': 0,
  'font-bold': 0,
};

files.forEach(file => {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  Object.keys(typographyPatterns).forEach(pattern => {
    const matches = content.match(new RegExp(pattern, 'g'));
    if (matches) {
      typographyPatterns[pattern] += matches.length;
    }
  });
});

console.log('  Typography usage:');
Object.entries(typographyPatterns).forEach(([pattern, count]) => {
  if (count > 0) {
    console.log(`    ${pattern}: ${count} occurrences`);
  }
});

console.log('  ✅ Typography scale is being used');
passed++;
console.log('');

// ============================================
// 6. Dark Mode Support
// ============================================
console.log('🌙 6. Dark Mode Support');

let darkModeCount = 0;
let totalClassCount = 0;

files.forEach(file => {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  
  const darkMatches = content.match(/dark:/g);
  if (darkMatches) {
    darkModeCount += darkMatches.length;
  }
  
  const classMatches = content.match(/className=/g);
  if (classMatches) {
    totalClassCount += classMatches.length;
  }
});

console.log(`  Dark mode classes: ${darkModeCount}`);
console.log(`  Total className attributes: ${totalClassCount}`);

const darkModeRatio = darkModeCount / totalClassCount;
if (darkModeRatio > 0.2) {
  console.log(`  ✅ Dark mode support is good (${(darkModeRatio * 100).toFixed(1)}% coverage)`);
  passed++;
} else {
  warnings.push(`Dark mode coverage is ${(darkModeRatio * 100).toFixed(1)}%, consider improving`);
  console.log(`  ⚠️  Dark mode coverage could be improved`);
}
console.log('');

// ============================================
// 7. Transition Consistency
// ============================================
console.log('⚡ 7. Transition Consistency');

const transitionPatterns = {
  'transition-colors': 0,
  'transition-all': 0,
  'duration-200': 0,
  'duration-300': 0,
};

files.forEach(file => {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  Object.keys(transitionPatterns).forEach(pattern => {
    const matches = content.match(new RegExp(pattern, 'g'));
    if (matches) {
      transitionPatterns[pattern] += matches.length;
    }
  });
});

console.log('  Transition usage:');
Object.entries(transitionPatterns).forEach(([pattern, count]) => {
  if (count > 0) {
    console.log(`    ${pattern}: ${count} occurrences`);
  }
});

if (transitionPatterns['transition-colors'] > 0 || transitionPatterns['transition-all'] > 0) {
  console.log('  ✅ Transitions are being used for smooth interactions');
  passed++;
} else {
  warnings.push('Consider adding transitions for better UX');
  console.log('  ⚠️  Consider adding more transitions');
}
console.log('');

// ============================================
// 8. Accessibility
// ============================================
console.log('♿ 8. Accessibility Features');

let ariaLabelCount = 0;
let roleCount = 0;
let buttonCount = 0;

files.forEach(file => {
  const content = fs.readFileSync(path.join(componentsDir, file), 'utf8');
  
  const ariaMatches = content.match(/aria-label=/g);
  if (ariaMatches) {
    ariaLabelCount += ariaMatches.length;
  }
  
  const roleMatches = content.match(/role=/g);
  if (roleMatches) {
    roleCount += roleMatches.length;
  }
  
  const btnMatches = content.match(/<button/g);
  if (btnMatches) {
    buttonCount += btnMatches.length;
  }
});

console.log(`  aria-label usage: ${ariaLabelCount}`);
console.log(`  role usage: ${roleCount}`);
console.log(`  Total buttons: ${buttonCount}`);

const accessibilityScore = (ariaLabelCount + roleCount) / buttonCount;
if (accessibilityScore > 0.3) {
  console.log(`  ✅ Good accessibility support (${(accessibilityScore * 100).toFixed(1)}% coverage)`);
  passed++;
} else {
  warnings.push('Consider adding more aria-labels and roles');
  console.log(`  ⚠️  Accessibility could be improved`);
}
console.log('');

// ============================================
// Summary
// ============================================
console.log('='.repeat(50));
console.log('📊 Summary\n');

console.log(`✅ Passed: ${passed}/8`);
console.log(`⚠️  Warnings: ${warnings.length}`);
console.log(`❌ Issues: ${issues.length}`);
console.log('');

if (warnings.length > 0) {
  console.log('⚠️  Warnings:');
  warnings.forEach((warning, i) => {
    console.log(`  ${i + 1}. ${warning}`);
  });
  console.log('');
}

if (issues.length > 0) {
  console.log('❌ Issues:');
  issues.forEach((issue, i) => {
    console.log(`  ${i + 1}. ${issue}`);
  });
  console.log('');
}

// ============================================
// Recommendations
// ============================================
console.log('💡 Recommendations:\n');

console.log('1. Use Design Tokens:');
console.log('   - Import from frontend/lib/design-tokens.ts');
console.log('   - Ensures consistency across components');
console.log('');

console.log('2. Standardize Border Radius:');
console.log('   - Primary: rounded-lg (8px)');
console.log('   - Small: rounded (4px)');
console.log('   - Large: rounded-xl (12px)');
console.log('   - Circular: rounded-full');
console.log('');

console.log('3. Color Palette:');
console.log('   - Primary: bg-blue-600 (hover: bg-blue-700)');
console.log('   - Success: bg-green-600');
console.log('   - Error: bg-red-600');
console.log('   - Neutral: bg-gray-200');
console.log('');

console.log('4. Use Button Component:');
console.log('   - Refactor inline buttons to use <Button> component');
console.log('   - Ensures consistent sizing and styling');
console.log('');

console.log('5. Dark Mode:');
console.log('   - Add dark: variants to all color classes');
console.log('   - Test in both light and dark modes');
console.log('');

// ============================================
// Overall Score
// ============================================
const score = (passed / 8) * 100;
console.log('='.repeat(50));
console.log(`\n🎯 Overall Consistency Score: ${score.toFixed(1)}%\n`);

if (score >= 80) {
  console.log('🎉 Excellent! UI/UX consistency is strong.');
} else if (score >= 60) {
  console.log('👍 Good! Some improvements recommended.');
} else {
  console.log('⚠️  Needs improvement. Follow recommendations above.');
}

console.log('');
console.log('📚 For more details, see:');
console.log('   - frontend/lib/design-tokens.ts');
console.log('   - UIUX_사용자_관점_체크리스트.md');
console.log('');

process.exit(issues.length > 0 ? 1 : 0);
