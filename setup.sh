#!/bin/bash

# Agentic RAG System Setup Script

echo "==================================="
echo "Agentic RAG System Setup"
echo "==================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ .env file created. Please edit it with your configuration."
else
    echo "✓ .env file already exists"
fi

# Setup backend
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt
echo "✓ Backend dependencies installed"

cd ..

# Setup frontend
echo ""
echo "Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node.js dependencies..."
    npm install
    echo "✓ Frontend dependencies installed"
else
    echo "✓ Frontend dependencies already installed"
fi

cd ..

# Start infrastructure
echo ""
echo "Starting infrastructure services (Milvus, Redis, etc.)..."
docker-compose up -d milvus redis etcd minio

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. (Optional) Install and start Ollama: https://ollama.ai"
echo "3. Start backend: python -m uvicorn backend.main:app --reload --port 8000"
echo "4. Start frontend: cd frontend && npm run dev"
echo ""
echo "Or use Docker Compose for all services:"
echo "  docker-compose up -d"
echo ""
