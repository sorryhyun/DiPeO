# Import Rules for DiPeO Frontend

This document establishes clear import rules to maintain a clean architecture and prevent circular dependencies.

## Module Hierarchy

```
@dipeo/domain-models (highest level - pure domain types)
    ↓
core/ (global state, utilities, types)
    ↓
shared/ (generic UI components and utilities)
    ↓
features/ (feature-specific modules)
```

## Import Rules

### 1. Domain Models (`@dipeo/domain-models`)
- **Can import from:** Nothing (pure domain layer)
- **Can be imported by:** All modules
- **Purpose:** Single source of truth for domain types

### 2. Core Module (`@/core/*`)
- **Can import from:** 
  - `@dipeo/domain-models`
- **Can be imported by:** 
  - `shared/*`
  - `features/*`
- **Cannot import from:** 
  - `shared/*`
  - `features/*`
- **Purpose:** Global state management, core utilities, type augmentations

### 3. Shared Module (`@/shared/*`)
- **Can import from:** 
  - `@dipeo/domain-models`
  - `@/core/*`
- **Can be imported by:** 
  - `features/*`
- **Cannot import from:** 
  - `features/*`
- **Purpose:** Generic, reusable UI components and utilities without domain logic

### 4. Feature Modules (`@/features/*`)
- **Can import from:** 
  - `@dipeo/domain-models`
  - `@/core/*`
  - `@/shared/*`
- **Cannot import from:** 
  - Other features (use events/store for communication)
- **Purpose:** Feature-specific components, hooks, services, and logic

## Feature Module Structure

Each feature should maintain this structure:
```
features/[feature-name]/
├── components/     # Feature-specific React components
├── hooks/          # Feature-specific hooks
├── store/          # Feature slice and related logic
├── config/         # Feature-specific configuration
├── services/       # Feature-specific services/API calls
├── types/          # Feature-specific type augmentations (optional)
├── utils/          # Feature-specific utilities (optional)
└── index.ts        # Public API exports
```

## Cross-Feature Communication

When features need to communicate:
1. **Via Global Store:** Use the unified store in `core/store`
2. **Via Events:** Dispatch actions that other features can listen to
3. **Via Context:** Use React Context for UI-specific state sharing

## Import Examples

### ✅ Good Imports
```typescript
// In a feature component
import { NodeType } from '@dipeo/domain-models';
import { useUnifiedStore } from '@/core/store';
import { Button } from '@/shared/components/ui';
import { DiagramCanvas } from '../components/DiagramCanvas';

// In shared component
import { PersonID } from '@/core/types';
import { logger } from '@/core/utils';
```

### ❌ Bad Imports
```typescript
// In core module
import { DiagramEditor } from '@/features/diagram-editor'; // ❌ Core cannot import from features

// In shared module
import { useExecutionData } from '@/features/execution-monitor/hooks'; // ❌ Shared cannot import from features

// In feature module
import { PersonList } from '@/features/person-management/components'; // ❌ Features cannot import from each other
```

## Verification

To verify no circular dependencies:
1. Run `pnpm typecheck` - TypeScript will detect circular dependencies
2. Use bundler analysis tools to visualize import graphs
3. Follow the hierarchy: dependencies should only flow downward

## Enforcement

1. **ESLint Rules:** Configure import restrictions in `.eslintrc`
2. **Code Reviews:** Check import patterns during reviews
3. **Module Boundaries:** Use TypeScript's module resolution to enforce boundaries