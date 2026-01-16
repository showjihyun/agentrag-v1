#!/usr/bin/env python3
"""
Docker Setup Verification Script
Updated: 2026-01-16
Purpose: Verify all Docker configuration files exist and are valid
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file_exists(filepath: str) -> bool:
    """Check if a file exists"""
    return Path(filepath).exists()

def check_directory_exists(dirpath: str) -> bool:
    """Check if a directory exists"""
    return Path(dirpath).is_dir()

def print_status(message: str, status: bool):
    """Print colored status message"""
    symbol = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
    print(f"{symbol} {message}")

def main():
    """Main verification function"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Docker Setup Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    checks: List[Tuple[str, str, bool]] = []
    
    # Docker configuration files
    print(f"{YELLOW}Checking Docker Configuration Files...{RESET}")
    docker_files = [
        ("backend/Dockerfile", "Backend Dockerfile"),
        ("backend/Dockerfile.optimized", "Optimized Dockerfile"),
        ("docker-compose.yml", "Development Compose"),
        ("docker-compose.prod.yml", "Production Compose"),
        ("backend/.dockerignore", "Docker ignore file"),
    ]
    
    for filepath, description in docker_files:
        exists = check_file_exists(filepath)
        checks.append((description, filepath, exists))
        print_status(f"{description}: {filepath}", exists)
    
    print()
    
    # Environment files
    print(f"{YELLOW}Checking Environment Files...{RESET}")
    env_files = [
        ("backend/.env.example", "Development env example"),
        ("backend/.env.production.example", "Production env example"),
    ]
    
    for filepath, description in env_files:
        exists = check_file_exists(filepath)
        checks.append((description, filepath, exists))
        print_status(f"{description}: {filepath}", exists)
    
    print()
    
    # Nginx configuration
    print(f"{YELLOW}Checking Nginx Configuration...{RESET}")
    nginx_files = [
        ("nginx/nginx.conf", "Nginx configuration"),
    ]
    
    for filepath, description in nginx_files:
        exists = check_file_exists(filepath)
        checks.append((description, filepath, exists))
        print_status(f"{description}: {filepath}", exists)
    
    print()
    
    # Monitoring configuration
    print(f"{YELLOW}Checking Monitoring Configuration...{RESET}")
    monitoring_files = [
        ("monitoring/prometheus.yml", "Prometheus config"),
        ("monitoring/grafana/datasources/prometheus.yml", "Grafana datasource"),
        ("monitoring/grafana/dashboards/dashboard.yml", "Grafana dashboard"),
    ]
    
    for filepath, description in monitoring_files:
        exists = check_file_exists(filepath)
        checks.append((description, filepath, exists))
        print_status(f"{description}: {filepath}", exists)
    
    print()
    
    # Database initialization
    print(f"{YELLOW}Checking Database Scripts...{RESET}")
    db_files = [
        ("backend/scripts/init-db.sql", "PostgreSQL init script"),
    ]
    
    for filepath, description in db_files:
        exists = check_file_exists(filepath)
        checks.append((description, filepath, exists))
        print_status(f"{description}: {filepath}", exists)
    
    print()
    
    # Management scripts (Windows)
    print(f"{YELLOW}Checking Windows Scripts...{RESET}")
    windows_scripts = [
        ("scripts/docker-build.bat", "Build script"),
        ("scripts/docker-start.bat", "Start script"),
        ("scripts/docker-stop.bat", "Stop script"),
        ("scripts/docker-restart.bat", "Restart script"),
        ("scripts/docker-logs.bat", "Logs script"),
        ("scripts/docker-shell.bat", "Shell script"),
        ("scripts/docker-migrate.bat", "Migration script"),
        ("scripts/docker-clean.bat", "Clean script"),
    ]
    
    for filepath, description in windows_scripts:
        exists = check_file_exists(filepath)
        checks.append((description, filepath, exists))
        print_status(f"{description}: {filepath}", exists)
    
    print()
    
    # Management scripts (Linux/Mac)
    print(f"{YELLOW}Checking Linux/Mac Scripts...{RESET}")
    unix_scripts = [
        ("scripts/docker-build.sh", "Build script"),
        ("scripts/docker-start.sh", "Start script"),
        ("scripts/docker-stop.sh", "Stop script"),
        ("scripts/docker-restart.sh", "Restart script"),
        ("scripts/docker-logs.sh", "Logs script"),
        ("scripts/docker-shell.sh", "Shell script"),
        ("scripts/docker-migrate.sh", "Migration script"),
        ("scripts/docker-clean.sh", "Clean script"),
    ]
    
    for filepath, description in unix_scripts:
        exists = check_file_exists(filepath)
        checks.append((description, filepath, exists))
        print_status(f"{description}: {filepath}", exists)
    
    print()
    
    # Documentation
    print(f"{YELLOW}Checking Documentation...{RESET}")
    doc_files = [
        ("docs/DOCKER_GUIDE.md", "Docker guide"),
        ("docs/DOCKER_COMPLETION_SUMMARY.md", "Completion summary"),
    ]
    
    for filepath, description in doc_files:
        exists = check_file_exists(filepath)
        checks.append((description, filepath, exists))
        print_status(f"{description}: {filepath}", exists)
    
    print()
    
    # Summary
    total_checks = len(checks)
    passed_checks = sum(1 for _, _, status in checks if status)
    failed_checks = total_checks - passed_checks
    
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Summary{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Total checks: {total_checks}")
    print(f"{GREEN}Passed: {passed_checks}{RESET}")
    if failed_checks > 0:
        print(f"{RED}Failed: {failed_checks}{RESET}")
    print()
    
    if failed_checks > 0:
        print(f"{RED}Some files are missing!{RESET}")
        print(f"{YELLOW}Missing files:{RESET}")
        for description, filepath, status in checks:
            if not status:
                print(f"  - {filepath}")
        print()
        return 1
    else:
        print(f"{GREEN}✓ All Docker configuration files are present!{RESET}")
        print()
        print(f"{BLUE}Next steps:{RESET}")
        print("1. Copy backend/.env.example to backend/.env")
        print("2. Edit backend/.env with your configuration")
        print("3. Run: scripts/docker-build.bat (Windows) or ./scripts/docker-build.sh (Linux/Mac)")
        print("4. Run: scripts/docker-start.bat (Windows) or ./scripts/docker-start.sh (Linux/Mac)")
        print()
        return 0

if __name__ == "__main__":
    sys.exit(main())
