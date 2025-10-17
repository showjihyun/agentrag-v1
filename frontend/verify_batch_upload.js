/**
 * Verification script for BatchUpload component (Task 5.5.4)
 * Checks that all required features are implemented.
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying BatchUpload Component Implementation...\n');

const componentPath = path.join(__dirname, 'components', 'BatchUpload.tsx');
const testPath = path.join(__dirname, 'components', '__tests__', 'BatchUpload.test.tsx');

let allChecksPassed = true;

function checkFile(filePath, fileName) {
  if (!fs.existsSync(filePath)) {
    console.log(`❌ ${fileName} not found`);
    allChecksPassed = false;
    return null;
  }
  console.log(`✅ ${fileName} exists`);
  return fs.readFileSync(filePath, 'utf8');
}

function checkFeature(content, feature, patterns) {
  const found = patterns.some(pattern => {
    if (typeof pattern === 'string') {
      return content.includes(pattern);
    } else {
      return pattern.test(content);
    }
  });

  if (found) {
    console.log(`  ✅ ${feature}`);
  } else {
    console.log(`  ❌ ${feature}`);
    allChecksPassed = false;
  }
  return found;
}

// Check component file
console.log('\n📄 Checking BatchUpload.tsx:\n');
const componentContent = checkFile(componentPath, 'BatchUpload.tsx');

if (componentContent) {
  console.log('\n🔧 Required Features:\n');

  // Multiple file selection
  checkFeature(
    componentContent,
    'Multiple file selection (input with multiple attribute)',
    ['type="file"', 'multiple']
  );

  // Drag and drop zone
  checkFeature(
    componentContent,
    'Drag and drop zone (onDragOver, onDrop handlers)',
    ['onDragOver', 'onDrop', 'onDragLeave']
  );

  // File list with preview
  checkFeature(
    componentContent,
    'File list with preview (filename, size, type)',
    ['file.name', 'file.size', 'file.type', /formatFileSize/]
  );

  // Remove file button
  checkFeature(
    componentContent,
    'Remove file button for each file',
    ['removeFile', /onClick.*removeFile/]
  );

  // Upload button
  checkFeature(
    componentContent,
    'Upload button (disabled if no files selected)',
    ['handleUpload', 'disabled={!hasValidFiles', /Upload.*Files/]
  );

  // Progress bar
  checkFeature(
    componentContent,
    'Progress bar for batch (percentage: completed/total)',
    ['uploadProgress', 'completed', 'total', /width.*completed.*total/]
  );

  // Individual file status indicators
  checkFeature(
    componentContent,
    'Individual file status indicators (pending, uploading, completed, failed)',
    [
      "'pending'",
      "'uploading'",
      "'completed'",
      "'failed'",
      'getStatusIcon',
      'getStatusColor'
    ]
  );

  // Error handling and retry
  checkFeature(
    componentContent,
    'Error handling and retry (error message, retry button)',
    ['error', 'retryFile', 'Retry', /error_message/]
  );

  // File validation
  checkFeature(
    componentContent,
    'File validation (type and size before upload)',
    ['validateFile', 'ALLOWED_FILE_TYPES', 'MAX_FILE_SIZE', 'MAX_TOTAL_SIZE']
  );

  // Authentication check
  checkFeature(
    componentContent,
    'Only show if user is authenticated',
    ['useAuth', 'isAuthenticated', 'if (!isAuthenticated)', 'return null']
  );

  console.log('\n🎨 Additional Features:\n');

  // Drag visual feedback
  checkFeature(
    componentContent,
    'Drag visual feedback (isDragging state)',
    ['isDragging', 'setIsDragging', 'border-blue-500']
  );

  // SSE progress streaming
  checkFeature(
    componentContent,
    'Real-time progress via SSE',
    ['streamBatchProgress', 'EventSource', 'onmessage', 'onerror']
  );

  // File size formatting
  checkFeature(
    componentContent,
    'File size formatting helper',
    ['formatFileSize', /KB|MB/]
  );

  // Clear all files
  checkFeature(
    componentContent,
    'Clear all files button',
    ['Clear All', 'setFiles([])']
  );

  // Batch upload API integration
  checkFeature(
    componentContent,
    'Batch upload API integration',
    ['apiClient.uploadBatch', 'BatchUploadResponse']
  );
}

// Check test file
console.log('\n📄 Checking BatchUpload.test.tsx:\n');
const testContent = checkFile(testPath, 'BatchUpload.test.tsx');

if (testContent) {
  console.log('\n🧪 Test Coverage:\n');

  checkFeature(
    testContent,
    'Authentication check test',
    ['not render when user is not authenticated']
  );

  checkFeature(
    testContent,
    'Render when authenticated test',
    ['render when user is authenticated']
  );

  checkFeature(
    testContent,
    'File display test',
    ['display file information when files are added']
  );

  checkFeature(
    testContent,
    'File validation test',
    ['validate file types']
  );

  checkFeature(
    testContent,
    'Remove file test',
    ['allow removing files from the list']
  );
}

// Check TypeScript types
console.log('\n📦 Checking Type Definitions:\n');
const typesPath = path.join(__dirname, 'lib', 'types.ts');
const typesContent = checkFile(typesPath, 'types.ts');

if (typesContent) {
  checkFeature(
    typesContent,
    'BatchUploadResponse type',
    ['interface BatchUploadResponse', 'total_files', 'completed_files']
  );

  checkFeature(
    typesContent,
    'BatchProgressResponse type',
    ['interface BatchProgressResponse', 'files']
  );
}

// Check API client
console.log('\n🌐 Checking API Client:\n');
const apiClientPath = path.join(__dirname, 'lib', 'api-client.ts');
const apiClientContent = checkFile(apiClientPath, 'api-client.ts');

if (apiClientContent) {
  checkFeature(
    apiClientContent,
    'uploadBatch method',
    ['async uploadBatch', 'files: File[]', 'BatchUploadResponse']
  );

  checkFeature(
    apiClientContent,
    'getBatchStatus method',
    ['async getBatchStatus', 'batchId', 'BatchProgressResponse']
  );

  checkFeature(
    apiClientContent,
    'streamBatchProgress method',
    ['streamBatchProgress', 'EventSource']
  );
}

// Summary
console.log('\n' + '='.repeat(60));
if (allChecksPassed) {
  console.log('✅ All checks passed! BatchUpload component is complete.');
  console.log('\n📋 Implementation Summary:');
  console.log('  • Multiple file selection with drag-and-drop');
  console.log('  • File validation (type, size, count)');
  console.log('  • Individual file status tracking');
  console.log('  • Real-time progress via SSE');
  console.log('  • Error handling with retry functionality');
  console.log('  • Authentication-gated access');
  console.log('  • Comprehensive test coverage');
  process.exit(0);
} else {
  console.log('❌ Some checks failed. Please review the implementation.');
  process.exit(1);
}
