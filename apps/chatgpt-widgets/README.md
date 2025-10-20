# DiPeO ChatGPT Widgets

React-based widgets for ChatGPT apps integration, providing rich UI for diagram visualization and execution monitoring.

## Quick Start

```bash
# Install dependencies (from project root)
make install

# Build widgets
make build-widgets

# Start dev server
make dev-widgets
```

## Available Widgets

### execution-results
Displays execution status, timing, and results.

### diagram-list
Browse and search available diagrams.

### execution-list
Monitor execution history with filtering.

## Development

### Project Structure

```
src/
├── lib/              # Utilities (GraphQL client)
├── hooks/            # React hooks (widget state, queries)
├── components/       # Shared components (StatusBadge, Layout)
├── shared/           # Shared styles
└── [widget-name]/    # Individual widget directories
    ├── index.tsx     # Widget component
    └── index.html    # Entry point
```

### Creating a New Widget

1. Create directory: `src/my-widget/`
2. Add `index.tsx` with React component
3. Add `index.html` entry point
4. Build: `make build-widgets`

See [ChatGPT Apps Integration](../../docs/features/chatgpt-apps-integration.md) for detailed guide.

## Build Output

Widgets are built to `apps/server/static/widgets/` with hashed filenames for cache busting.

## Tech Stack

- **React 19**: UI components
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **GraphQL**: Data fetching
