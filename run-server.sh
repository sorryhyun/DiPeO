#!/bin/bash
# Run the FastAPI server with single worker for development
cd server && WORKERS=1 python -m main "$@"