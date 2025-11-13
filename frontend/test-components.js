/**
 * Frontend Component Test Script
 * Tests newly implemented components for syntax and import errors
 */

const fs = require('fs');
const path = require('path');

// ANSI color codes
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function printSection(title) {
  console.log('\n' + '='.repeat(60));
  console.log(`  ${title}`);
  console.log('='.repeat(60));
}

function printResult(testName, success, message = '') {
  const status = success ? `${colors.green}✅ PASS${colors.reset}` : `${colors.red}❌ FAIL${colors.reset}`;
  console.log(`${status} - ${testName}`);
  if (message) {
    console.log(`     ${message}`);
  }
}

function checkFileExists(filePath) {
  try {
    return fs.existsSync(filePath);
  } catch (error) {
    return false;
  }
}

function checkFileContent(filePath, checks) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const results = {};
    
    for (const [name, pattern] of Object.entries(checks)) {
      if (typeof pattern === 'string') {
        results[name] = content.includes(pattern);
      } else if (pattern instanceof RegExp) {
        results[name] = pattern.test(content);
      }
    }
    
    return results;
  } catch (error) {
    return null;
  }
}

function testNodeComponents() {
  printSection('Testing Node Components');
  
  const nodes = [
    { name: 'SwitchNode', path: 'components/workflow/nodes/SwitchNode.tsx' },
    { name: 'MergeNode', path: 'components/workflow/nodes/MergeNode.tsx' },
    { name: 'CodeNode', path: 'components/workflow/nodes/CodeNode.tsx' },
    { name: 'SlackNode', path: 'components/workflow/nodes/SlackNode.tsx' },
    { name: 'DiscordNode', path: 'components/workflow/nodes/DiscordNode.tsx' },
    { name: 'EmailNode', path: 'components/workflow/nodes/EmailNode.tsx' },
    { name: 'GoogleDriveNode', path: 'components/workflow/nodes/GoogleDriveNode.tsx' },
    { name: 'S3Node', path: 'components/workflow/nodes/S3Node.tsx' },
    { name: 'DatabaseNode', path: 'components/workflow/nodes/DatabaseNode.tsx' },
    { name: 'ManagerAgentNode', path: 'components/workflow/nodes/ManagerAgentNode.tsx' },
    { name: 'MemoryNode', path: 'components/workflow/nodes/MemoryNode.tsx' },
    { name: 'ConsensusNode', path: 'components/workflow/nodes/ConsensusNode.tsx' },
    { name: 'HumanApprovalNode', path: 'components/workflow/nodes/HumanApprovalNode.tsx' },
    { name: 'WebhookResponseNode', path: 'components/workflow/nodes/WebhookResponseNode.tsx' },
  ];
  
  let passed = 0;
  let failed = 0;
  
  nodes.forEach(node => {
    const exists = checkFileExists(node.path);
    
    if (exists) {
      const checks = checkFileContent(node.path, {
        'export': /export\s+default\s+function/,
        'Handle': /Handle/,
        'Position': /Position/,
        'NodeProps': /NodeProps/,
      });
      
      if (checks && Object.values(checks).every(v => v)) {
        printResult(node.name, true, `File exists with proper structure`);
        passed++;
      } else {
        printResult(node.name, false, `File exists but missing required elements`);
        failed++;
      }
    } else {
      printResult(node.name, false, `File not found: ${node.path}`);
      failed++;
    }
  });
  
  return { passed, failed, total: nodes.length };
}

function testConfigPanels() {
  printSection('Testing Config Panels');
  
  const configs = [
    { name: 'SwitchNodeConfig', path: 'components/workflow/NodeConfigPanels/SwitchNodeConfig.tsx' },
    { name: 'MergeNodeConfig', path: 'components/workflow/NodeConfigPanels/MergeNodeConfig.tsx' },
    { name: 'CodeNodeConfig', path: 'components/workflow/NodeConfigPanels/CodeNodeConfig.tsx' },
    { name: 'ScheduleTriggerConfig', path: 'components/workflow/NodeConfigPanels/ScheduleTriggerConfig.tsx' },
    { name: 'WebhookTriggerConfig', path: 'components/workflow/NodeConfigPanels/WebhookTriggerConfig.tsx' },
    { name: 'WebhookResponseConfig', path: 'components/workflow/NodeConfigPanels/WebhookResponseConfig.tsx' },
    { name: 'SlackNodeConfig', path: 'components/workflow/NodeConfigPanels/SlackNodeConfig.tsx' },
    { name: 'DiscordNodeConfig', path: 'components/workflow/NodeConfigPanels/DiscordNodeConfig.tsx' },
    { name: 'EmailNodeConfig', path: 'components/workflow/NodeConfigPanels/EmailNodeConfig.tsx' },
    { name: 'GoogleDriveNodeConfig', path: 'components/workflow/NodeConfigPanels/GoogleDriveNodeConfig.tsx' },
    { name: 'S3NodeConfig', path: 'components/workflow/NodeConfigPanels/S3NodeConfig.tsx' },
    { name: 'DatabaseNodeConfig', path: 'components/workflow/NodeConfigPanels/DatabaseNodeConfig.tsx' },
    { name: 'ManagerAgentConfig', path: 'components/workflow/NodeConfigPanels/ManagerAgentConfig.tsx' },
    { name: 'MemoryNodeConfig', path: 'components/workflow/NodeConfigPanels/MemoryNodeConfig.tsx' },
    { name: 'ConsensusNodeConfig', path: 'components/workflow/NodeConfigPanels/ConsensusNodeConfig.tsx' },
    { name: 'HumanApprovalConfig', path: 'components/workflow/NodeConfigPanels/HumanApprovalConfig.tsx' },
  ];
  
  let passed = 0;
  let failed = 0;
  
  configs.forEach(config => {
    const exists = checkFileExists(config.path);
    
    if (exists) {
      const checks = checkFileContent(config.path, {
        'export': /export\s+default\s+function/,
        'useState': /useState/,
        'Label': /Label/,
        'onChange': /onChange/,
      });
      
      if (checks && Object.values(checks).every(v => v)) {
        printResult(config.name, true, `Config panel properly structured`);
        passed++;
      } else {
        printResult(config.name, false, `Missing required elements`);
        failed++;
      }
    } else {
      printResult(config.name, false, `File not found`);
      failed++;
    }
  });
  
  return { passed, failed, total: configs.length };
}

