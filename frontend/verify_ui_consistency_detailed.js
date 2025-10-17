#!/usr/bin/env node

/**
 * UI/UX Consistency Verification Script
 * 
 * This script checks for common UI/UX consistency issues:
 * - Hardcoded colors
 * - Missing dark mode support
 * - Inconsistent button styles
 * - Inconsistent form input styles
 * - Missing accessibility attributes
 * - Inconsistent spacing
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

// Issue severity levels
const SEVERITY = {
  CRITICAL: 'CRITICAL',
  HIGH: 'HIGH',
  MEDIUM: 'MEDIUM',
  LOW: 'LOW',
};

// Results storage
const results = {
  critical: [],
  high: [],
  medium: [],
  low: [],
  passed: [],
};

/**
 * Check for hardcoded hex colors
 */
function checkHardcodedColors(filePath, content) {
  const hexColorRegex = /#[0-9a-fA-F]{3,6}/g;
  const matches = content.match(hexColorRegex);
  
  if (matches && matches.length > 0) {
    const lines = content.split('\n');
    const issues = [];
    
    lines.forEach((line, index) => {
      const lineMatches = line.match(hexColorRegex);
      if (lineMatches) {
        issues.push({
          line: index + 1,
          content: line.trim(),
          colors: lineMatches,
        });
      }
    });
    
    results.medium.push({
      file: filePath,
      issue: 'Hardcoded hex colors found',
      severity: SEVERITY.MEDIUM,
      details: issues,
      recommendation: 'Use Tailwind color classes or design tokens instead',
    });
    
    return false;
  }
  
  return true;
}

/**
 * Check for dark mode support
 */
