"""
Plugin Dependency Resolution System for the orchestration plugin system.
"""

import logging
from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from backend.models.plugin import PluginInfo, PluginStatus, PluginManifest

logger = logging.getLogger(__name__)


class DependencyResolutionError(Exception):
    """Base exception for dependency resolution errors"""
    pass


class CircularDependencyError(DependencyResolutionError):
    """Circular dependency detected error"""
    def __init__(self, message: str, cycle: List[str] = None):
        super().__init__(message)
        self.cycle = cycle or []


class MissingDependencyError(DependencyResolutionError):
    """Missing dependency error"""
    def __init__(self, message: str, missing: List[str] = None):
        super().__init__(message)
        self.missing = missing or []


class VersionConflictError(DependencyResolutionError):
    """Version conflict error"""
    def __init__(self, message: str, conflicts: List[str] = None):
        super().__init__(message)
        self.conflicts = conflicts or []


class ResolutionStrategy(Enum):
    """Dependency resolution strategies"""
    STRICT = "strict"  # All dependencies must be satisfied exactly
    PERMISSIVE = "permissive"  # Allow compatible versions
    LATEST = "latest"  # Always use latest compatible version


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph"""
    name: str
    version: str
    dependencies: List[str]
    dependents: List[str]
    status: PluginStatus
    plugin_info: Optional[PluginInfo] = None


@dataclass
class ResolutionResult:
    """Result of dependency resolution"""
    success: bool
    resolved_order: List[str]
    missing_dependencies: List[str]
    version_conflicts: List[str]
    circular_dependencies: List[List[str]]
    warnings: List[str]


class VersionConstraint:
    """Enhanced version constraint parser and checker"""
    
    def __init__(self, constraint: str):
        self.constraint = constraint.strip()
        self.operator, self.version = self._parse_constraint(constraint)
    
    def _parse_constraint(self, constraint: str) -> Tuple[str, str]:
        """Parse version constraint into operator and version"""
        if constraint == "*" or constraint == "":
            return ">=", "0.0.0"
        
        # Match patterns like >=1.0.0, ~1.2.0, ^1.0.0, etc.
        import re
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
        except Exception as e:
            logger.warning(f"Version comparison failed: {e}")
            return False
    
    def _compare_versions(self, version1: str, version2: str, operator: str) -> bool:
        """Compare two semantic versions with given operator"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
        except ValueError:
            # Fallback to string comparison for non-numeric versions
            return self._string_version_compare(version1, version2, operator)
        
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
            return (v1_parts[0] == v2_parts[0] and 
                   v1_parts[1] == v2_parts[1] and 
                   v1_parts >= v2_parts)
        elif operator == "^":
            # Compatible within same major version
            return v1_parts[0] == v2_parts[0] and v1_parts >= v2_parts
        else:
            return False
    
    def _string_version_compare(self, version1: str, version2: str, operator: str) -> bool:
        """Fallback string-based version comparison"""
        if operator == "==":
            return version1 == version2
        elif operator == ">=":
            return version1 >= version2
        elif operator == ">":
            return version1 > version2
        elif operator == "<=":
            return version1 <= version2
        elif operator == "<":
            return version1 < version2
        else:
            return version1 == version2


class DependencyGraph:
    """Manages the plugin dependency graph"""
    
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.edges: Dict[str, Set[str]] = {}  # plugin -> dependencies
        self.reverse_edges: Dict[str, Set[str]] = {}  # plugin -> dependents
    
    def add_plugin(self, plugin_info: PluginInfo):
        """Add a plugin to the dependency graph"""
        node = DependencyNode(
            name=plugin_info.name,
            version=plugin_info.version,
            dependencies=plugin_info.manifest.dependencies,
            dependents=[],
            status=plugin_info.status,
            plugin_info=plugin_info
        )
        
        self.nodes[plugin_info.name] = node
        self.edges[plugin_info.name] = set(plugin_info.manifest.dependencies)
        
        # Update reverse edges
        for dep in plugin_info.manifest.dependencies:
            if dep not in self.reverse_edges:
                self.reverse_edges[dep] = set()
            self.reverse_edges[dep].add(plugin_info.name)
    
    def remove_plugin(self, plugin_name: str):
        """Remove a plugin from the dependency graph"""
        if plugin_name not in self.nodes:
            return
        
        # Remove from edges
        if plugin_name in self.edges:
            for dep in self.edges[plugin_name]:
                if dep in self.reverse_edges:
                    self.reverse_edges[dep].discard(plugin_name)
            del self.edges[plugin_name]
        
        # Remove from reverse edges
        if plugin_name in self.reverse_edges:
            for dependent in self.reverse_edges[plugin_name]:
                if dependent in self.edges:
                    self.edges[dependent].discard(plugin_name)
            del self.reverse_edges[plugin_name]
        
        # Remove node
        del self.nodes[plugin_name]
    
    def get_dependencies(self, plugin_name: str) -> Set[str]:
        """Get direct dependencies of a plugin"""
        return self.edges.get(plugin_name, set())
    
    def get_dependents(self, plugin_name: str) -> Set[str]:
        """Get direct dependents of a plugin"""
        return self.reverse_edges.get(plugin_name, set())
    
    def has_cycles(self) -> List[List[str]]:
        """Detect circular dependencies using DFS"""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.edges.get(node, set()):
                if neighbor in self.nodes:  # Only check existing nodes
                    dfs(neighbor, path.copy())
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def topological_sort(self) -> List[str]:
        """Perform topological sort to get dependency order"""
        in_degree = {node: 0 for node in self.nodes}
        
        # Calculate in-degrees
        for node in self.nodes:
            for dep in self.edges.get(node, set()):
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Queue for nodes with no incoming edges
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Reduce in-degree for neighbors
            for neighbor in self.reverse_edges.get(node, set()):
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        return result


