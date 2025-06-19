# DiPeO CLI

Command-line interface for DiPeO diagram operations.

## Installation

### For Development

```bash
# From the project root
./dipeo --help

# Or install in editable mode
cd apps/cli && pip install -e .
```

### For Production

```bash
cd apps/cli && pip install .
```

## Usage

```bash
# Run a diagram
dipeo run diagram.yaml --debug --timeout=60

# Convert between formats
dipeo convert diagram.json diagram.yaml

# Show diagram statistics
dipeo stats diagram.json

# Open monitoring interface
dipeo monitor
```

## Commands

- `run` - Execute a diagram file with GraphQL backend
- `convert` - Convert between JSON and YAML formats
- `stats` - Display diagram statistics
- `monitor` - Open browser monitoring interface

## Options for `run` command

- `--monitor` - Open browser monitor before execution
- `--mode=headless` - Run without browser
- `--no-browser` - Disable browser visualization
- `--no-stream` - Disable streaming output
- `--debug` - Enable debug mode
- `--timeout=<seconds>` - Set inactivity timeout (default: 300)

## Development

The CLI package structure:
```
apps/cli/
├── dipeo/                 # Main package
│   ├── __generated__/     # Auto-generated models
│   ├── __main__.py        # Entry point
│   ├── api_client.py      # GraphQL client
│   ├── convert.py         # Format conversion
│   ├── models.py          # CLI models
│   ├── monitor.py         # Browser monitoring
│   ├── run.py             # Diagram execution
│   ├── stats.py           # Statistics
│   └── utils.py           # Utilities
├── setup.py               # Package configuration
└── requirements.txt       # Dependencies
```

## Regenerating Models

The CLI uses auto-generated models from TypeScript definitions:

```bash
pnpm --filter @dipeo/domain-models generate:cli
```