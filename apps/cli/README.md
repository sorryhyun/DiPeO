# DiPeO CLI

## Overview

The `dipeo` CLI is the **command-line interface** for executing, converting, monitoring, and analyzing DiPeO diagrams. It provides a minimal, focused interface that orchestrates the backend server and handles diagram operations through clean command patterns.

## Architecture

### CLI Structure

```
┌─────────────────────────────────┐
│         dipeo CLI               │
│   (Entry Point & Orchestrator)  │
└────────────┬────────────────────┘
             │
    ┌────────▼────────┐
    │  Server Manager │ ◄── Auto-starts backend
    └────────┬────────┘
             │
┌────────────▼────────────────────┐
│        Commands                 │
├──────────────────────────────────┤
│ RunCommand     │ Execute diagrams│
│ ConvertCommand │ Format conversion│
│ MetricsCommand │ Performance data │
│ UtilsCommand   │ Stats & monitor  │
└──────────────────────────────────┘
             │
    ┌────────▼────────┐
    │  Backend Server │ ◄── GraphQL API
    └─────────────────┘
```

### Key Components

```
apps/cli/
├── pyproject.toml           # Package configuration
└── src/dipeo_cli/
    ├── __main__.py          # Entry point & argument parsing
    ├── server_manager.py    # Backend server lifecycle
    └── commands/
        ├── base.py          # Shared utilities (DiagramLoader)
        ├── run_command.py   # Diagram execution
        ├── convert_command.py # Format conversion
        ├── metrics_command.py # Performance metrics
        └── utils_command.py # Stats & monitoring
```

## Installation

The CLI is installed as the `dipeo` command when you set up the project:

```bash
# From project root
make install

# Or directly
cd apps/cli
pip install -e .
```

## Command Reference

### dipeo ask

Generate a diagram from natural language and optionally run it:

```bash
# Generate diagram from natural language
dipeo ask --to "create a workflow that analyzes sentiment from CSV data"

# Generate and immediately execute
dipeo ask --to "fetch weather data and create a summary" --and-run

# With custom timeouts
dipeo ask --to "complex data pipeline" --timeout 120 --run-timeout 600
```

**Options:**
- `--to`: Natural language description of what to create
- `--and-run`: Automatically run the generated diagram
- `--debug`: Enable debug output
- `--timeout N`: Generation timeout in seconds (default: 90)
- `--run-timeout N`: Execution timeout for generated diagram (default: 300)
- `--browser`: Open browser when running generated diagram

### dipeo run

Execute a diagram with real-time monitoring:

```bash
# Basic execution
dipeo run diagrams/example.yaml

# With format specification
dipeo run my_diagram --light
dipeo run my_diagram --native
dipeo run my_diagram --readable

# With input variables
dipeo run workflow --input-data '{"model": "gpt-4", "temperature": 0.7}'
dipeo run workflow --inputs variables.json

# Debug mode with browser monitoring
dipeo run diagram.yaml --debug --browser

# Custom timeout
dipeo run long_running --timeout 600

# Legacy monitoring (deprecated)
dipeo run diagram --legacy
```

**Options:**
- `--light`: Use light YAML format
- `--native`: Use native JSON format
- `--readable`: Use readable YAML format
- `--debug`: Enable debug output
- `--browser`: Open browser monitor
- `--timeout N`: Execution timeout in seconds (default: 300)
- `--input-data JSON`: Inline JSON input variables
- `--inputs FILE`: Input variables from JSON file
- `--legacy`: Use legacy monitoring architecture

### dipeo convert

Convert between diagram formats:

```bash
# Auto-detect formats from extensions
dipeo convert input.light.yaml output.native.json

# Explicit format specification
dipeo convert diagram.yaml diagram.json --from-format light --to-format native

# Format options: native, light, readable
dipeo convert old.json new.yaml --to-format readable
```

**Supported Formats:**
- **native**: Standard JSON format (`.native.json`)
- **light**: Simplified YAML format (`.light.yaml`)
- **readable**: Human-friendly YAML format (`.readable.yaml`)

### dipeo stats

Display diagram statistics:

```bash
dipeo stats diagrams/workflow.yaml

# Output includes:
# - Node count by type
# - Connection count
# - Complexity metrics
# - Input/output analysis
```

### dipeo monitor

Open browser-based execution monitor:

```bash
# Open monitor for all executions
dipeo monitor

# Open monitor for specific diagram
dipeo monitor my_diagram
```

### dipeo metrics

Display execution performance metrics:

