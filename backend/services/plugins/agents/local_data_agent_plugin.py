"""
Local Data Agent Plugin

기존 LocalDataAgent를 Plugin 형태로 래핑
"""
from typing import Dict, List, Any
from backend.services.plugins.agents.base_agent_plugin import (
    BaseAgentPlugin, 
    AgentCapability, 
    AgentExecutionContext
)
from backend.models.plugin import PluginManifest
from backend.agents.local_data import LocalDataAgent
from backend.agents.base import BaseAgent


class LocalDataAgentPlugin(BaseAgentPlugin):
    """Local Data Agent Plugin 구현"""
    
    def get_manifest(self) -> PluginManifest:
        """플러그인 매니페스트 반환"""
        return PluginManifest(
            name="local-data-agent",
            version="1.0.0",
            description="Local file system data access agent",
            author="AgenticRAG Team",
            category="orchestration",
            dependencies=["python-docx@>=0.8.11", "PyMuPDF@>=1.23.0"],
            permissions=["file_system_read", "document_processing"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "base_path": {
                        "type": "string",
                        "default": "./uploads",
                        "description": "Base directory path for file access"
                    },
                    "allowed_extensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": [".pdf", ".docx", ".txt", ".md", ".hwp", ".hwpx"],
                        "description": "Allowed file extensions"
                    },
                    "max_file_size": {
                        "type": "integer",
                        "default": 104857600,  # 100MB
                        "description": "Maximum file size in bytes"
                    },
                    "enable_ocr": {
                        "type": "boolean",
                        "default": true,
                        "description": "Enable OCR for image-based documents"
                    },
                    "ocr_language": {
                        "type": "string",
                        "default": "korean",
                        "description": "OCR language setting"
                    }
                },
                "required": ["base_path"]
            }
        )
    
    def get_agent_type(self) -> str:
        """Agent 타입 반환"""
        return "local_data"
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Agent 능력 반환"""
        return [
            AgentCapability(
                name="file_read",
                description="Read and process local files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        },
                        "extract_text": {
                            "type": "boolean",
                            "default": true,
                            "description": "Extract text content from file"
                        },
                        "extract_metadata": {
                            "type": "boolean",
                            "default": true,
                            "description": "Extract file metadata"
                        }
                    },
                    "required": ["file_path"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "metadata": {
                            "type": "object",
                            "properties": {
                                "file_name": {"type": "string"},
                                "file_size": {"type": "integer"},
                                "file_type": {"type": "string"},
                                "created_date": {"type": "string"},
                                "modified_date": {"type": "string"}
                            }
                        },
                        "processing_info": {
                            "type": "object",
                            "properties": {
                                "pages": {"type": "integer"},
                                "word_count": {"type": "integer"},
                                "ocr_used": {"type": "boolean"}
                            }
                        }
                    }
                },
                required_permissions=["file_system_read", "document_processing"]
            ),
            AgentCapability(
                name="directory_scan",
                description="Scan directory for files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "directory_path": {
                            "type": "string",
                            "description": "Directory path to scan"
                        },
                        "recursive": {
                            "type": "boolean",
                            "default": false,
                            "description": "Scan subdirectories recursively"
                        },
                        "filter_extensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by file extensions"
                        }
                    },
                    "required": ["directory_path"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "name": {"type": "string"},
                                    "size": {"type": "integer"},
                                    "extension": {"type": "string"},
                                    "modified_date": {"type": "string"}
                                }
                            }
                        },
                        "total_files": {"type": "integer"},
                        "total_size": {"type": "integer"}
                    }
                },
                required_permissions=["file_system_read"]
            ),
            AgentCapability(
                name="document_parse",
                description="Parse structured documents (PDF, DOCX, etc.)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to document file"
                        },
                        "extract_tables": {
                            "type": "boolean",
                            "default": true,
                            "description": "Extract table data"
                        },
                        "extract_images": {
                            "type": "boolean",
                            "default": false,
                            "description": "Extract embedded images"
                        }
                    },
                    "required": ["file_path"]
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "text_content": {"type": "string"},
                        "tables": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "headers": {"type": "array"},
                                    "rows": {"type": "array"}
                                }
                            }
                        },
                        "images": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "image_id": {"type": "string"},
                                    "format": {"type": "string"},
                                    "size": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                required_permissions=["file_system_read", "document_processing"]
            )
        ]
    
    def execute_agent(
        self, 
        input_data: Dict[str, Any], 
        context: AgentExecutionContext
    ) -> Dict[str, Any]:
        """Agent 실행"""
        try:
            agent = self.get_agent_instance()
            
            # 실행 컨텍스트 설정
            execution_context = {
                "user_id": context.user_id,
                "session_id": context.session_id,
                "workflow_id": context.workflow_id,
                **context.execution_metadata
            }
            
            # Agent 실행
            result = agent.execute(input_data, execution_context)
            
            return {
                "success": True,
                "result": result,
                "agent_type": self.get_agent_type(),
                "execution_context": execution_context
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_type": self.get_agent_type(),
                "input_data": input_data
            }
    
    def _create_agent_instance(self) -> BaseAgent:
        """LocalDataAgent 인스턴스 생성"""
        return LocalDataAgent(
            base_path=self.config.get("base_path", "./uploads"),
            allowed_extensions=self.config.get("allowed_extensions", [".pdf", ".docx", ".txt", ".md", ".hwp", ".hwpx"]),
            max_file_size=self.config.get("max_file_size", 104857600),
            enable_ocr=self.config.get("enable_ocr", True),
            ocr_language=self.config.get("ocr_language", "korean")
        )
    
    def _get_required_config_fields(self) -> List[str]:
        """필수 설정 필드"""
        return ["base_path"]
    
    def _validate_agent_specific_config(self, config: Dict[str, Any]) -> List[str]:
        """Local Data Agent 특화 설정 검증"""
        errors = []
        
        # 기본 경로 검증
        if "base_path" in config:
            base_path = config["base_path"]
            if not isinstance(base_path, str) or not base_path.strip():
                errors.append("base_path must be a non-empty string")
        
        # 허용된 확장자 검증
        if "allowed_extensions" in config:
            extensions = config["allowed_extensions"]
            if not isinstance(extensions, list):
                errors.append("allowed_extensions must be a list")
            else:
                for ext in extensions:
                    if not isinstance(ext, str) or not ext.startswith('.'):
                        errors.append(f"Invalid extension format: {ext}")
        
        # 최대 파일 크기 검증
        if "max_file_size" in config:
            max_size = config["max_file_size"]
            if not isinstance(max_size, int) or max_size <= 0:
                errors.append("max_file_size must be a positive integer")
        
        # OCR 언어 검증
        if "ocr_language" in config:
            ocr_lang = config["ocr_language"]
            valid_languages = ["korean", "english", "chinese", "japanese"]
            if ocr_lang not in valid_languages:
                errors.append(f"ocr_language must be one of: {', '.join(valid_languages)}")
        
        return errors
    
    def get_health_status(self) -> Dict[str, Any]:
        """Local Data Agent 상태 확인"""
        base_status = super().get_health_status()
        
        if self._initialized and self._agent_instance:
            try:
                import os
                base_path = self.config.get("base_path", "./uploads")
                
                agent_health = {
                    "base_path_exists": os.path.exists(base_path),
                    "base_path_readable": os.access(base_path, os.R_OK) if os.path.exists(base_path) else False,
                    "ocr_available": self.config.get("enable_ocr", True),  # 실제로는 OCR 라이브러리 확인
                    "supported_formats": self.config.get("allowed_extensions", [])
                }
                base_status.update(agent_health)
                
                if not agent_health["base_path_exists"]:
                    base_status["status"] = "unhealthy"
                    base_status["error"] = f"Base path does not exist: {base_path}"
                    
            except Exception as e:
                base_status["error"] = str(e)
                base_status["status"] = "unhealthy"
        
        return base_status