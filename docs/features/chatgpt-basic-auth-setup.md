# ChatGPT MCP Integration with Basic Authentication

Simple and secure setup for connecting ChatGPT to DiPeO MCP server using ngrok's built-in HTTP Basic Authentication.

## Overview

This setup provides:
- ✅ **Simple password protection** via ngrok
- ✅ **No code changes needed** to DiPeO
- ✅ **ChatGPT compatible** using standard HTTP Basic Auth
- ✅ **Easy to rotate** - just restart ngrok with new password

## Quick Setup

### Step 1: Configure DiPeO (No Auth)

In your `.env` file:

```bash
# Disable DiPeO's built-in auth (ngrok handles it)
MCP_AUTH_ENABLED=false

# Allow ChatGPT origins (for CORS)
MCP_CHATGPT_ORIGINS=https://chatgpt.com,https://chat.openai.com

# Development mode
ENVIRONMENT=development
```

### Step 2: Start DiPeO Server

```bash
make dev-server
```

Server runs on `http://localhost:8000`

### Step 3: Start ngrok with Basic Auth

```bash
# Choose a strong password
ngrok http 8000 --basic-auth="dipeo:your-secure-password-here"
```

**Generate a random password (recommended):**

```bash
# macOS/Linux
PASS=$(openssl rand -base64 16)
echo "Password: $PASS"
ngrok http 8000 --basic-auth="dipeo:$PASS"

# Save the password somewhere safe!
```

**ngrok output:**
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000

Basic Auth: dipeo:your-secure-password-here
```

### Step 4: Configure ChatGPT

#### Method 1: URL with Embedded Credentials (Easiest)

Use this URL format in ChatGPT MCP settings:

```
https://dipeo:your-secure-password-here@abc123.ngrok-free.app/mcp/messages
```

**Example:**
```
https://dipeo:Xy7K9mPq2NvB8@abc123.ngrok-free.app/mcp/messages
```

#### Method 2: Separate Authentication (If ChatGPT Supports)

In ChatGPT MCP configuration:

```json
{
  "mcpServers": {
    "dipeo": {
      "url": "https://abc123.ngrok-free.app/mcp/messages",
      "auth": {
        "type": "basic",
        "username": "dipeo",
        "password": "your-secure-password-here"
      }
    }
  }
}
```

### Step 5: Test Connection

In ChatGPT, try:

```
List available DiPeO diagrams
```

ChatGPT will authenticate automatically using the credentials you provided.

## Security Benefits

### What This Protects Against

✅ **Random internet users** - Can't access your ngrok URL without password
✅ **Port scanners** - ngrok URL requires authentication
✅ **Accidental URL sharing** - Password still required
✅ **Basic security** - Better than no authentication

### What This Doesn't Protect Against

❌ **If password is leaked** - Anyone with password can access
❌ **Man-in-the-middle** - Use HTTPS (ngrok provides this)
❌ **Advanced attacks** - This is basic authentication, not OAuth

## Verifying Protection

### Test 1: Without Password (Should Fail)

```bash
# Try accessing without credentials
curl https://abc123.ngrok-free.app/mcp/info

# Should return:
# HTTP 401 Unauthorized
# WWW-Authenticate: Basic realm="ngrok"
```

### Test 2: With Password (Should Succeed)

```bash
# Access with credentials
curl -u "dipeo:your-password" https://abc123.ngrok-free.app/mcp/info

# Should return server info (200 OK)
```

### Test 3: Wrong Password (Should Fail)

```bash
# Try with wrong password
curl -u "dipeo:wrong-password" https://abc123.ngrok-free.app/mcp/info

# Should return:
# HTTP 401 Unauthorized
```

## Managing Credentials

### Rotating Passwords

When you need to change the password:

1. Stop ngrok (Ctrl+C)
2. Start with new password:
   ```bash
   ngrok http 8000 --basic-auth="dipeo:new-password-here"
   ```
3. Update ChatGPT configuration with new password

### Multiple Users

ngrok supports multiple username/password combinations:

```bash
ngrok http 8000 --basic-auth="chatgpt:pass1" --basic-auth="claude:pass2"
```

### Using ngrok Config File

For persistent configuration, save to `ngrok.yml`:

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

## Troubleshooting

### ChatGPT Can't Connect

**Error: 401 Unauthorized**

**Cause:** Wrong password or credentials not configured

**Solution:**
1. Verify password in ngrok output
2. Check ChatGPT URL includes credentials: `https://user:pass@url`
3. Ensure no special characters that need URL encoding

