"""Export GraphQL schema to file."""
from .schema import schema

def export_schema(output_path="schema.graphql"):
    """Export the GraphQL schema to a file."""
    schema_str = schema.as_str()
    
    with open(output_path, "w") as f:
        f.write(schema_str)
    
    print(f"GraphQL schema exported to {output_path}")
    print(f"Schema length: {len(schema_str)} characters")
    return schema_str

if __name__ == "__main__":
    export_schema()