```bash
# Latest execution metrics
dipeo metrics

# Specific execution
dipeo metrics exec_123456

# Metrics for all executions of a diagram
dipeo metrics --diagram workflow.yaml

# Bottleneck analysis only
dipeo metrics --bottlenecks

# Optimization suggestions
dipeo metrics --optimizations

# JSON output for processing
dipeo metrics --json
```

### dipeo integrations

Manage API integrations and providers:

```bash
# Initialize integrations workspace
dipeo integrations init
dipeo integrations init --path ./my-integrations

# Validate provider manifests
dipeo integrations validate
dipeo integrations validate --provider my-api

# Import OpenAPI specification
dipeo integrations openapi-import api-spec.yaml --name my-api

# Test integration provider
dipeo integrations test my-provider --operation get_user

# Claude Code TODO synchronization
dipeo integrations claude-code --sync-mode auto --watch-todos
```

**Subcommands:**
- `init`: Initialize integrations workspace
  - `--path PATH`: Path to initialize (default: ./integrations)

- `validate`: Validate provider manifests
  - `--path PATH`: Path to integrations directory
  - `--provider NAME`: Validate specific provider only

- `openapi-import`: Import OpenAPI specification
  - `openapi_path`: Path to OpenAPI spec file
  - `--name`: Provider name (required)
  - `--output PATH`: Output directory
  - `--base-url URL`: Override base URL

- `test`: Test integration provider
  - `provider`: Provider name to test
  - `--operation NAME`: Specific operation to test
  - `--config JSON`: Test configuration
  - `--record`: Record test for replay
  - `--replay`: Replay recorded test

- `claude-code`: Manage Claude Code TODO synchronization
  - `--watch-todos`: Enable TODO monitoring
  - `--sync-mode MODE`: Synchronization mode (off/manual/auto/watch)
  - `--output-dir PATH`: Output directory for diagrams
  - `--auto-execute`: Automatically execute generated diagrams
  - `--debounce N`: Debounce time in seconds (default: 2.0)
  - `--timeout N`: Timeout for monitoring

### dipeocc

Convert Claude Code sessions to DiPeO diagrams:

```bash
# List recent Claude Code sessions
dipeocc list
dipeocc list --limit 100

# Convert the latest session to a diagram
dipeocc convert --latest
dipeocc convert --latest --auto-execute

# Convert a specific session by ID
dipeocc convert 7869d79f-e6ab-43f3-9919-2fe3b86f327b
dipeocc convert session-id --output-dir projects/my_sessions

# Watch for new sessions and convert automatically
dipeocc watch
dipeocc watch --interval 60 --auto-execute

# Show detailed session statistics
dipeocc stats 7869d79f-e6ab-43f3-9919-2fe3b86f327b
```

**Subcommands:**
- `list`: List recent Claude Code sessions from `~/.claude/projects/`
  - `--limit N`: Maximum number of sessions to list (default: 50)

- `convert`: Convert a session to a DiPeO diagram
  - `session_id`: Session ID to convert (or use `--latest`)
  - `--latest`: Convert the most recent session
  - `--output-dir PATH`: Output directory (default: `projects/claude_code`)
  - `--format TYPE`: Output format - light/native/readable (default: light)
  - `--auto-execute`: Automatically execute the generated diagram
  - `--merge-reads`: Merge consecutive file read operations
  - `--simplify`: Remove intermediate tool results

- `watch`: Monitor for new sessions and convert automatically
  - `--interval N`: Check interval in seconds (default: 30)
  - `--auto-execute`: Automatically execute new diagrams

- `stats`: Show detailed session statistics
  - `session_id`: Session ID to analyze

**Output Structure:**
```
projects/claude_code/
├── sessions/
│   ├── {session_id}/
│   │   ├── diagram.light.yaml    # Generated diagram
│   │   └── metadata.json         # Session metadata
│   └── ...
└── latest.light.yaml -> sessions/{latest_id}/diagram.light.yaml
```

**Node Mapping:**
Claude Code tools are mapped to DiPeO nodes as follows:
- User prompts → Start nodes
- Assistant responses → Person job nodes (claude_code)
- Read tool → DB nodes (SELECT)
- Write tool → DB nodes (INSERT)
- Edit tool → DB nodes (UPDATE)
- Bash tool → Code job nodes (language=bash)
- TodoWrite → DB nodes (task tracking)

## Core Components

### 1. DiPeOCLI Class (`__main__.py`)

Main orchestrator that coordinates commands:

