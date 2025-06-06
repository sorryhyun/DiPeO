#!/bin/bash

# Activate virtual environment
source apps/server/.venv/bin/activate

# Set environment variables (optional)
export RELOAD=true
export PORT=8000
export WORKERS=1

# Run the server
echo "Starting DiPeO server on port $PORT..."
python -m apps.server.main