function checkDarkModeSupport(filePath, content) {
  // Check if file has any color classes
  const hasColorClasses = /className=["'][^"']*(?:bg-|text-|border-)[^"']*["']/g.test(content);
  
  if (!hasColorClasses) {
    return true; // No color classes, skip check
  }
  
  // Check if dark mode classes are present
  const hasDarkMode = /dark:/g.test(content);
  
  if (hasColorClasses && !hasDarkMode) {
    results.high.push({
      file: filePath,
      issue: 'Missing dark mode support',
      severity: SEVERITY.HIGH,
      details: 'Component uses color classes but has no dark: variants',
      recommendation: 'Add dark mode variants (e.g., dark:bg-gray-800)',
    });
    
    return false;
  }
  
  return true;
}

/**
 * Check for inline button styles instead of Button component
 */
function checkButtonConsistency(filePath, content) {
  // Look for button elements with inline styles
  const inlineButtonRegex = /<button[^>]*className=["'][^"']*(?:bg-blue|bg-red|bg-green)[^"']*["']/g;
  const matches = content.match(inlineButtonRegex);
  
  if (matches && matches.length > 0) {
    // Check if Button component is imported
    const hasButtonImport = /import.*Button.*from.*['"]\.\/Button['"]/.test(content);
    
    if (!hasButtonImport) {
      results.high.push({
        file: filePath,
        issue: 'Inline button styles instead of Button component',
        severity: SEVERITY.HIGH,
        details: `Found ${matches.length} button(s) with inline styles`,
        recommendation: 'Import and use the Button component for consistency',
      });
      
      return false;
    }
  }
  
  return true;
}

/**
 * Check for inconsistent form input styles
 */
function checkFormInputConsistency(filePath, content) {
  // Look for input elements
  const inputRegex = /<input[^>]*className=["']([^"']*)["']/g;
  const matches = [...content.matchAll(inputRegex)];
  
  if (matches.length > 0) {
    const inputStyles = matches.map(m => m[1]);
    const uniqueStyles = [...new Set(inputStyles)];
    
    // Check if inputVariants is imported
    const hasInputVariants = /import.*inputVariants.*from.*design-tokens/.test(content);
    
    if (uniqueStyles.length > 1 && !hasInputVariants) {
      results.medium.push({
        file: filePath,
        issue: 'Inconsistent form input styles',
        severity: SEVERITY.MEDIUM,
        details: `Found ${uniqueStyles.length} different input styles`,
        recommendation: 'Use inputVariants from design-tokens for consistency',
      });
      
      return false;
    }
  }
  
  return true;
}

/**
 * Check for accessibility attributes
 */
function checkAccessibility(filePath, content) {
  const issues = [];
  
  // Check for buttons without aria-label or text content
  const buttonRegex = /<button[^>]*>[\s]*<svg/g;
  const iconButtons = content.match(buttonRegex);
  
  if (iconButtons) {
    iconButtons.forEach((match) => {
      if (!match.includes('aria-label') && !match.includes('title')) {
        issues.push('Icon button without aria-label or title');
      }
    });
  }
  
  // Check for images without alt text
  const imgRegex = /<img[^>]*>/g;
  const images = content.match(imgRegex);
  
  if (images) {
    images.forEach((match) => {
      if (!match.includes('alt=')) {
        issues.push('Image without alt attribute');
      }
    });
  }
  
  // Check for form inputs without labels
  const inputWithoutLabelRegex = /<input[^>]*id=["']([^"']*)["'][^>]*>/g;
  const inputs = [...content.matchAll(inputWithoutLabelRegex)];
  
  inputs.forEach((match) => {
    const inputId = match[1];
    const labelRegex = new RegExp(`<label[^>]*htmlFor=["']${inputId}["']`, 'g');
    
    if (!labelRegex.test(content)) {
      issues.push(`Input with id="${inputId}" has no associated label`);
    }
  });
  
  if (issues.length > 0) {
    results.medium.push({
      file: filePath,
      issue: 'Accessibility issues found',
      severity: SEVERITY.MEDIUM,
      details: issues,
      recommendation: 'Add proper accessibility attributes',
    });
    
    return false;
  }
  
  return true;
}

/**
 * Check for inconsistent spacing
 */
function checkSpacingConsistency(filePath, content) {
  // Check for custom spacing values (not using Tailwind scale)
  const customSpacingRegex = /(?:p|m|gap)-\[[\d.]+(?:px|rem|em)\]/g;
  const matches = content.match(customSpacingRegex);
  
  if (matches && matches.length > 0) {
    results.low.push({
      file: filePath,
      issue: 'Custom spacing values found',
      severity: SEVERITY.LOW,
      details: `Found ${matches.length} custom spacing value(s): ${[...new Set(matches)].join(', ')}`,
      recommendation: 'Use Tailwind spacing scale (p-4, m-6, etc.) for consistency',
    });
    
    return false;
  }
  
  return true;
}

/**
 * Check for inconsistent heading styles
 */
function checkHeadingConsistency(filePath, content) {
  const h2Regex = /<h2[^>]*className=["']([^"']*)["']/g;
  const matches = [...content.matchAll(h2Regex)];
  
  if (matches.length > 1) {
    const styles = matches.map(m => m[1]);
    const uniqueStyles = [...new Set(styles)];
    
    if (uniqueStyles.length > 1) {
      results.low.push({
        file: filePath,
        issue: 'Inconsistent heading styles',
        severity: SEVERITY.LOW,
        details: `Found ${uniqueStyles.length} different h2 styles`,
        recommendation: 'Standardize heading styles across components',
      });
      
      return false;
    }
  }
  
  return true;
}

/**
 * Scan a single file
 */
function scanFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  const fileName = path.basename(filePath);
  
  let passed = true;
  
  // Run all checks
  passed = checkHardcodedColors(filePath, content) && passed;
  passed = checkDarkModeSupport(filePath, content) && passed;
  passed = checkButtonConsistency(filePath, content) && passed;
  passed = checkFormInputConsistency(filePath, content) && passed;
  passed = checkAccessibility(filePath, content) && passed;
  passed = checkSpacingConsistency(filePath, content) && passed;
  passed = checkHeadingConsistency(filePath, content) && passed;
  
  if (passed) {
    results.passed.push(filePath);
  }
}

/**
 * Recursively scan directory
 */
function scanDirectory(dirPath) {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    
    if (entry.isDirectory()) {
      // Skip node_modules, .next, etc.
      if (!['node_modules', '.next', 'dist', 'build'].includes(entry.name)) {
        scanDirectory(fullPath);
      }
    } else if (entry.isFile()) {
      // Only scan .tsx and .jsx files
      if (/\.(tsx|jsx)$/.test(entry.name)) {
        scanFile(fullPath);
      }
    }
  }
}

/**
 * Print results
 */
function printResults() {
  console.log('\n' + '='.repeat(80));
  console.log(`${colors.cyan}UI/UX Consistency Verification Report${colors.reset}`);
  console.log('='.repeat(80) + '\n');
  
  // Summary
  const totalIssues = results.critical.length + results.high.length + results.medium.length + results.low.length;
  const totalFiles = totalIssues + results.passed.length;
  
  console.log(`${colors.blue}Summary:${colors.reset}`);
  console.log(`  Total files scanned: ${totalFiles}`);
  console.log(`  Files with issues: ${totalIssues}`);
  console.log(`  Files passed: ${results.passed.length}`);
  console.log('');
  
  // Critical issues
  if (results.critical.length > 0) {
    console.log(`${colors.red}🔴 CRITICAL Issues (${results.critical.length}):${colors.reset}`);
    results.critical.forEach((issue, index) => {
      console.log(`\n  ${index + 1}. ${issue.file}`);
      console.log(`     Issue: ${issue.issue}`);
      console.log(`     Details: ${JSON.stringify(issue.details, null, 2)}`);
      console.log(`     Recommendation: ${issue.recommendation}`);
    });
    console.log('');
  }
  
  // High priority issues
  if (results.high.length > 0) {
    console.log(`${colors.yellow}⚠️  HIGH Priority Issues (${results.high.length}):${colors.reset}`);
    results.high.forEach((issue, index) => {
      console.log(`\n  ${index + 1}. ${issue.file}`);
      console.log(`     Issue: ${issue.issue}`);
      console.log(`     Details: ${issue.details}`);
      console.log(`     Recommendation: ${issue.recommendation}`);
    });
    console.log('');
  }
  
  // Medium priority issues
  if (results.medium.length > 0) {
    console.log(`${colors.magenta}ℹ️  MEDIUM Priority Issues (${results.medium.length}):${colors.reset}`);
    results.medium.forEach((issue, index) => {
      console.log(`\n  ${index + 1}. ${issue.file}`);
      console.log(`     Issue: ${issue.issue}`);
      if (Array.isArray(issue.details)) {
        console.log(`     Details: ${issue.details.length} issue(s) found`);
      } else {
        console.log(`     Details: ${issue.details}`);
      }
      console.log(`     Recommendation: ${issue.recommendation}`);
    });
    console.log('');
  }
  
  // Low priority issues
  if (results.low.length > 0) {
    console.log(`${colors.cyan}💡 LOW Priority Issues (${results.low.length}):${colors.reset}`);
    results.low.forEach((issue, index) => {
      console.log(`\n  ${index + 1}. ${issue.file}`);
      console.log(`     Issue: ${issue.issue}`);
      console.log(`     Details: ${issue.details}`);
      console.log(`     Recommendation: ${issue.recommendation}`);
    });
    console.log('');
  }
  
  // Passed files
  if (results.passed.length > 0) {
    console.log(`${colors.green}✅ Passed Files (${results.passed.length}):${colors.reset}`);
    results.passed.forEach((file) => {
      console.log(`  ✓ ${file}`);
    });
    console.log('');
  }
  
  // Final score
  const score = Math.round((results.passed.length / totalFiles) * 100);
  const scoreColor = score >= 80 ? colors.green : score >= 60 ? colors.yellow : colors.red;
  
  console.log('='.repeat(80));
  console.log(`${scoreColor}Consistency Score: ${score}/100${colors.reset}`);
  console.log('='.repeat(80) + '\n');
  
  // Exit code
  if (results.critical.length > 0 || results.high.length > 0) {
    process.exit(1);
  }
}

/**
 * Main execution
 */
function main() {
  const componentsDir = path.join(__dirname, 'components');
  const appDir = path.join(__dirname, 'app');
  
  console.log(`${colors.cyan}Scanning components...${colors.reset}`);
  
  if (fs.existsSync(componentsDir)) {
    scanDirectory(componentsDir);
  }
  
  if (fs.existsSync(appDir)) {
    scanDirectory(appDir);
  }
  
  printResults();
}

// Run the script
main();
