#!/bin/bash
# Run the FastAPI server with single worker for development
WORKERS=1 python -m apps.server.main "$@"