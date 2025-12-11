#!/bin/bash
# Backend Server Startup Script (Linux/Mac)
# This script activates the virtual environment and starts the FastAPI server

echo "========================================"
echo "Agentic RAG Backend Server"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if venv exists
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${RED}[ERROR] Virtual environment not found!${NC}"
    echo -e "${YELLOW}Please run: python -m venv venv${NC}"
    echo -e "${YELLOW}Then install dependencies: pip install -r requirements.txt${NC}"
    read -p "Press Enter to exit"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}[1/3] Activating virtual environment...${NC}"
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to activate virtual environment${NC}"
    read -p "Press Enter to exit"
    exit 1
fi

echo -e "${GREEN}[OK] Virtual environment activated${NC}"
echo ""

# Check if uvicorn is installed
echo -e "${YELLOW}[2/3] Checking dependencies...${NC}"
python -c "import uvicorn" 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}[WARNING] uvicorn not found. Installing dependencies...${NC}"
    pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Failed to install dependencies${NC}"
        read -p "Press Enter to exit"
        exit 1
    fi
fi

echo -e "${GREEN}[OK] Dependencies ready${NC}"
echo ""

# Start the server
echo -e "${YELLOW}[3/3] Starting FastAPI server...${NC}"
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}Server will start on: http://localhost:8000${NC}"
echo -e "${GREEN}API Documentation: http://localhost:8000/docs${NC}"
echo -e "${GREEN}ReDoc: http://localhost:8000/redoc${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Trap Ctrl+C to deactivate venv
trap 'echo ""; echo "Server stopped. Deactivating virtual environment..."; deactivate; exit 0' INT

# Change to parent directory so Python can find 'backend' module
cd ..
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Deactivate venv when server stops
deactivate
