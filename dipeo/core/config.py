"""Configuration management for DiPeO containers."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dipeo.core.constants import BASE_DIR


@dataclass
class StorageConfig:
    type: str = "local"
    local_path: str = str(BASE_DIR / "files")
    s3_bucket: Optional[str] = None
    s3_region: Optional[str] = None


@dataclass
class LLMConfig:
    provider: str = "openai"
    api_key: Optional[str] = None
    default_model: str = "gpt-4.1-nano"
    timeout: int = 30


@dataclass
class Config:
    """Main configuration for DiPeO containers.
    
    Replaces complex dependency-injector configuration with simple dataclass.
    """
    
    base_dir: str = str(BASE_DIR)
    storage: StorageConfig = None
    llm: LLMConfig = None
    debug: bool = False
    enable_profiling: bool = False
    
    def __post_init__(self):
        if self.storage is None:
            self.storage = StorageConfig()
        if self.llm is None:
            self.llm = LLMConfig()
    
    @classmethod
    def from_env(cls) -> "Config":
        config = cls()
        
        config.base_dir = os.environ.get("DIPEO_BASE_DIR", str(BASE_DIR))
        config.storage.type = os.environ.get("DIPEO_STORAGE_TYPE", "local")
        config.storage.local_path = os.environ.get(
            "DIPEO_STORAGE_PATH", 
            str(Path(config.base_dir) / "files")
        )
        config.storage.s3_bucket = os.environ.get("DIPEO_S3_BUCKET")
        config.storage.s3_region = os.environ.get("DIPEO_S3_REGION", "us-east-1")
        config.llm.provider = os.environ.get("DIPEO_LLM_PROVIDER", "openai")
        config.llm.api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        config.llm.default_model = os.environ.get("DIPEO_DEFAULT_MODEL", "gpt-4.1-nano")
        config.llm.timeout = int(os.environ.get("DIPEO_LLM_TIMEOUT", "30"))
        config.debug = os.environ.get("DIPEO_DEBUG", "false").lower() == "true"
        config.enable_profiling = os.environ.get("DIPEO_ENABLE_PROFILING", "false").lower() == "true"
        
        return config
    
    def to_dict(self) -> dict:
        return {
            "base_dir": self.base_dir,
            "storage": {
                "type": self.storage.type,
                "local_path": self.storage.local_path,
                "s3_bucket": self.storage.s3_bucket,
                "s3_region": self.storage.s3_region,
            },
            "llm": {
                "provider": self.llm.provider,
                "api_key": "***" if self.llm.api_key else None,
                "default_model": self.llm.default_model,
                "timeout": self.llm.timeout,
            },
            "debug": self.debug,
            "enable_profiling": self.enable_profiling,
        }