# Memory System Design in DiPeO

## Overview

DiPeO implements a sophisticated memory management system that allows LLM agents (Persons) to have different views of a shared global conversation. This design enables powerful workflow patterns where the same agent can have different memory contexts at different points in the workflow.

## Core Concepts

### 1. Global Conversation Model

All messages in a DiPeO workflow are stored in a single, global conversation that serves as the source of truth:

```
┌─────────────────────────────┐
│   Global Conversation       │
│ ┌─────────────────────────┐ │
│ │ Message 1: A → B        │ │
│ │ Message 2: B → A        │ │
│ │ Message 3: System → C   │ │
│ │ Message 4: C → A        │ │
│ │ ...                     │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

**Key Properties:**
- **Immutable**: Messages are never deleted, only filtered
- **Auditable**: Complete history is always preserved
- **Shared**: All persons access the same conversation

### 2. Memory Views (Filters)

Each person sees the global conversation through a configurable filter:

| View | Description | Use Case |
|------|-------------|----------|
| `ALL_INVOLVED` | Messages where person is sender or recipient | General conversation participant |
| `SENT_BY_ME` | Only messages sent by this person | Self-reflection, output review |
| `SENT_TO_ME` | Only messages sent to this person | Input processing, classification |
| `SYSTEM_AND_ME` | System messages and person's responses | Task-focused execution |
| `CONVERSATION_PAIRS` | Request/response pairs | Debate, Q&A scenarios |

### 3. Memory Limits (Windows)

After filtering, a sliding window can limit the number of messages:

```python
# Example: See only last 10 messages from my filtered view
memory_settings = MemorySettings(
    view=MemoryView.ALL_INVOLVED,
    max_messages=10,
    preserve_system=True  # Always keep system messages
)
```

### 4. Per-Job Configuration

Memory settings are configured at the **job level**, not the person level:

```yaml
nodes:
  - id: analyzer
    type: person_job
    person: alice
    memory_config:
      forget_mode: no_forget  # See everything
    
  - id: summarizer
    type: person_job  
    person: alice  # Same person!
    memory_config:
      forget_mode: on_every_turn  # Limited context
      max_messages: 5
```

## Memory Configuration Syntax


The `memory_config` syntax continues to work:

```yaml
- label: PersonNode
  type: person_job
  props:
    memory_config:
      forget_mode: on_every_turn
      max_messages: 10
```

## Common Patterns

### 1. Debate Pattern

Participants focus on the current exchange while judges need full context:

```yaml
- label: Optimist
  type: person_job
  props:
    memory_config:
      forget_mode: on_every_turn  # See Q&A pairs
    max_iteration: 3

- label: Judge
  type: person_job
  props:
    memory_config:
      forget_mode: no_forget       # See everything
```

### 2. Pipeline Pattern

Progressive refinement with decreasing context:

```yaml
# Stage 1: Full analysis
- label: Analyze
  memory_config:
    forget_mode: no_forget
    
# Stage 2: Focused summary
- label: Summarize  
  memory_config:
    forget_mode: on_every_turn   # Focus on exchanges
    
# Stage 3: Final extraction
- label: Extract
  memory_config:
    forget_mode: upon_request          # Only direct input
```

### 3. Multi-Agent Collaboration

Different agents with different perspectives on the same conversation:

```yaml
persons:
  researcher:
    # Sees all messages for comprehensive analysis
  critic:
    # Sees only conversation pairs for focused critique
  moderator:
    # Sees all messages to manage discussion
```

## Implementation Details

### Message Routing

When a message is added to the conversation:
1. It's stored in the global conversation
2. Each person's view automatically includes/excludes it based on their filter
3. No duplication or per-person storage needed

### Memory Application Timing

The node handler determines when to apply memory settings:
- `on_every_turn`: Applied when `execution_count > 0`
- `upon_request`: Applied when explicitly triggered
- `no_forget`: No memory management applied

### Non-Destructive Forgetting

"Forgetting" in DiPeO means limiting what a person can see, not deleting data:
- Original messages remain in global conversation
- Person's view is restricted through filters and limits
- Can be reversed by changing memory settings


## Best Practices

### 1. Choose Appropriate Memory Views

- **Debates/Arguments**: Use `conversation_pairs` to focus on exchanges
- **Analysis Tasks**: Use `all_involved` for full context
- **Classification**: Use `sent_to_me` for just the input
- **Monitoring**: Use `system_and_me` for task-specific messages

### 2. Set Reasonable Limits

- **No limit**: Judges, analyzers, final reviewers
- **10-20 messages**: General conversation tasks
- **1-5 messages**: Quick reactions, classifiers
- **0 messages**: Complete reset (rare)

### 3. Consider Workflow Flow

Design memory settings to match the cognitive requirements of each step:
```
Full Context → Filtered Context → Minimal Context → Decision
```

### 4. Preserve System Messages

Usually keep `preserve_system=True` to maintain task instructions:
```yaml
memory_config:
  max_messages: 5
  preserve_system: true  # Keep system prompts
```

## Advanced Configurations

### Custom Memory Profiles

Create reusable memory configurations:

```python
MEMORY_PROFILES = {
    "ANALYST": MemorySettings(view=ALL_INVOLVED, max_messages=None),
    "DEBATER": MemorySettings(view=CONVERSATION_PAIRS, max_messages=4),
    "CLASSIFIER": MemorySettings(view=SENT_TO_ME, max_messages=1),
    "GOLDFISH": MemorySettings(view=CONVERSATION_PAIRS, max_messages=2),
}
```

### Dynamic Memory Management

Adjust memory based on execution state:

```python
if execution_count > 10:
    # Reduce context after many iterations
    person.apply_memory_settings(
        MemorySettings(max_messages=5)
    )
```

## Future Enhancements

1. **Semantic Filtering**: Filter by message content/topic
2. **Time-Based Windows**: Keep messages from last N minutes
3. **Priority Preservation**: Keep important messages regardless of limits
4. **Memory Profiles**: Predefined configurations for common patterns

## Summary

DiPeO's memory system provides flexible, per-job control over what each LLM agent can see from a shared global conversation. This enables sophisticated multi-agent workflows while maintaining simplicity and auditability. The key insight is that memory configuration belongs to the job (task), not the person (agent), allowing the same agent to have different memory contexts for different tasks in the workflow.