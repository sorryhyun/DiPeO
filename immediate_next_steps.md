# Immediate Next Steps for GraphQL Migration

## 1. Fix strawberry_types.j2 template
- Generate data-only types (no Node interface)
- Use `*NodeData` models from `/models/`
- Create a union type for all data types

## 2. Fix strawberry_mutations.j2 template  
- Generate typed input classes with actual fields from specs
- Not just generic `data: dict`
- Example:
  ```python
  @strawberry.input
  class CreateApiJobNodeInput:
      diagram_id: str
      position: Vec2Input
      # From ApiJobNodeData:
      url: str
      method: HttpMethod
      headers: Optional[Dict[str, str]]
      # ... etc
  ```

## 3. Test the generation
```bash
make codegen
make apply
# Check generated files
```

## 4. Integration
- Import generated types in schema_factory.py
- Test server starts
- Try a mutation with typed input

## 5. Cleanup
- Remove v2 GraphQL directory
- Update documentation

This approach gives us type safety where it matters (node data fields) while keeping the flexible architecture intact.