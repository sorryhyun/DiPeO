#!/bin/bash

# For now, we'll create a placeholder Python model
# In production, this would run the actual TS to Python converter
mkdir -p output/generated/python

# Get nodeType from spec (it's passed as an environment variable)
NODE_TYPE="${spec['nodeType']}"
NODE_TYPE_CAPITALIZED="${NODE_TYPE^}"

cat > output/generated/python/${NODE_TYPE}_node.py << EOF
# Generated Python model for ${NODE_TYPE} node
from dataclasses import dataclass, field
from typing import Optional, Literal
from dipeo.core.static.generated_nodes import BaseNode
from dipeo.models import NodeType

@dataclass
class ${NODE_TYPE_CAPITALIZED}Node(BaseNode):
    type: NodeType = field(default=NodeType.${NODE_TYPE}, init=False)
EOF

echo "Generated Python model for ${NODE_TYPE} node"