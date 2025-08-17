#!/usr/bin/env python3
"""Script to update all imports from core.ports to use compatibility imports for Wave 5 migration."""

import os
import re
from pathlib import Path


# Files to update and their import changes
IMPORT_UPDATES = [
    # GraphQL resolvers
    ("dipeo/application/graphql/resolvers/person.py", 
     "from dipeo.core.ports import APIKeyPort",
     "from dipeo.application.migration.compat_imports import APIKeyPort"),
    
    # GraphQL mutations
    ("dipeo/application/graphql/schema/mutations/execution.py",
     "from dipeo.core.ports import StateStorePort, MessageRouterPort",
     "from dipeo.application.migration.compat_imports import StateStorePort, MessageRouterPort"),
    
    ("dipeo/application/graphql/schema/mutations/api_key.py",
     "from dipeo.core.ports import APIKeyPort",
     "from dipeo.application.migration.compat_imports import APIKeyPort"),
    
    # GraphQL subscriptions
    ("dipeo/application/graphql/schema/subscriptions.py",
     "from dipeo.core.ports import MessageRouterPort, StateStorePort",
     "from dipeo.application.migration.compat_imports import MessageRouterPort, StateStorePort"),
    
    # Application services
    ("dipeo/application/services/apikey_service.py",
     "from dipeo.core.ports import APIKeyPort",
     "from dipeo.application.migration.compat_imports import APIKeyPort"),
    
    # Execution observers
    ("dipeo/application/execution/observers/unified_event_observer.py",
     "from dipeo.core.ports import ExecutionObserver, MessageRouterPort",
     "from dipeo.application.migration.compat_imports import ExecutionObserver, MessageRouterPort"),
    
    ("dipeo/application/execution/observers/scoped_observer.py",
     "from dipeo.core.ports import ExecutionObserver",
     "from dipeo.application.migration.compat_imports import ExecutionObserver"),
    
    # Infrastructure adapters
    ("dipeo/infrastructure/adapters/llm/llm_adapter.py",
     "from dipeo.core.ports import LLMServicePort",
     "from dipeo.application.migration.compat_imports import LLMServicePort"),
    
    ("dipeo/infrastructure/adapters/state/state_adapter.py",
     "from dipeo.core.ports import StateStorePort",
     "from dipeo.application.migration.compat_imports import StateStorePort"),
    
    ("dipeo/infrastructure/adapters/api/api_adapter.py",
     "from dipeo.core.ports import IntegratedApiServicePort",
     "from dipeo.application.migration.compat_imports import IntegratedApiServicePort"),
    
    ("dipeo/infrastructure/adapters/messaging/messaging_adapter.py",
     "from dipeo.core.ports import MessageRouterPort",
     "from dipeo.application.migration.compat_imports import MessageRouterPort"),
    
    ("dipeo/infrastructure/adapters/messaging/message_router.py",
     "from dipeo.core.ports import MessageRouterPort",
     "from dipeo.application.migration.compat_imports import MessageRouterPort"),
    
    ("dipeo/infrastructure/adapters/storage/file_service_adapter.py",
     "from dipeo.core.ports import FileServicePort",
     "from dipeo.application.migration.compat_imports import FileServicePort"),
    
    ("dipeo/infrastructure/adapters/events/observer_to_event_adapter.py",
     "from dipeo.core.ports import ExecutionObserver",
     "from dipeo.application.migration.compat_imports import ExecutionObserver"),
    
    ("dipeo/infrastructure/adapters/events/legacy/observer_consumer_adapter.py",
     "from dipeo.core.ports import ExecutionObserver",
     "from dipeo.application.migration.compat_imports import ExecutionObserver"),
    
    # Infrastructure services
    ("dipeo/infrastructure/services/llm/service.py",
     "from dipeo.core.ports import LLMServicePort",
     "from dipeo.application.migration.compat_imports import LLMServicePort"),
    
    ("dipeo/infrastructure/services/integrated_api/service.py",
     "from dipeo.core.ports import IntegratedApiServicePort, ApiProviderPort, APIKeyPort",
     "from dipeo.application.migration.compat_imports import IntegratedApiServicePort, ApiProviderPort, APIKeyPort"),
    
    ("dipeo/infrastructure/services/integrated_api/registry.py",
     "from dipeo.core.ports import ApiProviderPort",
     "from dipeo.application.migration.compat_imports import ApiProviderPort"),
    
    ("dipeo/infrastructure/services/integrated_api/generic_provider.py",
     "from dipeo.core.ports import ApiProviderPort, APIKeyPort",
     "from dipeo.application.migration.compat_imports import ApiProviderPort, APIKeyPort"),
    
    ("dipeo/infrastructure/services/integrated_api/auth_strategies.py",
     "from dipeo.core.ports import APIKeyPort",
     "from dipeo.application.migration.compat_imports import APIKeyPort"),
    
    ("dipeo/infrastructure/services/diagram/converter_service.py",
     "from dipeo.core.ports import DiagramStorageSerializer, FormatStrategy",
     "from dipeo.application.migration.compat_imports import DiagramStorageSerializer, FormatStrategy"),
    
    # Infrastructure state
    ("dipeo/infrastructure/state/async_state_manager.py",
     "from dipeo.core.ports import StateStorePort",
     "from dipeo.application.migration.compat_imports import StateStorePort"),
    
    ("dipeo/infrastructure/state/event_based_state_store.py",
     "from dipeo.core.ports import StateStorePort",
     "from dipeo.application.migration.compat_imports import StateStorePort"),
    
    ("dipeo/infrastructure/state/async_queue_state_store.py",
     "from dipeo.core.ports import StateStorePort",
     "from dipeo.application.migration.compat_imports import StateStorePort"),
    
    # Infrastructure monitoring
    ("dipeo/infrastructure/monitoring/streaming_monitor.py",
     "from dipeo.core.ports import MessageRouterPort",
     "from dipeo.application.migration.compat_imports import MessageRouterPort"),
    
    # Domain (these should use domain ports directly in the future)
    ("dipeo/domain/conversation/person.py",
     "from dipeo.core.ports import LLMServicePort",
     "from dipeo.application.migration.compat_imports import LLMServicePort"),
    
    ("dipeo/domain/diagram/strategies/base_strategy.py",
     "from dipeo.core.ports import FormatStrategy",
     "from dipeo.application.migration.compat_imports import FormatStrategy"),
    
    # Infrastructure HTTP
    ("dipeo/infrastructure/adapters/http/api_service.py",
     "from dipeo.core.ports import FileServicePort",
     "from dipeo.application.migration.compat_imports import FileServicePort"),
]


