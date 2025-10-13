# MCP Server Integration

This guide explains how to expose DiPeO's diagram execution capabilities as an MCP (Model Context Protocol) server, allowing external LLM applications (like Claude) to execute DiPeO diagrams as tools.

## Overview

DiPeO's MCP server integration provides:

1. **MCP Tool**: `dipeo_run` - Execute DiPeO diagrams remotely
2. **MCP Resource**: `dipeo://diagrams` - List available diagrams
3. **SSE Transport**: Server-Sent Events for real-time communication
4. **ngrok Integration**: HTTPS exposure for local development

## Architecture

```
External LLM Client (Claude, etc.)
    ↓ (HTTPS via ngrok)
MCP Server (/mcp/sse + /mcp/messages)
    ↓
DiPeO CLI Runner
    ↓
Diagram Execution
```

### Endpoints

- **GET /mcp/info** - Server information and capabilities
- **GET /mcp/sse** - SSE connection endpoint for persistent connection
- **POST /mcp/messages** - JSON-RPC 2.0 endpoint for tool calls

## Quick Start

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

### 3. Expose via ngrok

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
- SSE: `https://abc123.ngrok-free.app/mcp/sse`
- Messages: `https://abc123.ngrok-free.app/mcp/messages`

## Using with Claude Desktop

To use the MCP server with Claude Desktop:

### 1. Configure MCP Client

Add to Claude Desktop's MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "dipeo": {
      "url": "https://your-ngrok-url.ngrok-free.app/mcp/sse",
      "transport": {
        "type": "sse"
      }
    }
  }
}
```

### 2. Restart Claude Desktop

Close and reopen Claude Desktop for the configuration to take effect.

### 3. Use the Tool

In Claude Desktop, you can now:

```
Execute the simple_iter diagram using DiPeO
```

Claude will use the `dipeo_run` tool to execute the diagram.

## Available Tools

### dipeo_run

Execute a DiPeO diagram with optional input variables.

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

## Available Resources

### dipeo://diagrams

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

## Security Considerations

### Production Deployment

For production use:

1. **Use Authentication**: Add basic auth or API keys
   ```yaml
   # In ngrok.yml
   auth: "username:password"
   ```

2. **Restrict Origins**: Configure CORS in DiPeO server
   ```python
   # In main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-client-domain.com"],
       allow_methods=["GET", "POST"],
       allow_headers=["*"],
   )
   ```

3. **Use Custom Domain**: Instead of ngrok free tier
   - Paid ngrok plan with custom domain
   - Or deploy to production server (AWS, GCP, etc.)

4. **Rate Limiting**: Add rate limiting middleware
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)

   @app.post("/mcp/messages")
   @limiter.limit("10/minute")
   async def mcp_messages_endpoint(request: Request):
       ...
   ```

5. **Monitor Access**: Enable logging and monitoring
   ```bash
   export DIPEO_LOG_LEVEL=DEBUG
   ```

### Local Development

For local development with ngrok:

1. **Free Tier Limitations**:
   - ngrok free tier has connection limits
   - URLs change on restart (unless using paid plan)
   - Consider ngrok's free tier acceptable use policy

2. **Firewall**: Ensure DiPeO server is not exposed to public internet except via ngrok

3. **Secrets**: Don't commit ngrok auth tokens to git
   - Use environment variables
   - Add `ngrok.yml` to `.gitignore` if it contains secrets

## Troubleshooting

### Common Issues

#### 1. "Connection refused" when accessing ngrok URL

**Solution**: Ensure DiPeO server is running on port 8000
```bash
# Check if server is running
curl http://localhost:8000/health

# If not, start it
make dev-server
```

#### 2. "Invalid JSON-RPC request"

**Solution**: Ensure request has correct format:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": { ... }
}
```

#### 3. "Tool execution failed"

**Solution**: Check DiPeO logs
```bash
tail -f .dipeo/logs/cli.log
```

#### 4. "ngrok tunnel not established"

**Solutions**:
- Verify ngrok auth token: `ngrok config check`
- Check ngrok status: `ngrok diagnose`
- Try restarting ngrok

#### 5. "Diagram not found"

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

### Debug Mode

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

## Advanced Usage

### Custom Diagram Execution

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

### Integration with Other MCP Clients

The MCP server follows the Model Context Protocol specification and can be used with any MCP-compatible client:

1. **Claude Desktop** (as shown above)
2. **Custom MCP Clients** (using the official MCP SDKs)
3. **Other LLM Applications** that support MCP

Example with Python MCP client:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to MCP server
server_params = StdioServerParameters(
    command="curl",
    args=["-N", "https://your-ngrok-url.ngrok-free.app/mcp/sse"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize
        await session.initialize()

        # List tools
        tools = await session.list_tools()
        print(f"Available tools: {tools}")

        # Call dipeo_run tool
        result = await session.call_tool(
            "dipeo_run",
            arguments={
                "diagram": "simple_iter",
                "format_type": "light"
            }
        )
        print(f"Result: {result}")
```

## Performance Considerations

### Diagram Execution Timeouts

- Default timeout: 300 seconds (5 minutes)
- Adjust based on diagram complexity
- Use `timeout` parameter in tool arguments

### Connection Limits

- ngrok free tier: Limited connections per minute
- Consider upgrading for production use
- Or deploy to production infrastructure

### Resource Usage

- Each diagram execution runs in the same process
- Monitor memory usage for long-running diagrams
- Consider implementing execution queuing for high load

## Next Steps

1. **Try the Example**: Execute `simple_iter` via MCP
2. **Create Custom Diagrams**: Build diagrams for your use cases
3. **Integrate with Applications**: Use MCP server in your LLM workflows
4. **Scale to Production**: Deploy with proper authentication and monitoring

## See Also

- [DiPeO CLI Documentation](../guides/developer-guide-diagrams.md)
- [Diagram Formats](../architecture/diagram-compilation.md)
- [Webhook Integration](./webhook-integration.md)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [ngrok Documentation](https://ngrok.com/docs)
