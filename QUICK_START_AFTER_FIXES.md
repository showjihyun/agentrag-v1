# Quick Start After Schema Fixes

## ✅ Schema Status: COMPLETE

All database schema issues have been fixed. Follow these steps to get the application running.

## 1. Verify Migrations

```bash
cd backend
alembic current
```

Expected output: `20260120_add_system_config (head)`

## 2. Restart Backend Server

### Option A: Direct Python
```bash
cd backend
python main.py
```

### Option B: Uvicorn
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option C: Using Scripts
```bash
# Windows
start-backend.bat

# Linux/Mac
./start-backend.sh
```

## 3. Start Frontend (if needed)

```bash
cd frontend
npm run dev
```

## 4. Test the Application

### Test Knowledge Bases
1. Navigate to Agent Builder → Knowledge Bases
2. Try creating a new knowledge base
3. Verify it appears in the list

### Test Chatflows
1. Navigate to Agent Builder → Flows
2. Create a new chatflow
3. Add tools to the chatflow
4. Test the chat interface

### Test Agents
1. Navigate to Agent Builder → Agents
2. Create a new agent
3. Attach knowledge bases and tools
4. Test agent execution

## 5. Verify System Config

The system should automatically initialize with:
- Embedding model: `jhgan/ko-sroberta-multitask`
- Embedding dimension: `768`

Check logs for: `"Embedding configuration initialized"`

## Common Issues & Solutions

### Issue: "Migration not at head"
```bash
cd backend
alembic upgrade head
```

### Issue: "Cannot connect to database"
1. Check PostgreSQL is running
2. Verify DATABASE_URL in `.env`
3. Test connection: `psql $DATABASE_URL`

### Issue: "Port already in use"
```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Kill the process or use different port
uvicorn main:app --port 8001
```

### Issue: "Module not found"
```bash
cd backend
pip install -r requirements.txt
```

## What's Fixed

✅ Knowledge base operations (list, create, update, delete)  
✅ Chatflow operations (create, configure, chat)  
✅ Agentflow operations (multi-agent workflows)  
✅ System configuration (embedding models, settings)  
✅ Execution tracking (logs, metrics, costs)  
✅ Marketplace features (share, browse, templates)  

## Monitoring

Watch the logs for:
- ✅ "Embedding configuration initialized"
- ✅ "Application startup complete"
- ✅ No schema-related errors
- ✅ Successful API requests

## Need Help?

1. Check `DATABASE_SCHEMA_FIXES_SUMMARY.md` for detailed info
2. Check `SCHEMA_FIXES_COMPLETE.md` for verification results
3. Review migration files in `backend/alembic/versions/`
4. Check application logs for specific errors

## Success Indicators

You'll know everything is working when:
- ✅ Backend starts without errors
- ✅ Frontend connects successfully
- ✅ Knowledge bases can be created
- ✅ Chatflows can be created and used
- ✅ Agents can be configured and executed
- ✅ No database schema errors in logs

---

**Ready to go!** 🚀

Start the backend server and begin using the application.
