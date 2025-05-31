# AgentDiagram Web Frontend

React-based visual workflow editor for multi-LLM agent orchestration.

## Quick Start

```bash
pnpm install
pnpm dev        # http://localhost:3000
pnpm build      # Production build
pnpm analyze    # Bundle analysis
```

## Tech Stack

- **React 19** + **TypeScript**
- **Zustand** (state management)
- **React Flow** (diagram editor)
- **Tailwind CSS** (styling)
- **Vite** (build tool)

## Key Features

- 🎨 Drag-drop workflow designer
- 🤖 Multi-LLM support (OpenAI, Claude, Gemini, Grok)
- ⚡ Real-time execution with SSE streaming
- 💾 YAML/JSON import/export
- 🧠 3D memory layer visualization
- 💬 Conversation tracking & cost analytics

## Project Structure

```
src/
├── features/          # Feature modules
│   ├── diagram/       # Canvas, nodes, execution
│   ├── nodes/         # Node components & logic
│   ├── properties/    # Property panels
│   ├── conversation/  # Chat dashboard
│   └── layout/        # TopBar, Sidebar, modals
├── shared/           # Shared code
│   ├── stores/       # Zustand stores
│   ├── hooks/        # Custom hooks
│   ├── components/   # UI components
│   └── types/        # TypeScript types
└── App.tsx           # Root component
```

## Development

### API Proxy
Dev server proxies `/api/*` to `localhost:8000`

### State Management
- `consolidatedDiagramStore` - nodes, arrows, persons
- `consolidatedUIStore` - selections, UI state
- `executionStore` - runtime state

### Adding a Node Type
1. Define in `shared/types/nodeConfig.ts`
2. Create component in `features/nodes/components/nodes/`
3. Add to `features/nodes/components/NodesGeneric.tsx`

### Key Hooks
- `useDiagramRunner()` - execute workflows
- `usePropertyPanel()` - property form state
- `useNodeExecutionState()` - node runtime state

## Common Commands

```bash
# Type checking
pnpm typecheck

# Bundle analysis
pnpm analyze

# Preview production build
pnpm serve
```

## Environment

```env
VITE_API_HOST=localhost:8000  # Backend URL
```

## Tips

- Nodes auto-save on property changes
- Double-click arrows to straighten
- Hold Shift for multi-select
- Ctrl+S saves to backend