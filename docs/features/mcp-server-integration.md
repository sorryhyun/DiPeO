# MCP Server Integration

This guide explains how to expose DiPeO's diagram execution capabilities as an MCP (Model Context Protocol) server, allowing external LLM applications (like Claude) to execute DiPeO diagrams as tools.

## Overview {#overview}

DiPeO's MCP server integration provides:

1. **MCP Tool**: `dipeo_run` - Execute DiPeO diagrams remotely
2. **MCP Resource**: `dipeo://diagrams` - List available diagrams
3. **HTTP Transport**: Standard HTTP JSON-RPC 2.0 protocol (SDK-based implementation)
4. **ngrok Integration**: HTTPS exposure for local development
5. **Diagram Upload**: Compile and push diagrams via `dipeo compile --push-as`

**Protocol Version**: MCP 2024-11-05 (SDK-based, not legacy HTTP/SSE)

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

## Typical MCP Workflow {#typical-mcp-workflow}

The DiPeO MCP server enables the following workflow:

1. **Create/Validate Diagram**: Write a light diagram (see Light Diagram Guide)
2. **Compile & Push**: Validate and upload diagram to MCP directory using `dipeo compile --push-as`
3. **Automatic Discovery**: DiPeO MCP server scans `projects/mcp-diagrams/` and `examples/` directories
4. **Expose via Resources**: Diagrams appear in `dipeo://diagrams` resource list
5. **Execute via Tools**: MCP clients can execute diagrams using the `dipeo_run` tool

**Key Benefits:**
- **Safe by Design**: Only validated diagrams can be uploaded
- **LLM-Friendly**: Diagrams can be created and pushed from text (stdin) without file access
- **Immediate Availability**: Pushed diagrams are instantly available for execution
- **Standard Protocol**: Uses JSON-RPC 2.0 and follows MCP specification

## Quick Start {#quick-start}

### 1. Start DiPeO Server

```bash
# Start the backend server
make dev-server

# Or directly with dipeo command
dipeo --server --port 8000
```

The MCP server will be available at `http://localhost:8000/mcp/`

### 2. Test MCP Server Locally

```bash
# Check server info
curl http://localhost:8000/mcp/info

# List available tools
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'

# Execute a diagram
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "dipeo_run",
      "arguments": {
        "diagram": "simple_iter",
        "format_type": "light"
      }
    }
  }'
```

### 3. Uploading Diagrams for MCP Access {#uploading-diagrams}

DiPeO provides a convenient way to make diagrams available via the MCP server using the `dipeo compile` command with the `--push-as` flag.

#### Validation Only

Validate a diagram without uploading:

```bash
# From file
dipeo compile my_diagram.light.yaml --light

# From stdin (LLM-friendly)
echo '<diagram-content>' | dipeo compile --stdin --light
```

#### Validation + Upload

Compile, validate, and push to MCP directory in one command:

```bash
# From file
dipeo compile my_diagram.light.yaml --light --push-as my_workflow

# From stdin (LLM-friendly - no filesystem access needed!)
cat <<'EOF' | dipeo compile --stdin --light --push-as my_workflow
version: light
nodes:
- label: start
  type: start
  position: {x: 100, y: 100}
  trigger_mode: manual
- label: greet
  type: person_job
  position: {x: 300, y: 100}
  default_prompt: Say hello
  max_iteration: 1
  person: assistant
- label: end
  type: endpoint
  position: {x: 500, y: 100}
  file_format: txt
connections:
- {from: start, to: greet, content_type: raw_text}
- {from: greet, to: end, content_type: raw_text}
persons:
  assistant:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F
EOF

# Custom target directory
dipeo compile --stdin --light --push-as my_workflow --target-dir /custom/path
```

**Benefits:**
- **Safe Upload**: Only diagrams that pass compilation validation are pushed
- **No File Persistence**: LLMs can validate and push diagrams from text without filesystem access
- **Automatic MCP Integration**: Pushed diagrams are immediately available via `dipeo_run`
- **Simple Interface**: Single parameter combines filename and upload action

