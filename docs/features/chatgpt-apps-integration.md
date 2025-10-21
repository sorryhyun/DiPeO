# ChatGPT Apps Integration

DiPeO integrates with ChatGPT apps to provide rich UI widgets for diagram rendering, execution monitoring, and results visualization.

## Overview {#overview}

The ChatGPT apps integration enables:
- **Diagram List Widget**: Browse and search available diagrams
- **Execution Results Widget**: View execution status, timing, and outputs
- **Execution List Widget**: Monitor execution history with filtering

## Architecture {#architecture}

```
┌─────────────────────────────────────────┐
│          ChatGPT Client                 │
│  (Renders widgets in conversation)      │
└──────────────┬──────────────────────────┘
               │ MCP JSON-RPC
               │
┌──────────────▼──────────────────────────┐
│     DiPeO MCP Server (FastAPI)          │
│  ┌──────────────────────────────────┐   │
│  │  MCP Tools (with widget metadata)│   │
│  │  - dipeo_run                     │   │
│  │  - see_result                    │   │
│  │  - search                        │   │
│  │  - fetch                         │   │
│  └──────────────────────────────────┘   │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │  Static Widget Assets            │   │
│  │  /widgets/execution-results.html │   │
│  │  /widgets/diagram-list.html      │   │
│  │  /widgets/execution-list.html    │   │
│  └──────────────────────────────────┘   │
└──────────────┬──────────────────────────┘
               │ GraphQL
               │
┌──────────────▼──────────────────────────┐
│     DiPeO GraphQL API                   │
└─────────────────────────────────────────┘
```

## Setup {#setup}

### 1. Install Dependencies

```bash
make install
```

This installs all dependencies including the widget workspace.

### 2. Build Widgets

```bash
make build-widgets
```

This builds all widgets to `apps/server/static/widgets/`.

### 3. Start the Server

```bash
make dev-server
```

The server will serve widgets at `http://localhost:8000/widgets/`.

### 4. Expose via ngrok (for ChatGPT integration)

```bash
ngrok http 8000
```

Use the ngrok URL to connect ChatGPT to your DiPeO MCP server.

## Development {#development}

### Widget Workspace Structure {#widget-workspace-structure}

```
apps/chatgpt-widgets/
├── src/
│   ├── lib/
│   │   └── graphql-client.ts    # GraphQL client
│   ├── hooks/
│   │   ├── use-widget-state.ts  # Widget state hook
│   │   └── use-graphql-query.ts # GraphQL query hook
│   ├── components/
│   │   ├── StatusBadge.tsx      # Shared status badge
│   │   └── WidgetLayout.tsx     # Shared layout wrapper
│   ├── shared/
│   │   └── index.css            # Shared styles
│   ├── execution-results/       # Execution results widget
│   │   ├── index.tsx
│   │   └── index.html
│   ├── diagram-list/            # Diagram list widget
│   │   ├── index.tsx
│   │   └── index.html
│   └── execution-list/          # Execution list widget
│       ├── index.tsx
│       └── index.html
├── package.json
├── vite.config.ts
└── tsconfig.json
```

### Running Widget Dev Server {#running-widget-dev-server}

```bash
make dev-widgets
```

This starts the Vite dev server at `http://localhost:4445` for widget development.

### Creating a New Widget {#creating-new-widget}

1. Create a new directory in `src/` (e.g., `src/my-widget/`)
2. Create `index.tsx` with your React component
3. Create `index.html` as the entry point
4. Build with `make build-widgets`

Example widget:

```tsx
// src/my-widget/index.tsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import { useWidgetProps } from '../hooks/use-widget-state';
import { WidgetLayout } from '../components/WidgetLayout';
import '../shared/index.css';

interface MyWidgetProps {
  data: any;
}

function MyWidget() {
  const props = useWidgetProps<MyWidgetProps>();

  return (
    <WidgetLayout title="My Widget">
      <div>{JSON.stringify(props)}</div>
    </WidgetLayout>
  );
}

const rootElement = document.getElementById('my-widget-root');
if (rootElement) {
  const root = createRoot(rootElement);
  root.render(<MyWidget />);
}
```

```html
<!-- src/my-widget/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Widget</title>
  <script type="module" src="./index.tsx"></script>
</head>
<body>
  <div id="my-widget-root"></div>
</body>
</html>
```

## Using Widgets in MCP Tools {#using-widgets-in-mcp-tools}

Use the `widgets.py` utilities to create widget responses:

```python
from dipeo_server.api.mcp_sdk_server.widgets import create_widget_response

@mcp_server.tool()
async def my_tool() -> list[types.TextContent]:
    """My tool with a widget."""

    data = {
        "executionId": "exec_123",
        "status": "completed",
    }

    return create_widget_response(
        widget_name="execution-results",
        data=data,
        text_summary="Execution completed successfully"
    )
```

The widget will be automatically embedded in the ChatGPT response.

## Available Widgets {#available-widgets}

### Execution Results

Displays comprehensive execution information:
- Status and metadata
- Timing information
- Execution outputs

**Usage:**
```python
create_widget_response(
    widget_name="execution-results",
    data={"executionId": "exec_123"}
)
```

### Diagram List

Browse and search available diagrams:
- Search by name/description
- Filter by format type
- View metadata

**Usage:**
```python
create_widget_response(
    widget_name="diagram-list",
    data={}
)
```

### Execution List

Monitor execution history:
- Filter by status
- View timing information
- Real-time updates

**Usage:**
```python
create_widget_response(
    widget_name="execution-list",
    data={}
)
```

## Configuration {#configuration}

### Environment Variables

- `VITE_DIPEO_GRAPHQL_URL`: GraphQL endpoint (default: `http://localhost:8000/graphql`)

Set in `apps/chatgpt-widgets/.env`:

```bash
VITE_DIPEO_GRAPHQL_URL=http://localhost:8000/graphql
```

## Troubleshooting {#troubleshooting}

### Widgets not loading

1. Verify widgets are built: `ls apps/server/static/widgets/`
2. Check server logs for errors
3. Verify ngrok is running and accessible

### Widget shows "not available"

1. Run `make build-widgets` to build widgets
2. Restart the server with `make dev-server`
3. Check that `apps/server/static/widgets/` contains HTML files

### GraphQL queries failing

1. Verify the GraphQL endpoint is accessible
2. Check the `VITE_DIPEO_GRAPHQL_URL` environment variable
3. Ensure the server is running

## Next Steps

- Add diagram rendering widget (with XYFlow visualization)
- Add diagram compiler widget (with YAML/JSON editor)
- Add real-time execution updates via WebSocket
- Add token usage metrics visualization

See [MCP Server Integration](./mcp-server-integration.md) for more details on the MCP server.
