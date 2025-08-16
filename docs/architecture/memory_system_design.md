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
| `ALL_MESSAGES` | All messages in the conversation | Complete visibility for coordinators |

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
    memory_profile: FULL  # See everything
    
  - id: summarizer
    type: person_job  
    person: alice  # Same person!
    memory_profile: MINIMAL  # Limited context (5 messages)
```

## Memory Configuration Syntax

There are two ways to configure memory:

1. **Memory Profiles** (Recommended) - Predefined configurations:
```yaml
- label: PersonNode
  type: person_job
  props:
    memory_profile: FOCUSED  # Options: GOLDFISH, MINIMAL, FOCUSED, FULL, ONLY_ME, ONLY_I_SENT, CUSTOM
```

2. **Custom Memory Settings** - Fine-grained control (used when `memory_profile: CUSTOM`):
```yaml
- label: PersonNode
  type: person_job
  props:
    memory_profile: CUSTOM
    memory_settings:
      view: conversation_pairs
      max_messages: 10
      preserve_system: true
```

### Memory Profile Definitions:
- **GOLDFISH**: 2 messages, conversation pairs view (complete reset between runs)
- **MINIMAL**: 5 messages, conversation pairs view
- **FOCUSED**: 20 messages, conversation pairs view
- **FULL**: All messages, all messages view
- **ONLY_ME**: Messages sent to this person only
- **ONLY_I_SENT**: Messages sent by this person only
- **CUSTOM**: Use explicit `memory_settings`

## Common Patterns

### 1. Debate Pattern

Participants focus on the current exchange while judges need full context:

```yaml
- label: Optimist
  type: person_job
  props:
    memory_profile: FOCUSED  # Limited conversation context
    max_iteration: 3

- label: Judge
  type: person_job
  props:
    memory_profile: FULL     # See everything
```

### 2. Pipeline Pattern

Progressive refinement with decreasing context:

```yaml
# Stage 1: Full analysis
- label: Analyze
  memory_profile: FULL
    
# Stage 2: Focused summary
- label: Summarize  
  memory_profile: FOCUSED   # Focus on recent exchanges
    
# Stage 3: Final extraction
- label: Extract
  memory_profile: MINIMAL   # Only recent context
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

Memory settings are applied based on the chosen profile:
- **GOLDFISH**: Complete reset between executions (clears conversation history)
- **Other profiles**: Applied at node initialization, persists throughout execution
- **Custom settings**: Applied when `memory_profile: CUSTOM` is set

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

### Using Memory Profiles in Code

The system provides predefined memory profiles via `MemoryProfileFactory`:

```python
from dipeo.domain.conversation.memory_profiles import MemoryProfile, MemoryProfileFactory

# Get settings for a profile
settings = MemoryProfileFactory.get_settings(MemoryProfile.FOCUSED)
# Returns: MemorySettings(view=CONVERSATION_PAIRS, max_messages=20, preserve_system=True)
```

### Available Memory Profiles

```python
class MemoryProfile(Enum):
    FULL = auto()        # All messages, no limit
    FOCUSED = auto()     # 20 messages, conversation pairs
    MINIMAL = auto()     # 5 messages, conversation pairs  
    GOLDFISH = auto()    # 2 messages, conversation pairs (with reset)
    ONLY_ME = auto()     # Messages sent to person only
    ONLY_I_SENT = auto() # Messages sent by person only
    CUSTOM = auto()      # Use explicit memory_settings
```

### Dynamic Memory Management

Memory is typically set at the job level, but can be adjusted programmatically:

```python
# Apply memory settings to a person
person.set_memory_view(MemoryView.CONVERSATION_PAIRS)
person.set_memory_limit(max_messages=10, preserve_system=True)
```

## Future Enhancements

1. **Semantic Filtering**: Filter by message content/topic
2. **Time-Based Windows**: Keep messages from last N minutes
3. **Priority Preservation**: Keep important messages regardless of limits
4. **Memory Profiles**: Predefined configurations for common patterns

## Summary

DiPeO's memory system provides flexible, per-job control over what each LLM agent can see from a shared global conversation. This enables sophisticated multi-agent workflows while maintaining simplicity and auditability. The key insight is that memory configuration belongs to the job (task), not the person (agent), allowing the same agent to have different memory contexts for different tasks in the workflow.