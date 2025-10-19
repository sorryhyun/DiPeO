# ChatGPT MCP Integration (Simplified - No OAuth)

This guide shows you how to connect DiPeO to ChatGPT using the MCP (Model Context Protocol) **without OAuth authentication** for local development and testing.

> **⚠️ Security Notice**: This setup disables authentication and is only suitable for:
> - Local development on your machine
> - Testing ChatGPT integration
> - Trusted network environments
>
> For production deployments with authentication, see [MCP OAuth Authentication](./mcp-oauth-authentication.md).

## Quick Start

### 1. Configure DiPeO for No-Auth Access

Add to your `.env` file (or create one in the project root):

```bash
# Disable authentication
MCP_AUTH_ENABLED=false

# Allow ChatGPT origins
MCP_CHATGPT_ORIGINS=https://chatgpt.com,https://chat.openai.com

# Development mode
ENVIRONMENT=development
```

### 2. Start DiPeO Server

```bash
make dev-server
```

The server will start on `http://localhost:8000`

### 3. Expose via ngrok (for ChatGPT access)

ChatGPT needs HTTPS access to your local server. Use ngrok:

```bash
# Install ngrok if you haven't
# macOS: brew install ngrok/ngrok/ngrok
# Linux: see https://ngrok.com/download

# Authenticate with ngrok (first time only)
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Start ngrok tunnel
ngrok http 8000
```

You'll get a public URL like: `https://abc123.ngrok-free.app`

**🔒 RECOMMENDED: Add Password Protection**

For better security, use ngrok's built-in HTTP Basic Authentication:

```bash
# Generate a secure password
PASS=$(openssl rand -base64 16)
echo "Password: $PASS"

# Start ngrok with basic auth
ngrok http 8000 --basic-auth="dipeo:$PASS"
```

**Save the password!** You'll need it for ChatGPT configuration.

👉 **See [ChatGPT MCP with Basic Auth](./chatgpt-basic-auth-setup.md)** for complete guide on password-protected setup.

### 4. Verify MCP Server

Test the MCP info endpoint:

```bash
# Replace with your ngrok URL
curl https://abc123.ngrok-free.app/mcp/info
```

You should see:

```json
{
  "server": {
    "name": "dipeo-mcp-server",
    "version": "1.0.0"
  },
  "authentication": {
    "enabled": false,
    "required": false
  },
  "tools": [
    {
      "name": "dipeo_run",
      "description": "Execute a DiPeO diagram with optional input variables"
    }
  ]
}
```

### 5. Connect to ChatGPT

#### Option A: ChatGPT Web (Direct)

1. Go to https://chatgpt.com
2. Click on your profile → Settings → Beta Features
3. Enable "Use MCP servers"
4. Add new MCP server:
   - **Name**: DiPeO
   - **URL**: `https://your-ngrok-url.ngrok-free.app/mcp/messages`
   - **Transport**: HTTP

**If you used ngrok --basic-auth**, use this URL format instead:
```
https://dipeo:your-password@your-ngrok-url.ngrok-free.app/mcp/messages
```

#### Option B: ChatGPT Desktop (Config File)

Add to your ChatGPT configuration file:

**macOS**: `~/Library/Application Support/ChatGPT/chatgpt_config.json`
**Windows**: `%APPDATA%\ChatGPT\chatgpt_config.json`
**Linux**: `~/.config/ChatGPT/chatgpt_config.json`

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

Restart ChatGPT Desktop.

### 6. Test the Integration

In ChatGPT, try:

```
Can you list the available DiPeO diagrams?
```

ChatGPT should use the MCP tool to fetch and display available diagrams.

Then try:

```
Execute the simple_iter diagram using DiPeO
```

ChatGPT will execute the diagram and show you the results!

## Available MCP Tools

### dipeo_run

Execute a DiPeO diagram with optional input variables.

**Parameters:**
- `diagram` (required) - Diagram name or path (e.g., "simple_iter")
- `format_type` (optional) - Format type: "light", "native", or "readable" (default: "light")
- `input_data` (optional) - Input variables as JSON object
- `timeout` (optional) - Timeout in seconds (default: 300)

**Example ChatGPT prompts:**

```
Run the greeting workflow diagram
```

```
Execute simple_iter with a timeout of 60 seconds
```

```
Run my_diagram with input data: user_name = "Alice", count = 5
```

### search

Search for available DiPeO diagrams.

**Example:**

```
Search for diagrams related to "greeting"
```

### fetch

Fetch the content of a specific diagram.

**Example:**

```
Show me the contents of the simple_iter diagram
```

## Creating Diagrams for ChatGPT

You can create diagrams and make them available to ChatGPT:

### 1. Create a Light Diagram

Save as `my_workflow.light.yaml`:

```yaml
version: light
nodes:
- label: start
  type: start
  position: {x: 100, y: 100}
  trigger_mode: manual
- label: process
  type: person_job
  position: {x: 300, y: 100}
  default_prompt: Process the user input
  max_iteration: 1
  person: assistant
- label: end
  type: endpoint
  position: {x: 500, y: 100}
  file_format: txt
connections:
- {from: start, to: process, content_type: raw_text}
- {from: process, to: end, content_type: raw_text}
persons:
  assistant:
    service: openai
    model: gpt-4o-mini
    api_key_id: APIKEY_52609F
```

