# DiPeOCC - Claude Code Session Converter Guide

## Overview

`dipeocc` (DiPeO Claude Code) is a powerful command-line tool that converts Claude Code session records (JSONL files) into executable DiPeO diagrams. This enables you to:

- Visualize your Claude Code conversations as workflow diagrams
- Replay and analyze past AI interactions
- Modify and enhance automated workflows
- Share reproducible AI-driven processes with your team

## How It Works

### Session Storage

Claude Code automatically saves all conversation sessions as JSONL files in:
```
~/.claude/projects/-home-soryhyun-DiPeO/
```

Each session file contains:
- User prompts and AI responses
- Tool usage (file operations, code execution, etc.)
- Timestamps and conversation flow
- Session metadata

### Conversion Process

The `dipeocc` command:
1. **Parses** JSONL session files to extract conversation events
2. **Maps** Claude Code tools to appropriate DiPeO node types
3. **Generates** executable Light format diagrams
4. **Creates** metadata for tracking and analysis

### Node Mapping Strategy

| Claude Code Tool | DiPeO Node Type | Description |
|-----------------|-----------------|-------------|
| User prompt | `start` | Initial user request |
| Assistant response | `person_job` (claude_code) | AI reasoning and responses |
| Read tool | `db` (SELECT) | File reading operations |
| Write tool | `db` (INSERT) | File creation/updates |
| Edit tool | `db` (UPDATE) | File modifications |
| Bash tool | `code_job` (bash) | Command execution |
| TodoWrite | `db` (WRITE) | Task tracking updates |
| Glob/Grep | `code_job` | Search operations |
| WebFetch | `api_job` | Web content retrieval |

## Quick Start

### List Available Sessions

```bash
# Show recent sessions with summary
dipeocc list

# Show more sessions
dipeocc list --limit 100
```

Output:
```
📋 Listing recent Claude Code sessions (limit: 50)
   Directory: /home/user/.claude/projects/-home-user-DiPeO

  1. Session: 03070ee3-c2d8-488b-a11e-ce8d5ac1f1ec
     Modified: 2025-09-18 14:32:10
     Duration: 45 minutes
     Events: 234 total (12 user, 12 assistant)
     Tools: Read:25, Edit:8, Bash:5, TodoWrite:3
     File: 03070ee3-c2d8-488b-a11e-ce8d5ac1f1ec.jsonl
```

### Convert a Session

```bash
# Convert the latest session
dipeocc convert --latest

# Convert specific session
dipeocc convert 03070ee3-c2d8-488b-a11e-ce8d5ac1f1ec

# Convert and execute immediately
dipeocc convert --latest --auto-execute

# Convert with optimizations
dipeocc convert --latest --merge-reads --simplify
```

### Monitor for New Sessions

```bash
# Watch for new sessions and convert automatically
dipeocc watch

# Watch with custom interval and auto-execution
dipeocc watch --interval 60 --auto-execute
```

### Analyze Session Statistics

```bash
# Show detailed session statistics
dipeocc stats 03070ee3-c2d8-488b-a11e-ce8d5ac1f1ec
```

Output includes:
- Session overview (events, duration, messages)
- Tool usage breakdown
- File operations summary
- Bash commands executed

## Output Structure

Generated diagrams are organized as:

```
projects/claude_code/
├── sessions/
│   ├── 03070ee3-c2d8-488b-a11e-ce8d5ac1f1ec/
│   │   ├── diagram.light.yaml    # Executable diagram
│   │   ├── metadata.json         # Session metadata
│   │   └── analysis.json         # Usage statistics
│   └── 6e9c0a5a-c073-4684-bbc6-ab4d2bacfc4d/
│       ├── diagram.light.yaml
│       └── metadata.json
└── latest.light.yaml → sessions/{latest}/diagram.light.yaml
```

## Advanced Usage

### Custom Output Directory

```bash
# Save to specific location
dipeocc convert --latest \
  --output-dir projects/my_workflows \
  --format light
```

### Optimization Flags

```bash
# Merge consecutive file reads for cleaner diagrams
dipeocc convert session-id --merge-reads

# Simplify by removing intermediate results
dipeocc convert session-id --simplify

# Combine optimizations
dipeocc convert --latest --merge-reads --simplify
```

### Different Output Formats

```bash
# Light format (default) - human-readable YAML
dipeocc convert --latest --format light

# Native format - standard JSON
dipeocc convert --latest --format native

# Readable format - verbose YAML
dipeocc convert --latest --format readable
```

## Executing Generated Diagrams

### Direct Execution

```bash
# Run a converted diagram
dipeo run projects/claude_code/sessions/{session-id}/diagram.light.yaml --debug

# Run the latest converted diagram
dipeo run projects/claude_code/latest.light.yaml --debug
```

### Auto-Execution

```bash
# Convert and execute in one command
dipeocc convert --latest --auto-execute

# Watch and auto-execute new sessions
dipeocc watch --auto-execute
```

