#!/usr/bin/env python3
"""
Test Results Tracker
Simple script to track manual test results
"""

import json
import sys
from datetime import datetime
from pathlib import Path

class Colors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    OKCYAN = '\033[96m'

def load_results():
    """Load existing test results"""
    results_file = Path('test-results/manual-tests.json')
    if results_file.exists():
        with open(results_file, 'r') as f:
            return json.load(f)
    return {'tests': [], 'summary': {}}

def save_results(results):
    """Save test results"""
    results_file = Path('test-results/manual-tests.json')
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

def add_test_result():
    """Interactive test result entry"""
    print(f"\n{Colors.BOLD}Add Test Result{Colors.ENDC}\n")
    
    categories = [
        "Basic", "AI Tools", "Communication", "API Integration",
        "Data Tools", "Code Execution", "Control Flow", "Triggers",
        "Complex Workflows", "Real World"
    ]
    
    print("Categories:")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    
    cat_idx = int(input("\nSelect category (1-10): ")) - 1
    category = categories[cat_idx]
    
    test_name = input("Test name: ")
    status = input("Status (pass/fail/skip): ").lower()
    notes = input("Notes (optional): ")
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'category': category,
        'test_name': test_name,
        'status': status,
        'notes': notes
    }
    
    results = load_results()
    results['tests'].append(result)
    
    # Update summary
    summary = results.get('summary', {})
    summary[category] = summary.get(category, {'pass': 0, 'fail': 0, 'skip': 0})
    summary[category][status] = summary[category].get(status, 0) + 1
    results['summary'] = summary
    
    save_results(results)
    
    status_color = Colors.OKGREEN if status == 'pass' else Colors.FAIL if status == 'fail' else Colors.WARNING
    print(f"\n{status_color}✓ Test result saved{Colors.ENDC}")

def show_summary():
    """Show test results summary"""
    results = load_results()
    
    if not results['tests']:
        print(f"\n{Colors.WARNING}No test results found{Colors.ENDC}")
        return
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Test Results Summary{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    summary = results.get('summary', {})
    total_pass = sum(cat.get('pass', 0) for cat in summary.values())
    total_fail = sum(cat.get('fail', 0) for cat in summary.values())
    total_skip = sum(cat.get('skip', 0) for cat in summary.values())
    total = total_pass + total_fail + total_skip
    
    print(f"Total Tests: {total}")
    print(f"{Colors.OKGREEN}Passed: {total_pass}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {total_fail}{Colors.ENDC}")
    print(f"{Colors.WARNING}Skipped: {total_skip}{Colors.ENDC}")
    
    if total > 0:
        pass_rate = (total_pass / total) * 100
        print(f"\nPass Rate: {pass_rate:.1f}%")
    
    print(f"\n{Colors.BOLD}By Category:{Colors.ENDC}\n")
    
    for category, stats in sorted(summary.items()):
        passed = stats.get('pass', 0)
        failed = stats.get('fail', 0)
        skipped = stats.get('skip', 0)
        cat_total = passed + failed + skipped
        
        status_str = f"{Colors.OKGREEN}{passed}✓{Colors.ENDC} "
        status_str += f"{Colors.FAIL}{failed}✗{Colors.ENDC} "
        status_str += f"{Colors.WARNING}{skipped}○{Colors.ENDC}"
        
        print(f"  {category:20} [{status_str}] ({cat_total} tests)")
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def show_recent():
    """Show recent test results"""
    results = load_results()
    
    if not results['tests']:
        print(f"\n{Colors.WARNING}No test results found{Colors.ENDC}")
        return
    
    print(f"\n{Colors.BOLD}Recent Test Results (Last 10){Colors.ENDC}\n")
    
    for test in results['tests'][-10:]:
        timestamp = datetime.fromisoformat(test['timestamp']).strftime('%Y-%m-%d %H:%M')
        status = test['status']
        status_icon = '✓' if status == 'pass' else '✗' if status == 'fail' else '○'
        status_color = Colors.OKGREEN if status == 'pass' else Colors.FAIL if status == 'fail' else Colors.WARNING
        
        print(f"{status_color}{status_icon}{Colors.ENDC} [{timestamp}] {test['category']:15} - {test['test_name']}")
        if test.get('notes'):
            print(f"  └─ {test['notes']}")

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'add':
            add_test_result()
        elif command == 'summary':
            show_summary()
        elif command == 'recent':
            show_recent()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python track-results.py [add|summary|recent]")
    else:
        print(f"\n{Colors.BOLD}Test Results Tracker{Colors.ENDC}\n")
        print("Commands:")
        print("  add     - Add a new test result")
        print("  summary - Show test summary")
        print("  recent  - Show recent tests")
        print("\nUsage: python track-results.py [command]")

if __name__ == '__main__':
    main()
