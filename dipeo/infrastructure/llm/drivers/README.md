# LLM Infrastructure Drivers

## Overview

The LLM infrastructure drivers layer provides a clean abstraction for interacting with various Large Language Model providers (OpenAI, Anthropic, Google, Ollama) while maintaining separation of concerns between domain logic and infrastructure details.

## Architecture

```
dipeo/infrastructure/llm/
├── drivers/                 # LLM orchestration and utilities
│   ├── service.py          # Main LLM service orchestrator
│   ├── system_prompt_handler.py # System prompt resolution and loading
│   ├── message_formatter.py     # Message formatting for providers
│   ├── base.py             # Base adapter class
│   └── factory.py          # Adapter factory for provider instantiation
└── adapters/               # Provider-specific implementations
    ├── openai.py
    ├── claude.py
    ├── gemini.py
    └── ollama.py
```

## Core Components

### 1. LLMInfraService (`service.py`)

The main orchestrator that implements `LLMServicePort` and provides:
- Adapter pooling and caching for performance
- Provider inference from model names
- Retry logic with exponential backoff
- Two completion methods:
  - `complete()` - Standard completion with raw messages
  - `complete_with_person()` - Person-aware completion with proper formatting

#### Key Features:
- **Adapter Pooling**: Reuses adapters for 1 hour to reduce connection overhead
- **Single-flight Cache**: Prevents duplicate adapter creation during concurrent requests
- **Provider Mapping**: Automatically determines provider from model name

### 2. SystemPromptHandler (`system_prompt_handler.py`)

Handles system prompt resolution with the following priorities:
1. Load from `prompt_file` if specified and exists
2. Fall back to `system_prompt` if file loading fails
3. Return `None` if no prompt is configured

#### Provider-Specific Roles:
- **OpenAI**: Uses `"developer"` role for stronger instruction adherence
- **Others**: Uses standard `"system"` role

### 3. MessageFormatter (`message_formatter.py`)

Converts domain `Message` objects to provider-specific formats:
- Determines correct role mapping (`user`/`assistant`)
- Prepends system prompts with appropriate role
- Maintains conversation context

### 4. BaseLLMAdapter (`base.py`)

Abstract base class for all LLM provider adapters:
- Lazy client initialization
- Common parameter extraction
- Token usage tracking
- Tool support detection

## Usage

### Standard Completion

```python
# Direct completion with formatted messages
result = await llm_service.complete(
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"}
    ],
    model="gpt-4.1-nano",
    api_key_id="openai_key",
    service=LLMService.OPENAI
)
```

### Person-Aware Completion

```python
# Completion with automatic formatting and system prompt handling
result = await llm_service.complete_with_person(
    person_messages=person.get_messages(),  # Domain Message objects
    person_id=person.id,
    llm_config=person.llm_config,  # Contains prompt settings
    temperature=0.7,
    max_tokens=4096
)
```

## Provider Adapters

Located in `dipeo/infrastructure/llm/adapters/`:

| Provider | Adapter | Features |
|----------|---------|----------|
| OpenAI | `ChatGPTAdapter` | Tools, structured outputs, "developer" role |
| Anthropic | `ClaudeAdapter` | Vision, large context window |
| Google | `GeminiAdapter` | Multi-modal, function calling |
| Ollama | `OllamaAdapter` | Local models, no API key required |

## Design Principles

### 1. Separation of Concerns
- **Domain Layer** (Person class): Only manages conversation state and memory
- **Infrastructure Layer**: Handles all LLM-specific logic:
  - System prompt loading
  - Message formatting
  - Provider-specific adaptations

### 2. Clean Architecture
The refactored design follows hexagonal architecture:
- Domain defines `LLMServicePort` interface
- Infrastructure implements the port
- No LLM-specific logic in domain entities

### 3. Backward Compatibility
The Person class maintains a deprecated `_prepare_messages_for_llm()` method with a warning for smooth migration.

## Configuration

### Environment Variables
```bash
DIPEO_BASE_DIR=/path/to/project  # Base directory for prompt files
DIPEO_LLM_TIMEOUT=300            # LLM request timeout
DIPEO_LLM_MAX_RETRIES=3          # Retry attempts
```

### Person LLM Configuration
```python
PersonLLMConfig(
    service=LLMService.OPENAI,
    model="gpt-4.1-nano",
    api_key_id="openai_key",
    system_prompt="You are a helpful assistant",  # Inline prompt
    prompt_file="prompts/assistant.txt"  # Or file-based prompt
)
```

## Error Handling

The service provides comprehensive error handling:
- **APIKeyError**: Invalid or missing API keys
- **LLMServiceError**: Provider-specific failures
- **Retry Logic**: Automatic retry for transient failures
- **Fallback Mechanisms**: Graceful degradation when prompt files are missing

## Performance Optimization

### 1. Connection Pooling
Adapters are cached for 1 hour to reduce initialization overhead.

### 2. Single-Flight Cache
Prevents thundering herd problem during concurrent adapter creation.

### 3. Async Operations
All LLM calls are async for non-blocking execution.

## Testing

### Unit Tests
```python
# Test system prompt handler
handler = SystemPromptHandler(base_dir="/test/dir")
prompt = handler.get_system_prompt(llm_config)
assert prompt == expected_content

# Test message formatter
formatter = MessageFormatter()
messages = formatter.format_messages_for_llm(
    messages=domain_messages,
    person_id="person1",
    system_prompt="Test prompt",
    service=LLMService.OPENAI,
    system_role="developer"
)
```

### Integration Tests
```python
# Test complete flow with mock adapter
mock_adapter = MockLLMAdapter()
service = LLMInfraService(api_key_service, llm_domain_service)
result = await service.complete_with_person(...)
```

## Migration Guide

### From Old Architecture (Domain-Embedded)
```python
# OLD: Person class handled LLM logic
person._prepare_messages_for_llm()  # Deprecated

# NEW: Infrastructure handles formatting
llm_service.complete_with_person(
    person_messages=person.get_messages(),
    person_id=person.id,
    llm_config=person.llm_config
)
```

## Future Enhancements

1. **Streaming Support**: Add streaming response handling for all providers
2. **Caching Layer**: Add Redis-based response caching
3. **Metrics Collection**: Add detailed metrics for monitoring
4. **Dynamic Routing**: Route to different providers based on load/cost
5. **Prompt Templates**: Support for advanced prompt templating