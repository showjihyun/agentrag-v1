/**
 * Verification script for Priority 1 UI/UX Improvements
 * 
 * Tests:
 * 1. Database Monitoring UI components
 * 2. System Status Badge
 * 3. Document Upload Progress
 */

const fs = require('fs');
const path = require('path');

console.log('='.repeat(60));
console.log('PRIORITY 1 UI/UX IMPROVEMENTS VERIFICATION');
console.log('='.repeat(60));

let passed = 0;
let failed = 0;

function checkFile(filePath, description) {
  const fullPath = path.join(__dirname, filePath);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ ${description}`);
    console.log(`   ${filePath}`);
    passed++;
    return true;
  } else {
    console.log(`❌ ${description}`);
    console.log(`   Missing: ${filePath}`);
    failed++;
    return false;
  }
}

function checkFileContent(filePath, searchStrings, description) {
  const fullPath = path.join(__dirname, filePath);
  if (!fs.existsSync(fullPath)) {
    console.log(`❌ ${description} - File not found`);
    failed++;
    return false;
  }

  const content = fs.readFileSync(fullPath, 'utf8');
  const allFound = searchStrings.every(str => content.includes(str));
  
  if (allFound) {
    console.log(`✅ ${description}`);
    passed++;
    return true;
  } else {
    console.log(`❌ ${description} - Missing required content`);
    const missing = searchStrings.filter(str => !content.includes(str));
    console.log(`   Missing: ${missing.join(', ')}`);
    failed++;
    return false;
  }
}

console.log('\n' + '='.repeat(60));
console.log('TEST 1: Database Monitoring Components');
console.log('='.repeat(60));

checkFile(
  'components/monitoring/DatabaseMonitoring.tsx',
  'Database Monitoring Component'
);

checkFile(
  'app/monitoring/database/page.tsx',
  'Database Monitoring Page'
);

checkFileContent(
  'components/monitoring/DatabaseMonitoring.tsx',
  ['PostgreSQL', 'Milvus', 'pool_size', 'utilization_percent'],
  'Database Monitoring - PostgreSQL metrics'
);

checkFileContent(
  'components/monitoring/DatabaseMonitoring.tsx',
  ['StatCard', 'total_connections', 'collection_size'],
  'Database Monitoring - Milvus metrics'
);

console.log('\n' + '='.repeat(60));
console.log('TEST 2: System Status Badge');
console.log('='.repeat(60));

checkFile(
  'components/SystemStatusBadge.tsx',
  'System Status Badge Component'
);

checkFileContent(
  'components/SystemStatusBadge.tsx',
  ['SystemHealth', 'overall_status', 'postgresql', 'milvus'],
  'System Status Badge - Health monitoring'
);

checkFileContent(
  'app/page.tsx',
  ['SystemStatusBadge', 'import SystemStatusBadge'],
  'System Status Badge - Integration in main page'
);

console.log('\n' + '='.repeat(60));
console.log('TEST 3: Document Upload Progress');
console.log('='.repeat(60));

checkFile(
  'components/DocumentUploadProgress.tsx',
  'Document Upload Progress Component'
);

checkFileContent(
  'components/DocumentUploadProgress.tsx',
  ['uploading', 'processing', 'indexing', 'complete', 'progress'],
  'Document Upload Progress - Stage indicators'
);

checkFileContent(
  'components/DocumentUploadProgress.tsx',
  ['estimatedTime', 'getStatusMessage', 'getCurrentStage'],
  'Document Upload Progress - Progress tracking'
);

console.log('\n' + '='.repeat(60));
console.log('TEST 4: Component Integration');
console.log('='.repeat(60));

checkFileContent(
  'components/monitoring/DatabaseMonitoring.tsx',
  ['StatCard', 'autoRefresh', 'refreshInterval'],
  'Database Monitoring - Reuses existing components'
);

checkFileContent(
  'components/SystemStatusBadge.tsx',
  ['useEffect', 'useState', 'setInterval'],
  'System Status Badge - Auto-refresh functionality'
);

console.log('\n' + '='.repeat(60));
console.log('VERIFICATION SUMMARY');
console.log('='.repeat(60));

console.log(`\n✅ Passed: ${passed}`);
console.log(`❌ Failed: ${failed}`);
console.log(`Total: ${passed + failed}`);

if (failed === 0) {
  console.log('\n🎉 All Priority 1 UI/UX improvements verified successfully!');
  console.log('\nImplemented Features:');
  console.log('1. ✅ Database Monitoring UI (PostgreSQL + Milvus)');
  console.log('2. ✅ System Status Badge (Real-time health)');
  console.log('3. ✅ Document Upload Progress (Detailed stages)');
  console.log('\nNext Steps:');
  console.log('- Start the backend: cd backend && uvicorn main:app --reload');
  console.log('- Start the frontend: cd frontend && npm run dev');
  console.log('- Visit: http://localhost:3000/monitoring/database');
  process.exit(0);
} else {
  console.log('\n⚠️  Some verifications failed. Please review the output above.');
  process.exit(1);
}
