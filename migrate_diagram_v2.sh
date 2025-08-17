#!/bin/bash
# Migration script to enable V2 diagram adapters

echo "Enabling V2 Diagram Services..."

# Enable V2 for all diagram services
export DIAGRAM_PORT_V2=1
export DIAGRAM_COMPILER_V2=1
export DIAGRAM_SERIALIZER_V2=1
export DIAGRAM_RESOLUTION_V2=1

# Optional: Enable specific features
export DIAGRAM_USE_INTERFACE_COMPILER=1  # Use interface-based compiler
export DIAGRAM_COMPILER_CACHE=1          # Enable compilation caching
export DIAGRAM_COMPILER_VALIDATE=1       # Enable validation
export DIAGRAM_COMPILER_CACHE_SIZE=100   # Cache size

echo "V2 Diagram Services enabled!"
echo "Run your application to use the new adapters."