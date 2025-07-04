
This project provides a tool that converts diagram flows between the following formats:

1. Domain JSON
The canonical DomainDiagram format used throughout the system:
  - Used for quicksave/quickload and API communication
  - Compatible with the backend execution engine
  - Contains all essential diagram structure and data
  - Includes node positions to preserve layout
  - Used by CLI tools and direct API calls
  - Saved with `.json` extension
  - Stores nodes, arrows, handles, persons, and API keys as objects (not arrays) for easy ID-based access
  - Uses lowercase enum values for compatibility across the system

This is the persistent format that defines the diagram structure. React Flow UI properties (draggable, selectable, etc.) are applied at runtime by the DiagramAdapter but never persisted.

2. Light YAML
A simplified version of Domain JSON for better readability:
  - Handles are embedded within their parent nodes
  - Position coordinates are rounded to integers
  - IDs are removed and uses labels to index
  - Duplicate labels get suffixes (~1, ~2) to ensure uniqueness
  - Maintains the same structural information as Domain JSON

3. Readable YAML
An alternative representation optimized for understanding workflows:
  - Workflows are expressed as connected flows
  - Shows how data moves between nodes, next to the each arrow
  - Node and person definitions are listed separately
  - Designed for easy comprehension of diagram logic