class DependencyResolver:
    """Advanced dependency resolution system"""
    
    def __init__(self, strategy: ResolutionStrategy = ResolutionStrategy.PERMISSIVE):
        self.strategy = strategy
        self.graph = DependencyGraph()
    
    def add_plugin(self, plugin_info: PluginInfo):
        """Add a plugin to the resolver"""
        self.graph.add_plugin(plugin_info)
    
    def remove_plugin(self, plugin_name: str):
        """Remove a plugin from the resolver"""
        self.graph.remove_plugin(plugin_name)
    
    def resolve_dependencies(self, target_plugins: List[str]) -> ResolutionResult:
        """Resolve dependencies for target plugins"""
        try:
            # Check for circular dependencies
            cycles = self.graph.has_cycles()
            if cycles:
                return ResolutionResult(
                    success=False,
                    resolved_order=[],
                    missing_dependencies=[],
                    version_conflicts=[],
                    circular_dependencies=cycles,
                    warnings=[]
                )
            
            # Find all required plugins
            required_plugins = set()
            missing_dependencies = []
            
            for plugin in target_plugins:
                deps = self._get_transitive_dependencies(plugin)
                required_plugins.update(deps)
                
                # Check for missing dependencies
                for dep in deps:
                    if dep not in self.graph.nodes:
                        missing_dependencies.append(dep)
            
            if missing_dependencies:
                return ResolutionResult(
                    success=False,
                    resolved_order=[],
                    missing_dependencies=list(set(missing_dependencies)),
                    version_conflicts=[],
                    circular_dependencies=[],
                    warnings=[]
                )
            
            # Check version conflicts
            version_conflicts = self._check_version_conflicts(required_plugins)
            
            # Get installation order
            installation_order = self._get_installation_order(required_plugins)
            
            return ResolutionResult(
                success=len(version_conflicts) == 0,
                resolved_order=installation_order,
                missing_dependencies=[],
                version_conflicts=version_conflicts,
                circular_dependencies=[],
                warnings=[]
            )
            
        except Exception as e:
            logger.error(f"Dependency resolution failed: {str(e)}")
            return ResolutionResult(
                success=False,
                resolved_order=[],
                missing_dependencies=[],
                version_conflicts=[],
                circular_dependencies=[],
                warnings=[f"Resolution error: {str(e)}"]
            )
    
    def _get_transitive_dependencies(self, plugin_name: str, visited: Set[str] = None) -> Set[str]:
        """Get all transitive dependencies of a plugin"""
        if visited is None:
            visited = set()
        
        if plugin_name in visited or plugin_name not in self.graph.nodes:
            return set()
        
        visited.add(plugin_name)
        dependencies = {plugin_name}
        
        for dep in self.graph.get_dependencies(plugin_name):
            dependencies.update(self._get_transitive_dependencies(dep, visited.copy()))
        
        return dependencies
    
    def _check_version_conflicts(self, plugins: Set[str]) -> List[str]:
        """Check for version conflicts among plugins"""
        conflicts = []
        
        # Group plugins by name (different versions of same plugin)
        plugin_versions = {}
        for plugin_name in plugins:
            if plugin_name in self.graph.nodes:
                node = self.graph.nodes[plugin_name]
                base_name = plugin_name.split('@')[0] if '@' in plugin_name else plugin_name
                
                if base_name not in plugin_versions:
                    plugin_versions[base_name] = []
                plugin_versions[base_name].append((plugin_name, node.version))
        
        # Check for conflicts
        for base_name, versions in plugin_versions.items():
            if len(versions) > 1:
                version_list = [f"{name}@{version}" for name, version in versions]
                conflicts.append(f"Multiple versions of {base_name}: {', '.join(version_list)}")
        
        return conflicts
    
    def _get_installation_order(self, plugins: Set[str]) -> List[str]:
        """Get the correct installation order for plugins"""
        # Create subgraph with only required plugins
        subgraph_nodes = {name: self.graph.nodes[name] for name in plugins if name in self.graph.nodes}
        
        # Calculate in-degrees for subgraph
        in_degree = {node: 0 for node in subgraph_nodes}
        
        for node_name in subgraph_nodes:
            for dep in self.graph.get_dependencies(node_name):
                if dep in subgraph_nodes:
                    in_degree[dep] += 1
        
        # Topological sort
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort queue for deterministic results
            queue.sort()
            node = queue.pop(0)
            result.append(node)
            
            # Update in-degrees
            for dependent in self.graph.get_dependents(node):
                if dependent in subgraph_nodes and dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        return result
    
    def can_uninstall(self, plugin_name: str) -> Tuple[bool, List[str]]:
        """Check if a plugin can be safely uninstalled"""
        dependents = list(self.graph.get_dependents(plugin_name))
        
        # Filter out dependents that are not installed/active
        active_dependents = []
        for dependent in dependents:
            if dependent in self.graph.nodes:
                node = self.graph.nodes[dependent]
                if node.status in [PluginStatus.INSTALLED, PluginStatus.ACTIVE]:
                    active_dependents.append(dependent)
        
        return len(active_dependents) == 0, active_dependents
    
    def get_uninstall_order(self, plugin_names: List[str]) -> List[str]:
        """Get the correct order to uninstall plugins"""
        # Reverse topological order
        all_affected = set()
        for plugin_name in plugin_names:
            all_affected.update(self._get_transitive_dependents(plugin_name))
        
        installation_order = self._get_installation_order(all_affected)
        return list(reversed(installation_order))
    
    def _get_transitive_dependents(self, plugin_name: str, visited: Set[str] = None) -> Set[str]:
        """Get all transitive dependents of a plugin"""
        if visited is None:
            visited = set()
        
        if plugin_name in visited or plugin_name not in self.graph.nodes:
            return set()
        
        visited.add(plugin_name)
        dependents = {plugin_name}
        
        for dependent in self.graph.get_dependents(plugin_name):
            dependents.update(self._get_transitive_dependents(dependent, visited.copy()))
        
        return dependents
    
    def suggest_resolution(self, conflicts: List[str]) -> Dict[str, Any]:
        """Suggest resolution strategies for conflicts"""
        suggestions = {
            "version_conflicts": [],
            "missing_dependencies": [],
            "circular_dependencies": [],
            "recommended_actions": []
        }
        
        for conflict in conflicts:
            if "Multiple versions" in conflict:
                suggestions["version_conflicts"].append({
                    "conflict": conflict,
                    "suggestion": "Choose one version and update dependents to use compatible constraints"
                })
            elif "Missing" in conflict:
                suggestions["missing_dependencies"].append({
                    "conflict": conflict,
                    "suggestion": "Install the missing dependency or remove the dependent plugin"
                })
            elif "Circular" in conflict:
                suggestions["circular_dependencies"].append({
                    "conflict": conflict,
                    "suggestion": "Refactor plugins to remove circular dependency"
                })
        
        return suggestions
    
    def validate_manifest_dependencies(self, manifest: PluginManifest) -> List[str]:
        """Validate dependencies in a plugin manifest"""
        errors = []
        
        for dep_spec in manifest.dependencies:
            # Parse dependency specification
            if '@' in dep_spec:
                dep_name, version_constraint = dep_spec.split('@', 1)
            else:
                dep_name = dep_spec
                version_constraint = "*"
            
            # Check if dependency exists
            if dep_name not in self.graph.nodes:
                errors.append(f"Dependency '{dep_name}' not found")
                continue
            
            # Check version compatibility
            if version_constraint != "*":
                constraint = VersionConstraint(version_constraint)
                available_version = self.graph.nodes[dep_name].version
                
                if not constraint.satisfies(available_version):
                    errors.append(
                        f"Version conflict: {dep_name} requires {version_constraint}, "
                        f"but {available_version} is available"
                    )
        
        return errors