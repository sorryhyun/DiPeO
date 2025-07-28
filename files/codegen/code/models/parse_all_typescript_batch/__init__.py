"""Parse all TypeScript batch module."""

from .gather_typescript_files import main as gather_typescript_files
from .batch_parse_typescript import main as batch_parse_typescript
from .save_ast_cache import main as save_ast_cache

__all__ = ['gather_typescript_files', 'batch_parse_typescript', 'save_ast_cache']