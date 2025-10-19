"""
Prompt Version Manager for A/B testing and version control.

Manages prompt versions with:
- YAML-based prompt storage
- Version control and rollback
- A/B testing support
- Performance metrics tracking
"""

import logging
import yaml
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import random

logger = logging.getLogger(__name__)


@dataclass
class PromptVersion:
    """Prompt version data"""
    version: str
    name: str
    description: str
    system_prompt: str
    user_template: str
    response_template: Optional[str]
    parameters: Dict[str, Any]
    metrics: Dict[str, Any]
    ab_test: Dict[str, Any]
    created_at: str
    author: str


class PromptVersionManager:
    """
    Manages prompt versions with A/B testing support.
    
    Features:
    - Load prompts from YAML files
    - Version control
    - A/B testing
    - Performance tracking
    - Easy rollback
    """
    
    def __init__(
        self,
        prompts_dir: str = "backend/prompts",
        enable_ab_testing: bool = True
    ):
        """
        Initialize PromptVersionManager.
        
        Args:
            prompts_dir: Directory containing prompt YAML files
            enable_ab_testing: Enable A/B testing
        """
        self.prompts_dir = Path(prompts_dir)
        self.enable_ab_testing = enable_ab_testing
        
        # Cache for loaded prompts
        self.prompt_cache: Dict[str, PromptVersion] = {}
        
        # A/B test state
        self.ab_tests: Dict[str, Dict[str, Any]] = {}
        
        # Ensure prompts directory exists
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(
            f"PromptVersionManager initialized: "
            f"prompts_dir={prompts_dir}, "
            f"ab_testing={enable_ab_testing}"
        )
    
    def load_prompt(
        self,
        name: str,
        version: str = "latest"
    ) -> PromptVersion:
        """
        Load prompt from YAML file.
        
        Args:
            name: Prompt name (e.g., "web_search")
            version: Version string or "latest"
            
        Returns:
            PromptVersion object
        """
        cache_key = f"{name}:{version}"
        
        # Check cache
        if cache_key in self.prompt_cache:
            return self.prompt_cache[cache_key]
        
        # Find prompt file
        if version == "latest":
            prompt_file = self._find_latest_version(name)
        else:
            prompt_file = self.prompts_dir / f"{name}_v{version}.yaml"
        
        if not prompt_file.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_file}"
            )
        
        # Load YAML
        with open(prompt_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Create PromptVersion
        prompt = PromptVersion(
            version=data.get('version', version),
            name=data.get('name', name),
            description=data.get('description', ''),
            system_prompt=data.get('system_prompt', ''),
            user_template=data.get('user_template', ''),
            response_template=data.get('response_template'),
            parameters=data.get('parameters', {}),
            metrics=data.get('metrics', {}),
            ab_test=data.get('ab_test', {}),
            created_at=data.get('created_at', ''),
            author=data.get('author', '')
        )
        
        # Cache
        self.prompt_cache[cache_key] = prompt
        
        logger.info(
            f"Loaded prompt: {name} v{prompt.version}"
        )
        
        return prompt
    
    def _find_latest_version(self, name: str) -> Path:
        """Find latest version of prompt"""
        pattern = f"{name}_v*.yaml"
        files = list(self.prompts_dir.glob(pattern))
        
        if not files:
            raise FileNotFoundError(
                f"No prompt files found for: {name}"
            )
        
        # Sort by version number
        def extract_version(path: Path) -> float:
            try:
                version_str = path.stem.split('_v')[1]
                return float(version_str)
            except:
                return 0.0
        
        latest = max(files, key=extract_version)
        return latest
    
    def get_prompt_for_request(
        self,
        name: str,
        session_id: Optional[str] = None
    ) -> PromptVersion:
        """
        Get prompt for request with A/B testing support.
        
        Args:
            name: Prompt name
            session_id: Optional session ID for consistent A/B assignment
            
        Returns:
            PromptVersion (may be control or test version)
        """
        # Load latest version
        latest = self.load_prompt(name, "latest")
        
        # Check if A/B testing is enabled
        if not self.enable_ab_testing or not latest.ab_test.get('enabled'):
            return latest
        
        # Get A/B test configuration
        control_version = latest.ab_test.get('control_version')
        traffic_split = latest.ab_test.get('traffic_split', 0.5)
        
        if not control_version:
            return latest
        
        # Determine which version to use
        # Use session_id for consistent assignment
        if session_id:
            # Hash session_id to get consistent random value
            hash_value = hash(session_id) % 100 / 100.0
            use_test = hash_value < traffic_split
        else:
            # Random assignment
            use_test = random.random() < traffic_split
        
        if use_test:
            logger.debug(f"A/B test: Using test version {latest.version}")
            return latest
        else:
            logger.debug(f"A/B test: Using control version {control_version}")
            return self.load_prompt(name, control_version)
    
    def save_prompt(
        self,
        name: str,
        version: str,
        system_prompt: str,
        user_template: str,
        response_template: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        description: str = "",
        author: str = "System"
    ) -> Path:
        """
        Save new prompt version.
        
        Args:
            name: Prompt name
            version: Version string
            system_prompt: System prompt text
            user_template: User prompt template
            response_template: Optional response template
            parameters: Optional parameters
            description: Version description
            author: Author name
            
        Returns:
            Path to saved file
        """
        prompt_file = self.prompts_dir / f"{name}_v{version}.yaml"
        
        data = {
            'version': version,
            'name': name,
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'author': author,
            'system_prompt': system_prompt,
            'user_template': user_template,
            'response_template': response_template,
            'parameters': parameters or {
                'temperature': 0.5,
                'max_tokens': 300
            },
            'metrics': {
                'average_quality_score': None,
                'average_token_usage': None,
                'user_satisfaction': None,
                'test_count': 0
            },
            'ab_test': {
                'enabled': False,
                'traffic_split': 0.5,
                'control_version': None,
                'test_duration_days': 7
            }
        }
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"Saved prompt: {name} v{version} to {prompt_file}")
        
        # Clear cache
        self.prompt_cache.clear()
        
        return prompt_file
    
    def update_metrics(
        self,
        name: str,
        version: str,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Update prompt metrics.
        
        Args:
            name: Prompt name
            version: Version string
            metrics: Metrics to update
        """
        prompt_file = self.prompts_dir / f"{name}_v{version}.yaml"
        
        if not prompt_file.exists():
            logger.warning(f"Prompt file not found: {prompt_file}")
            return
        
        # Load current data
        with open(prompt_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Update metrics
        if 'metrics' not in data:
            data['metrics'] = {}
        
        data['metrics'].update(metrics)
        
        # Save
        with open(prompt_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"Updated metrics for {name} v{version}")
        
        # Clear cache
        cache_key = f"{name}:{version}"
        if cache_key in self.prompt_cache:
            del self.prompt_cache[cache_key]
    
    def enable_ab_test(
        self,
        name: str,
        test_version: str,
        control_version: str,
        traffic_split: float = 0.5,
        duration_days: int = 7
    ) -> None:
        """
        Enable A/B test for prompt.
        
        Args:
            name: Prompt name
            test_version: Test version
            control_version: Control version
            traffic_split: Percentage of traffic for test (0.0-1.0)
            duration_days: Test duration in days
        """
        prompt_file = self.prompts_dir / f"{name}_v{test_version}.yaml"
        
        if not prompt_file.exists():
            raise FileNotFoundError(f"Test version not found: {prompt_file}")
        
        # Load test version
        with open(prompt_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Update A/B test config
        data['ab_test'] = {
            'enabled': True,
            'traffic_split': traffic_split,
            'control_version': control_version,
            'test_duration_days': duration_days,
            'start_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Save
        with open(prompt_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(
            f"Enabled A/B test: {name} "
            f"(test={test_version}, control={control_version}, "
            f"split={traffic_split})"
        )
        
        # Clear cache
        self.prompt_cache.clear()
    
    def disable_ab_test(self, name: str, version: str) -> None:
        """Disable A/B test"""
        prompt_file = self.prompts_dir / f"{name}_v{version}.yaml"
        
        if not prompt_file.exists():
            return
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'ab_test' in data:
            data['ab_test']['enabled'] = False
        
        with open(prompt_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        
        logger.info(f"Disabled A/B test for {name} v{version}")
        
        # Clear cache
        self.prompt_cache.clear()
    
    def list_versions(self, name: str) -> List[Dict[str, Any]]:
        """
        List all versions of a prompt.
        
        Args:
            name: Prompt name
            
        Returns:
            List of version info
        """
        pattern = f"{name}_v*.yaml"
        files = list(self.prompts_dir.glob(pattern))
        
        versions = []
        for file in sorted(files):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                versions.append({
                    'version': data.get('version'),
                    'description': data.get('description'),
                    'created_at': data.get('created_at'),
                    'author': data.get('author'),
                    'metrics': data.get('metrics', {}),
                    'ab_test_enabled': data.get('ab_test', {}).get('enabled', False)
                })
            except Exception as e:
                logger.warning(f"Failed to load {file}: {e}")
        
        return versions


# Singleton instance
_prompt_version_manager: Optional[PromptVersionManager] = None


def get_prompt_version_manager(
    prompts_dir: str = "backend/prompts"
) -> PromptVersionManager:
    """
    Get or create global PromptVersionManager instance.
    
    Args:
        prompts_dir: Prompts directory
        
    Returns:
        PromptVersionManager instance
    """
    global _prompt_version_manager
    
    if _prompt_version_manager is None:
        _prompt_version_manager = PromptVersionManager(
            prompts_dir=prompts_dir
        )
    
    return _prompt_version_manager
