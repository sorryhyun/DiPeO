# Light Diagram Format - Analysis & Improvement Suggestions

## Current State Analysis

The light diagram format is DiPeO's human-friendly YAML format designed for manual editing and AI-driven generation. It emphasizes readability and simplicity.

### Current Strengths

1. **Label-based References**: Uses human-readable labels instead of UUIDs
2. **Flat Structure**: Simple top-level sections (`nodes`, `connections`, `persons`)
3. **Inline Props**: Node properties nested directly under each node
4. **Template Support**: Variable interpolation in prompts (`{{variable}}`)
5. **Multi-line Content**: Supports multi-line code blocks and prompts
6. **Minimal Boilerplate**: No redundant IDs or verbose syntax

### Current Structure

```yaml
version: light
nodes:
  - label: node_name
    type: NODE_TYPE
    position: {x: 100, y: 200}
    props:
      field: value

connections:
  - from: source_label
    to: target_label
    content_type: raw_text
    label: optional_label

persons:
  person_name:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_ID
```

## Suggested Improvements

### 1. Enhanced Validation & Error Messages

**Current Issue**: Generic validation errors don't point to specific diagram locations.

**Improvement**: Add line number tracking and context-aware error messages.

```yaml
# When validation fails, provide:
# - Line number in YAML
# - Node/connection label context
# - Suggestion for fix
# - Related documentation link
```

**Implementation**: Enhance `LightDiagramParser` to track source locations.

### 2. Schema Documentation & IDE Support

**Current Issue**: No autocomplete or validation in editors.

**Improvement**: Generate JSON Schema for light format.

```yaml
# Add $schema reference support
$schema: https://dipeo.dev/schemas/light-v1.json
version: light
nodes: [...]
```

**Benefits**:
- VSCode/IDE autocomplete
- Real-time validation
- Inline documentation
- Type checking

**Implementation**: Generate from `LightNode` and `LightConnection` Pydantic models.

### 3. Default Values & Shorthand Notation

**Current Issue**: Repetitive boilerplate for common patterns.

**Improvement**: Support shorthand notations and implicit defaults.

```yaml
# Shorthand for simple person_job nodes
nodes:
  - label: analyzer
    type: person_job
    # Shorthand: prompt directly without props wrapper
    prompt: "Analyze this data"
    person: analyst

  # Instead of:
  - label: analyzer
    type: person_job
    props:
      default_prompt: "Analyze this data"
      person_id: analyst
      max_iteration: 1
      memorize_to: ALL_MESSAGES
```

**Implementation**: Add field alias support in parser for common fields.

### 4. Variable Definitions Section

**Current Issue**: Variables are implicit in templates, no declaration.

**Improvement**: Add optional `variables` section for documentation and validation.

```yaml
version: light

variables:
  dataset_name:
    type: string
    default: "unknown"
    description: "Name of the dataset being processed"
  temperature:
    type: number
    default: 0.7
    range: [0, 2]

nodes: [...]
```

**Benefits**:
- Self-documenting diagrams
- Type validation
- Default value management
- Better AI understanding

### 5. Reusable Templates & Mixins

**Current Issue**: Similar node configurations are duplicated.

**Improvement**: Support node templates and mixins.

```yaml
version: light

templates:
  standard_analyzer:
    type: person_job
    props:
      max_iteration: 1
      memorize_to: CONVERSATION_PAIRS
      person: analyst

nodes:
  - label: analyze_sales
    template: standard_analyzer
    prompt: "Analyze sales data"

  - label: analyze_trends
    template: standard_analyzer
    prompt: "Analyze trends"
```

### 6. Inline Comments & Documentation

**Current Issue**: YAML comments are lost during parsing.

**Improvement**: Preserve and use structured documentation.

```yaml
nodes:
  - label: processor
    type: code_job
    description: |
      This node processes raw CSV data by:
      1. Removing empty rows
      2. Validating data types
      3. Calculating statistics
    tags: [data-processing, validation]
    props:
      code: |
        def process(data):
          # implementation
```

**Benefits**:
- Self-documenting workflows
- Better AI comprehension
- Searchable metadata
- Auto-generated documentation

### 7. Connection Shortcuts

**Current Issue**: Connections are verbose for linear flows.

**Improvement**: Support implicit connection chaining.

```yaml
# Current verbose style:
connections:
  - from: start
    to: node1
    content_type: raw_text
  - from: node1
    to: node2
    content_type: raw_text
  - from: node2
    to: end
    content_type: raw_text

# Shorthand for linear flow:
flow:
  - start -> node1 -> node2 -> end
  content_type: raw_text
```

### 8. Better Handle Specification

**Current Issue**: Handle types are implicit, causing confusion.

**Improvement**: Optional handle definitions for clarity.

```yaml
nodes:
  - label: condition_node
    type: condition
    handles:
      input: [DEFAULT]
      output: [TRUE, FALSE]  # Explicit handle names
    props:
      condition_type: detect_max_iterations

connections:
  - from: condition_node[TRUE]   # Explicit handle reference
    to: next_node
```

### 9. Metadata & Version Control

**Current Issue**: Limited diagram metadata.

**Improvement**: Enhanced metadata section.

```yaml
version: light

metadata:
  name: "Data Processing Pipeline"
  description: "Processes CSV data and generates reports"
  version: "1.2.0"
  author: "team@example.com"
  created: "2025-01-01"
  modified: "2025-01-15"
  tags: ["data-processing", "reporting"]
  dependencies:
    - openai-api
    - csv-parser
  inputs:
    - dataset_path: string
  outputs:
    - report: markdown
```

### 10. Validation Rules

**Current Issue**: No declarative validation for node inputs.

**Improvement**: Add validation specifications.

```yaml
nodes:
  - label: data_processor
    type: code_job
    validation:
      inputs:
        required: [raw_data]
        types:
          raw_data: string
          config: object
      outputs:
        provides: [cleaned_data, statistics]
    props:
      code: |
        # implementation
```

## Priority Recommendations

For immediate implementation, prioritize:

1. **Schema Documentation** (High Impact, Low Effort)
   - Generate JSON Schema from Pydantic models
   - Enable IDE support

2. **Enhanced Error Messages** (High Impact, Medium Effort)
   - Add source location tracking
   - Context-aware validation

3. **Shorthand Notations** (Medium Impact, Low Effort)
   - Field aliases for common patterns
   - Reduce boilerplate

4. **Variable Definitions** (Medium Impact, Medium Effort)
   - Improve self-documentation
   - Enable type validation

## Implementation Strategy

### Phase 1: Foundation (Current Sprint)
- ✅ Add `dipeo compile` command (validation tooling)
- ✅ Add `dipeo list` command (discovery)
- Generate JSON Schema
- Enhance error messages

### Phase 2: Usability (Next Sprint)
- Implement shorthand notations
- Add variable definitions section
- Preserve comments in parsing

### Phase 3: Advanced (Future)
- Template system
- Connection shortcuts
- Advanced validation rules

## Backward Compatibility

All improvements should maintain backward compatibility:
- Existing diagrams continue to work
- New features are opt-in
- Parser detects and adapts to format version

## Conclusion

The light format is already well-designed for human editing. These improvements would enhance:
- **Discoverability**: JSON Schema enables IDE support
- **Reliability**: Better validation catches errors early
- **Productivity**: Shorthand notation reduces boilerplate
- **Documentation**: Self-documenting workflows

The format would become even more suitable for LLM-driven generation and human-AI collaborative workflows.
