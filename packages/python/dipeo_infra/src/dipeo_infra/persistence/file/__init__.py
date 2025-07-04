"""File persistence adapters."""

from .modular_file_service import ModularFileService as ConsolidatedFileService

# Create factory function for backward compatibility
def create_consolidated_file_service(base_dir=None, **kwargs):
    """Factory function to create file service."""
    return ConsolidatedFileService(base_dir=base_dir)

__all__ = [
    "ConsolidatedFileService",
    "create_consolidated_file_service"
]
