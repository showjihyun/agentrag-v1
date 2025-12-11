# Scripts Directory

Organized collection of utility scripts for the Agentic RAG project.

## Directory Structure

```
scripts/
├── startup/        # Application startup scripts
├── install/        # Dependency installation scripts
├── setup/          # Initial setup and configuration
├── database/       # Database operations and migrations
├── maintenance/    # System maintenance and troubleshooting
└── benchmark/      # Performance testing and benchmarking
```

## Quick Reference

### Starting the Application

```bash
# Windows - Quick start
scripts/startup/quick-start.bat

# Windows - Start all services
scripts/startup/start-all.bat

# Linux/Mac
scripts/startup/start-linux.sh
```

### Installation

```bash
# Clean install of Python dependencies
scripts/install/install-dependencies-clean.bat

# Install frontend dependencies
scripts/install/install-frontend-deps.bat
```

### Database Operations

```bash
# Initialize database
scripts/setup/init-database.bat

# Create database schema
psql -f scripts/database/create-database.sql
```

### Maintenance

```bash
# Restart backend
scripts/maintenance/restart-backend.bat

# Fix common issues
scripts/maintenance/fix-dependencies.bat
```

### Benchmarking

```bash
# Run performance benchmarks
python scripts/benchmark/benchmark_gpu_performance.py
python scripts/benchmark/load_test.py
```

## Notes

- All `.bat` files are for Windows
- All `.sh` files are for Linux/Mac
- Python scripts (`.py`) work on all platforms
- SQL scripts (`.sql`) require PostgreSQL client
