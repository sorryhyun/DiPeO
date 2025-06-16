#!/bin/bash
# Run the FastAPI server with single worker for development
cd server && source .venv/bin/activate
WORKERS=1 python -m main "$@"