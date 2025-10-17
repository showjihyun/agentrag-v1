"""
Deployment Checklist Script

Interactive checklist for production deployment.
"""

import os
import sys
from typing import List, Tuple

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class DeploymentChecklist:
    """Interactive deployment checklist."""
    
    def __init__(self):
        self.checks: List[Tuple[str, str, bool]] = []
    
    def add_check(self, category: str, item: str, auto_check: bool = False):
        """Add a checklist item."""
        self.checks.append((category, item, auto_check))
    
    def run(self):
        """Run the checklist interactively."""
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}Production Deployment Checklist{RESET}")
        print(f"{BLUE}{'='*70}{RESET}\n")
        
        completed = 0
        total = len(self.checks)
        current_category = None
        
        for category, item, auto_check in self.checks:
            # Print category header
            if category != current_category:
                print(f"\n{YELLOW}=== {category} ==={RESET}")
                current_category = category
            
            # Auto-check or ask user
            if auto_check:
                checked = self._auto_check(item)
                status = f"{GREEN}✓{RESET}" if checked else f"{RED}✗{RESET}"
                print(f"{status} {item}")
                if checked:
                    completed += 1
            else:
                response = input(f"[ ] {item} (y/n): ").strip().lower()
                if response == 'y':
                    print(f"{GREEN}✓{RESET} {item}")
                    completed += 1
                else:
                    print(f"{RED}✗{RESET} {item}")
        
        # Print summary
        print(f"\n{BLUE}{'='*70}{RESET}")
        print(f"{BLUE}Summary{RESET}")
        print(f"{BLUE}{'='*70}{RESET}")
        print(f"\nCompleted: {completed}/{total} ({completed/total*100:.1f}%)")
        
        if completed == total:
            print(f"\n{GREEN}All checks completed! Ready for deployment! 🚀{RESET}")
            return True
        else:
            print(f"\n{YELLOW}Please complete remaining items before deployment.{RESET}")
            return False
    
    def _auto_check(self, item: str) -> bool:
        """Automatically check certain items."""
        # Check if files exist
        if "exists" in item.lower():
            if ".env.example" in item:
                return os.path.exists(".env.example")
            elif "PRODUCTION_DEPLOYMENT_GUIDE.md" in item:
                return os.path.exists("PRODUCTION_DEPLOYMENT_GUIDE.md")
            elif "docker-compose" in item.lower():
                return os.path.exists("docker-compose.yml")
        
        # Check if documentation exists
        if "documentation" in item.lower():
            docs = [
                "PHASE3_FEEDBACK_CACHE_COMPLETE.md",
                "PHASE4_PRODUCTION_READY_COMPLETE.md",
                "PRODUCTION_DEPLOYMENT_GUIDE.md"
            ]
            return all(os.path.exists(doc) for doc in docs)
        
        return False


def main():
    """Main function."""
    checklist = DeploymentChecklist()
    
    # Environment Configuration
    checklist.add_check("Environment Configuration", ".env.example exists", auto_check=True)
    checklist.add_check("Environment Configuration", "Created .env from .env.example")
    checklist.add_check("Environment Configuration", "Set LLM_PROVIDER (ollama/openai/claude)")
    checklist.add_check("Environment Configuration", "Set LLM_MODEL")
    checklist.add_check("Environment Configuration", "Set API keys (if using cloud LLM)")
    checklist.add_check("Environment Configuration", "Set MILVUS_HOST and MILVUS_PORT")
    checklist.add_check("Environment Configuration", "Set REDIS_HOST and REDIS_PORT")
    checklist.add_check("Environment Configuration", "Set REDIS_PASSWORD (production)")
    checklist.add_check("Environment Configuration", "Set ENABLE_SEMANTIC_CACHE=true")
    checklist.add_check("Environment Configuration", "Set FEEDBACK_STORAGE_BACKEND=redis (production)")
    checklist.add_check("Environment Configuration", "Set DEBUG=false (production)")
    checklist.add_check("Environment Configuration", "Set LOG_LEVEL=INFO (production)")
    
    # Infrastructure
    checklist.add_check("Infrastructure", "Redis is running and accessible")
    checklist.add_check("Infrastructure", "Milvus is running and accessible")
    checklist.add_check("Infrastructure", "Ollama is running (if using local LLM)")
    checklist.add_check("Infrastructure", "Required models are downloaded")
    checklist.add_check("Infrastructure", "Network connectivity verified")
    
    # Backend
    checklist.add_check("Backend", "Python dependencies installed (pip install -r requirements.txt)")
    checklist.add_check("Backend", "Backend starts without errors")
    checklist.add_check("Backend", "Health check passes (curl /api/health)")
    checklist.add_check("Backend", "Feedback API accessible (curl /api/feedback/stats)")
    checklist.add_check("Backend", "Query API accessible (curl /api/query)")
    
    # Frontend
    checklist.add_check("Frontend", "Node dependencies installed (npm install)")
    checklist.add_check("Frontend", "Frontend builds successfully (npm run build)")
    checklist.add_check("Frontend", "Frontend starts without errors")
    checklist.add_check("Frontend", "Can access frontend in browser")
    
    # Testing
    checklist.add_check("Testing", "Unit tests pass (pytest tests/unit/)")
    checklist.add_check("Testing", "Integration tests pass (pytest tests/integration/)")
    checklist.add_check("Testing", "Basic query test successful")
    checklist.add_check("Testing", "Feedback submission test successful")
    checklist.add_check("Testing", "Cache functionality verified")
    
    # Security
    checklist.add_check("Security", "Redis password set")
    checklist.add_check("Security", "API keys stored in environment variables (not in code)")
    checklist.add_check("Security", "CORS configured for allowed domains only")
    checklist.add_check("Security", "Rate limiting enabled")
    checklist.add_check("Security", "HTTPS configured (production)")
    checklist.add_check("Security", "Firewall rules configured")
    
    # Monitoring
    checklist.add_check("Monitoring", "Logging configured")
    checklist.add_check("Monitoring", "Log rotation set up")
    checklist.add_check("Monitoring", "Monitoring dashboard configured (optional)")
    checklist.add_check("Monitoring", "Alert rules configured (optional)")
    
    # Backup
    checklist.add_check("Backup", "Redis backup strategy defined")
    checklist.add_check("Backup", "Milvus backup strategy defined")
    checklist.add_check("Backup", "Backup schedule configured")
    checklist.add_check("Backup", "Backup restoration tested")
    
    # Documentation
    checklist.add_check("Documentation", "All documentation exists", auto_check=True)
    checklist.add_check("Documentation", "Team trained on deployment process")
    checklist.add_check("Documentation", "Runbook created for common issues")
    
    # Final Checks
    checklist.add_check("Final Checks", "Rollback plan documented")
    checklist.add_check("Final Checks", "Stakeholders notified of deployment")
    checklist.add_check("Final Checks", "Maintenance window scheduled (if needed)")
    
    # Run checklist
    success = checklist.run()
    
    if success:
        print(f"\n{GREEN}Ready to deploy!{RESET}")
        print(f"\nNext steps:")
        print(f"1. Review PRODUCTION_DEPLOYMENT_GUIDE.md")
        print(f"2. Run: docker-compose -f docker-compose.prod.yml up -d")
        print(f"3. Monitor logs: docker-compose logs -f")
        print(f"4. Verify health: curl http://localhost:8000/api/health")
        sys.exit(0)
    else:
        print(f"\n{YELLOW}Please complete all checklist items before deploying.{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Checklist interrupted.{RESET}")
        sys.exit(1)
