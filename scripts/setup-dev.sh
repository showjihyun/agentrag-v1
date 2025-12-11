#!/bin/bash
# Development Environment Setup Script for Linux/Mac

set -e  # Exit on error

echo "========================================"
echo "Agentic RAG - Development Setup"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found! Please install Python 3.10+"
    exit 1
fi

echo "[1/8] Python found: $(python3 --version)"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js not found! Please install Node.js 18+"
    exit 1
fi

echo "[2/8] Node.js found: $(node --version)"
echo ""

# Create backend virtual environment
echo "[3/8] Creating Python virtual environment..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo ""
echo "[4/8] Installing backend dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment file
echo ""
echo "[5/8] Setting up environment files..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ .env file created from .env.example"
    echo "⚠️  Please edit .env and add your configuration!"
else
    echo "✓ .env file already exists"
fi

# Generate API key encryption key
echo ""
echo "[6/8] Generating API key encryption key..."
python3 -c "from cryptography.fernet import Fernet; print('API_KEY_ENCRYPTION_KEY=' + Fernet.generate_key().decode())" > .env.generated
echo "✓ API key encryption key generated in .env.generated"
echo "⚠️  Please copy it to your .env file!"

# Run database migrations
echo ""
echo "[7/8] Running database migrations..."
alembic upgrade head || echo "⚠️  Migration failed. Make sure PostgreSQL is running!"

# Install frontend dependencies
echo ""
echo "[8/8] Installing frontend dependencies..."
cd ../frontend
npm install

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your configuration"
echo "2. Copy API_KEY_ENCRYPTION_KEY from backend/.env.generated to backend/.env"
echo "3. Start Docker services: docker-compose up -d"
echo "4. Start backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "5. Start frontend: cd frontend && npm run dev"
echo ""
echo "Happy coding! 🚀"
echo ""
