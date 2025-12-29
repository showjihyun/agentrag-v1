#!/usr/bin/env python3
"""
Database Optimization Script
Applies the database optimizations from DATABASE_REVIEW.md recommendations.

Usage:
    python optimize_database.py --phase 1  # Apply basic optimizations
    python optimize_database.py --phase 2  # Apply partitioning (requires downtime)
    python optimize_database.py --phase 3  # Apply security enhancements
    python optimize_database.py --all      # Apply all phases
    python optimize_database.py --status   # Check optimization status
    python optimize_database.py --health   # Run health check
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from config import get_settings
from db.database import get_db_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_optimization.log')
    ]
)
logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization manager."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_url = get_db_url()
        self.engine = create_engine(self.db_url)
        self.migrations_dir = Path(__file__).parent / "migrations"
        
    def execute_sql_file(self, file_path: Path, description: str = None) -> bool:
        """Execute SQL file with proper error handling."""
        try:
            logger.info(f"Executing {description or file_path.name}...")
            
            with open(file_path, 'r') as f:
                sql_content = f.read()
            
            # Split by statements and execute one by one for better error reporting
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            with self.engine.connect() as conn:
                # Set autocommit for DDL operations
                conn.execute(text("SET autocommit = ON"))
                
                for i, statement in enumerate(statements):
                    if statement.strip():
                        try:
                            logger.debug(f"Executing statement {i+1}/{len(statements)}")
                            conn.execute(text(statement))
                        except Exception as e:
                            # Log warning but continue for non-critical errors
                            if "already exists" in str(e).lower() or "does not exist" in str(e).lower():
                                logger.warning(f"Statement {i+1} warning: {e}")
                            else:
                                logger.error(f"Statement {i+1} failed: {e}")
                                raise
                
                conn.commit()
            
            logger.info(f"Successfully executed {file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute {file_path.name}: {e}")
            return False
    
    def apply_phase_1(self) -> bool:
        """Apply Phase 1: Basic performance optimizations."""
        logger.info("=== PHASE 1: Basic Performance Optimizations ===")
        
        migration_file = self.migrations_dir / "001_database_optimizations.sql"
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        success = self.execute_sql_file(
            migration_file,
            "Phase 1: Enhanced indexing, constraints, and analytics views"
        )
        
        if success:
            logger.info("Phase 1 optimizations completed successfully!")
            logger.info("- Enhanced indexing (partial, covering, GIN, full-text)")
            logger.info("- Advanced constraints for data integrity")
            logger.info("- Materialized views for analytics performance")
            logger.info("- Real-time statistics triggers")
            logger.info("- Health monitoring and maintenance functions")
        
        return success
    
    def apply_phase_2(self) -> bool:
        """Apply Phase 2: Table partitioning (requires careful planning)."""
        logger.info("=== PHASE 2: Table Partitioning ===")
        logger.warning("This phase creates partitioned tables but does NOT switch to them automatically.")
        logger.warning("Review the migration plan before applying in production!")
        
        migration_file = self.migrations_dir / "002_table_partitioning.sql"
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        success = self.execute_sql_file(
            migration_file,
            "Phase 2: Table partitioning setup"
        )
        
        if success:
            logger.info("Phase 2 partitioning setup completed successfully!")
            logger.info("- Created partitioned tables for workflow_executions, audit_logs, agent_executions")
            logger.info("- Set up automatic partition management functions")
            logger.info("- Created monitoring views for partition health")
            logger.warning("")
            logger.warning("NEXT STEPS FOR PRODUCTION:")
            logger.warning("1. Test partitioned tables in staging environment")
            logger.warning("2. Schedule maintenance window for data migration")
            logger.warning("3. Run migrate_to_partitioned_tables() during maintenance")
            logger.warning("4. Run switch_to_partitioned_tables() to activate")
            logger.warning("5. Set up cron job for partition_maintenance()")
        
        return success
    
    def apply_phase_3(self) -> bool:
        """Apply Phase 3: Security enhancements."""
        logger.info("=== PHASE 3: Security Enhancements ===")
        
        migration_file = self.migrations_dir / "003_security_enhancements.sql"
        if not migration_file.exists():
            logger.error(f"Migration file not found: {migration_file}")
            return False
        
        success = self.execute_sql_file(
            migration_file,
            "Phase 3: Row-Level Security and encryption"
        )
        
        if success:
            logger.info("Phase 3 security enhancements completed successfully!")
            logger.info("- Row-Level Security (RLS) enabled for sensitive tables")
            logger.info("- Application roles created (application_role, admin_role, readonly_role)")
            logger.info("- Advanced encryption functions implemented")
            logger.info("- Enhanced audit logging with security context")
            logger.info("- Suspicious activity detection functions")
            logger.info("- Data masking and permission validation")
            logger.warning("")
            logger.warning("IMPORTANT: Configure these settings in production:")
            logger.warning("1. Set app.encryption_key to a strong 32-byte key")
            logger.warning("2. Create database users and assign appropriate roles")
            logger.warning("3. Configure connection pooling with role-based connections")
            logger.warning("4. Set up monitoring for security events")
        
        return success
    
    def check_optimization_status(self) -> Dict[str, bool]:
        """Check which optimizations have been applied."""
        logger.info("=== OPTIMIZATION STATUS CHECK ===")
        
        status = {
            "phase_1_indexes": False,
            "phase_1_views": False,
            "phase_1_functions": False,
            "phase_2_partitions": False,
            "phase_2_functions": False,
            "phase_3_rls": False,
            "phase_3_encryption": False,
            "phase_3_security": False
        }
        
        try:
            with self.engine.connect() as conn:
                # Check Phase 1: Enhanced indexes
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_indexes 
                    WHERE indexname LIKE 'ix_%_active_%' OR indexname LIKE 'ix_%_covering'
                """)).scalar()
                status["phase_1_indexes"] = result > 0
                
                # Check Phase 1: Materialized views
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_matviews 
                    WHERE matviewname IN ('workflow_analytics', 'agent_analytics')
                """)).scalar()
                status["phase_1_views"] = result >= 2
                
                # Check Phase 1: Functions
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_proc 
                    WHERE proname IN ('refresh_analytics', 'database_health_check', 'cleanup_old_executions')
                """)).scalar()
                status["phase_1_functions"] = result >= 3
                
                # Check Phase 2: Partitioned tables
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_tables 
                    WHERE tablename LIKE '%_partitioned'
                """)).scalar()
                status["phase_2_partitions"] = result >= 3
                
                # Check Phase 2: Partition functions
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_proc 
                    WHERE proname IN ('create_monthly_partitions', 'partition_maintenance')
                """)).scalar()
                status["phase_2_functions"] = result >= 2
                
                # Check Phase 3: RLS policies
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_policies 
                    WHERE policyname LIKE '%_access_policy'
                """)).scalar()
                status["phase_3_rls"] = result >= 5
                
                # Check Phase 3: Encryption functions
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_proc 
                    WHERE proname IN ('encrypt_data', 'decrypt_data', 'hash_password')
                """)).scalar()
                status["phase_3_encryption"] = result >= 3
                
                # Check Phase 3: Security functions
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_proc 
                    WHERE proname IN ('log_security_event', 'detect_suspicious_activity', 'set_user_context')
                """)).scalar()
                status["phase_3_security"] = result >= 3
        
        except Exception as e:
            logger.error(f"Error checking optimization status: {e}")
            return status
        
        # Print status report
        logger.info("Phase 1 (Basic Optimizations):")
        logger.info(f"  ✓ Enhanced Indexes: {'✓' if status['phase_1_indexes'] else '✗'}")
        logger.info(f"  ✓ Analytics Views: {'✓' if status['phase_1_views'] else '✗'}")
        logger.info(f"  ✓ Maintenance Functions: {'✓' if status['phase_1_functions'] else '✗'}")
        
        logger.info("Phase 2 (Partitioning):")
        logger.info(f"  ✓ Partitioned Tables: {'✓' if status['phase_2_partitions'] else '✗'}")
        logger.info(f"  ✓ Partition Functions: {'✓' if status['phase_2_functions'] else '✗'}")
        
        logger.info("Phase 3 (Security):")
        logger.info(f"  ✓ Row-Level Security: {'✓' if status['phase_3_rls'] else '✗'}")
        logger.info(f"  ✓ Encryption Functions: {'✓' if status['phase_3_encryption'] else '✗'}")
        logger.info(f"  ✓ Security Functions: {'✓' if status['phase_3_security'] else '✗'}")
        
        return status
    
    def run_health_check(self) -> Dict[str, any]:
        """Run comprehensive database health check."""
        logger.info("=== DATABASE HEALTH CHECK ===")
        
        health_data = {}
        
        try:
            with self.engine.connect() as conn:
                # Run the database health check function
                result = conn.execute(text("SELECT * FROM database_health_check()"))
                health_metrics = result.fetchall()
                
                logger.info("Health Check Results:")
                for metric, value, status, recommendation in health_metrics:
                    status_icon = "✓" if status == "OK" else "⚠" if status == "WARNING" else "ℹ"
                    logger.info(f"  {status_icon} {metric}: {value} ({status})")
                    if status != "OK":
                        logger.info(f"    → {recommendation}")
                    
                    health_data[metric] = {
                        "value": value,
                        "status": status,
                        "recommendation": recommendation
                    }
                
                # Additional checks
                logger.info("\nAdditional Metrics:")
                
                # Table sizes
                result = conn.execute(text("""
                    SELECT tablename, pg_size_pretty(pg_total_relation_size('public.'||tablename)) as size
                    FROM pg_tables 
                    WHERE schemaname = 'public' 
                    ORDER BY pg_total_relation_size('public.'||tablename) DESC 
                    LIMIT 5
                """))
                
                logger.info("  Top 5 Largest Tables:")
                for table, size in result.fetchall():
                    logger.info(f"    - {table}: {size}")
                
                # Index usage
                result = conn.execute(text("""
                    SELECT COUNT(*) as unused_indexes
                    FROM pg_stat_user_indexes 
                    WHERE idx_scan = 0
                """)).scalar()
                
                logger.info(f"  Unused Indexes: {unused_indexes}")
                
                # Recent activity
                result = conn.execute(text("""
                    SELECT COUNT(*) as recent_executions
                    FROM workflow_executions 
                    WHERE started_at > NOW() - INTERVAL '24 hours'
                """)).scalar()
                
                logger.info(f"  Workflow Executions (24h): {recent_executions}")
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_data["error"] = str(e)
        
        return health_data
    
    def refresh_analytics(self) -> bool:
        """Refresh materialized views for analytics."""
        logger.info("=== REFRESHING ANALYTICS VIEWS ===")
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT refresh_analytics()"))
                conn.commit()
            
            logger.info("Analytics views refreshed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Failed to refresh analytics: {e}")
            return False
    
    def run_maintenance(self) -> bool:
        """Run database maintenance tasks."""
        logger.info("=== RUNNING DATABASE MAINTENANCE ===")
        
        try:
            with self.engine.connect() as conn:
                # Run vacuum analyze
                logger.info("Running vacuum analyze on key tables...")
                conn.execute(text("SELECT maintenance_vacuum_analyze()"))
                
                # Clean up old executions (90 days retention)
                logger.info("Cleaning up old execution records...")
                result = conn.execute(text("SELECT cleanup_old_executions(90)")).scalar()
                logger.info(f"Cleaned up {result} old execution records")
                
                conn.commit()
            
            logger.info("Database maintenance completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Database maintenance failed: {e}")
            return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database Optimization Manager")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3], 
                       help="Apply specific optimization phase")
    parser.add_argument("--all", action="store_true", 
                       help="Apply all optimization phases")
    parser.add_argument("--status", action="store_true", 
                       help="Check optimization status")
    parser.add_argument("--health", action="store_true", 
                       help="Run database health check")
    parser.add_argument("--refresh", action="store_true", 
                       help="Refresh analytics views")
    parser.add_argument("--maintenance", action="store_true", 
                       help="Run database maintenance")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    optimizer = DatabaseOptimizer()
    
    try:
        if args.status:
            optimizer.check_optimization_status()
        
        elif args.health:
            optimizer.run_health_check()
        
        elif args.refresh:
            optimizer.refresh_analytics()
        
        elif args.maintenance:
            optimizer.run_maintenance()
        
        elif args.phase:
            if args.phase == 1:
                success = optimizer.apply_phase_1()
            elif args.phase == 2:
                success = optimizer.apply_phase_2()
            elif args.phase == 3:
                success = optimizer.apply_phase_3()
            
            if success:
                logger.info(f"Phase {args.phase} completed successfully!")
                # Run health check after optimization
                optimizer.run_health_check()
            else:
                logger.error(f"Phase {args.phase} failed!")
                sys.exit(1)
        
        elif args.all:
            logger.info("Applying all optimization phases...")
            
            phases = [
                (1, optimizer.apply_phase_1),
                (2, optimizer.apply_phase_2),
                (3, optimizer.apply_phase_3)
            ]
            
            for phase_num, phase_func in phases:
                logger.info(f"\n{'='*50}")
                if not phase_func():
                    logger.error(f"Phase {phase_num} failed! Stopping.")
                    sys.exit(1)
                time.sleep(2)  # Brief pause between phases
            
            logger.info("\n" + "="*50)
            logger.info("ALL OPTIMIZATION PHASES COMPLETED SUCCESSFULLY!")
            logger.info("="*50)
            
            # Final health check
            optimizer.run_health_check()
        
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()