**Default Target Directory**: `projects/mcp-diagrams/`

The MCP server automatically scans this directory, making all pushed diagrams available for execution.

**File Extensions**: The system automatically adds the correct extension (`.yaml` for light/readable, `.json` for native) based on the format type.

**Verifying Upload**: After pushing, verify the diagram appears in the resource list:

```bash
curl -s -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"method": "resources/read", "params": {"uri": "dipeo://diagrams"}}' \
  | python -m json.tool
```

The response will include your pushed diagram in the list:

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "contents": [
      {
        "uri": "dipeo://diagrams",
        "mimeType": "text/plain",
        "text": "{\"diagrams\": [{\"name\": \"my_workflow\", \"path\": \"/path/to/projects/mcp-diagrams/my_workflow.yaml\", \"format\": \"light\"}, ...]}"
      }
    ]
  }
}
```

### 4. Expose via ngrok

#### Install ngrok

```bash
# macOS
brew install ngrok/ngrok/ngrok

# Linux
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | \
  sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null && \
  echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | \
  sudo tee /etc/apt/sources.list.d/ngrok.list && \
  sudo apt update && sudo apt install ngrok

# Windows (using Chocolatey)
choco install ngrok
```

#### Configure ngrok

1. Sign up at https://dashboard.ngrok.com/signup
2. Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
3. Configure ngrok:

```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

Or use the provided configuration file:

```bash
# Copy the example config and edit with your auth token
cp integrations/mcp/ngrok.yml.example integrations/mcp/ngrok.yml
# Edit ngrok.yml with your auth token
# Then start ngrok with config file
ngrok start dipeo-mcp --config integrations/mcp/ngrok.yml
```

#### Start ngrok Tunnel

```bash
# Simple HTTP tunnel
ngrok http 8000

# Or with custom configuration
ngrok start dipeo-mcp --config integrations/mcp/ngrok.yml
```

ngrok will display the public HTTPS URL:

```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

Your MCP server is now accessible at:
- Info: `https://abc123.ngrok-free.app/mcp/info`
- Messages: `https://abc123.ngrok-free.app/mcp/messages`

## Quick Start: ChatGPT Integration {#quick-start-chatgpt-integration}

For connecting DiPeO to ChatGPT:

👉 **See [ChatGPT MCP Integration](./chatgpt-mcp-integration.md)**

This guide shows you how to:
- Configure DiPeO for MCP access
- Use ngrok for HTTPS tunneling (with optional basic auth)
- Connect ChatGPT to your DiPeO server
- Execute diagrams from ChatGPT

**Use this approach for:**
- Local development and testing
- ChatGPT integration
- Password-protected access via ngrok basic auth

## Using with Claude Desktop {#using-with-claude-desktop}

To use the MCP server with Claude Desktop:

### 1. Configure MCP Client

Add to Claude Desktop's MCP configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "dipeo": {
      "url": "https://your-ngrok-url.ngrok-free.app/mcp/messages",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

**For local testing without ngrok** (if Claude Desktop and DiPeO server are on the same machine):

```json
{
  "mcpServers": {
    "dipeo": {
      "url": "http://localhost:8000/mcp/messages",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

Close and reopen Claude Desktop for the configuration to take effect.

### 3. Verify Connection

In Claude Desktop, check the MCP connection status. You should see the DiPeO server listed with:
- Tool: `dipeo_run`
- Resource: `dipeo://diagrams`

### 4. Use the Tool

In Claude Desktop, you can now request diagram execution in natural language:

**Example 1: Simple Execution**
```
Execute the simple_iter diagram using DiPeO
```

**Example 2: With Input Data**
```
Run the greeting_workflow diagram with input data: user_name = "Alice"
```

**Example 3: List Available Diagrams**
```
Show me what DiPeO diagrams are available
```

**Example 4: Create and Execute**
```
Create a new DiPeO workflow that greets a user, then push it to MCP and execute it
```

Claude will automatically:
1. Use the `dipeo://diagrams` resource to discover available diagrams
2. Call the `dipeo_run` tool to execute the diagram
3. Return the execution results

