# MCP Server Integration

This guide explains how to expose DiPeO's diagram execution capabilities as an MCP (Model Context Protocol) server, allowing external LLM applications (like Claude) to execute DiPeO diagrams as tools.

## Overview

DiPeO's MCP server integration provides:

1. **MCP Tool**: `dipeo_run` - Execute DiPeO diagrams remotely
2. **MCP Resource**: `dipeo://diagrams` - List available diagrams
3. **HTTP Transport**: Standard HTTP JSON-RPC 2.0 protocol
4. **ngrok Integration**: HTTPS exposure for local development

## Architecture

```
External LLM Client (Claude, etc.)
    ↓ (HTTPS via ngrok)
MCP Server (/mcp/messages)
    ↓
DiPeO CLI Runner
    ↓
Diagram Execution
```

### Endpoints

- **GET /mcp/info** - Server information and capabilities
- **POST /mcp/messages** - JSON-RPC 2.0 endpoint for tool calls and responses

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

### 3. Uploading Diagrams for MCP Access

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
echo 'nodes:
  - id: start
    type: start
  - id: llm
    type: llm_call
    config:
      model: gpt-5-nano-2025-08-07
      system_prompt: "You are helpful"
      user_prompt: "Hello"
  - id: end
    type: end
connections:
  - from: start
    to: llm
  - from: llm
    to: end' | dipeo compile --stdin --light --push-as my_workflow

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

## Using with Claude Desktop

To use the MCP server with Claude Desktop:

### 1. Configure MCP Client

Add to Claude Desktop's MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

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

## Authentication

DiPeO MCP server supports **OAuth 2.1 authentication** as required by the MCP specification (2025-03-26). This enables secure integration with LLM services like ChatGPT and Claude Desktop.

### Authentication Methods

The MCP server supports two authentication methods:

1. **OAuth 2.1 JWT Bearer Tokens** (Production)
   - Industry-standard OAuth 2.1 with PKCE
   - Supports external OAuth providers (Auth0, Google, GitHub, etc.)
   - Required for ChatGPT and similar services

2. **API Keys** (Development/Testing)
   - Simple authentication via `X-API-Key` header
   - Useful for development and testing

### Quick Start: Development Mode

For local development without authentication:

```bash
# Disable authentication (default: authentication is optional)
export MCP_AUTH_ENABLED=false

# Start server
make dev-server
```

### Quick Start: API Key Authentication

For simple authentication during development:

```bash
# Enable API key authentication
export MCP_AUTH_ENABLED=true
export MCP_AUTH_REQUIRED=false  # Optional authentication
export MCP_API_KEY_ENABLED=true
export MCP_API_KEYS="dev-key-123,test-key-456"

# Start server
make dev-server
```

Test with API key:

```bash
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-123" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### Production: OAuth 2.1 Setup

#### Step 1: Choose an OAuth Provider

Select an OAuth 2.1 provider:
- **Auth0** (recommended for ease of use)
- **Google OAuth**
- **GitHub OAuth**
- **Your own OAuth server**

#### Step 2: Configure OAuth Provider

Example with Auth0:

1. Create an Auth0 application
2. Configure application settings:
   - Application Type: "Machine to Machine" or "Single Page Application"
   - Allowed Callback URLs: Your MCP server URL
3. Note your credentials:
   - Domain (e.g., `your-tenant.auth0.com`)
   - Client ID
   - Client Secret (if using confidential client)

#### Step 3: Configure DiPeO MCP Server

Create `.env` file with OAuth configuration:

```bash
# Enable OAuth authentication
MCP_AUTH_ENABLED=true
MCP_AUTH_REQUIRED=true  # Require authentication for all requests

# OAuth 2.1 JWT validation
MCP_JWT_ENABLED=true
MCP_JWT_ALGORITHM=RS256
MCP_JWT_AUDIENCE=https://your-mcp-server.example.com
MCP_JWT_ISSUER=https://your-tenant.auth0.com/

