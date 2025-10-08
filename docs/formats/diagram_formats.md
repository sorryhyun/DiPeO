# Diagram Formats

DiPeO supports three diagram formats, each optimized for different use cases. All formats are interconvertible without data loss.

## Format Overview

### 1. Domain JSON

The canonical DomainDiagram format used for system operations:

**Use Cases:**
- API communication and persistence
- CLI tool operations
- Backend execution engine compatibility
- Quicksave/quickload functionality

**Characteristics:**
- Saved with `.json` extension
- Stores nodes, arrows, handles, persons, and API keys as objects (not arrays) for ID-based access
- Uses lowercase enum values for cross-system compatibility
- Includes node positions to preserve visual layout
- Contains all essential diagram structure and data

**Note:** React Flow UI properties (draggable, selectable) are applied at runtime by the DiagramAdapter and are not persisted.

### 2. Light YAML

A simplified, human-readable format for diagram authoring:

**Use Cases:**
- Manual diagram creation and editing
- Version control and code review
- Documentation and examples
- Rapid prototyping

**Characteristics:**
- Handles embedded within parent nodes
- Position coordinates rounded to integers
- Uses labels instead of IDs for node references
- Duplicate labels receive suffixes (~1, ~2) for uniqueness
- Maintains structural equivalence with Domain JSON

**Recommended for:** Most development and documentation workflows.

See [Comprehensive Light Diagram Guide](comprehensive_light_diagram_guide.md) for complete documentation.

### 3. Readable YAML

An alternative representation optimized for workflow comprehension:

**Use Cases:**
- Understanding complex workflows
- Diagram documentation
- Visual data flow analysis
- Stakeholder communication

**Characteristics:**
- Workflows expressed as connected flows
- Data movement shown alongside connections
- Node and person definitions listed separately
- Optimized for human comprehension over machine processing

**Recommended for:** Understanding and communicating workflow logic.

## Format Conversion

All formats are interconvertible using DiPeO's conversion tools:

```bash
# Convert to Light YAML (recommended for manual editing)
dipeo convert diagram.json --format light

# Convert to Readable YAML (recommended for documentation)
dipeo convert diagram.json --format readable

# Convert back to Domain JSON (for execution)
dipeo convert diagram.light.yaml --format native
```

## Choosing a Format

| Format | Best For | File Extension |
|--------|----------|----------------|
| Domain JSON | System operations, API calls | `.json` |
| Light YAML | Development, version control | `.light.yaml` |
| Readable YAML | Documentation, comprehension | `.readable.yaml` |

## Related Documentation

- [Comprehensive Light Diagram Guide](comprehensive_light_diagram_guide.md) - Complete Light format documentation
- [Overall Architecture](../architecture/overall_architecture.md) - System architecture overview
