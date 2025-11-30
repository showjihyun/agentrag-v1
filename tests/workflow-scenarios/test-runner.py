#!/usr/bin/env python3
"""
Workflow Test Runner
Executes workflow test scenarios and generates reports
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

# Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
API_TOKEN = os.getenv('API_TOKEN', '')

# Test user credentials
TEST_USER_EMAIL = 'test@workflow.com'
TEST_USER_PASSWORD = 'testpassword123'

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class WorkflowTestRunner:
    def __init__(self, base_url: str, token: str = ''):
        self.base_url = base_url
        self.token = token or self.get_or_create_test_user()
        self.results = []
        self.stats = defaultdict(int)
    
    def get_or_create_test_user(self) -> str:
        """Get or create test user and return token"""
        try:
            # Try to login first
            response = requests.post(
                f'{self.base_url}/api/auth/login',
                json={
                    'email': TEST_USER_EMAIL,
                    'password': TEST_USER_PASSWORD
                }
            )
            if response.ok:
                return response.json()['access_token']
        except:
            pass
        
        try:
            # Create user if login failed
            response = requests.post(
                f'{self.base_url}/api/auth/register',
                json={
                    'email': TEST_USER_EMAIL,
                    'password': TEST_USER_PASSWORD,
                    'username': 'testuser'
                }
            )
            if response.ok:
                return response.json()['access_token']
        except Exception as e:
            print(f"{Colors.WARNING}Warning: Could not create test user: {e}{Colors.ENDC}")
            print(f"{Colors.WARNING}Continuing without authentication...{Colors.ENDC}")
            return ''
        
    def load_scenario(self, scenario_path: Path) -> Dict:
        """Load test scenario from JSON file"""
        with open(scenario_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_workflow(self, workflow_data: Dict) -> str:
        """Create workflow via API"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        response = requests.post(
            f'{self.base_url}/api/agent-builder/workflows',
            json=workflow_data,
            headers=headers
        )
        
        if not response.ok:
            try:
                error_detail = response.json()
                print(f"\n{Colors.FAIL}API Error Details:{Colors.ENDC}")
                print(json.dumps(error_detail, indent=2))
            except:
                print(f"\n{Colors.FAIL}Response: {response.text}{Colors.ENDC}")
        
        response.raise_for_status()
        return response.json()['id']
    
    def execute_workflow(self, workflow_id: str, input_data: Dict) -> Dict:
        """Execute workflow with input data"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        response = requests.post(
            f'{self.base_url}/api/agent-builder/workflows/{workflow_id}/execute',
            json={'input': input_data},
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    
    def validate_assertions(self, result: Dict, assertions: List[Dict]) -> List[Dict]:
        """Validate test assertions"""
        validation_results = []
        
        for assertion in assertions:
            assertion_type = assertion['type']
            passed = False
            message = ''
            
            if assertion_type == 'response_time':
                max_seconds = assertion.get('max_seconds', 10)
                actual_time = result.get('execution_time', 0)
                passed = actual_time <= max_seconds
                message = f"Response time: {actual_time:.2f}s (max: {max_seconds}s)"
            
            elif assertion_type == 'no_errors':
                passed = result.get('status') == 'success' and not result.get('errors')
                message = "No errors occurred" if passed else f"Errors: {result.get('errors')}"
            
            elif assertion_type == 'output_not_empty':
                passed = bool(result.get('output'))
                message = "Output is not empty" if passed else "Output is empty"
            
            elif assertion_type == 'http_status_code':
                expected = assertion.get('expected', 200)
                actual = result.get('output', {}).get('status_code')
                passed = actual == expected
                message = f"HTTP status: {actual} (expected: {expected})"
            
            validation_results.append({
                'type': assertion_type,
                'passed': passed,
                'message': message
            })
        
        return validation_results
    
    def run_test_case(self, scenario: Dict, test_case: Dict, workflow_id: str) -> Dict:
        """Run a single test case"""
        print(f"  Running: {test_case['name']}...", end=' ')
        
        start_time = time.time()
        try:
            result = self.execute_workflow(workflow_id, test_case['input'])
            execution_time = time.time() - start_time
            result['execution_time'] = execution_time
            
            # Validate assertions
            validations = self.validate_assertions(result, scenario.get('assertions', []))
            all_passed = all(v['passed'] for v in validations)
            
            if all_passed:
                print(f"{Colors.OKGREEN}✓ PASS{Colors.ENDC} ({execution_time:.2f}s)")
                self.stats['passed'] += 1
            else:
                print(f"{Colors.FAIL}✗ FAIL{Colors.ENDC}")
                self.stats['failed'] += 1
                for v in validations:
                    if not v['passed']:
                        print(f"    {Colors.FAIL}✗{Colors.ENDC} {v['message']}")
            
            return {
                'test_case': test_case['name'],
                'passed': all_passed,
                'execution_time': execution_time,
                'validations': validations,
                'result': result
            }
        
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"{Colors.FAIL}✗ ERROR{Colors.ENDC}")
            print(f"    {Colors.FAIL}Error: {str(e)}{Colors.ENDC}")
            self.stats['errors'] += 1
            
            return {
                'test_case': test_case['name'],
                'passed': False,
                'execution_time': execution_time,
                'error': str(e)
            }
    
    def run_scenario(self, scenario_path: Path) -> Dict:
        """Run all test cases in a scenario"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        
        scenario = self.load_scenario(scenario_path)
        print(f"{Colors.HEADER}{Colors.BOLD}Scenario: {scenario['name']}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}Category: {scenario['category']}{Colors.ENDC}")
        print(f"Description: {scenario['description']}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        # Create workflow
        try:
            # Convert nodes to backend format
            converted_nodes = []
            for node in scenario['workflow']['nodes']:
                converted_node = {
                    'id': node['id'],
                    'node_type': node['type'],
                    'position_x': node['position']['x'],
                    'position_y': node['position']['y'],
                    'configuration': node.get('data', {})
                }
                converted_nodes.append(converted_node)
            
            # Convert edges to backend format
            converted_edges = []
            for edge in scenario['workflow']['edges']:
                converted_edge = {
                    'id': edge['id'],
                    'source_node_id': edge['source'],
                    'target_node_id': edge['target'],
                    'edge_type': edge.get('type', 'normal'),
                    'source_handle': edge.get('sourceHandle'),
                    'target_handle': edge.get('targetHandle')
                }
                converted_edges.append(converted_edge)
            
            # Find entry point (start node)
            start_node = next((n for n in scenario['workflow']['nodes'] if n['type'] == 'start'), None)
            entry_point = start_node['id'] if start_node else scenario['workflow']['nodes'][0]['id']
            
            workflow_data = {
                'name': f"Test: {scenario['name']}",
                'description': scenario['description'],
                'nodes': converted_nodes,
                'edges': converted_edges,
                'entry_point': entry_point,
                'is_public': False
            }
            workflow_id = self.create_workflow(workflow_data)
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} Workflow created: {workflow_id}")
        except Exception as e:
            print(f"{Colors.FAIL}✗ Failed to create workflow: {e}{Colors.ENDC}")
            return {
                'scenario': scenario['name'],
                'passed': False,
                'error': str(e)
            }
        
        # Run test cases
        test_results = []
        for test_case in scenario.get('test_cases', []):
            result = self.run_test_case(scenario, test_case, workflow_id)
            test_results.append(result)
        
        # Summary
        passed_count = sum(1 for r in test_results if r['passed'])
        total_count = len(test_results)
        
        return {
            'scenario': scenario['name'],
            'category': scenario['category'],
            'passed': passed_count == total_count,
            'test_results': test_results,
            'summary': {
                'total': total_count,
                'passed': passed_count,
                'failed': total_count - passed_count
            }
        }
    
    def run_all_scenarios(self, scenarios_dir: Path, category: str = None) -> List[Dict]:
        """Run all scenarios in directory"""
        results = []
        
        # Find all scenario files
        if category:
            pattern = f"{category}/*.json"
        else:
            pattern = "**/*.json"
        
        scenario_files = sorted(scenarios_dir.glob(pattern))
        
        if not scenario_files:
            print(f"{Colors.WARNING}No scenario files found{Colors.ENDC}")
            return results
        
        print(f"\n{Colors.BOLD}Found {len(scenario_files)} scenario(s){Colors.ENDC}")
        
        for scenario_file in scenario_files:
            if scenario_file.name == 'README.md':
                continue
            
            result = self.run_scenario(scenario_file)
            results.append(result)
        
        return results
    
    def generate_report(self, results: List[Dict], output_dir: Path):
        """Generate test report"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Summary
        total_scenarios = len(results)
        passed_scenarios = sum(1 for r in results if r['passed'])
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_scenarios': total_scenarios,
                'passed_scenarios': passed_scenarios,
                'failed_scenarios': total_scenarios - passed_scenarios,
                'total_tests': self.stats['passed'] + self.stats['failed'] + self.stats['errors'],
                'passed_tests': self.stats['passed'],
                'failed_tests': self.stats['failed'],
                'errors': self.stats['errors']
            },
            'results': results
        }
        
        # Save JSON report
        report_file = output_dir / 'summary.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"Total Scenarios: {total_scenarios}")
        print(f"{Colors.OKGREEN}Passed: {passed_scenarios}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {total_scenarios - passed_scenarios}{Colors.ENDC}")
        print(f"\nTotal Tests: {report['summary']['total_tests']}")
        print(f"{Colors.OKGREEN}Passed: {self.stats['passed']}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.stats['failed']}{Colors.ENDC}")
        print(f"{Colors.WARNING}Errors: {self.stats['errors']}{Colors.ENDC}")
        print(f"\n{Colors.OKBLUE}Report saved to: {report_file}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}\n")

def main():
    parser = argparse.ArgumentParser(description='Workflow Test Runner')
    parser.add_argument('--all', action='store_true', help='Run all scenarios')
    parser.add_argument('--category', type=str, help='Run specific category')
    parser.add_argument('--scenario', type=str, help='Run specific scenario file')
    parser.add_argument('--base-url', type=str, default=API_BASE_URL, help='API base URL')
    parser.add_argument('--token', type=str, default=API_TOKEN, help='API token')
    parser.add_argument('--output', type=str, default='test-results', help='Output directory')
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = WorkflowTestRunner(args.base_url, args.token)
    
    # Get scenarios directory
    scenarios_dir = Path(__file__).parent
    output_dir = Path(args.output)
    
    # Run tests
    if args.scenario:
        scenario_path = scenarios_dir / args.scenario
        results = [runner.run_scenario(scenario_path)]
    elif args.category:
        results = runner.run_all_scenarios(scenarios_dir, args.category)
    elif args.all:
        results = runner.run_all_scenarios(scenarios_dir)
    else:
        parser.print_help()
        return
    
    # Generate report
    runner.generate_report(results, output_dir)

if __name__ == '__main__':
    main()
