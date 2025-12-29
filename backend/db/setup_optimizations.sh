#!/bin/bash

# Database Optimization Setup Script
# Makes optimization tools executable and provides quick access

set -e

echo "🗄️ Setting up Database Optimization Tools..."

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make Python scripts executable
chmod +x optimize_database.py
chmod +x monitoring_dashboard.py

# Create convenience aliases
echo "📝 Creating convenience scripts..."

# Create optimization wrapper
cat > optimize << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python optimize_database.py "$@"
EOF
chmod +x optimize

# Create monitoring wrapper
cat > monitor << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python monitoring_dashboard.py "$@"
EOF
chmod +x monitor

# Create quick setup script
cat > quick_setup << 'EOF'
#!/bin/bash
echo "🚀 Quick Database Optimization Setup"
echo "===================================="
echo ""

cd "$(dirname "$0")"

echo "1. Checking database connection..."
if python -c "
import sys
sys.path.append('..')
from db.database import get_db_url
from sqlalchemy import create_engine
try:
    engine = create_engine(get_db_url())
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"; then
    echo ""
    echo "2. Applying basic optimizations (Phase 1)..."
    python optimize_database.py --phase 1
    
    echo ""
    echo "3. Running health check..."
    python optimize_database.py --health
    
    echo ""
    echo "✅ Quick setup completed!"
    echo ""
    echo "Next steps:"
    echo "- Start monitoring: ./monitor --server"
    echo "- Apply all phases: ./optimize --all"
    echo "- Check status: ./optimize --status"
else
    echo "❌ Setup failed due to database connection issues"
    exit 1
fi
EOF
chmod +x quick_setup

# Create help script
cat > help << 'EOF'
#!/bin/bash
echo "🗄️ Database Optimization Tools Help"
echo "==================================="
echo ""
echo "Quick Commands:"
echo "  ./quick_setup          - Apply basic optimizations and health check"
echo "  ./optimize --all       - Apply all optimization phases"
echo "  ./optimize --status    - Check optimization status"
echo "  ./optimize --health    - Run database health check"
echo "  ./monitor --server     - Start monitoring dashboard"
echo "  ./monitor --report     - Generate performance report"
echo ""
echo "Detailed Commands:"
echo ""
echo "Optimization (./optimize):"
echo "  --phase 1              - Basic performance optimizations"
echo "  --phase 2              - Table partitioning (requires planning)"
echo "  --phase 3              - Security enhancements"
echo "  --all                  - Apply all phases"
echo "  --status               - Check what's been applied"
echo "  --health               - Database health check"
echo "  --refresh              - Refresh analytics views"
echo "  --maintenance          - Run maintenance tasks"
echo ""
echo "Monitoring (./monitor):"
echo "  --server               - Start web dashboard (port 5001)"
echo "  --port 5002            - Use different port"
echo "  --report               - Generate performance report"
echo "  --alerts               - Check for alerts"
echo "  --json                 - Output in JSON format"
echo ""
echo "Files:"
echo "  DATABASE_OPTIMIZATION_README.md  - Complete documentation"
echo "  DATABASE_REVIEW.md               - Original analysis"
echo "  migrations/                      - SQL optimization scripts"
echo ""
echo "Examples:"
echo "  ./quick_setup                    # Quick start"
echo "  ./optimize --all                 # Full optimization"
echo "  ./monitor --server --port 5002   # Dashboard on port 5002"
echo "  ./optimize --health              # Health check"
echo "  ./monitor --report --json        # JSON performance report"
EOF
chmod +x help

echo "✅ Setup completed!"
echo ""
echo "📚 Available commands:"
echo "  ./quick_setup    - Quick optimization setup"
echo "  ./optimize       - Database optimization tool"
echo "  ./monitor        - Monitoring dashboard"
echo "  ./help           - Show detailed help"
echo ""
echo "🚀 Get started with: ./quick_setup"
echo ""
echo "📖 For complete documentation, see: DATABASE_OPTIMIZATION_README.md"