```python
class DiPeOCLI:
    """Minimal DiPeO CLI - thin orchestration layer."""
    
    def __init__(self):
        self.server = ServerManager()
        
        # Initialize command handlers
        self.run_command = RunCommand(self.server)
        self.convert_command = ConvertCommand()
        self.metrics_command = MetricsCommand(self.server)
        self.utils_command = UtilsCommand()
    
    def run(self, diagram: str, debug: bool = False, ...):
        """Execute diagram through server"""
        return self.run_command.execute(...)
```

### 2. ServerManager (`server_manager.py`)

Manages backend server lifecycle:

```python
class ServerManager:
    """Manages the backend server process."""
    
    def start(self, debug: bool = False) -> bool:
        """Start server if not running"""
        if self.is_running():
            return True
        
        # Start subprocess
        self.process = subprocess.Popen(
            ["python", "main.py"],
            cwd=server_path,
            env={"LOG_LEVEL": "DEBUG" if debug else "INFO"}
        )
        
        # Wait for ready
        return self._wait_for_ready()
    
    def execute_diagram(self, diagram_id: str, ...) -> dict:
        """Execute via GraphQL API"""
        return self._graphql_request(EXECUTE_MUTATION, variables)
```

### 3. Command Pattern

All commands follow consistent pattern:

```python
class RunCommand:
    """Command for running diagrams."""
    
    def __init__(self, server: ServerManager):
        self.server = server
        self.loader = DiagramLoader()
    
    def execute(self, diagram: str, **options) -> bool:
        """Execute the command."""
        # 1. Validate and prepare
        diagram_path = self.loader.resolve_diagram_path(diagram)
        
        # 2. Ensure server running
        if not self.server.start():
            return False
        
        # 3. Execute operation
        result = self.server.execute_diagram(diagram_path)
        
        # 4. Handle results
        return self._process_result(result)
```

### 4. DiagramLoader (`base.py`)

Shared utilities for diagram handling:

```python
class DiagramLoader:
    """Utilities for loading and resolving diagrams."""
    
    def resolve_diagram_path(self, 
                           diagram: str, 
                           format_type: str | None) -> str:
        """Resolve diagram path with format suffix"""
        # Handles: my_diagram --light → examples/my_diagram.light.yaml
    
    def load_diagram(self, file_path: str) -> dict:
        """Load diagram from JSON or YAML"""
        return yaml.safe_load(content) or json.loads(content)
    
    def get_diagram_format(self, path: str) -> str:
        """Detect format from filename"""
        # .native.json → "native"
        # .light.yaml → "light"
```

## Execution Flow

### Running a Diagram

```
1. User runs: dipeo run workflow.yaml --debug
                    │
2. CLI parses args  ▼
   ┌─────────────────────────┐
   │ Resolve diagram path    │
   │ Load input variables    │
   └──────────┬──────────────┘
              │
3. Start server ▼
   ┌─────────────────────────┐
   │ Check if running        │
   │ Start subprocess if not │
   │ Wait for health check   │
   └──────────┬──────────────┘
              │
4. Execute via API ▼
   ┌─────────────────────────┐
   │ GraphQL mutation        │
   │ Get execution ID        │
   └──────────┬──────────────┘
              │
5. Monitor progress ▼
   ┌─────────────────────────┐
   │ Poll for status         │
   │ Display progress        │
   │ Show results            │
   └─────────────────────────┘
```

## Input Variables

### From File

```json
// variables.json
{
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000,
  "system_prompt": "You are a helpful assistant"
}
```

```bash
dipeo run workflow --inputs variables.json
```

### Inline JSON

```bash
dipeo run workflow --input-data '{
  "model": "gpt-4",
  "temperature": 0.7
}'
```

### In Diagram

Input variables are passed to Start nodes:

```yaml
# workflow.light.yaml
nodes:
  - id: start
    type: Start
    properties:
      default_values:
        model: "{{ model }}"  # From input variables
        prompt: "Default prompt"
```

## Format Detection

The CLI intelligently detects diagram formats:

### By Extension

- `.native.json` → native format
- `.light.yaml` → light format
- `.readable.yaml` → readable format
- `.json` → native format (default)
- `.yaml` → light format (default)

### By Flag

```bash
dipeo run my_diagram --light   # Looks for my_diagram.light.yaml
dipeo run my_diagram --native  # Looks for my_diagram.native.json
```

### Search Paths

The CLI searches for diagrams in the following order:

1. Exact path if exists
2. `projects/` directory (default, searched first)
3. `files/` directory (backward compatibility, searched second)

