# DiPeO Configuration Management

This module provides centralized configuration management for the DiPeO infrastructure layer.

## Features

- ✅ Environment-based configuration (development, testing, production)
- ✅ Configuration validation on startup
- ✅ Environment variable support
- ✅ Type-safe configuration access
- ✅ Runtime configuration reloading
- ✅ Automatic directory creation

## Usage

### Basic Usage

```python
from dipeo_infra.config import get_settings

settings = get_settings()

# Access configuration values
print(settings.server_port)  # 8000
print(settings.files_dir)    # Path object to files directory
print(settings.default_llm_model)  # "gpt-4.1-nano"
```

### Environment Variables

All settings can be overridden using environment variables:

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `DIPEO_ENV` | Environment (development/testing/production) | `development` |
| `DIPEO_BASE_DIR` | Base directory for all file operations | Auto-detected |
| `DIPEO_HOST` | Server host | `0.0.0.0` |
| `DIPEO_PORT` | Server port | `8000` |
| `DIPEO_WORKERS` | Number of workers | `4` |
| `DIPEO_LOG_LEVEL` | Logging level | `INFO` |
| `DIPEO_DEFAULT_LLM_MODEL` | Default LLM model | `gpt-4.1-nano` |
| `DIPEO_LLM_TIMEOUT` | LLM request timeout (seconds) | `300` |
| `DIPEO_LLM_MAX_RETRIES` | Max LLM retry attempts | `3` |
| `DIPEO_API_MAX_RETRIES` | Max API retry attempts | `3` |
| `DIPEO_API_RETRY_DELAY` | API retry delay (seconds) | `1.0` |
| `DIPEO_API_TIMEOUT` | API request timeout (seconds) | `30` |
| `DIPEO_EXECUTION_TIMEOUT` | Max execution time (seconds) | `3600` |
| `DIPEO_NODE_TIMEOUT` | Max node execution time (seconds) | `300` |
| `DIPEO_PARALLEL_EXECUTION` | Enable parallel execution | `true` |
| `DIPEO_CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` |
| `DIPEO_ALLOWED_FILE_EXTENSIONS` | Allowed file extensions (comma-separated) | `.txt,.json,.yaml,...` |
| `DIPEO_MAX_UPLOAD_SIZE` | Max file upload size (bytes) | `10485760` |
| `DIPEO_ENABLE_MONITORING` | Enable monitoring/metrics | `false` |
| `DIPEO_DEBUG` | Enable debug mode | `false` |

### Environment-Specific Configuration

The configuration automatically adjusts based on the environment:

```python
# Production environment
DIPEO_ENV=production python app.py
# - Log level set to WARNING
# - Debug mode disabled
# - Increased retry attempts

# Testing environment  
DIPEO_ENV=testing python app.py
# - Log level set to DEBUG
# - Debug mode enabled
# - Reduced timeouts for faster tests
```

### Configuration Validation

Settings are validated on initialization:
- Port numbers must be valid (1-65535)
- Worker count must be positive
- Timeouts must be positive
- Required directories are created automatically

### Runtime Reloading

```python
from dipeo_infra.config import reload_settings

# Reload configuration from environment
reload_settings()
```

### Dependency Injection

Use with dependency injection containers:

```python
from dependency_injector import providers
from dipeo_infra.config import get_settings

class Container(containers.DeclarativeContainer):
    config = providers.Singleton(get_settings)
    
    file_service = providers.Singleton(
        FileService,
        base_dir=config.provided.files_dir,
        max_size=config.provided.max_upload_size,
    )
```

## Directory Structure

The configuration automatically creates the following directory structure:

```
{base_dir}/
├── files/
│   ├── uploads/         # User uploads
│   ├── results/         # Execution results
│   ├── diagrams/        # Diagram storage
│   ├── conversation_logs/  # LLM conversations
│   ├── prompts/         # Prompt templates
│   └── apikeys.json     # API key storage
└── .data/
    ├── dipeo_state.db   # State database
    └── dipeo_events.db  # Events database
```

## Migration Guide

See `migration_example.py` for examples of migrating from hardcoded values to configuration-based approach.