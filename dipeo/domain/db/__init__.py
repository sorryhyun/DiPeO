"""Backward compatibility re-export for db module.

This module maintains backward compatibility for imports during the migration
of db to integrations bounded context.

DEPRECATED: Use dipeo.domain.integrations instead.
"""

# Re-export for direct imports
from dipeo.domain.integrations.db_services import DBOperationsDomainService

__all__ = ["DBOperationsDomainService"]