When no prefix is provided:
- `dipeo run codegen/diagrams/my_diagram` → searches `projects/codegen/diagrams/my_diagram` first
- Falls back to `files/codegen/diagrams/my_diagram` if not found

With explicit prefix:
- `dipeo run projects/...` → searches only in `projects/`
- `dipeo run files/...` → searches only in `files/`

## Server Integration

### Automatic Server Management

The CLI automatically manages the backend server:

```python
# Server starts automatically
dipeo run diagram.yaml  # Starts server if needed

# Server stops on:
# - Execution completion
# - Ctrl+C interrupt
# - Error conditions
# - Timeout
```

### GraphQL Communication

All operations use GraphQL API:

```graphql
mutation ExecuteDiagram(
  $diagramId: ID
  $variables: JSON
  $useUnifiedMonitoring: Boolean
) {
  execute_diagram(input: {
    diagram_id: $diagramId
    variables: $variables
    use_unified_monitoring: $useUnifiedMonitoring
  }) {
    execution_id
    monitor_url
  }
}
```

## Browser Integration

### Monitor Mode

```bash
dipeo run diagram --browser
# Opens: http://localhost:3000/?monitor=true
```

The frontend automatically:
- Detects CLI executions
- Shows real-time progress
- Displays node outputs
- Visualizes execution flow

### Standalone Monitor

```bash
dipeo monitor
# Opens browser for monitoring all executions
```

## Error Handling

### Graceful Shutdown

```python
try:
    # Execute diagram
    cli.run(diagram)
except KeyboardInterrupt:
    print("Interrupted by user")
    cli.server.stop()  # Cleanup
    sys.exit(1)
```

### Timeout Handling

```python
if elapsed > timeout:
    print(f"Execution timed out after {timeout}s")
    self.server.stop()
    return False
```

### Server Failures

```python
if not self.server.start():
    print("Failed to start server")
    # Check logs in .logs/server.log
    return False
```

## Performance Features

### Metrics Collection

The CLI tracks:
- Node execution times
- Memory usage
- Token consumption
- Error rates
- Bottlenecks

### Optimization Suggestions

```bash
dipeo metrics --optimizations

# Suggests:
# - Parallel execution opportunities
# - Caching possibilities
# - Prompt optimization
# - Node consolidation
```

## Configuration

### Environment Variables

```bash
# Server configuration
export DIPEO_BASE_DIR=/path/to/project
export DIPEO_PORT=8000
export LOG_LEVEL=DEBUG

# Execution defaults
export DIPEO_DEFAULT_TIMEOUT=300
export DIPEO_DEFAULT_MODEL=gpt-4
```

### Debug Mode

```bash
dipeo run diagram --debug

# Enables:
# - Verbose logging
# - Stack traces
# - Server debug output
# - Detailed error messages
```

## Platform Support

### Windows

Special handling for encoding:
```python
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    os.environ["PYTHONIOENCODING"] = "utf-8"
```

### Unix/Linux/macOS

Standard subprocess and signal handling.

## Testing

### Unit Tests

```python
def test_diagram_loader():
    loader = DiagramLoader()
    path = loader.resolve_diagram_path("example", "light")
    assert path.endswith(".light.yaml")
```

### Integration Tests

```python
def test_full_execution():
    cli = DiPeOCLI()
    success = cli.run("test.yaml", debug=True)
    assert success
```

## Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
lsof -i :8000

# Check logs
cat .logs/server.log

# Try different port
export DIPEO_PORT=8001
```

### Execution Hangs

```bash
# Use debug mode
dipeo run diagram --debug

# Set shorter timeout
dipeo run diagram --timeout 30
```

### Format Conversion Fails

```bash
# Validate input format
dipeo stats input.yaml

# Try explicit formats
dipeo convert in.yaml out.json --from-format light --to-format native
```

## Best Practices

1. **Use Input Files**: For complex variables, use JSON files
2. **Set Timeouts**: Prevent runaway executions
3. **Enable Debug**: For development and troubleshooting
4. **Monitor Executions**: Use `--browser` for visual feedback
5. **Check Metrics**: Identify performance bottlenecks

## Future Enhancements

- **Parallel Execution**: Run multiple diagrams concurrently
- **Watch Mode**: Auto-run on diagram changes
- **Remote Execution**: Connect to remote servers
- **Export Results**: Save execution results to files
- **Diagram Validation**: Pre-execution validation
- **Interactive Mode**: Step-through debugging
- **Plugin System**: Extensible commands
