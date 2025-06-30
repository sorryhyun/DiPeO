"""Example of migrating from hardcoded values to configuration-based approach."""

# BEFORE: Hardcoded values
class OldFileService:
    def __init__(self):
        self.base_dir = "/path/to/files"  # Hardcoded
        self.max_file_size = 10 * 1024 * 1024  # Hardcoded 10MB
        self.allowed_extensions = [".txt", ".json"]  # Hardcoded

# AFTER: Using configuration
from dipeo_infra.config import get_settings

class NewFileService:
    def __init__(self):
        settings = get_settings()
        self.base_dir = settings.files_dir
        self.max_file_size = settings.max_upload_size
        self.allowed_extensions = settings.allowed_file_extensions


# BEFORE: Hardcoded LLM settings
class OldLLMService:
    def __init__(self):
        self.default_model = "gpt-4"  # Hardcoded
        self.timeout = 300  # Hardcoded
        self.max_retries = 3  # Hardcoded

# AFTER: Using configuration
class NewLLMService:
    def __init__(self):
        settings = get_settings()
        self.default_model = settings.default_llm_model
        self.timeout = settings.llm_timeout
        self.max_retries = settings.llm_max_retries


# BEFORE: Server configuration scattered
def start_old_server():
    host = "0.0.0.0"  # Hardcoded
    port = 8000  # Hardcoded
    workers = 4  # Hardcoded
    # ... start server

# AFTER: Centralized configuration
def start_new_server():
    settings = get_settings()
    host = settings.server_host
    port = settings.server_port
    workers = settings.workers
    # ... start server


# Example of environment-specific behavior
def get_log_level():
    settings = get_settings()
    
    # Configuration automatically adjusts based on environment
    if settings.environment == "production":
        return "WARNING"  # Less verbose in production
    else:
        return settings.log_level  # Use configured value


# Example of using feature flags
async def execute_diagram(diagram_id: str):
    settings = get_settings()
    
    if settings.enable_monitoring:
        # Enable monitoring/metrics collection
        start_monitoring()
    
    if settings.parallel_execution:
        # Use parallel execution
        result = await execute_parallel(diagram_id)
    else:
        # Use sequential execution
        result = await execute_sequential(diagram_id)
    
    return result


# Example of reloading configuration at runtime
def handle_config_reload_signal():
    """Handle SIGHUP or similar signal to reload config."""
    from dipeo_infra.config import reload_settings
    
    reload_settings()
    print("Configuration reloaded")