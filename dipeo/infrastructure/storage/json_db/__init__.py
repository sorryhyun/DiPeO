"""JSON-based database storage operations.

Provides file-based storage with database-like operations (read/write/append/update)
for JSON data. This is a lightweight alternative to full database systems for
simple key-value storage needs.
"""

from .service import DBOperationsDomainService

__all__ = ["DBOperationsDomainService"]
