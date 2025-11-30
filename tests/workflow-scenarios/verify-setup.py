#!/usr/bin/env python3
"""
Setup Verification Script
Verifies that the backend is running and configured correctly
"""

import requests
import sys

API_BASE_URL = 'http://localhost:8000'

class Colors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def check_api(endpoint, name):
    """Check if an API endpoint is accessible"""
    try:
        response = requests.get(f'{API_BASE_URL}{endpoint}', timeout=5)
        if response.ok:
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} {name}: OK")
            return True
        else:
            print(f"{Colors.FAIL}✗{Colors.ENDC} {name}: Failed (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print(f"{Colors.FAIL}✗{Colors.ENDC} {name}: Connection refused")
        return False
    except Exception as e:
        print(f"{Colors.FAIL}✗{Colors.ENDC} {name}: {str(e)}")
        return False

def main():
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Workflow System Setup Verification{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    checks = [
        ('/health', 'Backend Health Check'),
        ('/api/agent-builder/tools', 'Tools API'),
        ('/api/agent-builder/blocks', 'Blocks API'),
        ('/api/agent-builder/workflows', 'Workflows API'),
    ]
    
    results = []
    for endpoint, name in checks:
        results.append(check_api(endpoint, name))
    
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ All checks passed ({passed}/{total}){Colors.ENDC}")
        print(f"\n{Colors.OKGREEN}System is ready for testing!{Colors.ENDC}")
        print(f"\nNext steps:")
        print(f"1. Open http://localhost:3000/agent-builder/workflows/new")
        print(f"2. Follow the MANUAL_TESTING_GUIDE.md")
        return 0
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ Some checks failed ({passed}/{total}){Colors.ENDC}")
        print(f"\n{Colors.WARNING}Please ensure:{Colors.ENDC}")
        print(f"1. Backend is running: cd backend && uvicorn main:app --reload")
        print(f"2. Frontend is running: cd frontend && npm run dev")
        print(f"3. Database is running: docker-compose up -d postgres")
        print(f"4. Milvus is running: docker-compose up -d milvus")
        return 1
    
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

if __name__ == '__main__':
    sys.exit(main())