### 2. Push to MCP Directory

```bash
# Validate and push to MCP
dipeo compile my_workflow.light.yaml --light --push-as my_workflow
```

The diagram is now available to ChatGPT!

### 3. Use from ChatGPT

```
Execute my_workflow using DiPeO
```

## Troubleshooting

### ChatGPT can't connect

**Check CORS:**
```bash
# Test from browser console or curl
curl -X OPTIONS https://your-ngrok-url.ngrok-free.app/mcp/messages \
  -H "Origin: https://chatgpt.com" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

Should return `Access-Control-Allow-Origin: https://chatgpt.com`

**Check server logs:**
```bash
tail -f .dipeo/logs/server.log
```

### ngrok connection issues

**Free tier limitations:**
- ngrok free tier has connection limits
- URLs change when you restart ngrok
- Consider upgrading for stable URLs

**Use a static domain (ngrok paid):**
```bash
ngrok http 8000 --domain=your-static-domain.ngrok-free.app
```

### "Tool execution failed"

**Check diagram exists:**
```bash
# List available diagrams
curl https://your-ngrok-url.ngrok-free.app/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "resources/read",
    "params": {"uri": "dipeo://diagrams"}
  }'
```

**Check server logs:**
```bash
tail -f .dipeo/logs/cli.log
```

### Authentication errors (even with auth disabled)

**Verify config:**
```bash
# Check MCP info endpoint
curl https://your-ngrok-url.ngrok-free.app/mcp/info | jq '.authentication'
```

Should show:
```json
{
  "enabled": false,
  "required": false
}
```

If not, verify your `.env` file has `MCP_AUTH_ENABLED=false` and restart the server.

## Limitations

This no-auth setup has some limitations:

1. **No access control** - Anyone with your ngrok URL can execute diagrams
2. **No rate limiting** - No protection against abuse
3. **ngrok dependency** - Requires ngrok tunnel for ChatGPT access
4. **Development only** - Not suitable for production

## Upgrading to OAuth

When you're ready for production, upgrade to OAuth 2.1:

1. Set up an OAuth provider (Auth0, Keycloak, etc.)
2. Configure DiPeO with OAuth settings
3. Update `.env` to enable authentication
4. ChatGPT will automatically use OAuth flow

See [MCP OAuth Authentication](./mcp-oauth-authentication.md) for details.

## Advanced Usage

### Custom ChatGPT Origins

If you're using a custom ChatGPT deployment:

```bash
export MCP_CHATGPT_ORIGINS=https://your-custom-chatgpt.com,https://chatgpt.com
```

### IP-based Access Control

While not implemented by default, you can add middleware to restrict by IP:

```python
# In middleware.py
ALLOWED_IPS = ["127.0.0.1", "YOUR_IP_HERE"]

@app.middleware("http")
async def ip_filter(request: Request, call_next):
    if request.client.host not in ALLOWED_IPS:
        return JSONResponse({"error": "Forbidden"}, status_code=403)
    return await call_next(request)
```

### Logging MCP Requests

Enable debug logging to see all MCP requests:

```bash
export DIPEO_LOG_LEVEL=DEBUG
make dev-server
```

Check logs:
```bash
tail -f .dipeo/logs/server.log | grep MCP
```

## Complete Example Workflow

Here's a complete end-to-end example:

### Step 1: Setup Environment

```bash
# In project root
cat > .env << 'EOF'
MCP_AUTH_ENABLED=false
MCP_CHATGPT_ORIGINS=https://chatgpt.com,https://chat.openai.com
ENVIRONMENT=development
EOF
```

### Step 2: Start Services

```bash
# Terminal 1: Start DiPeO
make dev-server

# Terminal 2: Start ngrok
ngrok http 8000
```

Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### Step 3: Test Locally

```bash
# List tools
curl https://abc123.ngrok-free.app/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Execute diagram
curl https://abc123.ngrok-free.app/mcp/messages \
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

### Step 4: Connect ChatGPT

1. Add MCP server in ChatGPT settings
2. Use the ngrok URL: `https://abc123.ngrok-free.app/mcp/messages`

### Step 5: Use in ChatGPT

```
List available DiPeO diagrams
```

```
Execute the simple_iter diagram and show me the results
```

```
Create a new greeting workflow, upload it to DiPeO, and execute it
```

## Security Best Practices (Even Without OAuth)

1. **Use only on trusted networks**
2. **Don't expose sensitive data in diagrams**
3. **Rotate ngrok URLs frequently**
4. **Monitor server logs for suspicious activity**
5. **Consider IP whitelisting if deploying to cloud**
6. **Upgrade to OAuth before production use**

## See Also

- [MCP Server Integration](./mcp-server-integration.md) - General MCP server documentation
- [MCP OAuth Authentication](./mcp-oauth-authentication.md) - Production authentication setup
- [Comprehensive Light Diagram Guide](../formats/comprehensive_light_diagram_guide.md) - Creating diagrams
- [Diagram Compilation](./diagram-to-python-export.md) - Understanding diagram compilation
