# DiPeO Subagent Prompt System

This directory contains the subagent prompt architecture for DiPeO, designed to scale with project complexity while maintaining consistency and reusability.

## Overview

The subagent system follows Claude Code's best practices for specialized AI agents that can be proactively delegated to handle specific aspects of DiPeO workflows.

## Directory Structure

```
subagents/
├── prompts/        # Subagent system prompts
├── configs/        # YAML configurations for subagents
├── examples/       # Example usage patterns
└── templates/      # Reusable prompt templates
```

## Subagent Hierarchy

### Core Subagents

1. **Diagram Architect** (`diagram-architect`)
   - Designs and validates Light YAML diagrams
   - Optimizes node connections and data flow
   - Suggests architectural improvements

2. **Node Specialist** (`node-specialist`)
   - Configures specific node types (person_job, api_job, etc.)
   - Validates node properties and connections
   - Recommends appropriate node types for tasks

3. **Prompt Engineer** (`prompt-engineer`)
   - Optimizes prompts for person nodes
   - Creates context-aware system prompts
   - Adapts prompts based on workflow requirements

4. **Integration Expert** (`integration-expert`)
   - Handles API and service integrations
   - Configures authentication and endpoints
   - Manages external service connections

5. **Codegen Assistant** (`codegen-assistant`)
   - Manages code generation pipeline
   - Validates TypeScript specifications
   - Ensures generated code consistency

### Domain-Specific Subagents

6. **Frontend Generator** (`frontend-generator`)
   - Creates React components and UI elements
   - Implements responsive designs
   - Integrates with DiPeO's frontend architecture

7. **Data Flow Analyzer** (`data-flow-analyzer`)
   - Analyzes data transformations between nodes
   - Identifies bottlenecks and optimization opportunities
   - Validates data schemas

8. **Memory Manager** (`memory-manager`)
   - Optimizes conversation memory usage
   - Selects relevant context for person nodes
   - Manages memory profiles (FOCUSED, BALANCED, COMPREHENSIVE)

9. **Test Designer** (`test-designer`)
   - Creates test cases for diagrams
   - Generates sample input data
   - Validates expected outputs

10. **Performance Optimizer** (`performance-optimizer`)
    - Analyzes diagram execution performance
    - Suggests parallel execution opportunities
    - Optimizes resource usage

## Usage Patterns

### Automatic Delegation

Claude Code will automatically delegate to appropriate subagents based on context:

```yaml
# In your Light YAML diagram
nodes:
  - label: Design Workflow
    type: person_job
    props:
      person: Claude Code Agent
      default_prompt: |
        Design a workflow to process customer orders.
        # This will automatically trigger the diagram-architect subagent
```

### Explicit Invocation

You can explicitly request a specific subagent:

```yaml
nodes:
  - label: Optimize Prompts
    type: person_job
    props:
      person: Claude Code Agent
      default_prompt: |
        Use the prompt-engineer subagent to optimize this prompt:
        "Analyze the data and provide insights"
```

## Configuration

Each subagent has a YAML configuration in `configs/`:

```yaml
name: diagram-architect
description: Designs and optimizes DiPeO Light YAML diagrams
tools:
  - read
  - write
  - edit
model: claude-3-sonnet-20240229  # Optional: specific model
proactive_triggers:
  - "design a workflow"
  - "create a diagram"
  - "optimize the flow"
```

## Best Practices

1. **Single Responsibility**: Each subagent handles one specific domain
2. **Clear Boundaries**: Define what each subagent can and cannot do
3. **Consistent Format**: Use templates for similar subagent types
4. **Proactive Design**: Include trigger phrases for automatic delegation
5. **Context Preservation**: Subagents maintain their own context windows

## Integration with DiPeO

The subagent system integrates seamlessly with:
- DiPeO's node-based architecture
- Light YAML diagram format
- Code generation pipeline
- Claude Code SDK integration
- Enhanced Service Registry

## Examples

See the `examples/` directory for:
- Complete workflow examples using subagents
- Chaining multiple subagents
- Complex diagram generation patterns
- Performance optimization workflows

## Contributing

When adding new subagents:
1. Create the system prompt in `prompts/`
2. Add configuration in `configs/`
3. Provide examples in `examples/`
4. Update this README with the new subagent
5. Test with real DiPeO workflows