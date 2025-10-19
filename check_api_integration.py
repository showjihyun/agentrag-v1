"""
Check Frontend and Backend API Endpoints Integration
"""
import os
import re
from pathlib import Path
from collections import defaultdict

print("\n" + "="*80)
print("Frontend & Backend API Endpoints Integration Check")
print("="*80)

# 1. Extract Backend API Endpoints
print("\n[1] Scanning Backend API Endpoints...")
backend_endpoints = defaultdict(list)

backend_api_dir = Path("backend/api")
for api_file in backend_api_dir.glob("*.py"):
    if api_file.name.startswith("__"):
        continue
    
    content = api_file.read_text(encoding='utf-8')
    
    # Find router prefix
    prefix_match = re.search(r'router = APIRouter\(prefix="([^"]+)"', content)
    if not prefix_match:
        continue
    
    prefix = prefix_match.group(1)
    
    # Find all route decorators
    routes = re.findall(r'@router\.(get|post|put|patch|delete)\("([^"]+)"', content)
    
    for method, path in routes:
        full_path = prefix + path if path != "/" else prefix
        backend_endpoints[full_path].append(method.upper())

print(f"   Found {len(backend_endpoints)} unique backend endpoints")

# 2. Extract Frontend API Calls
print("\n[2] Scanning Frontend API Calls...")
frontend_calls = defaultdict(set)

frontend_dir = Path("frontend")
for tsx_file in frontend_dir.rglob("*.tsx"):
    if "node_modules" in str(tsx_file):
        continue
    
    try:
        content = tsx_file.read_text(encoding='utf-8')
        
        # Find fetch calls with API paths
        # Pattern: fetch('/api/...') or fetch(`/api/...`)
        fetch_patterns = [
            r"fetch\(['\"]([^'\"]+)['\"]",
            r"fetch\(`([^`]+)`",
        ]
        
        for pattern in fetch_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if '/api/' in match or match.startswith('/api'):
                    # Extract just the path part (remove query params)
                    path = match.split('?')[0].split('${')[0]
                    if path:
                        frontend_calls[path].add(str(tsx_file.relative_to(frontend_dir)))
    except Exception as e:
        pass

print(f"   Found {len(frontend_calls)} unique frontend API calls")

# 3. Check Integration
print("\n[3] Checking Integration...")
print("\n" + "-"*80)

# Backend endpoints
print("\n[BACKEND] API ENDPOINTS:")
print("-"*80)
sorted_backend = sorted(backend_endpoints.items())
for endpoint, methods in sorted_backend:
    methods_str = ", ".join(sorted(methods))
    print(f"  {endpoint:<50} [{methods_str}]")

# Frontend calls
print("\n[FRONTEND] API CALLS:")
print("-"*80)
sorted_frontend = sorted(frontend_calls.items())
for endpoint, files in sorted_frontend:
    file_count = len(files)
    print(f"  {endpoint:<50} (used in {file_count} file{'s' if file_count > 1 else ''})")

# Integration check
print("\n[CHECK] INTEGRATION STATUS:")
print("-"*80)

matched = []
unmatched_frontend = []
unmatched_backend = []

# Check frontend calls against backend
for fe_endpoint in frontend_calls.keys():
    # Try to match with backend endpoints
    # Handle dynamic paths like /api/bookmarks/${id}
    base_path = re.sub(r'/\$\{[^}]+\}', '/{id}', fe_endpoint)
    base_path = re.sub(r'/\d+', '/{id}', base_path)
    
    found = False
    for be_endpoint in backend_endpoints.keys():
        # Simple matching (can be improved)
        if base_path == be_endpoint or fe_endpoint == be_endpoint:
            matched.append((fe_endpoint, be_endpoint))
            found = True
            break
        # Check if it's a parameterized route
        be_pattern = re.sub(r'\{[^}]+\}', '[^/]+', be_endpoint)
        if re.match(f"^{be_pattern}$", base_path):
            matched.append((fe_endpoint, be_endpoint))
            found = True
            break
    
    if not found:
        unmatched_frontend.append(fe_endpoint)

# Check backend endpoints not used by frontend
for be_endpoint in backend_endpoints.keys():
    found = False
    for fe_endpoint, be_match in matched:
        if be_match == be_endpoint:
            found = True
            break
    if not found:
        unmatched_backend.append(be_endpoint)

print(f"\n[OK] Matched Endpoints: {len(matched)}")
for fe, be in sorted(matched)[:10]:  # Show first 10
    print(f"    {fe} -> {be}")
if len(matched) > 10:
    print(f"    ... and {len(matched) - 10} more")

if unmatched_frontend:
    print(f"\n[WARN] Frontend calls without backend match: {len(unmatched_frontend)}")
    for endpoint in sorted(unmatched_frontend)[:10]:
        print(f"    {endpoint}")
    if len(unmatched_frontend) > 10:
        print(f"    ... and {len(unmatched_frontend) - 10} more")

if unmatched_backend:
    print(f"\n[INFO] Backend endpoints not used by frontend: {len(unmatched_backend)}")
    for endpoint in sorted(unmatched_backend)[:10]:
        print(f"    {endpoint}")
    if len(unmatched_backend) > 10:
        print(f"    ... and {len(unmatched_backend) - 10} more")

# 4. Check Monitoring Endpoints Specifically
print("\n" + "="*80)
print("MONITORING ENDPOINTS INTEGRATION")
print("="*80)

monitoring_be = {k: v for k, v in backend_endpoints.items() if '/monitoring' in k}
monitoring_fe = {k: v for k, v in frontend_calls.items() if '/monitoring' in k}

print(f"\nBackend Monitoring Endpoints: {len(monitoring_be)}")
for endpoint, methods in sorted(monitoring_be.items()):
    print(f"  [OK] {endpoint} [{', '.join(methods)}]")

print(f"\nFrontend Monitoring Calls: {len(monitoring_fe)}")
for endpoint, files in sorted(monitoring_fe.items()):
    print(f"  [OK] {endpoint} (in {len(files)} file(s))")

# 5. Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

total_be = len(backend_endpoints)
total_fe = len(frontend_calls)
match_rate = (len(matched) / total_fe * 100) if total_fe > 0 else 0

print(f"\nBackend API Endpoints: {total_be}")
print(f"Frontend API Calls: {total_fe}")
print(f"Matched: {len(matched)} ({match_rate:.1f}%)")
print(f"Unmatched Frontend: {len(unmatched_frontend)}")
print(f"Unused Backend: {len(unmatched_backend)}")

if match_rate > 80:
    print("\n[EXCELLENT] Integration Status: EXCELLENT")
elif match_rate > 60:
    print("\n[GOOD] Integration Status: GOOD")
elif match_rate > 40:
    print("\n[WARN] Integration Status: NEEDS ATTENTION")
else:
    print("\n[ERROR] Integration Status: POOR")

print("\n" + "="*80 + "\n")
