#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🔍 Analyzing bundle size...\n');

// Build the application
console.log('📦 Building application...');
try {
  execSync('npm run build', { stdio: 'inherit' });
} catch (error) {
  console.error('❌ Build failed:', error.message);
  process.exit(1);
}

// Analyze .next directory
const nextDir = path.join(process.cwd(), '.next');
const staticDir = path.join(nextDir, 'static');

if (!fs.existsSync(staticDir)) {
  console.error('❌ .next/static directory not found');
  process.exit(1);
}

// Get bundle information
function getDirectorySize(dirPath) {
  let totalSize = 0;
  const files = fs.readdirSync(dirPath);
  
  for (const file of files) {
    const filePath = path.join(dirPath, file);
    const stats = fs.statSync(filePath);
    
    if (stats.isDirectory()) {
      totalSize += getDirectorySize(filePath);
    } else {
      totalSize += stats.size;
    }
  }
  
  return totalSize;
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Analyze chunks
const chunksDir = path.join(staticDir, 'chunks');
if (fs.existsSync(chunksDir)) {
  console.log('📊 Bundle Analysis:');
  console.log('==================');
  
  const chunks = fs.readdirSync(chunksDir)
    .filter(file => file.endsWith('.js'))
    .map(file => {
      const filePath = path.join(chunksDir, file);
      const stats = fs.statSync(filePath);
      return {
        name: file,
        size: stats.size,
        formattedSize: formatBytes(stats.size)
      };
    })
    .sort((a, b) => b.size - a.size);

  console.log('\n🎯 Largest Chunks:');
  chunks.slice(0, 10).forEach((chunk, index) => {
    const indicator = chunk.size > 500000 ? '🔴' : chunk.size > 250000 ? '🟡' : '🟢';
    console.log(`${indicator} ${index + 1}. ${chunk.name} - ${chunk.formattedSize}`);
  });

  const totalSize = chunks.reduce((sum, chunk) => sum + chunk.size, 0);
  console.log(`\n📦 Total JS Bundle Size: ${formatBytes(totalSize)}`);
  
  // Check for potential issues
  console.log('\n🔍 Optimization Opportunities:');
  
  const largeChunks = chunks.filter(chunk => chunk.size > 500000);
  if (largeChunks.length > 0) {
    console.log('⚠️  Large chunks detected (>500KB):');
    largeChunks.forEach(chunk => {
      console.log(`   - ${chunk.name}: ${chunk.formattedSize}`);
    });
    console.log('   Consider code splitting or dynamic imports');
  }
  
  const duplicateLibraries = chunks.filter(chunk => 
    chunk.name.includes('react') || 
    chunk.name.includes('lodash') || 
    chunk.name.includes('moment')
  );
  
  if (duplicateLibraries.length > 1) {
    console.log('⚠️  Potential duplicate libraries detected:');
    duplicateLibraries.forEach(chunk => {
      console.log(`   - ${chunk.name}: ${chunk.formattedSize}`);
    });
  }
  
  // Performance recommendations
  console.log('\n💡 Performance Recommendations:');
  
  if (totalSize > 2000000) { // 2MB
    console.log('🔴 Bundle size is large (>2MB). Consider:');
    console.log('   - Implementing more aggressive code splitting');
    console.log('   - Using dynamic imports for heavy components');
    console.log('   - Tree-shaking unused code');
  } else if (totalSize > 1000000) { // 1MB
    console.log('🟡 Bundle size is moderate (>1MB). Consider:');
    console.log('   - Adding more dynamic imports');
    console.log('   - Optimizing third-party libraries');
  } else {
    console.log('🟢 Bundle size looks good!');
  }
}

// Analyze pages
const pagesDir = path.join(staticDir, 'chunks', 'pages');
if (fs.existsSync(pagesDir)) {
  console.log('\n📄 Page Bundles:');
  const pages = fs.readdirSync(pagesDir)
    .filter(file => file.endsWith('.js'))
    .map(file => {
      const filePath = path.join(pagesDir, file);
      const stats = fs.statSync(filePath);
      return {
        name: file.replace('.js', ''),
        size: stats.size,
        formattedSize: formatBytes(stats.size)
      };
    })
    .sort((a, b) => b.size - a.size);

  pages.forEach(page => {
    const indicator = page.size > 100000 ? '🔴' : page.size > 50000 ? '🟡' : '🟢';
    console.log(`${indicator} /${page.name} - ${page.formattedSize}`);
  });
}

console.log('\n✅ Bundle analysis complete!');
console.log('\n💡 To get more detailed analysis, consider using:');
console.log('   - @next/bundle-analyzer');
console.log('   - webpack-bundle-analyzer');
console.log('   - bundlephobia.com for package analysis');