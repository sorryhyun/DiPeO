# Claude Code Integration

DiPeO now supports Claude Code SDK as an LLM provider, enabling integration with Anthropic's Claude Code for advanced AI agent capabilities.

## Installation

### Prerequisites

1. Install the Python SDK:
```bash
pip install claude-code-sdk
```

2. Install the required npm package globally:
```bash
npm install -g @anthropic-ai/claude-code
```

## Configuration

### API Key Setup

Use your Anthropic API key (same as regular Claude):
```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

### DiPeO Configuration

In your diagram YAML files, configure a person to use Claude Code:

```yaml
people:
  - id: claude_code_agent
    name: Claude Code Agent
    description: An agent powered by Claude Code SDK
    llm_config:
      service: claude-code
      model: claude-code
      api_key_id: anthropic_api_key
      system_prompt: "You are a helpful assistant"
      max_turns: 5  # Maximum conversation turns
```

## Supported Models

- `claude-code` - Default Claude Code model
- `claude-code-sdk` - Alias for Claude Code

## Service Aliases

The following service names are recognized:
- `claude-code` (primary)
- `claude-sdk`
- `claude_code`

## Example Usage

```yaml
name: Claude Code Example
diagram:
  nodes:
    - id: task
      type: PersonJob
      person_id: claude_agent
      inputs:
        prompt: "Analyze system performance"
      outputs:
        result: analysis

people:
  - id: claude_agent
    name: Performance Analyzer
    llm_config:
      service: claude-code
      model: claude-code
      api_key_id: anthropic_api_key
      system_prompt: "You are a performance engineer"
      max_turns: 3
```

## Key Differences from Regular Claude

1. **Streaming-First Architecture**: Claude Code uses streaming responses by default
2. **Context Manager Pattern**: Client lifecycle managed via async context managers
3. **Multi-Turn Support**: Built-in conversation management with configurable max turns
4. **Different API Pattern**: Uses `ClaudeSDKClient` instead of traditional API clients

## Limitations

- Tool/function calling is not yet supported
- Response API pattern is not available
- Models list API is not available (returns predefined list)

## Running Diagrams

Execute diagrams with Claude Code agents:
```bash
dipeo run examples/test_claude_code --light --debug
```

## Troubleshooting

### Import Error
If you see `ImportError: claude-code-sdk is required`:
```bash
pip install claude-code-sdk
```

### Node CLI Not Found
If the Claude Code CLI is not found:
```bash
npm install -g @anthropic-ai/claude-code
```

### Rate Limiting
The adapter includes automatic retry logic with exponential backoff for rate limit errors.