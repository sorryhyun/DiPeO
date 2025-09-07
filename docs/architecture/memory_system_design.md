# Memory System Design in DiPeO

## Overview

DiPeO implements an intelligent memory management system that allows LLM agents (Persons) to have different views of a shared global conversation. The system is designed to be simple for users while being powerful through LLM-based selection.

## The Dual-Persona Memory Selector

The memory system uses a "dual-persona" approach when intelligent selection is needed:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Memory Selection Process                         │
│                                                                      │
│  Global Conversation                                                 │
│  ┌─────────────┐                                                    │
│  │ Message 1   │     ┌──────────────────────┐                      │
│  │ Message 2   │────▶│  Selector Facet 🧠   │                      │
│  │ Message 3   │     │  (Alice.__selector)  │                      │
│  │ Message 4   │     │                      │                      │
│  │ Message 5   │     │ "Find messages about │                      │
│  │ ...         │     │  requirements and    │                      │
│  │ Message N   │     │  API design"         │                      │
│  └─────────────┘     └──────────┬───────────┘                      │
│                                  │                                  │
│                                  ▼                                  │
│                         Analyzes & Selects                          │
│                                  │                                  │
│                                  ▼                                  │
│                      Selected Messages [2,5,7]                      │
│                                  │                                  │
│                                  ▼                                  │
│                      ┌──────────────────────┐                      │
│                      │   Base Person 👤     │                      │
│                      │      (Alice)         │                      │
│                      │                      │                      │
│                      │  Sees only:          │                      │
│                      │  - Message 2         │                      │
│                      │  - Message 5         │                      │
│                      │  - Message 7         │                      │
│                      └──────────────────────┘                      │
│                                  │                                  │
│                                  ▼                                  │
│                          Executes Task                              │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Insight**: The same person becomes two entities:
- **Selector Facet** (`{person_id}.__selector`): An intelligent analyst that reviews ALL messages
- **Base Person** (`{person_id}`): The task executor that sees only selected messages

## Simple Memory Configuration

### Just Two User Options

1. **Natural Language Selection** (default for any non-keyword string)
   ```yaml
   memorize_to: "requirements, API design, authentication"
   ```
   The LLM intelligently selects relevant messages based on your criteria.

2. **GOLDFISH Mode** (special keyword)
   ```yaml
   memorize_to: "GOLDFISH"
   ```
   Complete memory reset - no conversation history at all.

3. **Default Behavior** (when `memorize_to` is not specified)
   ```yaml
   # memorize_to not specified - uses internal ALL_INVOLVED filter
   ```
   Shows messages where the person is sender or recipient.

### That's It!

No complex enums. No rule names to remember. Just describe what you want in natural language, or use GOLDFISH for no memory.

## Core Concepts

### Global Conversation Model

All messages are stored in a single, immutable global conversation:

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

**Properties:**
- **Immutable**: Messages are never deleted
- **Shared**: All persons access the same conversation
- **Filtered**: Each person sees a filtered view based on memory settings

### Per-Job Configuration

Memory is configured at the **job level**, not the person level:

```yaml
nodes:
  - id: analyzer
    type: person_job
    person: alice
    memorize_to: "technical requirements, constraints"
    
  - id: summarizer
    type: person_job  
    person: alice  # Same person, different memory!
    memorize_to: "key findings, conclusions"
    at_most: 5
```

## How It Works

### LLM-Based Selection Process

When you specify natural language criteria:

1. **Selector Creation**: System creates `{person_id}.__selector` facet
2. **Intelligent Analysis**: Selector analyzes all relevant messages
3. **Semantic Understanding**: Uses natural language understanding to identify relevant content
4. **Message Selection**: Returns IDs of most relevant messages
5. **Task Execution**: Base person executes with selected messages only

### Configuration Parameters

```yaml
- label: "Technical Analysis"
  type: person_job
  props:
    person: Analyst
    memorize_to: "requirements, API design, performance constraints"
    at_most: 8  # Optional: limit to 8 messages
```

**Parameters:**
- `memorize_to`: Natural language criteria or "GOLDFISH"
- `at_most`: Maximum number of messages (optional)

## Example Patterns

### 1. Progressive Refinement Pipeline

```yaml
# Stage 1: Broad analysis
- label: Analyze
  type: person_job
  props:
    memorize_to: "user requirements, specifications, constraints"
    at_most: 30
    
# Stage 2: Focused summary
- label: Summarize  
  type: person_job
  props:
    memorize_to: "key decisions, analysis results"
    at_most: 15
    
# Stage 3: Final extraction
- label: Extract
  type: person_job
  props:
    memorize_to: "final conclusions, action items"
    at_most: 5
```

### 2. Multi-Agent Collaboration

```yaml
- label: Researcher
  type: person_job
  props:
    memorize_to: "research findings, data, evidence"
    at_most: 25
    
- label: Critic
  type: person_job
  props:
    memorize_to: "arguments, counterpoints, rebuttals"
    at_most: 10
    
- label: Moderator
  type: person_job
  props:
    # No memorize_to - sees all messages they're involved in
    at_most: 50
```

