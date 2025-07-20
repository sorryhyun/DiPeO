import os
import json

# Create registry update summary
registry_updates = {
    'nodeType': spec['nodeType'],
    'files_generated': [
        f"output/generated/{spec['nodeType']}Node.ts",
        f"output/generated/python/{spec['nodeType']}_node.py", 
        f"output/generated/{spec['nodeType']}.graphql",
        f"output/generated/{spec['nodeType']}Node.tsx",
        f"output/generated/{spec['nodeType']}Config.ts",
        f"output/generated/{spec['nodeType']}Fields.ts"
    ],
    'next_steps': [
        f"1. Add {spec['nodeType']} to NODE_TYPE_MAP in dipeo/models/src/conversions.ts",
        f"2. Import and register {spec['nodeType']}Node in dipeo/core/static/generated_nodes.py",
        f"3. Add {spec['nodeType']} to the GraphQL schema union types",
        f"4. Register the node config in the frontend node registry"
    ]
}

# Write summary file
os.makedirs('output/generated', exist_ok=True)
with open('output/generated/registry_updates.json', 'w') as f:
    json.dump(registry_updates, f, indent=2)

result = registry_updates