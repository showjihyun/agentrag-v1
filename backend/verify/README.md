# Verification Scripts

This directory contains verification scripts used during development.

## ⚠️ Deprecation Notice

These scripts are **development-time utilities** and should NOT be used in production.
Most of these scripts should be converted to proper tests in `backend/tests/`.

## Migration Plan

### Scripts to Convert to Tests

The following scripts should be migrated to `backend/tests/integration/`:

1. **Database Verification**
   - `verify_db_improvements.py` → `tests/integration/test_db_improvements.py`
   - `verify_database_error_handling.py` → `tests/integration/test_db_error_handling.py`
   - `verify_tables.py` → `tests/integration/test_db_tables.py`

2. **Auth Verification**
   - `verify_auth_dependencies.py` → `tests/integration/test_auth.py`
   - `verify_auth_dependencies_v2.py` → `tests/integration/test_auth_v2.py`

3. **RAG Feature Verification**
   - `verify_all_rag_features.py` → `tests/integration/test_rag_features.py`
   - `verify_adaptive_routing_integration.py` → `tests/integration/test_adaptive_routing.py`

### Scripts to Delete (Obsolete)

These scripts are no longer needed:
- `verify_setup.py` - One-time setup verification
- `verify_migration.py` - Migration already applied
- `verify_env_config.py` - Covered by config validation

### Scripts to Keep (Utilities)

These scripts are useful for manual debugging:
- `verify_production_deployment.py` - Pre-deployment checklist
- `verify_comprehensive_testing.py` - Manual test runner

## Recommended Actions

1. **Do not add new scripts here** - Write proper tests instead
2. **Convert existing scripts** - Move logic to `backend/tests/`
3. **Clean up periodically** - Remove obsolete scripts

## Running Verification

For development verification, use pytest instead:

```bash
# Run all tests
pytest backend/tests/

# Run integration tests
pytest backend/tests/integration/

# Run with coverage
pytest --cov=backend --cov-report=html
```
