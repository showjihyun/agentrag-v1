# Database Schema Files

**Last Updated**: 2026-01-20  
**Database**: agenticrag (PostgreSQL 15)

---

## 📁 Files

### schema_latest.sql
**Description**: Latest database schema export  
**Generated**: Automatically updated when running `export_schema.py`  
**Size**: ~38 KB  
**Tables**: 47

**Contents**:
- DROP statements for all tables
- CREATE TABLE statements with all columns
- PRIMARY KEY constraints
- FOREIGN KEY constraints
- UNIQUE constraints
- INDEX definitions

---

## 🚀 Usage

### Import Schema to New Database

```bash
# Create database
createdb -U postgres agenticrag

# Import schema
psql -U postgres -d agenticrag -f backend/schemas/schema_latest.sql
```

### Docker Environment

```bash
# Copy schema to container
docker cp backend/schemas/schema_latest.sql agenticrag-postgres:/tmp/

# Import in container
docker exec -it agenticrag-postgres psql -U postgres -d agenticrag -f /tmp/schema_latest.sql
```

### Compare Schemas

```bash
# Export current schema
python backend/scripts/export_schema.py

# Compare with previous version
diff backend/schemas/schema_20260120_132859.sql backend/schemas/schema_latest.sql
```

---

## 📊 Schema Overview

### Total Tables: 47

#### Core Tables (14)
- users
- documents
- agents
- agent_templates
- agentflows
- blocks
- chatflows
- flow_executions
- knowledge_bases
- messages
- prompt_templates
- sessions
- tools
- workflows

#### Agent System (7)
- agent_versions
- agent_tools
- agent_knowledgebases
- agent_executions
- agent_memories
- agentflow_agents
- agentflow_edges

#### Plugin System (6)
- plugin_registry
- plugin_configurations
- plugin_metrics
- plugin_dependencies
- plugin_audit_logs
- plugin_security_scans

#### Marketplace (3)
- marketplace_purchases
- marketplace_reviews
- marketplace_revenue

#### Organization (2)
- organizations
- teams

#### Conversations (3)
- conversations
- feedback
- conversation_shares

#### Other (12)
- bookmarks
- notifications
- api_keys
- event_store
- knowledge_graphs
- tool_executions
- query_logs
- user_settings
- credits
- rate_limit_configs
- migration_history
- alembic_version

---

## 🔄 Generating New Schema Export

### Manual Export

```bash
python backend/scripts/export_schema.py
```

### Automated Export (After Migration)

```bash
# Run migration
alembic upgrade head

# Export schema
python backend/scripts/export_schema.py
```

---

## 📝 Schema Versioning

Schema files are timestamped:
- `schema_YYYYMMDD_HHMMSS.sql` - Timestamped version
- `schema_latest.sql` - Always points to latest

**Example**:
```
schema_20260120_132859.sql  # Specific version
schema_latest.sql           # Latest (copy of above)
```

---

## 🔍 Schema Details

### Key Features

1. **UUID Primary Keys**
   - All tables use UUID for primary keys
   - Better for distributed systems
   - No auto-increment issues

2. **JSONB Columns**
   - Flexible data storage
   - Indexable with GIN indexes
   - Used for: configuration, metadata, settings

3. **Soft Deletes**
   - `deleted_at` column in key tables
   - Data preservation
   - Audit trail

4. **Timestamps**
   - `created_at` - Record creation
   - `updated_at` - Last modification
   - Automatic via DEFAULT

5. **Foreign Keys**
   - CASCADE on user deletion
   - SET NULL for optional references
   - Referential integrity

---

## 🛠️ Maintenance

### Regular Tasks

1. **Export Schema** (Weekly)
   ```bash
   python backend/scripts/export_schema.py
   ```

2. **Backup Schema Files** (Monthly)
   ```bash
   cp backend/schemas/schema_latest.sql backups/schema_$(date +%Y%m%d).sql
   ```

3. **Review Changes** (After migrations)
   ```bash
   git diff backend/schemas/schema_latest.sql
   ```

---

## 📚 Related Documentation

- [Alembic Migrations](../alembic/MIGRATIONS.md)
- [Database Models](../db/models/README.md)
- [API Documentation](../../docs/api.md)

---

## ⚠️ Important Notes

### Before Importing

1. **Backup existing database**
   ```bash
   pg_dump -U postgres -d agenticrag > backup_$(date +%Y%m%d).sql
   ```

2. **Check PostgreSQL version**
   - Requires PostgreSQL 12+
   - Tested on PostgreSQL 15

3. **Verify extensions**
   ```sql
   CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
   ```

### After Importing

1. **Verify tables**
   ```sql
   SELECT COUNT(*) FROM information_schema.tables 
   WHERE table_schema = 'public';
   -- Should return 47
   ```

2. **Check constraints**
   ```sql
   SELECT COUNT(*) FROM information_schema.table_constraints 
   WHERE constraint_schema = 'public';
   ```

3. **Test application**
   - Run migrations: `alembic upgrade head`
   - Run tests: `pytest`
   - Start application

---

## 🐛 Troubleshooting

### Import Fails

**Error**: "relation already exists"
```bash
# Drop all tables first
psql -U postgres -d agenticrag -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Then import
psql -U postgres -d agenticrag -f backend/schemas/schema_latest.sql
```

**Error**: "permission denied"
```bash
# Grant permissions
psql -U postgres -d agenticrag -c "GRANT ALL ON SCHEMA public TO postgres;"
```

### Schema Mismatch

If schema doesn't match migrations:

1. Check alembic version
   ```sql
   SELECT * FROM alembic_version;
   ```

2. Run migrations
   ```bash
   alembic upgrade head
   ```

3. Re-export schema
   ```bash
   python backend/scripts/export_schema.py
   ```

---

**Maintained by**: Database Team  
**Last Export**: 2026-01-20 13:28:59
