"""
Plugin Registry Service for managing plugin lifecycle and metadata.
"""

import hashlib
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from backend.models.plugin import (
    PluginInfo, PluginManifest, PluginStatus, ValidationResult, 
    PluginCategory, PluginDependency as PluginDependencyModel
)
from backend.db.models.plugin import (
    PluginRegistry as PluginRegistryDB, 
    PluginConfiguration as PluginConfigurationDB,
    PluginDependency as PluginDependencyDB,
    PluginAuditLog
)
from backend.core.cache_manager import MultiLevelCache

logger = logging.getLogger(__name__)


class PluginValidationError(Exception):
    """Plugin validation error"""
    pass


class PluginDependencyError(Exception):
    """Plugin dependency error"""
    def __init__(self, message: str, missing: List[str] = None):
        super().__init__(message)
        self.missing = missing or []


class PluginVersionError(Exception):
    """Plugin version compatibility error"""
    pass


class CircularDependencyError(Exception):
    """Circular dependency detected error"""
    def __init__(self, message: str, cycle: List[str] = None):
        super().__init__(message)
        self.cycle = cycle or []


class DependencyCheckResult:
    """Dependency check result"""
    def __init__(self, satisfied: bool, missing: List[str] = None, conflicts: List[str] = None):
        self.satisfied = satisfied
        self.missing = missing or []
        self.conflicts = conflicts or []


class VersionConstraint:
    """Version constraint parser and checker"""
    
    def __init__(self, constraint: str):
        self.constraint = constraint.strip()
        self.operator, self.version = self._parse_constraint(constraint)
    
    def _parse_constraint(self, constraint: str) -> Tuple[str, str]:
        """Parse version constraint into operator and version"""
        if constraint == "*" or constraint == "":
            return ">=", "0.0.0"
        
        # Match patterns like >=1.0.0, ~1.2.0, ^1.0.0, etc.
        pattern = r'^([><=~^]+)?(.+)$'
        match = re.match(pattern, constraint)
        
        if not match:
            return "==", constraint
        
        operator = match.group(1) or "=="
        version = match.group(2)
        
        return operator, version
    
    def satisfies(self, version: str) -> bool:
        """Check if a version satisfies this constraint"""
        try:
            return self._compare_versions(version, self.version, self.operator)
        except Exception:
            return False
    
    def _compare_versions(self, version1: str, version2: str, operator: str) -> bool:
        """Compare two semantic versions with given operator"""
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        # Pad with zeros to make same length
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        if operator == "==":
            return v1_parts == v2_parts
        elif operator == ">=":
            return v1_parts >= v2_parts
        elif operator == ">":
            return v1_parts > v2_parts
        elif operator == "<=":
            return v1_parts <= v2_parts
        elif operator == "<":
            return v1_parts < v2_parts
        elif operator == "~":
            # Compatible within same minor version
            return v1_parts[0] == v2_parts[0] and v1_parts[1] == v2_parts[1] and v1_parts >= v2_parts
        elif operator == "^":
            # Compatible within same major version
            return v1_parts[0] == v2_parts[0] and v1_parts >= v2_parts
        else:
            return False


