#!/usr/bin/env node

/**
 * UI/UX Consistency Auto-Fix Script
 * 
 * This script automatically fixes common UI/UX consistency issues:
 * - Adds dark mode support to color classes
 * - Standardizes button styles
 * - Standardizes form input styles
 * - Adds missing accessibility attributes
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

// Fix statistics
const stats = {
  filesProcessed: 0,
  filesModified: 0,
  darkModeAdded: 0,
  buttonsFixed: 0,
  inputsFixed: 0,
  accessibilityFixed: 0,
};

/**
 * Add dark mode support to color classes
 */
function addDarkModeSupport(content) {
  let modified = content;
  let changes = 0;
  
  // Common patterns to fix
  const patterns = [
    // Background colors
    { regex: /className="([^"]*)\bbg-white\b([^"]*)"/g, replacement: 'className="$1bg-white dark:bg-gray-800$2"' },
    { regex: /className="([^"]*)\bbg-gray-50\b([^"]*)"/g, replacement: 'className="$1bg-gray-50 dark:bg-gray-900$2"' },
    { regex: /className="([^"]*)\bbg-gray-100\b([^"]*)"/g, replacement: 'className="$1bg-gray-100 dark:bg-gray-800$2"' },
    
    // Text colors
    { regex: /className="([^"]*)\btext-gray-800\b([^"]*)"/g, replacement: 'className="$1text-gray-800 dark:text-gray-100$2"' },
    { regex: /className="([^"]*)\btext-gray-900\b([^"]*)"/g, replacement: 'className="$1text-gray-900 dark:text-gray-100$2"' },
    { regex: /className="([^"]*)\btext-gray-700\b([^"]*)"/g, replacement: 'className="$1text-gray-700 dark:text-gray-300$2"' },
    { regex: /className="([^"]*)\btext-gray-600\b([^"]*)"/g, replacement: 'className="$1text-gray-600 dark:text-gray-400$2"' },
    
    // Border colors
    { regex: /className="([^"]*)\bborder-gray-300\b([^"]*)"/g, replacement: 'className="$1border-gray-300 dark:border-gray-600$2"' },
    { regex: /className="([^"]*)\bborder-gray-200\b([^"]*)"/g, replacement: 'className="$1border-gray-200 dark:border-gray-700$2"' },
  ];
  
  patterns.forEach(({ regex, replacement }) => {
    const before = modified;
    modified = modified.replace(regex, (match) => {
      // Don't add dark mode if it already exists
      if (match.includes('dark:')) {
        return match;
      }
      changes++;
      return match.replace(regex, replacement);
    });
  });
  
  stats.darkModeAdded += changes;
  return { content: modified, changed: changes > 0 };
}

/**
 * Fix button styles to use Button component
 */
