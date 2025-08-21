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