class PluginRegistry:
    """Central registry for plugin management"""
    
    def __init__(self, db_session: Session, cache_manager: MultiLevelCache, security_manager=None):
        self.db = db_session
        self.cache = cache_manager
        self.security = security_manager
        self._plugins: Dict[str, PluginInfo] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
    
    async def register_plugin(self, plugin_path: str, manifest: PluginManifest) -> str:
        """Register a new plugin with enhanced validation and dependency management"""
        try:
            # Check for existing plugin with same name and version
            existing = await self._find_plugin_by_name_version(manifest.name, manifest.version)
            if existing:
                raise PluginValidationError(f"Plugin {manifest.name} v{manifest.version} already exists")
            
            # Validate plugin if security manager is available
            if self.security:
                validation_result = await self.security.validate_plugin(plugin_path)
                if not validation_result.is_valid:
                    raise PluginValidationError(f"Plugin validation failed: {validation_result.errors}")
            
            # Enhanced dependency checking with version constraints
            dependency_check = await self._check_dependencies_with_versions(manifest.dependencies)
            if not dependency_check.satisfied:
                error_msg = f"Dependency issues: missing={dependency_check.missing}, conflicts={dependency_check.conflicts}"
                raise PluginDependencyError(error_msg, dependency_check.missing)
            
            # Check for circular dependencies
            await self._check_circular_dependencies(manifest.name, manifest.dependencies)
            
            # Calculate file hash for integrity
            file_hash = self._calculate_file_hash(plugin_path)
            
            # Store in database with enhanced metadata
            plugin_id = await self._store_plugin_metadata(manifest, plugin_path, file_hash)
            
            # Store dependencies with version constraints
            await self._store_plugin_dependencies_with_versions(plugin_id, manifest.dependencies)
            
            # Update dependency graph
            self._dependency_graph[manifest.name] = set(manifest.dependencies)
            
            # Cache plugin info
            plugin_info = PluginInfo(
                id=plugin_id,
                name=manifest.name,
                version=manifest.version,
                description=manifest.description,
                author=manifest.author,
                category=manifest.category,
                status=PluginStatus.REGISTERED,
                manifest=manifest,
                path=plugin_path
            )
            self._plugins[plugin_id] = plugin_info
            
            # Invalidate discovery cache
            await self._invalidate_discovery_cache()
            
            # Log registration
            await self._log_plugin_action(plugin_id, "register", {"manifest": manifest.dict()})
            
            logger.info(f"Plugin {manifest.name} v{manifest.version} registered with ID {plugin_id}")
            return plugin_id
            
        except Exception as e:
            logger.error(f"Failed to register plugin {manifest.name}: {str(e)}")
            raise
    
    async def discover_plugins(self, filters: Dict[str, Any] = None) -> List[PluginInfo]:
        """Enhanced plugin discovery with advanced filtering and sorting"""
        cache_key = f"plugins:discover:{hash(str(sorted((filters or {}).items())))}"
        cached_result = await self.cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            query = self.db.query(PluginRegistryDB)
            
            # Apply enhanced filters
            if filters:
                # Category filter
                if 'category' in filters:
                    categories = filters['category'] if isinstance(filters['category'], list) else [filters['category']]
                    query = query.filter(PluginRegistryDB.category.in_(categories))
                
                # Status filter
                if 'status' in filters:
                    statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
                    query = query.filter(PluginRegistryDB.status.in_(statuses))
                
                # Name search (fuzzy)
                if 'name' in filters:
                    query = query.filter(PluginRegistryDB.name.ilike(f"%{filters['name']}%"))
                
                # Author search
                if 'author' in filters:
                    query = query.filter(PluginRegistryDB.author.ilike(f"%{filters['author']}%"))
                
                # Description search
                if 'description' in filters:
                    query = query.filter(PluginRegistryDB.description.ilike(f"%{filters['description']}%"))
                
                # Tags search (in manifest)
                if 'tags' in filters:
                    tags = filters['tags'] if isinstance(filters['tags'], list) else [filters['tags']]
                    for tag in tags:
                        query = query.filter(PluginRegistryDB.manifest.op('->>')('tags').ilike(f"%{tag}%"))
                
                # Version constraint
                if 'version' in filters:
                    query = query.filter(PluginRegistryDB.version == filters['version'])
                
                # Date range filters
                if 'created_after' in filters:
                    query = query.filter(PluginRegistryDB.created_at >= filters['created_after'])
                if 'created_before' in filters:
                    query = query.filter(PluginRegistryDB.created_at <= filters['created_before'])
            
            # Apply sorting
            sort_by = filters.get('sort_by', 'created_at') if filters else 'created_at'
            sort_order = filters.get('sort_order', 'desc') if filters else 'desc'
            
            if hasattr(PluginRegistryDB, sort_by):
                column = getattr(PluginRegistryDB, sort_by)
                if sort_order.lower() == 'desc':
                    query = query.order_by(desc(column))
                else:
                    query = query.order_by(column)
            
            # Apply pagination
            limit = filters.get('limit', 100) if filters else 100
            offset = filters.get('offset', 0) if filters else 0
            query = query.limit(limit).offset(offset)
            
            plugins = query.all()
            result = [self._plugin_from_db_row(row) for row in plugins]
            
            # Cache for 5 minutes
            await self.cache.set(cache_key, result, ttl=300)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to discover plugins: {str(e)}")
            return []
    
    async def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get plugin by ID with caching"""
        # Check cache first
        if plugin_id in self._plugins:
            return self._plugins[plugin_id]
        
        try:
            plugin_row = self.db.query(PluginRegistryDB).filter(
                PluginRegistryDB.id == plugin_id
            ).first()
            
            if not plugin_row:
                return None
            
            plugin_info = self._plugin_from_db_row(plugin_row)
            self._plugins[plugin_id] = plugin_info
            return plugin_info
            
        except Exception as e:
            logger.error(f"Failed to get plugin {plugin_id}: {str(e)}")
            return None
    
    async def get_plugin_by_name(self, name: str, version: str = None) -> Optional[PluginInfo]:
        """Get plugin by name and optionally version"""
        try:
            query = self.db.query(PluginRegistryDB).filter(PluginRegistryDB.name == name)
            
            if version:
                query = query.filter(PluginRegistryDB.version == version)
            else:
                # Get latest version if no version specified
                query = query.order_by(desc(PluginRegistryDB.created_at))
            
            plugin_row = query.first()
            
            if plugin_row:
                return self._plugin_from_db_row(plugin_row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get plugin by name {name}: {str(e)}")
            return None
    
    async def get_plugin_versions(self, name: str) -> List[str]:
        """Get all available versions of a plugin"""
        try:
            versions = self.db.query(PluginRegistryDB.version).filter(
                PluginRegistryDB.name == name
            ).order_by(desc(PluginRegistryDB.created_at)).all()
            
            return [v[0] for v in versions]
            
        except Exception as e:
            logger.error(f"Failed to get versions for plugin {name}: {str(e)}")
            return []
    
    async def get_plugin_dependencies(self, plugin_id: str) -> List[str]:
        """Get plugin dependency tree with enhanced resolution"""
        try:
            plugin = await self.get_plugin(plugin_id)
            if not plugin:
                return []
            
            return await self._resolve_dependency_tree(plugin.name, set())
            
        except Exception as e:
            logger.error(f"Failed to get dependencies for plugin {plugin_id}: {str(e)}")
            return []
    
    async def get_plugin_dependents(self, plugin_name: str) -> List[str]:
        """Get plugins that depend on the given plugin"""
        try:
            dependents = []
            
            # Query all plugins that have this plugin as a dependency
            deps = self.db.query(PluginDependencyDB).filter(
                PluginDependencyDB.dependency_name == plugin_name
            ).all()
            
            for dep in deps:
                plugin = await self.get_plugin(dep.plugin_id)
                if plugin:
                    dependents.append(plugin.name)
            
            return dependents
            
        except Exception as e:
            logger.error(f"Failed to get dependents for plugin {plugin_name}: {str(e)}")
            return []
    
    async def check_plugin_compatibility(self, plugin_name: str, target_version: str) -> Dict[str, Any]:
        """Check if a plugin version is compatible with current system"""
        try:
            # Get current plugin if exists
            current_plugin = await self.get_plugin_by_name(plugin_name)
            
            # Get all dependents
            dependents = await self.get_plugin_dependents(plugin_name)
            
            compatibility_issues = []
            
            # Check each dependent for version compatibility
            for dependent_name in dependents:
                dependent = await self.get_plugin_by_name(dependent_name)
                if dependent:
                    # Check if dependent's version constraint is satisfied by target version
                    deps = self.db.query(PluginDependencyDB).filter(
                        and_(
                            PluginDependencyDB.plugin_id == dependent.id,
                            PluginDependencyDB.dependency_name == plugin_name
                        )
                    ).first()
                    
                    if deps and deps.version_constraint:
                        constraint = VersionConstraint(deps.version_constraint)
                        if not constraint.satisfies(target_version):
                            compatibility_issues.append({
                                "dependent": dependent_name,
                                "constraint": deps.version_constraint,
                                "target_version": target_version
                            })
            
            return {
                "compatible": len(compatibility_issues) == 0,
                "current_version": current_plugin.version if current_plugin else None,
                "target_version": target_version,
                "issues": compatibility_issues,
                "dependents": dependents
            }
            
        except Exception as e:
            logger.error(f"Failed to check compatibility for {plugin_name}: {str(e)}")
            return {"compatible": False, "error": str(e)}
    
    async def get_plugin_statistics(self) -> Dict[str, Any]:
        """Get comprehensive plugin registry statistics"""
        try:
            # Basic counts
            total_plugins = self.db.query(func.count(PluginRegistryDB.id)).scalar()
            
            # Status distribution
            status_counts = self.db.query(
                PluginRegistryDB.status,
                func.count(PluginRegistryDB.id)
            ).group_by(PluginRegistryDB.status).all()
            
            # Category distribution
            category_counts = self.db.query(
                PluginRegistryDB.category,
                func.count(PluginRegistryDB.id)
            ).group_by(PluginRegistryDB.category).all()
            
            # Recent activity
            recent_registrations = self.db.query(func.count(PluginRegistryDB.id)).filter(
                PluginRegistryDB.created_at >= datetime.utcnow().replace(day=1)  # This month
            ).scalar()
            
            return {
                "total_plugins": total_plugins,
                "status_distribution": dict(status_counts),
                "category_distribution": dict(category_counts),
                "recent_registrations": recent_registrations,
                "dependency_graph_size": len(self._dependency_graph)
            }
            
        except Exception as e:
            logger.error(f"Failed to get plugin statistics: {str(e)}")
            return {}
    
    async def unregister_plugin(self, plugin_id: str, force: bool = False) -> bool:
        """Unregister a plugin with dependency checking"""
        try:
            plugin = await self.get_plugin(plugin_id)
            if not plugin:
                return False
            
            # Check for dependents unless force is True
            if not force:
                dependents = await self.get_plugin_dependents(plugin.name)
                if dependents:
                    raise PluginDependencyError(
                        f"Cannot unregister plugin {plugin.name}: has dependents {dependents}",
                        dependents
                    )
            
            # Remove from database
            self.db.query(PluginRegistryDB).filter(
                PluginRegistryDB.id == plugin_id
            ).delete()
            
            self.db.commit()
            
            # Remove from cache
            if plugin_id in self._plugins:
                del self._plugins[plugin_id]
            
            # Update dependency graph
            if plugin.name in self._dependency_graph:
                del self._dependency_graph[plugin.name]
            
            # Invalidate discovery cache
            await self._invalidate_discovery_cache()
            
            # Log unregistration
            await self._log_plugin_action(plugin_id, "unregister", {"force": force})
            
            logger.info(f"Plugin {plugin.name} v{plugin.version} unregistered")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister plugin {plugin_id}: {str(e)}")
            self.db.rollback()
            return False
    
    async def update_plugin_status(self, plugin_id: str, status: PluginStatus) -> bool:
        """Update plugin status"""
        try:
            plugin_row = self.db.query(PluginRegistryDB).filter(
                PluginRegistryDB.id == plugin_id
            ).first()
            
            if not plugin_row:
                return False
            
            plugin_row.status = status.value
            plugin_row.last_updated = datetime.utcnow()
            
            if status == PluginStatus.INSTALLED:
                plugin_row.installed_at = datetime.utcnow()
            
            self.db.commit()
            
            # Update cache
            if plugin_id in self._plugins:
                self._plugins[plugin_id].status = status
            
            # Invalidate discovery cache
            await self._invalidate_discovery_cache()
            
            logger.info(f"Plugin {plugin_id} status updated to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update plugin status {plugin_id}: {str(e)}")
            self.db.rollback()
            return False
    
    async def _check_dependencies_with_versions(self, dependencies: List[str]) -> DependencyCheckResult:
        """Enhanced dependency checking with version constraints"""
        if not dependencies:
            return DependencyCheckResult(satisfied=True)
        
        missing = []
        conflicts = []
        
        for dep_spec in dependencies:
            # Parse dependency specification (name@version or name>=version, etc.)
            if '@' in dep_spec:
                dep_name, version_constraint = dep_spec.split('@', 1)
            elif any(op in dep_spec for op in ['>=', '<=', '>', '<', '==', '~', '^']):
                # Find the operator position
                for op in ['>=', '<=', '>', '<', '==', '~', '^']:
                    if op in dep_spec:
                        dep_name, version_constraint = dep_spec.split(op, 1)
                        version_constraint = op + version_constraint
                        break
            else:
                dep_name = dep_spec
                version_constraint = "*"
            
            dep_name = dep_name.strip()
            
            # Check if dependency plugin exists
            dep_plugin = await self._find_plugin_by_name(dep_name)
            
            if not dep_plugin:
                missing.append(dep_name)
                continue
            
            # Check if plugin is in compatible state
            if dep_plugin.status not in [PluginStatus.INSTALLED, PluginStatus.ACTIVE]:
                missing.append(f"{dep_name} (not installed/active)")
                continue
            
            # Check version constraint
            if version_constraint != "*":
                constraint = VersionConstraint(version_constraint)
                if not constraint.satisfies(dep_plugin.version):
                    conflicts.append(f"{dep_name}: need {version_constraint}, have {dep_plugin.version}")
        
        return DependencyCheckResult(
            satisfied=len(missing) == 0 and len(conflicts) == 0,
            missing=missing,
            conflicts=conflicts
        )
    
    async def _check_circular_dependencies(self, plugin_name: str, dependencies: List[str], visited: Set[str] = None) -> None:
        """Check for circular dependencies in the dependency graph"""
        if visited is None:
            visited = set()
        
        if plugin_name in visited:
            cycle = list(visited) + [plugin_name]
            raise CircularDependencyError(f"Circular dependency detected: {' -> '.join(cycle)}", cycle)
        
        visited.add(plugin_name)
        
        for dep_spec in dependencies:
            # Extract dependency name (handle version constraints)
            dep_name = dep_spec.split('@')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].split('==')[0].split('~')[0].split('^')[0].strip()
            
            # Get dependency's dependencies
            dep_plugin = await self._find_plugin_by_name(dep_name)
            if dep_plugin and dep_name in self._dependency_graph:
                await self._check_circular_dependencies(dep_name, list(self._dependency_graph[dep_name]), visited.copy())
    
    async def _resolve_dependency_tree(self, plugin_name: str, visited: Set[str]) -> List[str]:
        """Resolve complete dependency tree for a plugin"""
        if plugin_name in visited:
            return []  # Avoid infinite recursion
        
        visited.add(plugin_name)
        dependencies = []
        
        # Get direct dependencies
        plugin = await self._find_plugin_by_name(plugin_name)
        if not plugin:
            return []
        
        deps = self.db.query(PluginDependencyDB).filter(
            PluginDependencyDB.plugin_id == plugin.id
        ).all()
        
        for dep in deps:
            dependencies.append(dep.dependency_name)
            
            # Recursive resolution
            sub_deps = await self._resolve_dependency_tree(dep.dependency_name, visited.copy())
            dependencies.extend(sub_deps)
        
        return list(set(dependencies))  # Remove duplicates
    
    async def _find_plugin_by_name_version(self, name: str, version: str) -> Optional[PluginInfo]:
        """Find plugin by exact name and version"""
        try:
            plugin_row = self.db.query(PluginRegistryDB).filter(
                and_(
                    PluginRegistryDB.name == name,
                    PluginRegistryDB.version == version
                )
            ).first()
            
            if plugin_row:
                return self._plugin_from_db_row(plugin_row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find plugin by name/version {name}@{version}: {str(e)}")
            return None
    
    async def _store_plugin_dependencies_with_versions(self, plugin_id: str, dependencies: List[str]):
        """Store plugin dependencies with version constraints"""
        for dep_spec in dependencies:
            # Parse dependency specification
            if '@' in dep_spec:
                dep_name, version_constraint = dep_spec.split('@', 1)
            elif any(op in dep_spec for op in ['>=', '<=', '>', '<', '==', '~', '^']):
                for op in ['>=', '<=', '>', '<', '==', '~', '^']:
                    if op in dep_spec:
                        dep_name, version_constraint = dep_spec.split(op, 1)
                        version_constraint = op + version_constraint
                        break
            else:
                dep_name = dep_spec
                version_constraint = "*"
            
            dep_row = PluginDependencyDB(
                plugin_id=plugin_id,
                dependency_name=dep_name.strip(),
                version_constraint=version_constraint,
                optional=False
            )
            self.db.add(dep_row)
        
        self.db.commit()
    
    async def _log_plugin_action(self, plugin_id: str, action: str, details: Dict[str, Any]):
        """Log plugin actions for audit trail"""
        try:
            audit_log = PluginAuditLog(
                plugin_id=plugin_id,
                action=action,
                details=details,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_log)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to log plugin action: {str(e)}")
    
    async def _check_dependencies(self, dependencies: List[str]) -> DependencyCheckResult:
        """Legacy method for backward compatibility"""
        return await self._check_dependencies_with_versions(dependencies)
    
    async def _find_plugin_by_name(self, name: str) -> Optional[PluginInfo]:
        """Find plugin by name"""
        try:
            plugin_row = self.db.query(PluginRegistryDB).filter(
                PluginRegistryDB.name == name
            ).first()
            
            if plugin_row:
                return self._plugin_from_db_row(plugin_row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find plugin by name {name}: {str(e)}")
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of plugin file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {str(e)}")
            return ""
    
    async def _store_plugin_metadata(self, manifest: PluginManifest, plugin_path: str, file_hash: str) -> str:
        """Store plugin metadata in database"""
        plugin_row = PluginRegistryDB(
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            category=manifest.category.value,
            status=PluginStatus.REGISTERED.value,
            manifest=manifest.dict(),
            file_path=plugin_path,
            file_hash=file_hash
        )
        
        self.db.add(plugin_row)
        self.db.commit()
        self.db.refresh(plugin_row)
        
        return str(plugin_row.id)
    
    async def _store_plugin_dependencies(self, plugin_id: str, dependencies: List[str]):
        """Legacy method for backward compatibility"""
        await self._store_plugin_dependencies_with_versions(plugin_id, dependencies)
    
    def _plugin_from_db_row(self, row: PluginRegistryDB) -> PluginInfo:
        """Convert database row to PluginInfo"""
        manifest = PluginManifest(**row.manifest)
        
        return PluginInfo(
            id=str(row.id),
            name=row.name,
            version=row.version,
            description=row.description or "",
            author=row.author or "",
            category=PluginCategory(row.category),
            status=PluginStatus(row.status),
            manifest=manifest,
            path=row.file_path,
            installed_at=row.installed_at,
            last_updated=row.last_updated
        )
    
    async def _invalidate_discovery_cache(self):
        """Invalidate plugin discovery cache"""
        try:
            # Clear all discovery cache entries
            cache_pattern = "plugins:discover:*"
            await self.cache.delete_pattern(cache_pattern)
        except Exception as e:
            logger.warning(f"Failed to invalidate discovery cache: {str(e)}")