# OAuth server configuration
MCP_OAUTH_SERVER_URL=https://your-tenant.auth0.com
MCP_OAUTH_JWKS_URI=https://your-tenant.auth0.com/.well-known/jwks.json

# Optional: API key fallback
MCP_API_KEY_ENABLED=true
MCP_API_KEYS=emergency-access-key-123
```

#### Step 4: Provide Public Key

For RS256 algorithm, provide the OAuth provider's public key:

**Option 1:** Inline public key
```bash
export MCP_JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----"
```

**Option 2:** Public key file
```bash
# Save public key to file
echo "-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----" > /path/to/public-key.pem

# Configure path
export MCP_JWT_PUBLIC_KEY_FILE=/path/to/public-key.pem
```

**Option 3:** JWKS URI (recommended)
```bash
# OAuth provider's JWKS endpoint (automatic key rotation)
export MCP_OAUTH_JWKS_URI=https://your-tenant.auth0.com/.well-known/jwks.json
```

#### Step 5: Test Authentication

```bash
# Get access token from OAuth provider
# (using OAuth 2.1 authorization code flow or client credentials)
ACCESS_TOKEN="your-jwt-token-here"

# Test authenticated request
curl -X POST https://your-mcp-server.example.com/mcp/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }'
```

### OAuth Metadata Discovery

The MCP server exposes OAuth metadata for automatic discovery:

```bash
# Get OAuth authorization server metadata (RFC 8414)
curl https://your-mcp-server.example.com/.well-known/oauth-authorization-server
```

This endpoint returns:
- Authorization endpoint
- Token endpoint
- Supported grant types (authorization_code, client_credentials)
- PKCE support (S256)
- JWKS URI (if configured)

### Configuration Reference

See `.env.mcp.example` for complete configuration options:

```bash
cp .env.mcp.example .env
# Edit .env with your settings
```

**Key Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_AUTH_ENABLED` | `true` | Enable/disable authentication |
| `MCP_AUTH_REQUIRED` | `false` | Require authentication (if false, optional) |
| `MCP_API_KEY_ENABLED` | `true` | Enable API key authentication |
| `MCP_API_KEYS` | - | Comma-separated list of valid API keys |
| `MCP_JWT_ENABLED` | `true` | Enable JWT validation |
| `MCP_JWT_ALGORITHM` | `RS256` | JWT algorithm (HS256, RS256, etc.) |
| `MCP_JWT_PUBLIC_KEY` | - | Public key for RS256 |
| `MCP_JWT_PUBLIC_KEY_FILE` | - | Path to public key file |
| `MCP_JWT_AUDIENCE` | - | Expected audience claim |
| `MCP_JWT_ISSUER` | - | Expected issuer claim |
| `MCP_OAUTH_SERVER_URL` | - | OAuth server base URL |
| `MCP_OAUTH_JWKS_URI` | - | JWKS endpoint for key discovery |

## Security Considerations

### Production Deployment

For production use:

1. **Enable OAuth 2.1 Authentication**
   - Use a trusted OAuth provider (Auth0, Google, etc.)
   - Set `MCP_AUTH_REQUIRED=true` to require authentication
   - Use RS256 algorithm with public key validation
   - Configure JWKS URI for automatic key rotation

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

3. **Use HTTPS**: Always use HTTPS in production
   - OAuth requires HTTPS for security
   - Use ngrok with custom domain or deploy to cloud

4. **Token Security**
   - Never include tokens in query strings
   - Use `Authorization: Bearer <token>` header
   - Validate token expiration
   - Implement token refresh if needed

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

## Performance Considerations

### Diagram Execution Timeouts

- Default timeout: 300 seconds (5 minutes)
- Configure default via environment variable: `export MCP_DEFAULT_TIMEOUT=600`
- Adjust per-request using `timeout` parameter in tool arguments

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

- [DiPeO CLI Documentation](../developer-guide.md)
- [Diagram Formats](../architecture/detailed/diagram-compilation.md)
- [Webhook Integration](./webhook-integration.md)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [ngrok Documentation](https://ngrok.com/docs)
