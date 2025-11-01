# MCP Server Integration - Architecture Reference

This document provides architectural details and design decisions for DiPeO's MCP (Model Context Protocol) server implementation.

**For setup and usage instructions**, see [ChatGPT MCP Integration](./chatgpt-mcp-integration.md).

## Overview {#overview}

DiPeO's MCP server integration provides:

1. **MCP Tools** (6 tools available):
   - **Execution Tools**:
     - `dipeo_run` - Execute diagrams synchronously (in-process, fast)
     - `run_backend` - Execute diagrams asynchronously (background, returns session ID)
     - `see_result` - Retrieve results from background executions
   - **Diagram Management Tools**:
     - `compile_diagram` - Validate and persist diagrams to MCP directory (**required push**)
     - `search` - Search for diagrams by name (MCP-only feature)
     - `fetch` - Retrieve full diagram content (MCP-only feature)
2. **MCP Resource**: `dipeo://diagrams` - List available diagrams
3. **HTTP Transport**: Standard HTTP JSON-RPC 2.0 protocol (SDK-based implementation)
4. **ngrok Integration**: HTTPS exposure for local development

**Protocol Version**: MCP 2024-11-05 (SDK-based, not legacy HTTP/SSE)

**Note:** MCP tools have [intentional differences](#mcp-vs-cli-differences) from CLI commands to optimize for remote workflows. See [Implementation Patterns](#implementation-patterns) for architectural details.

## Architecture {#architecture}

```
External LLM Client (Claude, etc.)
    ↓ (HTTPS via ngrok)
MCP Server (/mcp/messages)
    ↓
DiPeO CLI Runner
    ↓
Diagram Execution
```

### Endpoints {#endpoints}

- **GET /mcp/info** - Server information and capabilities
- **POST /mcp/messages** - JSON-RPC 2.0 endpoint for tool calls and responses

## Implementation Patterns and Design Decisions {#implementation-patterns}

DiPeO's MCP server uses three distinct implementation patterns, each optimized for different use cases. Understanding these patterns helps explain why MCP tools may behave differently from their CLI counterparts.

### Pattern 1: CLI Wrapper Pattern {#cli-wrapper-pattern}

**Tools using this pattern:** `run_backend`, `see_result`, `compile_diagram`

**Implementation approach:**
```python
cmd_args = [sys.executable, "-m", "cli.entry_point", "command", ...]
proc = await asyncio.create_subprocess_exec(*cmd_args, ...)
```

**Characteristics:**
- Spawns subprocess calling DiPeO CLI commands
- Complete reuse of CLI implementation and validation logic
- Process isolation for safety
- JSON output parsing for structured results
- Ideal for commands that benefit from CLI's mature error handling

**Use cases:**
- Background execution with session management (`run_backend` → `dipeo run --background`)
- Result retrieval with formatting (`see_result` → `dipeo results`)
- Diagram compilation and persistence (`compile_diagram` → `dipeo compile --stdin --push-as`)

### Pattern 2: Shared Utility Pattern {#shared-utility-pattern}

**Tools using this pattern:** `dipeo_run`

**Implementation approach:**
```python
from ..mcp_utils import execute_diagram_shared
result = await execute_diagram_shared(diagram, input_data, ...)
```

**Characteristics:**
- Direct function calls to shared utility layer
- In-process execution (no subprocess overhead)
- Shared code between MCP and CLI contexts
- Lower latency for synchronous operations
- Ideal for performance-critical paths

**Use cases:**
- Synchronous diagram execution with immediate results
- High-frequency operations where subprocess overhead matters
- Scenarios requiring fine-grained control over execution context

### Pattern 3: MCP-Only Pattern {#mcp-only-pattern}

**Tools using this pattern:** `search`, `fetch`

**Implementation approach:**
```python
def search_diagrams(query):
    # Custom MCP-specific logic
    # Direct filesystem access and filtering
```

**Characteristics:**
- Custom implementation specific to MCP use cases
- No CLI equivalent command
- Direct filesystem and data access
- Optimized for remote LLM client workflows
- Ideal for features unique to MCP context

**Use cases:**
- Discovery and search (`search` - find diagrams by name)
- Content retrieval (`fetch` - get full diagram YAML/JSON)
- Features designed specifically for LLM-driven workflows

### MCP vs CLI: Intentional Differences {#mcp-vs-cli-differences}

While MCP tools often mirror CLI commands, some intentional differences exist to optimize for remote execution contexts:

#### 1. Mandatory Persistence in compile_diagram {#mandatory-persistence}

**CLI behavior:**
```bash
dipeo compile diagram.yaml --light              # Validate only
dipeo compile diagram.yaml --light --push-as my_workflow  # Validate + push
```

**MCP behavior:**
```python
compile_diagram(diagram_content="...", push_as="my_workflow")  # Always validates AND pushes
```

**Rationale:**
- **Remote Environment Safety**: MCP typically runs in remote/cloud contexts where diagram persistence is essential
- **Workflow Optimization**: LLM clients creating diagrams want them immediately available for execution
- **Atomic Operations**: Validation + persistence as a single atomic operation reduces round-trips
- **Intentional Design**: This is not a bug but a feature - MCP's `compile_diagram` is purpose-built for "validate and deploy" workflows

**Example use case:**
```
Claude (via MCP) → Creates diagram content → compile_diagram → Diagram persisted to projects/mcp-diagrams/ → Immediately available for dipeo_run
```

#### 2. Background Execution by Default {#background-execution}

**CLI:** Offers both sync (`dipeo run`) and async (`dipeo run --background`) modes

**MCP:** Separates into distinct tools:
- `dipeo_run` - Synchronous (wait for completion)
- `run_backend` - Asynchronous (returns session ID immediately)

**Rationale:**
- Clear separation of concerns for LLM clients
- Prevents timeout issues on long-running diagrams
- Better UX for conversational interfaces

### Tool Mapping Reference {#tool-mapping-reference}

| MCP Tool | CLI Command | Pattern | Notes |
|----------|-------------|---------|-------|
| `run_backend` | `dipeo run --background` | CLI Wrapper | Async execution with session tracking |
| `see_result` | `dipeo results` | CLI Wrapper | Retrieve execution results by session ID |
| `dipeo_run` | `dipeo run` | Shared Utility | Synchronous execution, lower latency |
| `compile_diagram` | `dipeo compile --stdin --push-as` | CLI Wrapper | **Always pushes** (vs CLI optional push) |
| `search` | *(no CLI equivalent)* | MCP-Only | Diagram discovery for LLM workflows |
| `fetch` | *(no CLI equivalent)* | MCP-Only | Retrieve diagram content for inspection |

### CLI Commands Not Available in MCP {#missing-in-mcp}

The following CLI commands are **not exposed** in MCP, as they're designed for local/interactive use:

- `dipeo export` - Generate Python scripts (local development workflow)
- `dipeo ask` - Interactive diagram generation (CLI-specific)
- `dipeo convert` - Format conversion (development tool)
- `dipeo stats` - Diagram statistics (analysis tool)
- `dipeo monitor` - Browser-based monitoring (requires browser)
- `dipeo metrics` - Performance profiling (development tool)
- `dipeo integrations` - API integration management (configuration)
- `dipeo dipeocc` - Claude Code session conversion (local workflow)

**Rationale:** These commands require interactive prompts, browser access, or local filesystem workflows that don't fit the MCP remote execution model.

## Setup and Usage {#setup-and-usage}

For complete setup instructions including:
- Starting the DiPeO server
- Configuring ngrok with basic auth
- Connecting ChatGPT
- Creating and uploading diagrams
- Testing the integration

See the **[ChatGPT MCP Integration Guide](./chatgpt-mcp-integration.md)**.

### Testing Locally {#testing-locally}

```bash
# Start server
make dev-server

# Check MCP info endpoint
curl http://localhost:8000/mcp/info

# List available tools
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Execute a diagram
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "dipeo_run",
      "arguments": {"diagram": "simple_iter", "format_type": "light"}
    }
  }'
```

### Uploading Diagrams {#uploading-diagrams}

```bash
# Validate and push to MCP directory
dipeo compile my_diagram.light.yaml --light --push-as my_workflow

# From stdin (LLM-friendly)
cat my_diagram.yaml | dipeo compile --stdin --light --push-as my_workflow
```

**Default Target**: `projects/mcp-diagrams/`

See [ChatGPT MCP Integration Guide](./chatgpt-mcp-integration.md) for complete setup instructions.

## Available Tools {#available-tools}

DiPeO exposes 6 MCP tools for diagram execution and management. For detailed parameter documentation and examples, use the MCP `tools/list` method or inspect the tool descriptions in [`server/api/mcp/tools.py`](../../server/api/mcp/tools.py).

### Execution Tools

- **`dipeo_run`** - Execute diagrams synchronously (in-process, fast)
  - Parameters: `diagram`, `input_data`, `format_type`, `timeout`
  - Returns: Immediate execution results

- **`run_backend`** - Execute diagrams asynchronously (background process)
  - Parameters: `diagram`, `input_data`, `format_type`, `timeout`
  - Returns: Session ID for status tracking
  - Use cases: Long-running diagrams, parallel execution, fire-and-forget workflows

- **`see_result`** - Retrieve results from background executions
  - Parameters: `session_id`
  - Returns: Execution status, node outputs, LLM usage statistics

### Diagram Management Tools

- **`compile_diagram`** - Validate and persist diagrams to MCP directory
  - Parameters: `diagram_content`, `push_as` (**required**), `format_type`
  - Returns: Validation results, node/edge counts
  - Note: Unlike CLI's optional `--push-as`, this tool **always pushes** (see [Mandatory Persistence](#mandatory-persistence))

- **`search`** - Search for diagrams by name (MCP-only, no CLI equivalent)
  - Parameters: `query`
  - Returns: Matching diagrams from `projects/mcp-diagrams/` and `examples/`

- **`fetch`** - Retrieve full diagram content (MCP-only, no CLI equivalent)
  - Parameters: `uri` (supports `dipeo://diagrams/name`, shorthand, or absolute path)
  - Returns: Complete YAML/JSON diagram content

### Async Execution Workflow {#async-execution-workflow}

For long-running diagrams, use the async execution pattern:

```python
# 1. Start background execution
result = await call_mcp_tool(
    "run_backend",
    {
        "diagram": "data_processing",
        "input_data": {"batch_size": 1000},
        "timeout": 600
    }
)
session_id = result["session_id"]

# 2. Poll for results periodically
import asyncio

while True:
    status = await call_mcp_tool("see_result", {"session_id": session_id})

    if status["status"] == "completed":
        print("Execution completed!")
        print(f"Results: {status.get('node_outputs', {})}")
        break
    elif status["status"] == "failed":
        print(f"Execution failed: {status.get('error')}")
        break
    else:
        print(f"Still running... {len(status.get('executed_nodes', []))} nodes completed")
        await asyncio.sleep(5)  # Check every 5 seconds
```

**CLI Alternative:**

The async execution tools use DiPeO's CLI commands under the hood:

```bash
# Start background execution
dipeo run examples/simple_diagrams/simple_iter --light --background
# Output: {"session_id": "exec_...", "status": "started"}

# Check results
dipeo results exec_9ebb3df7180a4a7383079680c28c6028
# Output: Full execution status with results
```

## Available Resources {#available-resources}

### dipeo://diagrams {#dipeodiagrams}

List available DiPeO diagrams in the examples directory.

**Example:**

```json
{
  "method": "resources/read",
  "params": {
    "uri": "dipeo://diagrams"
  }
}
```

**Response:**

```json
{
  "contents": [
    {
      "uri": "dipeo://diagrams",
      "mimeType": "application/json",
      "text": "{\"diagrams\": [{\"name\": \"simple_iter\", \"path\": \"examples/simple_diagrams/simple_iter.light.yaml\", \"format\": \"light\"}]}"
    }
  ]
}
```

## Authentication and Security {#authentication-and-security}

For authentication setup (ngrok basic auth), security best practices, and CORS configuration, see [ChatGPT MCP Integration Guide](./chatgpt-mcp-integration.md).

## Debugging {#debugging}

### Enable Debug Logging

```bash
export DIPEO_LOG_LEVEL=DEBUG
make dev-server
```

### Check Logs

```bash
tail -f .dipeo/logs/server.log  # Server logs
tail -f .dipeo/logs/cli.log      # Execution logs
```

### Verify Server is Running

```bash
curl http://localhost:8000/mcp/info
```

For troubleshooting ChatGPT connection issues, ngrok problems, and authentication errors, see [ChatGPT MCP Integration Guide - Troubleshooting](./chatgpt-mcp-integration.md#troubleshooting).

## Quick Reference {#quick-reference}

### Common MCP Endpoints {#common-mcp-endpoints}

```bash
# Get server info
curl http://localhost:8000/mcp/info

# List available tools
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'

# List available resources
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"method": "resources/list"}'

# Read diagrams resource
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"method": "resources/read", "params": {"uri": "dipeo://diagrams"}}'

# Execute diagram
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "dipeo_run",
      "arguments": {
        "diagram": "my_diagram",
        "format_type": "light"
      }
    }
  }'
```

### Common Diagram Operations {#common-diagram-operations}

```bash
# Validate diagram only
dipeo compile my_diagram.light.yaml --light

# Validate and push to MCP
dipeo compile my_diagram.light.yaml --light --push-as my_workflow

# Validate and push from stdin
cat my_diagram.light.yaml | dipeo compile --stdin --light --push-as my_workflow

# List MCP diagrams directory
ls -la projects/mcp-diagrams/

# Run diagram locally (not via MCP)
dipeo run examples/simple_diagrams/simple_iter --light --debug
```

### Environment Variables {#environment-variables}

```bash
# Disable authentication (development)
export MCP_AUTH_ENABLED=false

# Enable API key authentication
export MCP_AUTH_ENABLED=true
export MCP_API_KEY_ENABLED=true
export MCP_API_KEYS="dev-key-123,dev-key-456"

# Set default timeout
export MCP_DEFAULT_TIMEOUT=600

# Enable debug logging
export DIPEO_LOG_LEVEL=DEBUG
```

## See Also {#see-also}

**User Guides:**
- [ChatGPT MCP Integration](./chatgpt-mcp-integration.md) - Complete setup and usage guide
- [Comprehensive Light Diagram Guide](../formats/comprehensive_light_diagram_guide.md) - Creating diagrams

**Developer Resources:**
- [MCP Tools Implementation](../../server/api/mcp/tools.py) - Source code with detailed docstrings
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/) - Official MCP spec
- [DiPeO CLI Documentation](../developer-guide.md) - CLI command reference
