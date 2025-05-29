
# AgentDiagram Packages – Essential Guide

## 1. Overview

AgentDiagram's shared packages provide reusable TypeScript components, utilities, and types that power both the frontend and future applications. Built with framework independence in mind.

Key principles:
* **Zero coupling** – packages don't depend on app-specific stores
* **Type safety** – full TypeScript with strict mode
* **Tree-shakeable** – optimized for bundle size
* **React 19 ready** – concurrent features support

## 2. Package Directory

| Package               | Purpose                                              | Dependencies      |
| --------------------- | ---------------------------------------------------- | ----------------- |
| **@repo/core-model**  | Types, interfaces, node configs for entire system    | None              |
| **@repo/ui-kit**      | Design system components (Button, Input, Modal...)   | React, Tailwind   |
| **@repo/diagram-ui**  | React Flow nodes, edges, context menus              | React Flow, ui-kit |
| **@repo/properties-ui** | Dynamic property panels with form builders        | ui-kit            |

## 3. Package Relationships

```text
core-model (types & configs)
    ↓
ui-kit (base components)
    ↓
diagram-ui & properties-ui (specialized components)
    ↓
apps/web (consumes all)
```

## 4. Developer Guide

```bash
# Install all packages
pnpm install

# Type check all packages
pnpm -r typecheck

# Build specific package
pnpm --filter @repo/ui-kit build
```

## 5. Key Exports

### @repo/core-model
* `DiagramState`, `PersonDefinition`, `ApiKey` – core types
* `UNIFIED_NODE_CONFIGS` – node configuration system
* `getNodeConfig()`, `getReactFlowType()` – config helpers

### @repo/ui-kit
* `Button`, `Input`, `Select`, `Modal` – Tailwind components
* `Spinner`, `Switch` – utility components
* All components use `forwardRef` for flexibility

### @repo/diagram-ui
* `BaseNode`, `GenericNode` – node primitives
* `CustomArrow` – bezier edge with draggable control points
* `useContextMenu`, `useKeyboardShortcuts` – diagram hooks

### @repo/properties-ui
* `GenericPropertiesPanel` – auto-generated property forms
* `Panel`, `Form`, `FormField` – building blocks
* Field components with inline variants

## 6. Design Patterns

* **Props forwarding** – components accept store update functions
* **Memoization** – heavy components use React.memo
* **Composition** – small, focused components
* **CSS-in-Config** – Tailwind classes in node configs

## 7. Adding New Components

1. Choose appropriate package based on dependencies
2. Export from `index.ts`
3. Add TypeScript types to `core-model` if shared
4. Use existing patterns (forwardRef, memoization)

## 8. Testing Approach

* Unit tests for utilities
* Component testing with React Testing Library
* Type coverage with `tsc --noEmit`
* Bundle size monitoring

## 9. Performance Tips

* Import specific components: `import { Button } from '@repo/ui-kit'`
* Use dynamic imports for heavy components
* Leverage React.memo for node components
* Keep `core-model` pure types only

## 10. Common Issues

| Issue                    | Solution                               |
| ------------------------ | -------------------------------------- |
| Circular dependency      | Move shared types to core-model        |
| Bundle too large         | Check for accidental React Flow import |
| Type errors in app       | Run `pnpm typecheck` in package first  |
| Tailwind classes missing | Add to safelist in consuming app       |

## 11. Future Packages

* `@repo/hooks` – shared React hooks
* `@repo/llm-adapters` – LLM provider interfaces
* `@repo/diagram-parser` – YAML/UML converters

## 12. Package Scripts

Each package typically has:
* `typecheck` – TypeScript validation
* `lint` – ESLint checks
* `test` – Jest tests (where applicable)

No build step needed – apps consume TypeScript directly via Vite.