**Special Characters in Password:**

If password contains special characters, URL-encode them:
- `@` → `%40`
- `:` → `%3A`
- `#` → `%23`
- `&` → `%26`

**Example:**
```
Password: p@ss:word#123
URL: https://dipeo:p%40ss%3Aword%23123@abc123.ngrok-free.app/mcp/messages
```

**Better:** Use alphanumeric passwords only for URLs:
```bash
# Generate alphanumeric password
openssl rand -base64 16 | tr -dc 'a-zA-Z0-9'
```

### ngrok URL Changed

ngrok free tier generates new URLs when restarted.

**Solutions:**
1. **Paid ngrok** - Get static domain: `--domain=your-name.ngrok-free.app`
2. **Auto-update script** - Script to update ChatGPT config
3. **Manual update** - Update URL in ChatGPT when ngrok restarts

### Forgot Password

**If you forgot the password:**

1. Check ngrok terminal output (shows password)
2. Stop and restart ngrok with new password
3. Update ChatGPT with new password

## Advanced Usage

### Combining with ngrok Features

```bash
# Basic auth + custom domain (ngrok paid)
ngrok http 8000 \
  --domain=my-dipeo.ngrok-free.app \
  --basic-auth="dipeo:password123"

# Basic auth + IP restrictions (ngrok paid)
ngrok http 8000 \
  --basic-auth="dipeo:password123" \
  --cidr-allow="1.2.3.4/32"

# Basic auth + request logging
ngrok http 8000 \
  --basic-auth="dipeo:password123" \
  --log=stdout \
  --log-level=info
```

### Monitoring Access

ngrok Web Interface: `http://localhost:4040`

Shows:
- All HTTP requests
- Authentication attempts
- Failed auth attempts (401s)
- Request/response details

### Emergency Access Revocation

If credentials are compromised:

1. **Immediately** stop ngrok (Ctrl+C)
2. Check ngrok web interface for suspicious requests
3. Restart with new password
4. Check DiPeO logs for executed diagrams:
   ```bash
   tail -f .dipeo/logs/server.log
   ```

## Comparison with Other Methods

| Method | Complexity | Security | ChatGPT Compatible | Cost |
|--------|-----------|----------|-------------------|------|
| **ngrok Basic Auth** | ⭐ Easy | ⭐⭐ Medium | ✅ Yes | Free |
| OAuth 2.1 | ⭐⭐⭐ Complex | ⭐⭐⭐ High | ✅ Yes | Free/Paid |
| API Keys | ⭐⭐ Medium | ⭐⭐ Medium | ⚠️ Maybe | Free |
| IP Whitelist | ⭐⭐ Medium | ⭐⭐ Medium | ❌ No (dynamic IPs) | Free |
| No Auth | ⭐ Easy | ❌ None | ✅ Yes | Free |

## Recommendations

### For Local Development
✅ **Use ngrok basic auth** - Perfect balance of simplicity and security

### For Production
❌ **Don't use basic auth** - Upgrade to OAuth 2.1 (see [MCP OAuth Authentication](./mcp-oauth-authentication.md))

### For Team Sharing
✅ **One password per person** - Easy to revoke access
```bash
ngrok http 8000 \
  --basic-auth="alice:pass1" \
  --basic-auth="bob:pass2"
```

### For Public Demo
❌ **Don't use ngrok free** - URL changes too often
✅ **Upgrade to ngrok paid** - Get static domain

## Next Steps

1. ✅ Start ngrok with basic auth
2. ✅ Get the HTTPS URL and password
3. ✅ Configure ChatGPT with URL (including credentials)
4. ✅ Test connection
5. ✅ Monitor ngrok web interface (http://localhost:4040)

## See Also

- [ChatGPT MCP Integration (No Auth)](./chatgpt-mcp-integration.md) - Simple setup without auth
- [MCP OAuth Authentication](./mcp-oauth-authentication.md) - Production-grade authentication
- [MCP Server Integration](./mcp-server-integration.md) - General MCP documentation
- [ngrok Documentation](https://ngrok.com/docs) - ngrok features and pricing
