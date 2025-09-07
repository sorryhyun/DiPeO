# MCP (Model Context Protocol) Integration for DiPeO

This directory contains the MCP tool integration for DiPeO, enabling MCP tools to be used through `integrated_api` nodes in diagrams.

## Overview

MCP tools are now fully integrated into DiPeO's existing `integrated_api` node system. This means you can use MCP tools (browser automation, file system operations, etc.) in the same way you use other API providers like Notion or Slack.

## Features

- **Unified Interface**: Use MCP tools through the same `integrated_api` node type
- **Manifest-Based Configuration**: Define MCP tools via YAML manifests without writing code
- **Auto-Discovery**: MCP tools are automatically discovered and registered at startup
- **Category Support**: Tools can be grouped by category (browser, filesystem, etc.)
- **Type Safety**: Full parameter validation and type checking

## Available MCP Providers

After integration, the following providers are available:

1. **`mcp`** - All MCP tools in one provider
2. **`mcp_browser`** - Browser automation tools only
3. **`mcp_filesystem`** - File system operation tools only

## Usage in Diagrams

### Browser Automation Example

```yaml
- label: Navigate to Website
  type: integrated_api
  position: {x: 250, y: 200}
  props:
    provider: mcp_browser
    operation: browser_navigate
    config:
      url: "https://example.com"
      wait_until: "networkidle"

- label: Click Button
  type: integrated_api
  position: {x: 450, y: 200}
  props:
    provider: mcp_browser
    operation: browser_click
    config:
      selector: "#submit-button"
      wait_for_selector: true
```

### File System Operations Example

```yaml
- label: Read Configuration
  type: integrated_api
  position: {x: 250, y: 200}
  props:
    provider: mcp_filesystem
    operation: file_read
    config:
      path: "config/settings.json"
      encoding: "utf-8"

- label: Write Results
  type: integrated_api
  position: {x: 450, y: 200}
  props:
    provider: mcp_filesystem
    operation: file_write
    config:
      path: "output/results.json"
      content: "{{processed_data}}"
      create_dirs: true
```

## Available Tools

### Browser Tools (`mcp_browser`)
- `browser_navigate` - Navigate to URLs
- `browser_click` - Click elements
- `browser_type` - Type text into inputs
- `browser_wait` - Wait for conditions
- `browser_snapshot` - Capture page state
- `browser_screenshot` - Take screenshots
- `browser_select_option` - Select dropdown options
- `browser_hover` - Hover over elements
- `browser_press_key` - Press keyboard keys
- `browser_get_console_logs` - Get console logs
- `browser_go_back` / `browser_go_forward` - Navigation history

### File System Tools (`mcp_filesystem`)
- `file_read` - Read file contents
- `file_write` - Write to files
- `file_delete` - Delete files
- `file_move` - Move/rename files
- `file_copy` - Copy files
- `file_exists` - Check file existence
- `file_info` - Get file metadata
- `directory_list` - List directory contents
- `directory_create` - Create directories
- `directory_delete` - Delete directories
- `file_search` - Search for files
- `file_watch` - Watch for file changes

## Adding New MCP Tools

### Method 1: Create a Manifest

Create a new YAML file in `integrations/mcp/tools/`:

```yaml
name: mcp_custom
type: mcp
version: 1.0.0
description: Custom MCP tools

tools:
  custom_tool:
    description: Description of your tool
    type: custom
    parameters:
      param1:
        type: string
        required: true
        description: Parameter description
    returns:
      type: object
      properties:
        result: string
```

### Method 2: Programmatic Registration

```python
from dipeo.infrastructure.integrations.drivers.integrated_api.providers.mcp_provider import MCPTool
from dipeo.infrastructure.integrations.drivers.integrated_api.mcp_registry import get_mcp_registry

# Define your tool
tool = MCPTool(
    name="custom_tool",
    description="My custom tool",
    parameters={
        "input": {"type": "string", "required": True}
    }
)

# Set the handler
async def custom_handler(params, **kwargs):
    # Your tool logic here
    return {"result": f"Processed: {params['input']}"}

tool.handler = custom_handler

# Register with the registry
registry = await get_mcp_registry()
registry.register_tool(tool)
```

## Architecture

The MCP integration consists of:

1. **MCPProvider** (`providers/mcp_provider.py`) - Provider implementation that handles MCP tool execution
2. **MCPToolRegistry** (`mcp_registry.py`) - Registry for discovering and managing MCP tools
3. **Tool Manifests** (`tools/*.yaml`) - YAML definitions of available MCP tools
4. **Integration Layer** - Automatic registration with IntegratedApiService

## Testing

Run the MCP provider tests:

```bash
pytest tests/infrastructure/integrations/test_mcp_provider.py
```

## Example Diagrams

See complete working examples in:
- `examples/mcp_tools/web_scraping.light.yaml` - Web scraping with browser tools
- `examples/mcp_tools/file_processing.light.yaml` - File processing with filesystem tools

## Future Enhancements

- [ ] Real MCP protocol implementation (currently using mock handlers)
- [ ] Additional tool categories (database, cloud services, etc.)
- [ ] Tool composition and chaining
- [ ] Advanced parameter schemas with JSON Schema
- [ ] Tool versioning and compatibility checks
