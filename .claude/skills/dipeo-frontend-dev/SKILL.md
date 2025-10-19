# dipeo-frontend-dev

**Router skill for DiPeO frontend development (React, visual editor, GraphQL integration)**

This is a **thin router skill** that provides decision criteria and documentation anchors for frontend development tasks. Use this skill to determine whether to handle the task directly or escalate to the full `dipeo-frontend-dev` agent.

## When to Use This Skill

Use this skill when the task involves:
- React components in `/apps/web/src/`
- Visual diagram editor (XYFlow integration)
- GraphQL queries/mutations using generated hooks
- TypeScript type errors from `pnpm typecheck`
- UI/UX styling and component patterns
- State management with Zustand
- Frontend debugging and troubleshooting

## Decision Criteria

### Handle Directly (No Agent Needed)

**Simple, isolated tasks** that don't require complex analysis:

✅ **Quick fixes:**
- Fix a single TypeScript type error in one file
- Update a component's styling or layout
- Add a new prop to an existing component
- Fix an import statement or path

✅ **Small additions:**
- Add a simple UI element to existing component
- Update GraphQL hook usage (already familiar with pattern)
- Add basic form validation

✅ **Documentation lookups:**
- "Where is component X defined?"
- "What GraphQL hooks are available?"
- "How do I use the form manager hooks?"

### Escalate to dipeo-frontend-dev Agent

**Complex, multi-file tasks** requiring deep analysis:

🔴 **TypeScript type fixing:**
- Multiple related type errors across files
- Type errors involving GraphQL schema mismatches
- Complex generic type issues
- Type system refactoring

🔴 **Feature implementation:**
- Add new diagram editor features (custom nodes, edges)
- Implement new UI workflows (multi-step forms, wizards)
- Integrate new GraphQL operations with UI
- Add state management for new features

🔴 **Refactoring:**
- Restructure component hierarchy
- Extract shared logic into hooks
- Update component patterns across multiple files

🔴 **Debugging:**
- Track down runtime errors across components
- Fix GraphQL integration issues
- Resolve state synchronization problems

## Documentation Anchors

Use `Skill(doc-lookup)` with these anchors to retrieve specific sections from `docs/agents/frontend-development.md`:

### Core Responsibilities
- `#core-responsibilities` - Overview of frontend dev responsibilities
- `#react-components` - React component development patterns
- `#diagram-editor` - Visual diagram editor (XYFlow) guidance
- `#graphql-integration` - GraphQL integration patterns
- `#typescript-types` - TypeScript and type safety practices

### Technical Context
- `#technical-context` - Complete tech stack overview
- `#tech-stack` - Technologies used (React 19, XYFlow, Apollo, Zustand, etc.)
- `#project-structure` - Frontend directory structure
- `#dev-workflow` - Development workflow steps

### Code Quality & Patterns
- `#code-quality` - Code quality standards overview
- `#component-patterns` - Component best practices
- `#graphql-usage` - GraphQL query/mutation patterns with examples
- `#state-management-general` - General state management guidance
- `#state-management-zustand` - Zustand-specific patterns
- `#styling` - TailwindCSS and styling approach
- `#infrastructure-services` - ConversionService, NodeService, ValidationService
- `#node-system` - Node configs and component composition
- `#common-patterns` - Custom hooks, factories, error boundaries

### Constraints & Guidelines
- `#constraints` - Important constraints (never edit generated files, etc.)
- `#escalation` - When to escalate to backend/codegen agents
- `#quality-checklist` - Pre-completion quality checklist

## Example Workflows

### Pattern 1: Direct Handling (Simple Fix)
```
User: "Fix the TypeScript error in DiagramEditor.tsx line 42"
→ Load this router skill
→ Review decision criteria
→ Task is simple (single file, single error)
→ Read file, fix error directly
→ Run pnpm typecheck to verify
```

### Pattern 2: Router + Doc-Lookup (Focused Task)
```
User: "How do I use the generated GraphQL hooks?"
→ Load this router skill
→ Determine need for GraphQL usage patterns
→ Skill(doc-lookup) --query "graphql-usage"
→ Provide guidance from retrieved section
```

### Pattern 3: Escalate to Agent (Complex Task)
```
User: "Add a new custom node type to the diagram editor with configuration panel"
→ Load this router skill
→ Review decision criteria
→ Complex: involves multiple files, XYFlow integration, state management
→ Task(dipeo-frontend-dev, "Add custom webhook node with config panel")
→ Agent handles implementation with access to doc-lookup as needed
```

## Cross-References

### Related Agents
- **dipeo-backend**: If GraphQL schema needs modification
- **dipeo-codegen-pipeline**: If TypeScript model definitions need updates
- **dipeo-package-maintainer**: If new node types need backend handlers

### Related Skills
- **doc-lookup**: Extract specific documentation sections by anchor
- **clean-comments**: Clean up component comments after implementation
- **maintain-docs**: Update frontend documentation after major changes

## Quick Commands

```bash
# Type checking
pnpm typecheck

# Development server
make dev-web  # Port 3000

# Monitor mode
# http://localhost:3000/?monitor=true

# GraphQL schema regeneration (if backend schema changed)
make graphql-schema
```

## Key Constraints

1. **NEVER modify generated files** in `/apps/web/src/__generated__/`
2. **ALWAYS use generated hooks** for GraphQL operations
3. **Run `pnpm typecheck`** before finalizing changes
4. **Prefer editing over creating** new files
5. **Follow existing patterns** - review similar components first

---

**Remember**: This is a router skill for decision-making and documentation access. For complex tasks, escalate to the full `dipeo-frontend-dev` agent which can perform deeper analysis and multi-file modifications.