### 3. Fresh Start Analysis

```yaml
- label: "Unbiased Review"
  type: person_job
  props:
    person: Reviewer
    memorize_to: "GOLDFISH"  # No memory - fresh perspective
```

## Best Practices

### 1. Use Natural Language Freely

The LLM understands context and semantics:
- ✅ `"requirements and constraints"`
- ✅ `"technical decisions, architecture choices"`
- ✅ `"user feedback, bug reports, feature requests"`
- ✅ `"everything about authentication and security"`

### 2. Set Reasonable Limits

- **No limit**: Comprehensive analysis (omit `at_most`)
- **20-30 messages**: Detailed context
- **10-15 messages**: Focused discussion
- **3-5 messages**: Quick summary
- **0 messages**: Use `"GOLDFISH"`

### 3. Design Memory for Cognitive Load

Match memory to task complexity:
```yaml
# Complex analysis needs more context
memorize_to: "all technical discussions, decisions, trade-offs"
at_most: 40

# Simple classification needs less
memorize_to: "current request and its context"
at_most: 3
```

## Key Benefits

1. **Simplicity**: Just describe what you want in plain English
2. **Intelligence**: LLM understands semantic relevance
3. **Flexibility**: Same person can have different memory per task
4. **Efficiency**: Only processes relevant information
5. **Clarity**: No complex enums or rules to memorize

## Common Use Cases

### Technical Review
```yaml
memorize_to: "code changes, review comments, technical debt"
```

### Customer Support
```yaml
memorize_to: "customer issue, previous solutions, related tickets"
```

### Project Management
```yaml
memorize_to: "deadlines, blockers, team decisions"
```

### Creative Writing
```yaml
memorize_to: "character development, plot points, themes"
```

## Memory Application Flow

```
User Configuration
       │
       ▼
"requirements, API design"  ──┐
                              │
       OR                     ├──→ MemorySelector.apply_memory_settings()
                              │
"GOLDFISH"  ──────────────────┘
       │
       ▼
   No Memory                     Intelligent Selection
                                        │
                                        ▼
                                 Create Selector Facet
                                        │
                                        ▼
                                 Analyze All Messages
                                        │
                                        ▼
                                 Select Relevant IDs
                                        │
                                        ▼
                                 Filter Messages
                                        │
                                        ▼
                                 Apply at_most Limit
                                        │
                                        ▼
                                 Execute with Filtered Memory
```

## Non-Destructive Memory

"Forgetting" in DiPeO is non-destructive:
- Original messages remain in global conversation
- Person's view is temporarily filtered
- Can be changed by modifying memory settings
- Full audit trail always preserved

## System Message Preservation

System messages are automatically preserved when using `at_most` limits - no configuration needed. This ensures critical system context is never lost.

---

## Internal Implementation Details

### Architecture Components

The memory system is implemented through the `MemorySelector` class:

```python
from dipeo.application.execution.handlers.person_job.memory_selector import MemorySelector

# Apply memory settings
selector = MemorySelector(orchestrator)
filtered_messages = await selector.apply_memory_settings(
    person=person,
    all_messages=all_messages,
    memorize_to="requirements, API design",
    at_most=10,
    task_prompt_preview=task_preview,
    llm_service=llm_service,
)
```

### Internal Filter Methods

The system uses these internal filters (not exposed to users):

- `_filter_all_involved()`: Messages where person is sender or recipient (default)
- `_filter_sent_by_me()`: Only messages sent by this person  
- `_filter_sent_to_me()`: Only messages sent to this person
- `_filter_system_and_me()`: System messages and person's responses
- `_filter_conversation_pairs()`: Request/response pairs
- `_apply_limit()`: Applies message count limits

These are implementation details that enable the default behavior and provide the foundation for future enhancements.

### Selector Facet Details

For LLM-based selection:
- Facet ID: `{base_person_id}.__selector`
- Inherits base person's LLM config
- Adds specialized selection prompt
- Receives candidate messages as structured list
- Returns JSON array of message IDs
- Temperature set to 0.1 for consistency

### Message ID Mapping

The system maintains message IDs for selection:
1. Selector receives messages with IDs
2. Returns selected IDs as JSON array
3. Maps IDs back to message objects
4. Applies final filtering and limits

## Future Enhancements

1. **Time-Based Windows**: Keep messages from last N minutes
2. **Priority Preservation**: Always keep critical messages
3. **Caching**: Cache selections for repeated patterns
4. **Hybrid Selection**: Combine multiple selection strategies
5. **Context Injection**: Add external context to selection criteria

## Summary

DiPeO's memory system provides powerful, intuitive control through natural language. The dual-persona approach (Selector Facet + Base Person) enables intelligent memory management without complexity. Users simply describe what they want to remember, and the system handles the rest through LLM-based understanding.

The consolidation to just two user options (natural language or GOLDFISH) makes the system accessible while maintaining all the power of semantic selection. This design philosophy - simple interface, intelligent implementation - guides the entire memory system architecture.
