# DiPeO Infrastructure

Simplified domain services for DiPeO that can be shared between server and CLI applications.

## Overview

This package provides lightweight implementations of domain services that are needed for diagram execution. These services implement the protocols defined in `dipeo-core` and can work with minimal dependencies.

## Services Included

- **SimpleConversationService**: Basic conversation management for person_job nodes
- **SimpleFileService**: File operations for DB nodes
- **SimpleMemoryService**: In-memory conversation storage

## Installation

```bash
pip install -e .
```

## Usage

```python
from dipeo_infra import ConversationService, FileService, MemoryService

# Create services
memory_service = emoryService()
file_service = FileService()
conversation_service = ConversationService(
    llm_service=your_llm_service,
    memory_service=memory_service
)

# Use in your application context
class MyAppContext:
    def __init__(self):
        self.conversation_service = conversation_service
        self.file_service = file_service
        # ... other services
```

## Design Philosophy

These services are designed to be:
- **Lightweight**: Minimal dependencies and simple implementations
- **Protocol-based**: Implement standard protocols from dipeo-core
- **Testable**: Easy to mock and test
- **Reusable**: Can be used by both server and CLI