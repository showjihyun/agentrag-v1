# 🚀 Quick Start Guide

Get up and running with the Workflow Platform in under 10 minutes!

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Docker & Docker Compose** (recommended for quick setup)
- **Python 3.10+** (for local development)
- **Node.js 18+** (for frontend development)
- **Git** (for cloning the repository)

## 🐳 Option 1: Docker Setup (Recommended)

The fastest way to get started is using Docker Compose.

### 1. Clone the Repository

```bash
git clone https://github.com/showjihyun/agentrag-v1.git
cd agentrag-v1
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (optional - defaults work for local development)
nano .env
```

### 3. Start All Services

```bash
# Start all services in background
docker-compose up -d

# Check status
docker-compose ps

# View logs (optional)
docker-compose logs -f
```

### 4. Access the Platform

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **Main Platform** | http://localhost:3000 | Redirects to Agent Builder |
| 🤖 **Agent Builder** | http://localhost:3000/agent-builder | Workflow builder interface |
| 🚀 **API** | http://localhost:8000 | Backend API |
| 📚 **API Docs** | http://localhost:8000/docs | Swagger documentation |

### 5. Create Your First Workflow

1. **Open Agent Builder**: Navigate to http://localhost:3000
2. **Choose Workflow Type**:
   - **Agentflow**: For task automation
   - **Chatflow**: For conversational AI
3. **Build Your Workflow**:
   - Drag nodes from the sidebar
   - Connect nodes to create flow
   - Configure each node
4. **Test & Execute**: Use the test button to run your workflow

## 💻 Option 2: Local Development Setup

For development or if you prefer running services locally.

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
docker-compose up -d postgres milvus redis

# Run migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access Services

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎯 Your First Workflow

Let's create a simple "Hello World" workflow to get familiar with the platform.

### Example 1: Simple Greeting Workflow

1. **Create New Agentflow**
2. **Add Nodes**:
   - Start node (automatically added)
   - AI Agent node
   - End node (automatically added)
3. **Configure AI Agent**:
   - Name: "Greeting Agent"
   - Prompt: "Say hello to the user and ask how you can help them today"
   - LLM Provider: Choose your preferred provider
4. **Connect Nodes**: Start → AI Agent → End
5. **Test**: Click the test button and provide input

### Example 2: Automated Email Workflow

1. **Create New Agentflow**
2. **Add Nodes**:
   - Webhook Trigger
   - Condition node
   - AI Agent node
   - Email node
3. **Configure Flow**:
   - Webhook: Set up to receive data
   - Condition: Check if email is provided
   - AI Agent: Generate personalized response
   - Email: Send the response
4. **Test**: Send a POST request to the webhook URL

### Example 3: Daily Report Workflow

1. **Create New Agentflow**
2. **Add Nodes**:
   - Schedule Trigger (daily at 9 AM)
   - Database Query node
   - AI Agent node
   - Slack node
3. **Configure Flow**:
   - Schedule: Set cron expression
   - Database: Query your data
   - AI Agent: Analyze and summarize data
   - Slack: Send report to channel

## 🔧 Configuration Options

### Environment Variables

Key configuration options in `.env`:

```env
# LLM Provider
LLM_PROVIDER=ollama              # ollama, openai, claude, gemini
LLM_MODEL=llama3.3:70b          # Model name

# Database URLs
DATABASE_URL=postgresql://raguser:ragpassword@localhost:5433/agentic_rag
MILVUS_HOST=localhost
REDIS_HOST=localhost

# Features
ENABLE_HYBRID_SEARCH=true
ADAPTIVE_ROUTING_ENABLED=true
DEFAULT_QUERY_MODE=balanced
```

### LLM Provider Setup

#### Using Ollama (Local, Free)
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.3:70b

# Set in .env
LLM_PROVIDER=ollama
LLM_MODEL=llama3.3:70b
```

#### Using OpenAI
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
LLM_MODEL=gpt-4
```

#### Using Claude
```env
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
LLM_MODEL=claude-3-sonnet-20240229
```

## 🧪 Testing Your Setup

### Health Check

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000
```

### API Test

```bash
# Test workflow creation
curl -X POST "http://localhost:8000/api/agent-builder/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Workflow",
    "description": "My first workflow",
    "nodes": [],
    "edges": []
  }'
```

## 🔍 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5433  # PostgreSQL

# Kill processes if needed
kill -9 <PID>
```

#### Docker Issues
```bash
# Restart all services
docker-compose down
docker-compose up -d

# View logs
docker-compose logs backend
docker-compose logs frontend

# Clean up (if needed)
docker-compose down -v
docker system prune -a
```

#### Database Connection Issues
```bash
# Check database status
docker-compose ps postgres

# Reset database
docker-compose down postgres
docker-compose up -d postgres

# Run migrations again
cd backend
alembic upgrade head
```

### Getting Help

If you encounter issues:

1. **Check Logs**: Look at Docker Compose logs
2. **Verify Ports**: Ensure no port conflicts
3. **Check Environment**: Verify `.env` configuration
4. **Database**: Ensure database is running and accessible
5. **GitHub Issues**: Search existing issues or create a new one

## 📚 Next Steps

Now that you have the platform running:

1. **Explore Examples**: Check out the `examples/` directory
2. **Read Documentation**: Browse the `docs/` folder
3. **Join Community**: Participate in GitHub Discussions
4. **Build Workflows**: Start creating your own automations
5. **Integrate Services**: Connect your favorite tools

### Recommended Learning Path

1. **Basic Workflows**: Start with simple 2-3 node workflows
2. **Conditions & Loops**: Learn control flow
3. **Integrations**: Connect external services
4. **AI Agents**: Explore multi-agent workflows
5. **Advanced Features**: Memory, human approval, etc.

## 🎉 Welcome to Workflow Platform!

You're now ready to build powerful AI workflows! 

- 🤖 **Create intelligent automations**
- 🔗 **Connect your favorite tools**
- 📊 **Monitor execution in real-time**
- 🚀 **Scale your productivity**

Happy building! 🎯