### 5. Advanced Usage

**Execute with Timeout:**
```
Run the data_processing diagram with a 10-minute timeout
```

**Execute with Complex Input:**
```
Execute the analysis_workflow diagram with the following inputs:
- dataset: "sales_2024"
- analysis_type: "trend"
- granularity: "monthly"
```

Claude Desktop will automatically format these requests into proper MCP tool calls.

## Complete Example Workflow {#complete-example-workflow}

Here's a complete end-to-end example of creating, uploading, and executing a diagram via MCP:

### Step 1: Create a Simple Greeting Diagram

Save this as `greeting.light.yaml`:

```yaml
version: light
nodes:
- label: start
  type: start
  position: {x: 100, y: 100}
  trigger_mode: manual
- label: greeter
  type: person_job
  position: {x: 300, y: 100}
  default_prompt: Greet the user warmly
  max_iteration: 1
  person: assistant
- label: end
  type: endpoint
  position: {x: 500, y: 100}
  file_format: txt
connections:
- {from: start, to: greeter, content_type: raw_text}
- {from: greeter, to: end, content_type: raw_text}
persons:
  assistant:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F
```

### Step 2: Compile and Push to MCP

```bash
# Validate and push in one command
dipeo compile greeting.light.yaml --light --push-as greeting_workflow

# Output:
# ✅ Diagram compiled successfully: greeting.light.yaml
#    Nodes: 3
#    Edges: 2
# ✅ Pushed diagram to: projects/mcp-diagrams/greeting_workflow.yaml
#    Available via MCP server at: dipeo://diagrams/greeting_workflow.yaml
```

### Step 3: Verify Diagram is Available

```bash
# List all available diagrams
curl -s -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"method": "resources/read", "params": {"uri": "dipeo://diagrams"}}' \
  | python -m json.tool | grep greeting_workflow

# You should see: "name": "greeting_workflow"
```

### Step 4: Execute via MCP Tool

```bash
# Execute the diagram
curl -s -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "dipeo_run",
      "arguments": {
        "diagram": "greeting_workflow",
        "format_type": "light",
        "timeout": 60
      }
    }
  }' | python -m json.tool
```

### Step 5: Execute with Input Data

```bash
# Execute with custom input variables
curl -s -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "dipeo_run",
      "arguments": {
        "diagram": "greeting_workflow",
        "format_type": "light",
        "input_data": {
          "user_name": "Alice",
          "greeting_style": "formal"
        },
        "timeout": 60
      }
    }
  }' | python -m json.tool
```

## Available Tools {#available-tools}

### dipeo_run

Execute a DiPeO diagram with optional input variables (synchronous execution).

**Parameters:**

- `diagram` (required, string) - Path or name of the diagram to execute
  - Examples: `"simple_iter"`, `"examples/simple_diagrams/simple_iter"`
- `input_data` (optional, object) - Input variables for diagram execution
  - Default: `{}`
- `format_type` (optional, string) - Diagram format type
  - Options: `"light"`, `"native"`, `"readable"`
  - Default: `"light"`
- `timeout` (optional, integer) - Execution timeout in seconds
  - Default: `300`

**Example:**

```json
{
  "name": "dipeo_run",
  "arguments": {
    "diagram": "simple_iter",
    "format_type": "light",
    "input_data": {
      "user_name": "Alice"
    },
    "timeout": 120
  }
}
```

### run_backend

Start a DiPeO diagram execution in the background and return immediately (asynchronous execution).

This tool starts diagram execution in a background process and returns a session ID that can be used with `see_result` to check status and retrieve results.

**Use Cases:**
- Long-running diagrams that exceed typical request timeouts
- Parallel execution of multiple diagrams
- Fire-and-forget workflows that don't require immediate results

**Parameters:**

- `diagram` (required, string) - Path or name of the diagram to execute
- `input_data` (optional, object) - Input variables for diagram execution
  - Default: `{}`
- `format_type` (optional, string) - Diagram format type
  - Options: `"light"`, `"native"`, `"readable"`
  - Default: `"light"`
