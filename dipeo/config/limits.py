"""System limits and constraints configuration for DiPeO."""

# Timeout configurations (in seconds)
DEFAULT_TIMEOUT = 30.0
MAX_EXECUTION_TIMEOUT = 600.0  # 10 minutes
DEFAULT_HTTP_TIMEOUT = 10.0

# Retry configurations
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF_FACTOR = 2.0

# File handling
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS: set[str] = {".json", ".yaml", ".yml", ".txt", ".md", ".py", ".js", ".ts"}

# Pagination
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000

# Execution limits
MAX_ITERATIONS = 100
MAX_NODE_EXECUTIONS = 1000

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
