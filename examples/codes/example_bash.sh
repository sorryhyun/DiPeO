#!/bin/bash
# Example Bash script for Code Job node execution

# Access inputs via environment variables (INPUT_<label>)
DATA_SOURCE="${INPUT_data_source:-No data source}"
CONFIG="${INPUT_config:-{}}"
TEXT="${INPUT_text:-Hello World}"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Main processing
log "Starting bash script execution"
log "Data source: $DATA_SOURCE"

# List all available inputs (new helper variable)
if [ -n "$INPUT_KEYS" ]; then
    log "Available inputs: $INPUT_KEYS"
fi

# Parse JSON config if provided
if command -v jq &> /dev/null && [ "$CONFIG" != "{}" ]; then
    CONFIG_KEYS=$(echo "$CONFIG" | jq -r 'keys[]' 2>/dev/null || echo "Invalid JSON")
    log "Config keys: $CONFIG_KEYS"
fi

# Process text input
PROCESSED_TEXT=$(echo "$TEXT" | tr '[:lower:]' '[:upper:]')

# Build JSON output
cat << EOF
{
  "message": "Bash script executed successfully",
  "data_source": "$DATA_SOURCE",
  "processed_text": "$PROCESSED_TEXT",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": {
    "user": "$USER",
    "hostname": "$(hostname)",
    "pwd": "$PWD"
  },
  "input_count": $(env | grep -c "^INPUT_")
}
EOF