- `timeout` (optional, integer) - Execution timeout in seconds
  - Default: `300`

**Example:**

```json
{
  "name": "run_backend",
  "arguments": {
    "diagram": "long_running_analysis",
    "format_type": "light",
    "input_data": {
      "dataset": "sales_2024"
    },
    "timeout": 600
  }
}
```

**Response:**

```json
{
  "success": true,
  "session_id": "exec_9ebb3df7180a4a7383079680c28c6028",
  "diagram": "long_running_analysis",
  "status": "started",
  "message": "Diagram execution started. Use see_result('exec_9ebb3df7180a4a7383079680c28c6028') to check status."
}
```

### see_result {#see_result}

Check status and retrieve results of a background diagram execution started with `run_backend`.

**Parameters:**

- `session_id` (required, string) - Session ID returned by `run_backend`

**Example:**

```json
{
  "name": "see_result",
  "arguments": {
    "session_id": "exec_9ebb3df7180a4a7383079680c28c6028"
  }
}
```

**Response (Running):**

```json
{
  "session_id": "exec_9ebb3df7180a4a7383079680c28c6028",
  "status": "running",
  "diagram_id": "long_running_analysis",
  "executed_nodes": ["node_0", "node_1", "node_2"],
  "started_at": "2025-10-19T14:30:07.986901"
}
```

**Response (Completed):**

```json
{
  "session_id": "exec_9ebb3df7180a4a7383079680c28c6028",
  "status": "completed",
  "diagram_id": "long_running_analysis",
  "executed_nodes": ["node_0", "node_1", "node_2", "node_3"],
  "node_outputs": {
    "node_3": "Analysis complete: Total sales increased by 15%"
  },
  "llm_usage": {
    "input_tokens": 2500,
    "output_tokens": 500,
    "total_tokens": 3000
  },
  "started_at": "2025-10-19T14:30:07.986901",
  "ended_at": "2025-10-19T14:32:15.245601"
}
```

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

## Authentication {#authentication}

The MCP server supports flexible authentication for development and production use.

### Authentication Options {#authentication-options}

1. **No Authentication** (Local Development) - Disabled authentication for rapid development
2. **ngrok Basic Auth** (Development/Testing) - Password protection via ngrok
3. **Custom Authentication** (Production) - Deploy to cloud with proper authentication

### Quick Setup {#quick-setup}

**Development (No Auth):**
```bash
export MCP_AUTH_ENABLED=false
make dev-server
```

**With ngrok Basic Auth (Recommended for Development):**
```bash
# Start DiPeO with auth disabled (ngrok handles it)
export MCP_AUTH_ENABLED=false
make dev-server

# In another terminal, start ngrok with basic auth
ngrok http 8000 --basic-auth="dipeo:your-secure-password"
```

See [ChatGPT MCP Integration](./chatgpt-mcp-integration.md) for detailed setup instructions.

## Security Considerations {#security-considerations}

### Production {#production}

- **Deploy to cloud**: Use a cloud provider with proper HTTPS and authentication
- **Enable rate limiting**: Implement request rate limiting in middleware
- **Configure CORS**: Restrict allowed origins in server configuration
- **Monitor Access**: Enable logging with `DIPEO_LOG_LEVEL=DEBUG` and set up alerting

### Development {#development}

- **Use ngrok basic auth**: Add password protection during development
- **ngrok Tunnels**: Free tier has connection limits and changing URLs
- **Don't Commit Secrets**: Use environment variables for passwords and ngrok auth tokens
- **Firewall**: Only expose server via ngrok, not directly to internet

## Troubleshooting {#troubleshooting}

### Common Issues {#common-issues}

#### 1. "Connection refused" when accessing ngrok URL {#1-connection-refused-when-accessing-ngrok-url}

**Solution**: Ensure DiPeO server is running on port 8000
```bash
# Check if server is running
curl http://localhost:8000/health

# If not, start it
make dev-server
```

#### 2. "Invalid JSON-RPC request" {#2-invalid-json-rpc-request}

