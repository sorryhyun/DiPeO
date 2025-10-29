# ChatGPT MCP Integration

This guide shows you how to connect DiPeO to ChatGPT using the MCP (Model Context Protocol) for local development and testing.

> **⚠️ Security Notice**:
> - **Development Only**: This setup is designed for local development and testing
> - **Optional Authentication**: Uses ngrok's HTTP Basic Authentication for password protection
> - **Production**: For production deployments, consider deploying to a cloud provider with proper authentication and HTTPS

## Quick Start {#quick-start}

### 1. Configure DiPeO for No-Auth Access

Add to your `.env` file (or create one in the project root):

```bash
# Disable authentication
MCP_AUTH_ENABLED=false

# Allow MCP client origins (ChatGPT or other MCP clients)
MCP_CLIENT_ORIGINS=https://chatgpt.com,https://chat.openai.com

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

**Using ngrok Config File** (for persistent configuration):

Save to `ngrok.yml`:
```yaml
version: "2"
authtoken: YOUR_NGROK_AUTH_TOKEN

tunnels:
  dipeo-mcp:
    proto: http
    addr: 8000
    auth: "dipeo:your-secure-password-here"
    inspect: true
```

Then start with:
```bash
ngrok start dipeo-mcp
```

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

**Note on Special Characters:** If your password contains special characters, URL-encode them:
- `@` → `%40`
- `:` → `%3A`
- `#` → `%23`
- `&` → `%26`

Example: `p@ss:word#123` becomes `https://dipeo:p%40ss%3Aword%23123@your-ngrok-url.ngrok-free.app/mcp/messages`

**Tip:** Use alphanumeric passwords to avoid encoding issues:
```bash
openssl rand -base64 16 | tr -dc 'a-zA-Z0-9'
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

## Available MCP Tools {#available-mcp-tools}

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

## Creating Diagrams for ChatGPT {#creating-diagrams-for-chatgpt}

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

## Troubleshooting {#troubleshooting}

### Testing Basic Auth Protection {#testing-basic-auth-protection}

Before connecting ChatGPT, verify your ngrok basic auth is working:

**Test 1: Without Password (Should Fail)**
```bash
# Try accessing without credentials
curl https://abc123.ngrok-free.app/mcp/info

# Should return:
# HTTP 401 Unauthorized
# WWW-Authenticate: Basic realm="ngrok"
```

**Test 2: With Password (Should Succeed)**
```bash
# Access with credentials
curl -u "dipeo:your-password" https://abc123.ngrok-free.app/mcp/info

# Should return server info (200 OK)
```

**Test 3: Wrong Password (Should Fail)**
```bash
# Try with wrong password
curl -u "dipeo:wrong-password" https://abc123.ngrok-free.app/mcp/info

# Should return:
# HTTP 401 Unauthorized
```

### ChatGPT can't connect {#chatgpt-cant-connect}

**Error: 401 Unauthorized**

- Verify password in ngrok output matches ChatGPT configuration
- Check URL includes credentials: `https://user:pass@url`
- Ensure special characters are URL-encoded (see above)

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

### ngrok connection issues {#ngrok-connection-issues}

**Free tier limitations:**
- ngrok free tier has connection limits
- URLs change when you restart ngrok
- Consider upgrading for stable URLs

**Use a static domain (ngrok paid):**
```bash
ngrok http 8000 --domain=your-static-domain.ngrok-free.app
```

### "Tool execution failed" {#tool-execution-failed}

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

### Authentication errors (even with auth disabled) {#authentication-errors-even-with-auth-disabled}

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

## Limitations {#limitations}

This development setup has some limitations:

1. **ngrok dependency** - Free tier has connection limits and changing URLs
2. **Basic auth only** - Password-based authentication (consider upgrading ngrok for IP restrictions)
3. **No rate limiting** - No built-in protection against abuse
4. **Development focused** - For production, consider cloud deployment with proper authentication

## Production Deployment {#production-deployment}

When you're ready for production:

1. **Deploy to cloud** - Use a cloud provider with HTTPS and proper authentication
2. **Upgrade ngrok** - Get static domains and IP restrictions
3. **Add rate limiting** - Implement request rate limiting in middleware
4. **Monitor access** - Set up logging and alerting
5. **Use environment secrets** - Store credentials securely

## Advanced Usage {#advanced-usage}

### Custom ChatGPT Origins {#custom-chatgpt-origins}

If you're using a custom ChatGPT deployment:

```bash
export MCP_CHATGPT_ORIGINS=https://your-custom-chatgpt.com,https://chatgpt.com
```

### IP-based Access Control {#ip-based-access-control}

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

### Logging MCP Requests {#logging-mcp-requests}

Enable debug logging to see all MCP requests:

```bash
export DIPEO_LOG_LEVEL=DEBUG
make dev-server
```

Check logs:
```bash
tail -f .dipeo/logs/server.log | grep MCP
```

## Complete Example Workflow {#complete-example-workflow}

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

## Security Best Practices {#security-best-practices}

1. **Use only on trusted networks** during development
2. **Use ngrok basic auth** for password protection
3. **Don't expose sensitive data in diagrams**
4. **Rotate passwords and ngrok URLs frequently**
5. **Monitor server logs for suspicious activity**
6. **Deploy to cloud with proper auth** for production use

## See Also {#see-also}

- [MCP Server Integration](./mcp-server-integration.md) - General MCP server documentation
- [Comprehensive Light Diagram Guide](../formats/comprehensive_light_diagram_guide.md) - Creating diagrams
- [Diagram to Python Export](./diagram-to-python-export.md) - Export diagrams as standalone scripts