## Example Workflow

### 1. Interactive Development Session

```bash
# Start a Claude Code session to develop a feature
# ... interact with Claude Code ...

# After the session, convert it to a diagram
dipeocc convert --latest

# Review the generated diagram
cat projects/claude_code/latest.light.yaml

# Execute to replay the workflow
dipeo run projects/claude_code/latest.light.yaml --debug
```

### 2. Continuous Monitoring

```bash
# In one terminal, watch for new sessions
dipeocc watch --interval 30

# In another terminal, work with Claude Code
# Each session automatically converts to a diagram
```

### 3. Batch Processing

```bash
# List all sessions
dipeocc list --limit 100 > sessions.txt

# Convert multiple sessions (example script)
for session_id in $(grep "Session:" sessions.txt | awk '{print $3}'); do
  dipeocc convert $session_id
done
```

## Diagram Structure

A typical converted diagram includes:

```yaml
version: light

persons:
  Claude Code Agent:
    service: claude-code
    model: claude-code-custom
    max_turns: 10

nodes:
  - label: User Request
    type: start
    position: {x: 100, y: 100}
    props:
      trigger_mode: manual
      custom_data:
        request: "Original user prompt..."

  - label: AI Analysis
    type: person_job
    position: {x: 300, y: 100}
    props:
      person: Claude Code Agent
      default_prompt: "{{user_request}}"

  - label: Read File
    type: db
    position: {x: 500, y: 100}
    props:
      operation: read
      sub_type: file
      source_details: "path/to/file.py"

  - label: Execute Command
    type: code_job
    position: {x: 700, y: 100}
    props:
      language: bash
      code: "npm test"

connections:
  - from: User Request
    to: AI Analysis
  - from: AI Analysis
    to: Read File
  - from: Read File
    to: Execute Command
```

## Best Practices

### 1. Session Management

- **Regular Conversion**: Convert important sessions promptly to preserve workflows
- **Use Metadata**: Check `metadata.json` for session context and statistics
- **Clean Up**: Periodically archive old session files and diagrams

### 2. Optimization Strategy

- **Use `--merge-reads`** when sessions have many consecutive file reads
- **Use `--simplify`** for overview diagrams without detailed results
- **Keep originals** before applying heavy optimizations

### 3. Workflow Enhancement

After conversion, you can:
- **Edit the diagram** to add error handling
- **Insert additional nodes** for logging or notifications
- **Modify prompts** to improve AI responses
- **Add parallel processing** for better performance

### 4. Team Collaboration

- **Share diagrams** via version control
- **Document sessions** with meaningful names
- **Create templates** from successful patterns
- **Build libraries** of reusable workflows

## Troubleshooting

### Session Not Found

```bash
# Check session directory
ls -la ~/.claude/projects/-home-*/

# Verify session ID format
dipeocc list | grep "your-session-id"
```

### Conversion Errors

```bash
# Enable debug mode
dipeocc convert --latest --debug

# Check logs
cat .logs/server.log
```

### Execution Issues

```bash
# Validate generated diagram
dipeo stats projects/claude_code/latest.light.yaml

# Run with debug output
dipeo run projects/claude_code/latest.light.yaml --debug
```

## Architecture Details

### Session Parser
- **Location**: `dipeo/infrastructure/claude_code/session_parser.py`
- **Functionality**: Parses JSONL files and extracts structured events

### Session Translator
- **Location**: `dipeo/domain/diagram/cc_translate/`
- **Functionality**: Maps Claude Code events to DiPeO nodes and connections
- **Components**:
  - `translator.py`: Main orchestration logic
  - `node_builders.py`: Node creation for different tool types
  - `diff_utils.py`: Enhanced diff generation with full-context support
  - `text_utils.py`: Text extraction and unescaping

### Enhanced Diff Generation
- **High-Fidelity Diffs**: When available, uses complete original file content from `toolUseResult` payloads to generate accurate unified diffs
- **Fallback Strategy**: Gracefully degrades to snippet-based diffs when full context is unavailable
- **YAML-Optimized Output**: Normalizes diff strings for clean YAML literal blocks without escaped newlines
- **Multi-Edit Support**: Combines multiple edits into single unified diff when original content is available
- **Benefits**:
  - Accurate context lines in diffs
  - Clean, readable YAML output
  - Better end-to-end diff application without manual fixes

### CLI Command
- **Location**: `apps/cli/src/dipeo_cli/commands/claude_code_command.py`
- **Functionality**: Orchestrates conversion process and file management


## Related Documentation

- [Claude Code Integration Guide](../integrations/claude-code.md) - Using Claude Code as an LLM provider
- [Light Diagram Format](../formats/comprehensive_light_diagram_guide.md) - Understanding generated diagrams
- [CLI Reference](../../apps/cli/README.md) - Complete CLI documentation
- [DiPeO Architecture](../architecture/overall_architecture.md) - System overview