**Solution**: Ensure request has correct format:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": { ... }
}
```

#### 3. "Tool execution failed" {#3-tool-execution-failed}

**Solution**: Check DiPeO logs
```bash
tail -f .dipeo/logs/cli.log
```

#### 4. "ngrok tunnel not established" {#4-ngrok-tunnel-not-established}

**Solutions**:
- Verify ngrok auth token: `ngrok config check`
- Check ngrok status: `ngrok diagnose`
- Try restarting ngrok

#### 5. "Diagram not found" {#5-diagram-not-found}

**Solution**: Use correct diagram path
```bash
# List available diagrams
curl http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "resources/read",
    "params": {"uri": "dipeo://diagrams"}
  }'
```

### Debug Mode {#debug-mode}

Enable debug logging:

```bash
export DIPEO_LOG_LEVEL=DEBUG
make dev-server
```

Check logs:
```bash
tail -f .dipeo/logs/server.log
tail -f .dipeo/logs/cli.log
```

## Advanced Usage {#advanced-usage}

### Custom Diagram Execution {#custom-diagram-execution}

Execute diagrams with complex input data:

```json
{
  "method": "tools/call",
  "params": {
    "name": "dipeo_run",
    "arguments": {
      "diagram": "examples/simple_diagrams/simple_iter",
      "format_type": "light",
      "input_data": {
        "iteration_count": 5,
        "prompt_template": "Process item {{index}}"
      },
      "timeout": 600
    }
  }
}
```

### Integration with Other MCP Clients {#integration-with-other-mcp-clients}

The MCP server follows the Model Context Protocol specification and can be used with any MCP-compatible client:

1. **Claude Desktop** (as shown above)
2. **Custom MCP Clients** (using the official MCP SDKs)
3. **Other LLM Applications** that support MCP

Example with Python MCP client using HTTP transport:

```python
import httpx
import json

# MCP server endpoint
MCP_URL = "https://your-ngrok-url.ngrok-free.app/mcp/messages"

async def call_mcp_tool(tool_name: str, arguments: dict):
    """Call an MCP tool via HTTP transport."""
    async with httpx.AsyncClient() as client:
        # Call the tool
        response = await client.post(
            MCP_URL,
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
        )
        return response.json()

# Example usage
result = await call_mcp_tool(
    "dipeo_run",
    {
        "diagram": "simple_iter",
        "format_type": "light"
    }
)
print(f"Result: {result}")
```

## Performance Considerations {#performance-considerations}

### Diagram Execution Timeouts {#diagram-execution-timeouts}

- Default timeout: 300 seconds (5 minutes)
- Configure default via environment variable: `export MCP_DEFAULT_TIMEOUT=600`
- Adjust per-request using `timeout` parameter in tool arguments

### Connection Limits {#connection-limits}

- ngrok free tier: Limited connections per minute
- Consider upgrading for production use
- Or deploy to production infrastructure

### Resource Usage {#resource-usage}

- Each diagram execution runs in the same process
- Monitor memory usage for long-running diagrams
- Consider implementing execution queuing for high load

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

## Next Steps {#next-steps}

1. **Try the Example**: Execute `simple_iter` via MCP
2. **Create Custom Diagrams**: Build diagrams for your use cases (see Light Diagram Guide)
3. **Integrate with Applications**: Use MCP server in your LLM workflows
4. **Scale to Production**: Deploy with proper authentication and monitoring

## See Also {#see-also}

- [ChatGPT MCP Integration](./chatgpt-mcp-integration.md) - ChatGPT-specific setup guide
- [Comprehensive Light Diagram Guide](../formats/comprehensive_light_diagram_guide.md) - Complete reference for writing light diagrams
- [Webhook Integration](./webhook-integration.md) - Alternative integration method
- [Diagram-to-Python Export](./diagram-to-python-export.md) - Export diagrams as standalone scripts
- [DiPeO CLI Documentation](../developer-guide.md) - CLI command reference
- [Diagram Formats](../architecture/detailed/diagram-compilation.md) - Architecture details
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/) - Official MCP spec
- [ngrok Documentation](https://ngrok.com/docs) - Tunnel setup and configuration