def update_file(filepath: str, old_import: str, new_import: str) -> bool:
    """Update imports in a single file.
    
    Returns True if file was updated, False otherwise.
    """
    full_path = Path("/home/soryhyun/DiPeO") / filepath
    
    if not full_path.exists():
        print(f"  ⚠️  File not found: {filepath}")
        return False
    
    try:
        content = full_path.read_text()
        
        if old_import not in content:
            print(f"  ℹ️  Import not found in {filepath}")
            return False
        
        updated_content = content.replace(old_import, new_import)
        full_path.write_text(updated_content)
        print(f"  ✅ Updated: {filepath}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating {filepath}: {e}")
        return False


def main():
    """Run the import updates."""
    print("Wave 5 Migration: Updating imports from core.ports to compatibility imports")
    print("=" * 70)
    
    total_files = len(IMPORT_UPDATES)
    updated_count = 0
    
    for filepath, old_import, new_import in IMPORT_UPDATES:
        if update_file(filepath, old_import, new_import):
            updated_count += 1
    
    print("=" * 70)
    print(f"Summary: {updated_count}/{total_files} files updated")
    
    if updated_count < total_files:
        print("\n⚠️  Some files were not updated. Please review the warnings above.")
        return 1
    
    print("\n✅ All imports updated successfully!")
    print("\nNext steps:")
    print("1. Run tests with PORT_V2 flags enabled")
    print("2. Add metrics/logging for port usage")
    print("3. Update migration status document")
    
    return 0


if __name__ == "__main__":
    exit(main())