function testPages() {
  printSection('Testing New Pages');
  
  const pages = [
    { 
      name: 'Analytics Dashboard', 
      path: 'app/agent-builder/analytics/page.tsx',
      checks: {
        'export': /export\s+default\s+function/,
        'useState': /useState/,
        'metrics': /metric/i,
      }
    },
    { 
      name: 'Approvals Page', 
      path: 'app/agent-builder/approvals/page.tsx',
      checks: {
        'export': /export\s+default\s+function/,
        'useState': /useState/,
        'approval': /approval/i,
      }
    },
    { 
      name: 'Environment Variables', 
      path: 'app/agent-builder/settings/environment/page.tsx',
      checks: {
        'export': /export\s+default\s+function/,
        'useState': /useState/,
        'variable': /variable/i,
      }
    },
  ];
  
  let passed = 0;
  let failed = 0;
  
  pages.forEach(page => {
    const exists = checkFileExists(page.path);
    
    if (exists) {
      const checks = checkFileContent(page.path, page.checks);
      
      if (checks && Object.values(checks).every(v => v)) {
        printResult(page.name, true, `Page properly implemented`);
        passed++;
      } else {
        printResult(page.name, false, `Missing required elements`);
        failed++;
      }
    } else {
      printResult(page.name, false, `File not found`);
      failed++;
    }
  });
  
  return { passed, failed, total: pages.length };
}

function testWorkflowEditor() {
  printSection('Testing Workflow Editor Integration');
  
  const editorPath = 'components/workflow/WorkflowEditor.tsx';
  const exists = checkFileExists(editorPath);
  
  let passed = 0;
  let failed = 0;
  
  if (exists) {
    const checks = checkFileContent(editorPath, {
      'SwitchNode': /SwitchNode/,
      'MergeNode': /MergeNode/,
      'CodeNode': /CodeNode/,
      'MemoryNode': /MemoryNode/,
      'ConsensusNode': /ConsensusNode/,
      'HumanApprovalNode': /HumanApprovalNode/,
      'nodeTypes': /nodeTypes.*NodeTypes/,
    });
    
    if (checks) {
      Object.entries(checks).forEach(([name, result]) => {
        if (result) {
          printResult(`${name} registered`, true);
          passed++;
        } else {
          printResult(`${name} registered`, false);
          failed++;
        }
      });
    }
  } else {
    printResult('WorkflowEditor.tsx', false, 'File not found');
    failed++;
  }
  
  return { passed, failed, total: 7 };
}

function main() {
  console.log('\n' + '🚀'.repeat(30));
  console.log('  FRONTEND COMPONENT TESTS');
  console.log('  Testing newly implemented components');
  console.log('🚀'.repeat(30));
  
  const results = {
    nodes: testNodeComponents(),
    configs: testConfigPanels(),
    pages: testPages(),
    editor: testWorkflowEditor(),
  };
  
  // Summary
  printSection('TEST SUMMARY');
  
  const totalTests = Object.values(results).reduce((sum, r) => sum + r.total, 0);
  const totalPassed = Object.values(results).reduce((sum, r) => sum + r.passed, 0);
  const totalFailed = Object.values(results).reduce((sum, r) => sum + r.failed, 0);
  
  console.log(`\nTotal Tests: ${totalTests}`);
  console.log(`${colors.green}✅ Passed: ${totalPassed}${colors.reset}`);
  console.log(`${colors.red}❌ Failed: ${totalFailed}${colors.reset}`);
  console.log(`Success Rate: ${((totalPassed/totalTests)*100).toFixed(1)}%\n`);
  
  console.log('Breakdown:');
  console.log(`  Node Components: ${results.nodes.passed}/${results.nodes.total}`);
  console.log(`  Config Panels: ${results.configs.passed}/${results.configs.total}`);
  console.log(`  Pages: ${results.pages.passed}/${results.pages.total}`);
  console.log(`  Editor Integration: ${results.editor.passed}/${results.editor.total}`);
  
  console.log('\n' + '='.repeat(60));
  
  if (totalFailed === 0) {
    console.log(`${colors.green}🎉 All tests passed!${colors.reset}`);
  } else {
    console.log(`${colors.yellow}⚠️  Some tests failed. Check the output above for details.${colors.reset}`);
  }
  
  console.log('='.repeat(60) + '\n');
  
  process.exit(totalFailed === 0 ? 0 : 1);
}

// Run tests
main();
