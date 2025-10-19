# MCP OAuth 2.1 Authentication

> **⚠️ DEPRECATED**: This OAuth 2.1 implementation has been simplified in favor of ngrok basic authentication for ease of use.
>
> **Current Setup**: DiPeO now uses **ngrok basic auth** (username:password in URL) for MCP connections. See:
> - [ChatGPT MCP with Basic Auth](./chatgpt-basic-auth-setup.md) - **Recommended setup**
> - [ChatGPT MCP Integration](./chatgpt-mcp-integration.md) - General MCP guide
>
> This document is kept for reference only and describes the **old** OAuth 2.1 implementation that has been removed.

---

This document provides comprehensive information about OAuth 2.1 authentication for the DiPeO MCP server, as required by the MCP specification (2025-03-26).

## Overview

DiPeO's MCP server implements **OAuth 2.1 authentication** to enable secure integration with LLM services like ChatGPT, Claude Desktop, and other MCP-compatible clients.

### Key Features

- ✅ **OAuth 2.1 compliant** - Follows MCP specification (2025-03-26)
- ✅ **PKCE support** - Proof Key for Code Exchange for public clients
- ✅ **Resource Server pattern** - Validates tokens from external OAuth providers
- ✅ **Metadata discovery** - RFC 8414 compliant (`.well-known/oauth-authorization-server`)
- ✅ **Flexible authentication** - Supports both OAuth JWT and API keys
- ✅ **Optional authentication** - Can be disabled or made optional for development
- ✅ **Multiple OAuth providers** - Works with Auth0, Google, GitHub, and custom providers

## Architecture

The DiPeO MCP server acts as an **OAuth 2.1 Resource Server**:

```
┌─────────────────────┐
│  MCP Client         │
│  (ChatGPT, Claude)  │
└──────────┬──────────┘
           │
           │ 1. Discover OAuth endpoints
           │    GET /.well-known/oauth-authorization-server
           │
           ▼
┌──────────────────────┐
│  DiPeO MCP Server    │◄─────────┐
│  (Resource Server)   │          │ 3. Validate JWT
└──────────┬───────────┘          │
           │                       │
           │ 2. Redirect to OAuth  │
           │                       │
           ▼                       │
┌──────────────────────┐          │
│  OAuth Provider      │          │
│  (Auth0, Google...)  │──────────┘
└──────────────────────┘
```

### Flow

1. **Discovery**: Client retrieves OAuth server metadata from DiPeO
2. **Authorization**: Client redirects user to OAuth provider for authentication
3. **Token Exchange**: Client exchanges authorization code for access token (with PKCE)
4. **API Access**: Client includes access token in requests to DiPeO MCP server
5. **Validation**: DiPeO validates JWT token using OAuth provider's public key

## Authentication Methods

### Method 1: OAuth 2.1 JWT (Production)

**Best for**: Production deployments, ChatGPT integration, enterprise use

- Industry-standard OAuth 2.1 protocol
- JWT bearer token authentication
- Supports external OAuth providers
- Automatic key rotation via JWKS
- PKCE for public clients

**Example:**

```bash
curl -X POST https://mcp.example.com/mcp/messages \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Method 2: API Key (Development)

**Best for**: Local development, testing, simple deployments

- Simple authentication via header
- No OAuth provider required
- Quick to set up

**Example:**

```bash
curl -X POST http://localhost:8000/mcp/messages \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## Quick Setup Guides

### For Development: No Authentication

```bash
# Disable authentication
export MCP_AUTH_ENABLED=false

# Start server
make dev-server

# Test (no auth required)
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### For Development: API Key

```bash
# Enable API key authentication
export MCP_AUTH_ENABLED=true
export MCP_AUTH_REQUIRED=false  # Optional auth
export MCP_API_KEY_ENABLED=true
export MCP_API_KEYS="dev-key-123"

# Start server
make dev-server

# Test with API key
curl -X POST http://localhost:8000/mcp/messages \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### For Production: OAuth 2.1 with Auth0

#### Step 1: Create Auth0 Application

