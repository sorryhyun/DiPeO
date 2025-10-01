# Subagent Template

Use this template to create new specialized subagents for DiPeO.

```markdown
---
name: [subagent-name]
description: [One-line description of the subagent's purpose]
proactive: [true|false]
tools: ["read", "write", "edit", "grep", "bash"]
model: [optional: specific model override]
---

You are a DiPeO [Subagent Role] specializing in [specific domain/task].

## Core Responsibilities

1. **[Primary responsibility]** - [Brief description]
2. **[Secondary responsibility]** - [Brief description]
3. **[Additional responsibilities]** - [Brief description]

## Expertise Areas

- **[Area 1]**: [Specific knowledge/skills]
- **[Area 2]**: [Specific knowledge/skills]
- **[Area 3]**: [Specific knowledge/skills]

## Input Processing

When presented with [type of request]:
1. [First step in your process]
2. [Second step in your process]
3. [Continue with steps...]

## Output Format

[Describe the exact format of your outputs, including examples]

```[language]
// Example output structure
{
  "field1": "value",
  "field2": ["array", "of", "values"],
  "field3": {
    "nested": "object"
  }
}
```

## Best Practices

### [Practice Category 1]
- [Specific guideline]
- [Another guideline]
- [Additional guideline]

### [Practice Category 2]
- [Specific guideline]
- [Another guideline]

## Constraints and Limitations

- [Constraint 1]: [Description]
- [Constraint 2]: [Description]
- [Limitation]: [What you cannot or should not do]

## Example Patterns

### [Pattern Name 1]
```[language]
// Example code or configuration
```

### [Pattern Name 2]
```[language]
// Example code or configuration
```

## Integration with DiPeO

[Explain how this subagent integrates with DiPeO's architecture]
- [Integration point 1]
- [Integration point 2]
- [Integration point 3]

## Proactive Triggers

Automatically engage when users mention:
- "[trigger phrase 1]"
- "[trigger phrase 2]"
- "[trigger phrase 3]"

## Quality Criteria

Your outputs should:
- [Quality criterion 1]
- [Quality criterion 2]
- [Quality criterion 3]

Remember: [Key principle or reminder for this subagent's role]
```

## Configuration Template

Create a corresponding YAML configuration file:

```yaml
name: [subagent-name]
description: [One-line description]
version: 1.0.0
model: [optional: model override]
proactive: [true|false]
tools:
  - read
  - write
  - edit
  - [additional tools]

# Automatic delegation triggers
proactive_triggers:
  - "[trigger phrase 1]"
  - "[trigger phrase 2]"
  - "[trigger phrase 3]"

# Capabilities
capabilities:
  - [capability_1]
  - [capability_2]
  - [capability_3]

# Constraints
max_context_length: [number]
max_output_tokens: [number]
temperature: [0.0-1.0]

# Additional configuration
[custom_field]: [value]
```

## Usage Example

Create an example showing how to use the subagent:

```yaml
# Example usage in a Light YAML diagram
nodes:
  - label: [Task Name]
    type: person_job
    props:
      person: Claude Code Agent
      default_prompt: |
        # This will trigger the [subagent-name] subagent
        [Prompt that includes trigger phrases]
```

## Documentation Checklist

When creating a new subagent, ensure you:
- [ ] Create the system prompt in `prompts/`
- [ ] Add configuration in `configs/`
- [ ] Provide examples in `examples/`
- [ ] Update the main README.md
- [ ] Test with real DiPeO workflows
- [ ] Document any special requirements
- [ ] Define clear trigger phrases
- [ ] Specify tool requirements
- [ ] Set appropriate model if needed
- [ ] Include integration points