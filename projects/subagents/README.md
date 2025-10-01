# DiPeO Subagent System

A comprehensive subagent architecture for DiPeO that enables specialized AI agents to collaborate on complex workflow creation and project development tasks.

## Overview

The DiPeO subagent system provides specialized AI agents that work together to handle different aspects of the DiPeO ecosystem. Each subagent has specific expertise, focused responsibilities, and defined collaboration patterns.

## Subagent Categories

### Workflow Design Subagents

1. **diagram-architect** - Overall workflow design and optimization
2. **prompt-engineer** - LLM prompt optimization and design
3. **node-specialist** - Node configuration and selection
4. **integration-expert** - API and service integration
5. **codegen-assistant** - Code generation pipeline support

### Development Subagents

6. **codegen-expert** - TypeScript-to-Python code generation specialist
7. **dipeocc-specialist** - Claude Code session conversion expert
8. **web-developer** - React frontend and UI development
9. **cli-engineer** - Command-line interface development
10. **dipeo-core** - Core package and execution engine
11. **typescript-architect** - TypeScript domain model design

## Directory Structure

```
projects/subagents/
├── prompts/           # Detailed system prompts for each subagent
│   ├── diagram-architect.md
│   ├── prompt-engineer.md
│   ├── node-specialist.md
│   ├── integration-expert.md
│   ├── codegen-assistant.md
│   ├── codegen-expert.md      # Development subagents
│   ├── dipeocc-specialist.md
│   ├── web-developer.md
│   ├── cli-engineer.md
│   ├── dipeo-core.md
│   └── typescript-architect.md
├── configs/           # YAML configurations with triggers
│   └── [corresponding .yaml files]
├── examples/          # Collaboration workflow examples
│   ├── workflow-optimization.md
│   └── new-node-type-workflow.md
└── templates/         # Templates for creating new subagents
    └── subagent-template.md

```

## How Subagents Work

### Automatic Delegation

Claude Code automatically delegates to appropriate subagents based on context triggers:

```yaml
# User says: "Help me optimize the code generation pipeline"
# → Triggers: codegen-expert

# User says: "Convert my last Claude session to a diagram"
# → Triggers: dipeocc-specialist

# User says: "Add a new UI component for the diagram editor"
# → Triggers: web-developer
```

### Explicit Request

Users can directly request specific subagents:

```
"Use the typescript-architect subagent to design a new node model"
"Have the dipeo-core subagent implement a new handler"
```

### Collaboration Patterns

Subagents work together on complex tasks:

1. **Sequential Collaboration**: One subagent completes work, then hands off to another
2. **Parallel Work**: Multiple subagents work on different aspects simultaneously
3. **Review & Refinement**: Subagents review and improve each other's work
4. **Integrated Development**: Full-stack changes involving multiple subagents

## Development Subagent Specializations

### codegen-expert
- **Focus**: TypeScript-to-Python code generation pipeline
- **Expertise**: IR builders, model transformation, import resolution
- **Key Commands**: `make codegen`, `make apply-test`

### dipeocc-specialist
- **Focus**: Claude Code session conversion
- **Expertise**: Session parsing, workflow extraction, tool mapping
- **Key Commands**: `dipeocc convert`, `dipeocc watch`

### web-developer
- **Focus**: React frontend and visual diagram editor
- **Expertise**: React Flow, GraphQL hooks, Tailwind CSS
- **Key Commands**: `make dev-web`, `pnpm typecheck`

### cli-engineer
- **Focus**: Command-line interface and CLI tools
- **Expertise**: Click framework, async operations, rich formatting
- **Key Commands**: `dipeo run`, `dipeo ask`

### dipeo-core
- **Focus**: Core execution engine and infrastructure
- **Expertise**: Service architecture, event bus, node handlers
- **Key Areas**: EnhancedServiceRegistry, mixins, envelope pattern

### typescript-architect
- **Focus**: TypeScript domain model design
- **Expertise**: Type safety, schema generation, cross-language mapping
- **Key Areas**: Node specs, GraphQL types, validation rules

## Creating New Subagents

Use the template in `templates/subagent-template.md`:

1. Define the subagent's focus area and expertise
2. Create a detailed prompt in `prompts/`
3. Configure triggers and capabilities in `configs/`
4. Add collaboration patterns with existing subagents
5. Provide examples of typical tasks

## Best Practices

### For Subagent Design

1. **Single Responsibility**: Each subagent should have one clear area of expertise
2. **Tool Restrictions**: Only provide access to necessary tools
3. **Context Awareness**: Include relevant files and documentation paths
4. **Collaboration Definition**: Clearly define how the subagent works with others
5. **Trigger Precision**: Use specific, non-overlapping trigger phrases

### For Using Subagents

1. **Choose the Right Agent**: Select based on the task's primary focus
2. **Provide Context**: Give subagents enough information to succeed
3. **Chain Operations**: Use multiple subagents for complex multi-layer tasks
4. **Review Output**: Verify subagent work meets requirements
5. **Iterate**: Refine prompts based on subagent performance

## Common Workflows

### Adding a New Feature
1. **typescript-architect** designs the model
2. **codegen-expert** generates Python code
3. **dipeo-core** implements handlers
4. **web-developer** creates UI components
5. **cli-engineer** adds CLI support

### Optimizing Performance
1. **dipeo-core** analyzes bottlenecks
2. **codegen-expert** optimizes generation
3. **web-developer** improves frontend rendering
4. **cli-engineer** adds caching to CLI

### Converting Claude Sessions
1. **dipeocc-specialist** parses session
2. **diagram-architect** optimizes structure
3. **prompt-engineer** refines prompts
4. **node-specialist** configures nodes

## Integration with Claude Code

These subagents are designed to work with Claude Code's subagent feature. They follow best practices from the [Claude Code documentation](https://docs.claude.com/en/docs/claude-code/sub-agents):

- Proactive triggering based on context
- Focused tool access
- Clear handoff patterns
- Specialized expertise areas

## Future Enhancements

- **Testing Subagent**: Automated test generation and execution
- **Documentation Subagent**: Automated documentation updates
- **Performance Subagent**: Profiling and optimization
- **Security Subagent**: Security analysis and hardening
- **DevOps Subagent**: CI/CD and deployment automation

## Contributing

To contribute new subagents or improvements:

1. Follow the template structure
2. Ensure clear trigger phrases
3. Document collaboration patterns
4. Provide practical examples
5. Test with real DiPeO tasks

---

*The DiPeO subagent system enables sophisticated, collaborative AI-driven development through specialized, focused agents working in harmony.*