1. Go to [Auth0 Dashboard](https://manage.auth0.com/)
2. Create a new application (Machine to Machine or SPA)
3. Note your domain: `your-tenant.auth0.com`
4. Configure Allowed Callback URLs

#### Step 2: Get Public Key

Download Auth0's public key:

```bash
# Get JWKS
curl https://your-tenant.auth0.com/.well-known/jwks.json

# Or get full metadata
curl https://your-tenant.auth0.com/.well-known/openid-configuration
```

#### Step 3: Configure DiPeO

Create `.env`:

```bash
# Enable OAuth 2.1
MCP_AUTH_ENABLED=true
MCP_AUTH_REQUIRED=true

# JWT validation
MCP_JWT_ENABLED=true
MCP_JWT_ALGORITHM=RS256
MCP_JWT_AUDIENCE=https://your-mcp-server.example.com
MCP_JWT_ISSUER=https://your-tenant.auth0.com/

# OAuth server
MCP_OAUTH_SERVER_URL=https://your-tenant.auth0.com
MCP_OAUTH_JWKS_URI=https://your-tenant.auth0.com/.well-known/jwks.json
```

#### Step 4: Start Server

```bash
make dev-server
```

#### Step 5: Test

```bash
# Get access token from Auth0
# (using authorization code flow or client credentials)

# Test with token
curl -X POST https://your-mcp-server.example.com/mcp/messages \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_AUTH_ENABLED` | `true` | Enable/disable authentication |
| `MCP_AUTH_REQUIRED` | `false` | Require authentication (if false, optional) |
| **API Key Settings** | | |
| `MCP_API_KEY_ENABLED` | `true` | Enable API key authentication |
| `MCP_API_KEYS` | - | Comma-separated list of valid API keys |
| **JWT Settings** | | |
| `MCP_JWT_ENABLED` | `true` | Enable JWT validation |
| `MCP_JWT_ALGORITHM` | `RS256` | JWT algorithm (HS256, RS256, ES256, etc.) |
| `MCP_JWT_SECRET` | - | Secret for HS256 algorithm |
| `MCP_JWT_PUBLIC_KEY` | - | Public key for RS256 (inline) |
| `MCP_JWT_PUBLIC_KEY_FILE` | - | Path to public key file |
| `MCP_JWT_AUDIENCE` | - | Expected audience claim |
| `MCP_JWT_ISSUER` | - | Expected issuer claim |
| **OAuth Server Settings** | | |
| `MCP_OAUTH_SERVER_URL` | - | OAuth server base URL |
| `MCP_OAUTH_AUTHORIZATION_ENDPOINT` | - | Custom authorization endpoint |
| `MCP_OAUTH_TOKEN_ENDPOINT` | - | Custom token endpoint |
| `MCP_OAUTH_REGISTRATION_ENDPOINT` | - | Custom registration endpoint |
| `MCP_OAUTH_JWKS_URI` | - | JWKS endpoint for key discovery |

### Configuration Examples

See `.env.mcp.example` for complete examples with:
- Development with API key
- Production with Auth0
- Production with Google OAuth
- Hybrid authentication (API key + JWT)

## OAuth Providers

### Auth0 (Recommended)

**Pros:**
- Easy to set up
- Excellent documentation
- Free tier available
- Automatic key rotation
- JWKS support

**Configuration:**

```bash
MCP_OAUTH_SERVER_URL=https://your-tenant.auth0.com
MCP_JWT_ISSUER=https://your-tenant.auth0.com/
MCP_OAUTH_JWKS_URI=https://your-tenant.auth0.com/.well-known/jwks.json
```

### Google OAuth

**Pros:**
- Wide adoption
- Free
- Good documentation

**Configuration:**

```bash
MCP_OAUTH_SERVER_URL=https://accounts.google.com
MCP_JWT_ISSUER=https://accounts.google.com
MCP_OAUTH_AUTHORIZATION_ENDPOINT=https://accounts.google.com/o/oauth2/v2/auth
MCP_OAUTH_TOKEN_ENDPOINT=https://oauth2.googleapis.com/token
MCP_OAUTH_JWKS_URI=https://www.googleapis.com/oauth2/v3/certs
```

### GitHub OAuth

**Pros:**
- Familiar for developers
- Free
- Easy integration

**Note:** GitHub uses OAuth 2.0 (not 2.1), so some adjustments may be needed.

### Custom OAuth Server

You can use any OAuth 2.1 compliant server:

```bash
MCP_OAUTH_SERVER_URL=https://your-oauth-server.com
MCP_JWT_ISSUER=https://your-oauth-server.com
MCP_OAUTH_JWKS_URI=https://your-oauth-server.com/.well-known/jwks.json
```

## Security Best Practices

### 1. Use HTTPS in Production

OAuth requires HTTPS for security:

```bash
# Use ngrok with HTTPS
ngrok http 8000

# Or deploy to cloud with HTTPS
```

### 2. Validate Token Claims

Always configure audience and issuer:

```bash
MCP_JWT_AUDIENCE=https://your-mcp-server.example.com
MCP_JWT_ISSUER=https://your-oauth-provider.com
```

### 3. Use JWKS for Key Rotation

Prefer JWKS URI over static public keys:

```bash
# Good: Automatic key rotation
MCP_OAUTH_JWKS_URI=https://provider.com/.well-known/jwks.json

# Less secure: Static key (manual rotation needed)
MCP_JWT_PUBLIC_KEY_FILE=/path/to/key.pem
```

### 4. Never Commit Secrets

- Add `.env` to `.gitignore`
- Use environment variables
- Rotate API keys regularly
- Use secret management services in production

### 5. Monitor Access

Enable logging and monitor for suspicious activity:

```bash
export DIPEO_LOG_LEVEL=DEBUG
make dev-server
```

Check logs:

```bash
tail -f .dipeo/logs/server.log
```

## Troubleshooting

### "Could not validate credentials"

**Causes:**
- Invalid JWT token
- Expired token
- Wrong public key
- Mismatched audience/issuer

**Solution:**

1. Check token is not expired:
   ```bash
   # Decode JWT (don't use in production, only for debugging)
   echo $TOKEN | base64 -d
   ```

2. Verify public key matches OAuth provider
3. Check audience and issuer configuration

### "JWT authentication is not enabled"

**Cause:** JWT validation is disabled

**Solution:**

```bash
export MCP_JWT_ENABLED=true
```

### "Invalid token audience"

**Cause:** Token `aud` claim doesn't match expected audience

**Solution:**

```bash
# Set correct audience
export MCP_JWT_AUDIENCE=https://your-mcp-server.example.com
```

### "OAuth authorization server not configured"

**Cause:** Metadata discovery endpoint called without OAuth server URL

**Solution:**

```bash
export MCP_OAUTH_SERVER_URL=https://your-oauth-provider.com
```

## Testing

### Test Authentication Disabled

```bash
export MCP_AUTH_ENABLED=false
make dev-server

# Should succeed without auth
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Test API Key

```bash
export MCP_AUTH_ENABLED=true
export MCP_API_KEY_ENABLED=true
export MCP_API_KEYS="test-key-123"
make dev-server

# Should succeed with API key
curl -X POST http://localhost:8000/mcp/messages \
  -H "X-API-Key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# Should fail without API key (if MCP_AUTH_REQUIRED=true)
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Test JWT

```bash
export MCP_AUTH_ENABLED=true
export MCP_JWT_ENABLED=true
export MCP_JWT_ALGORITHM=RS256
export MCP_JWT_PUBLIC_KEY_FILE=/path/to/public-key.pem
make dev-server

# Generate test JWT (using your OAuth provider)
# Then test:
curl -X POST http://localhost:8000/mcp/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'
```

### Test Metadata Discovery

```bash
curl http://localhost:8000/.well-known/oauth-authorization-server
```

Should return:

```json
{
  "issuer": "https://your-oauth-provider.com",
  "authorization_endpoint": "https://your-oauth-provider.com/authorize",
  "token_endpoint": "https://your-oauth-provider.com/token",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "client_credentials"],
  "code_challenge_methods_supported": ["S256"]
}
```

## Integration with LLM Services

### ChatGPT

ChatGPT requires OAuth 2.1 for MCP integration:

1. Configure DiPeO with OAuth as shown above
2. Expose via HTTPS (ngrok or cloud deployment)
3. Provide ChatGPT with your MCP server URL
4. ChatGPT will discover OAuth endpoints automatically

### Claude Desktop

Similar to ChatGPT, configure in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dipeo": {
      "url": "https://your-mcp-server.example.com/mcp/messages",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

Claude Desktop will automatically discover and use OAuth authentication.

## See Also

- [MCP Server Integration](./mcp-server-integration.md) - Main MCP server documentation
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization) - Official OAuth requirements
- [OAuth 2.1](https://oauth.net/2.1/) - OAuth 2.1 specification
- [RFC 8414](https://tools.ietf.org/html/rfc8414) - Authorization Server Metadata
- [RFC 7636](https://tools.ietf.org/html/rfc7636) - PKCE