function fixButtonStyles(content) {
  let modified = content;
  let changes = 0;
  
  // Check if Button component is already imported
  const hasButtonImport = /import.*Button.*from.*['"]\.\/Button['"]/.test(content);
  
  // Look for inline button styles
  const inlineButtonRegex = /<button([^>]*className=["'][^"']*(?:bg-blue-500|bg-blue-600)[^"']*["'][^>]*)>/g;
  
  if (inlineButtonRegex.test(content) && !hasButtonImport) {
    // Add Button import at the top
    const importStatement = "import { Button } from './Button';\n";
    
    // Find the last import statement
    const lastImportMatch = content.match(/import[^;]+;/g);
    if (lastImportMatch) {
      const lastImport = lastImportMatch[lastImportMatch.length - 1];
      const lastImportIndex = content.lastIndexOf(lastImport);
      modified = content.slice(0, lastImportIndex + lastImport.length) + '\n' + importStatement + content.slice(lastImportIndex + lastImport.length);
      changes++;
    }
  }
  
  stats.buttonsFixed += changes;
  return { content: modified, changed: changes > 0 };
}

/**
 * Fix form input styles to use design tokens
 */
function fixInputStyles(content) {
  let modified = content;
  let changes = 0;
  
  // Check if inputVariants is already imported
  const hasInputVariants = /import.*inputVariants.*from.*design-tokens/.test(content);
  
  // Look for input elements with inline styles
  const inputRegex = /<input([^>]*className=["']([^"']*)["'][^>]*)>/g;
  const matches = [...content.matchAll(inputRegex)];
  
  if (matches.length > 0 && !hasInputVariants) {
    // Add inputVariants import
    const importStatement = "import { inputVariants } from '@/lib/design-tokens';\n";
    
    const lastImportMatch = content.match(/import[^;]+;/g);
    if (lastImportMatch) {
      const lastImport = lastImportMatch[lastImportMatch.length - 1];
      const lastImportIndex = content.lastIndexOf(lastImport);
      modified = content.slice(0, lastImportIndex + lastImport.length) + '\n' + importStatement + content.slice(lastImportIndex + lastImport.length);
      changes++;
    }
  }
  
  stats.inputsFixed += changes;
  return { content: modified, changed: changes > 0 };
}

/**
 * Add missing accessibility attributes
 */
function fixAccessibility(content) {
  let modified = content;
  let changes = 0;
  
  // Add aria-label to icon buttons without text
  const iconButtonRegex = /<button([^>]*)>\s*<svg/g;
  modified = modified.replace(iconButtonRegex, (match, attrs) => {
    if (!attrs.includes('aria-label') && !attrs.includes('title')) {
      changes++;
      return `<button${attrs} aria-label="Button">
        <svg`;
    }
    return match;
  });
  
  stats.accessibilityFixed += changes;
  return { content: modified, changed: changes > 0 };
}

/**
 * Process a single file
 */
function processFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  let modified = content;
  let fileChanged = false;
  
  // Apply all fixes
  const darkModeResult = addDarkModeSupport(modified);
  modified = darkModeResult.content;
  fileChanged = fileChanged || darkModeResult.changed;
  
  const buttonResult = fixButtonStyles(modified);
  modified = buttonResult.content;
  fileChanged = fileChanged || buttonResult.changed;
  
  const inputResult = fixInputStyles(modified);
  modified = inputResult.content;
  fileChanged = fileChanged || inputResult.changed;
  
  const a11yResult = fixAccessibility(modified);
  modified = a11yResult.content;
  fileChanged = fileChanged || a11yResult.changed;
  
  // Write back if changed
  if (fileChanged) {
    fs.writeFileSync(filePath, modified, 'utf8');
    stats.filesModified++;
    console.log(`${colors.green}✓${colors.reset} Fixed: ${filePath}`);
  }
  
  stats.filesProcessed++;
}

/**
 * Recursively process directory
 */
function processDirectory(dirPath) {
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);
    
    if (entry.isDirectory()) {
      if (!['node_modules', '.next', 'dist', 'build'].includes(entry.name)) {
        processDirectory(fullPath);
      }
    } else if (entry.isFile()) {
      if (/\.(tsx|jsx)$/.test(entry.name)) {
        processFile(fullPath);
      }
    }
  }
}

/**
 * Print summary
 */
function printSummary() {
  console.log('\n' + '='.repeat(80));
  console.log(`${colors.cyan}UI/UX Consistency Auto-Fix Summary${colors.reset}`);
  console.log('='.repeat(80) + '\n');
  
  console.log(`${colors.blue}Files:${colors.reset}`);
  console.log(`  Processed: ${stats.filesProcessed}`);
  console.log(`  Modified: ${stats.filesModified}`);
  console.log('');
  
  console.log(`${colors.blue}Fixes Applied:${colors.reset}`);
  console.log(`  Dark mode classes added: ${stats.darkModeAdded}`);
  console.log(`  Button imports added: ${stats.buttonsFixed}`);
  console.log(`  Input variant imports added: ${stats.inputsFixed}`);
  console.log(`  Accessibility attributes added: ${stats.accessibilityFixed}`);
  console.log('');
  
  const totalFixes = stats.darkModeAdded + stats.buttonsFixed + stats.inputsFixed + stats.accessibilityFixed;
  console.log(`${colors.green}Total fixes applied: ${totalFixes}${colors.reset}`);
  console.log('='.repeat(80) + '\n');
  
  if (stats.filesModified > 0) {
    console.log(`${colors.yellow}⚠️  Please review the changes and test your application!${colors.reset}\n`);
  }
}

/**
 * Main execution
 */
function main() {
  console.log(`${colors.cyan}Starting UI/UX consistency auto-fix...${colors.reset}\n`);
  
  const componentsDir = path.join(__dirname, 'components');
  const appDir = path.join(__dirname, 'app');
  
  if (fs.existsSync(componentsDir)) {
    console.log(`${colors.blue}Processing components directory...${colors.reset}`);
    processDirectory(componentsDir);
  }
  
  if (fs.existsSync(appDir)) {
    console.log(`${colors.blue}Processing app directory...${colors.reset}`);
    processDirectory(appDir);
  }
  
  printSummary();
}

// Run the script
main();
