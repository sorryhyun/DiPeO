# Comprehensive DiPeO Light Diagram Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Core Concepts](#core-concepts)
3. [Node Types Reference](#node-types-reference)
4. [Data Flow and Variable Resolution](#data-flow-and-variable-resolution)
5. [Advanced Patterns](#advanced-patterns)
6. [Sub-Diagrams and Modular Composition](#sub-diagrams-and-modular-composition)
7. [Error Handling and Resilience](#error-handling-and-resilience)
8. [Performance Optimization](#performance-optimization)
9. [Best Practices](#best-practices)
10. [Production Patterns](#production-patterns)
11. [Debugging and Troubleshooting](#debugging-and-troubleshooting)

## Introduction

DiPeO Light format is a human-readable YAML syntax for creating executable diagrams. It's designed for rapid prototyping, complex orchestration, and production workflows. This guide covers everything from basic concepts to advanced patterns used in DiPeO's own code generation system.

### Key Principles

1. **Label-based Identity**: Nodes are identified by human-readable labels instead of UUIDs
2. **Explicit Data Flow**: Connection labels define variable names for downstream nodes
3. **Type Safety**: Each node type has specific properties and validation
4. **Composability**: Diagrams can be nested and composed via sub-diagrams
5. **Visual Execution**: All diagrams can be visualized and monitored in real-time

## Core Concepts

### Diagram Structure

```yaml
version: light  # Required version identifier

# Optional: Define AI agents
persons:
  Agent Name:
    service: openai
    model: gpt-4.1-nano
    api_key_id: APIKEY_XXXXX
    system_prompt: Optional system prompt

# Required: Define execution nodes
nodes:
  - label: Node Label
    type: node_type
    position: {x: 100, y: 200}  # Visual positioning
    props:
      # Node-specific properties

# Optional: Define data flow connections
connections:
  - from: Source Node
    to: Target Node
    content_type: raw_text  # Data transformation type
    label: variable_name    # Variable name in target node
```

### Node Labels and References

- Labels must be unique within a diagram
- Spaces in labels are allowed: `label: Data Processing Step`
- Duplicate labels auto-increment: `Process` → `Process~1`
- Condition nodes create special handles: `Check Value_condtrue`, `Check Value_condfalse`

## Node Types Reference

### 1. START Node

Entry point for diagram execution. Every diagram must have exactly one.

```yaml
- label: Start
  type: start
  position: {x: 50, y: 200}
  props:
    trigger_mode: manual  # or automatic
    custom_data:          # Optional: Initial variables
      config:
        timeout: 30
        retries: 3
```

**Key Features:**
- `custom_data` provides initial variables to all nodes
- Variables are accessible via template syntax: `{{config.timeout}}`
- Can be triggered manually or automatically

### 2. PERSON_JOB Node

Executes prompts with LLM agents, supporting iteration and memory management.

```yaml
- label: Analyzer
  type: person_job
  position: {x: 400, y: 200}
  props:
    person: Agent Name              # Reference to persons section
    default_prompt: 'Analyze {{data}}'
    first_only_prompt: 'Start analysis of {{data}}'  # First iteration only
    max_iteration: 5
    memory_profile: FOCUSED         # Memory management strategy
    tools:                          # Optional LLM tools
      - type: web_search_preview
        enabled: true
    memory_settings:                # Advanced memory control
      view: conversation_pairs
      max_messages: 20
      preserve_system: true
```

**Memory Profiles:**
- `FULL`: Complete conversation history
- `FOCUSED`: Recent 20 conversation pairs (default for analysis)
- `MINIMAL`: System + recent 5 messages
- `GOLDFISH`: Only last 2 messages, no system preservation

**Prompt Templates:**
- `first_only_prompt`: Used only on first iteration
- `default_prompt`: Used for all subsequent iterations
- Supports Handlebars syntax: `{{variable}}`, `{{nested.property}}`

### 3. CODE_JOB Node

Executes code in multiple languages with full access to input variables.

#### Inline Code

```yaml
- label: Transform Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    language: python  # python, typescript, bash, shell
    code: |
      # Input variables available from connections
      raw = raw_data  # From connection labeled 'raw_data'
      config = processing_config
      
      # Process data
      processed = {
          'total': len(raw),
          'valid': sum(1 for r in raw if r.get('valid')),
          'transformed': [transform(r) for r in raw]
      }
      
      # Output via 'result' variable or return
      result = processed
      # OR: return processed
```

#### External Code (Recommended for Complex Logic)

```yaml
# Method 1: Using filePath property
- label: Process Complex Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    language: python
    filePath: files/code/data_processor.py
    functionName: process_data

# Method 2: Using code property with file path
- label: Process Data Alternative
  type: code_job
  position: {x: 400, y: 200}
  props:
    code_type: python  # Note: can use code_type or language
    code: files/code/data_processor.py  # File path in code field
    functionName: process_data
```

**Important Notes about External Code:**
- The `code` property can contain either inline code OR a file path
- When `code` contains a path (detected by file extension), it's treated as external code
- Both `filePath` and `code` with file path achieve the same result
- `functionName` is required when using external files
- Use `code_type` or `language` interchangeably for language specification

**External File Structure:**
```python
# files/code/data_processor.py
def process_data(raw_data, config, **kwargs):
    """
    Function receives all input variables as keyword arguments.
    The function name must match 'functionName' in the node.
    All connection variables are passed as keyword arguments.
    """
    # Process data
    result = transform(raw_data, config)
    return result  # Return value becomes node output

# You can have multiple functions in the same file
def validate_data(raw_data, **kwargs):
    """Another function that can be called with functionName: validate_data"""
    return {"valid": True, "data": raw_data}
```

**Language Support:**
- **Python**: Full Python 3.13+ with async support
- **TypeScript**: Node.js runtime with TypeScript compilation
- **Bash/Shell**: System commands with proper escaping

**Important Notes:**
- Variables from connections are available by their label names
- Use `result =` or `return` to pass data to next nodes
- External files relative to project root
- Function receives all inputs as keyword arguments

### 4. CONDITION Node

Controls flow based on boolean expressions or built-in conditions.

```yaml
# Built-in condition
- label: Check Iterations
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: detect_max_iterations  # All person_jobs at max?
    flipped: true  # Invert true/false outputs

# Custom expression
- label: Validate Quality
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: custom
    expression: score >= 70 and len(errors) == 0
```

**Built-in Conditions:**
- `detect_max_iterations`: True when all person_job nodes reached max_iteration
- `nodes_executed`: Check if specific nodes have executed
- `custom`: Evaluate Python expression with access to all variables

**Connection Handles:**
- `NodeLabel_condtrue`: When condition evaluates to true
- `NodeLabel_condfalse`: When condition evaluates to false

### 5. DB Node

File system operations for reading/writing data.

```yaml
# Read single file
- label: Load Config
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details: files/config/settings.json

# Read multiple files
- label: Load All Configs
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details:
      - files/config/main.json
      - files/config/override.json
      - files/config/secrets.json

# Read files using glob patterns
- label: Load JSON Files with Glob
  type: db
  position: {x: 200, y: 300}
  props:
    operation: read
    sub_type: file
    serialize_json: true  # Parse JSON files automatically
    glob: true            # Enable glob pattern expansion
    source_details:
      - "temp/*.json"         # All JSON files in temp/
      - "config/*.yaml"       # All YAML files in config/
      - "logs/2025-*.log"     # Date-pattern logs
      - "temp/**/*.csv"       # Recursive CSV files
```

**Glob Pattern Support:**
- Set `glob: true` to enable pattern expansion
- Supports `*` (any characters), `?` (single character), `[abc]` (character sets)
- Without `glob: true`, patterns are treated as literal filenames
- Useful for dynamic file discovery in code generation

**Output:**
- Single file: Returns file content as string
- Multiple files: Returns dictionary with filepath as key, content as value
- Glob patterns (with `glob: true`): Expands to all matching files, returns as dictionary
- JSON files are NOT auto-parsed unless `serialize_json: true` is set

### 6. ENDPOINT Node

Saves results to files with format conversion.

```yaml
- label: Save Report
  type: endpoint
  position: {x: 800, y: 200}
  props:
    file_format: md      # txt, json, yaml, md
    save_to_file: true
    file_path: files/results/report.md  # Relative to project root
```

**Format Handling:**
- `json`: Serializes objects to JSON
- `yaml`: Converts to YAML format
- `txt`/`md`: Saves text content as-is

### 7. API_JOB Node

HTTP requests with template support.

```yaml
- label: Fetch Exchange Rates
  type: api_job
  position: {x: 400, y: 200}
  props:
    url: https://api.example.com/{{endpoint}}
    method: POST  # GET, POST, PUT, DELETE
    headers:
      Authorization: Bearer {{api_token}}
      Content-Type: application/json
    body:
      currency: USD
      amount: {{amount}}
    timeout: 30
```

**Features:**
- Template variables in URL, headers, and body
- Automatic JSON serialization for body
- Response available as text to downstream nodes

### 8. SUB_DIAGRAM Node

Execute another diagram as a node, enabling modular composition.

```yaml
# Single execution
- label: Process Batch
  type: sub_diagram
  position: {x: 400, y: 200}  
  props:
    diagram_name: workflows/data_processor
    diagram_format: light
    passInputData: true  # Pass all inputs to sub-diagram

# Batch execution
- label: Process Items
  type: sub_diagram
  position: {x: 400, y: 200}
  props:
    diagram_name: workflows/process_single_item
    diagram_format: light
    batch: true
    batch_input_key: items  # Array variable for batching
    batch_parallel: true    # Execute in parallel
```

**Key Properties:**
- `passInputData`: Forward all current variables to sub-diagram
- `batch`: Execute once per array item
- `batch_parallel`: Run batch items concurrently
- `ignoreIfSub`: Skip if already running as sub-diagram

### 9. TEMPLATE_JOB Node

Advanced template rendering with Jinja2.

```yaml
- label: Generate Code
  type: template_job
  position: {x: 600, y: 300}
  props:
    engine: jinja2
    template_path: files/templates/model.j2
    output_path: generated/model.py
    variables:
      models: "{{extracted_models}}"
      config: "{{generation_config}}"
```

**Features:**
- Full Jinja2 syntax support
- Custom filters (ts_to_python, snake_case, etc.)
- Direct file output
- Access to all upstream variables

### 10. USER_RESPONSE Node

Interactive user input during execution.

```yaml
- label: Get Confirmation
  type: user_response
  position: {x: 400, y: 200}
  props:
    prompt: 'Review the results and confirm (yes/no):'
    timeout: 300  # 5 minutes
    validation_type: text  # or number, boolean
```

## Data Flow and Variable Resolution

### Connection Labels Are Critical

Connection labels define variable names in the target node:

```yaml
connections:
  # Without label - data flows but isn't accessible by name
  - from: Load Data
    to: Process
    
  # With label - creates 'raw_data' variable in Process node
  - from: Load Data
    to: Process
    label: raw_data
    
  # Multiple inputs with different names
  - from: Load Config
    to: Process
    label: config
    
  # In Process node, access as:
  # Python: raw_data, config
  # Templates: {{raw_data}}, {{config}}
```

### Content Types

Control how data transforms between nodes:

```yaml
# Plain text output (default)
- from: Source
  to: Target
  content_type: raw_text
  
# Full conversation history (for person_job)
- from: Agent 1
  to: Agent 2
  content_type: conversation_state
  
# Structured data from code execution
- from: Code Job
  to: Person Job
  content_type: object
```

### Variable Scope and Propagation

1. **Start Node Variables**: Available globally via `custom_data`
2. **Connection Variables**: Scoped to target node
3. **Code Variables**: `result` or return value propagates
4. **Template Variables**: All upstream variables accessible

## Advanced Patterns

### 1. Iterative Processing with Conditions

```yaml
nodes:
  - label: Initialize Counter
    type: code_job
    props:
      code: |
        counter = 0
        max_retries = 5
        items_to_process = load_items()
        result = {"counter": counter, "items": items_to_process}
        
  - label: Process Item
    type: code_job
    props:
      code: |
        current = state["items"][state["counter"]]
        processed = process_item(current)
        state["counter"] += 1
        result = state
        
  - label: Check Complete
    type: condition
    props:
      condition_type: custom
      expression: state["counter"] >= len(state["items"])
      
connections:
  - from: Initialize Counter
    to: Process Item
    label: state
  - from: Process Item
    to: Check Complete
    label: state
  - from: Check Complete_condfalse
    to: Process Item
    label: state  # Loop back
  - from: Check Complete_condtrue
    to: Save Results
```

### 2. Multi-Agent Debate Pattern

```yaml
persons:
  Proposer:
    service: openai
    model: gpt-4.1-nano
    system_prompt: You propose innovative solutions
    
  Critic:
    service: openai
    model: gpt-4.1-nano
    system_prompt: You critically evaluate proposals
    
  Synthesizer:
    service: openai
    model: gpt-4.1-nano
    system_prompt: You synthesize different viewpoints

nodes:
  - label: Initial Proposal
    type: person_job
    props:
      person: Proposer
      first_only_prompt: 'Propose a solution for: {{problem}}'
      default_prompt: 'Refine your proposal based on criticism'
      max_iteration: 3
      memory_profile: FOCUSED
      
  - label: Critical Review
    type: person_job
    props:
      person: Critic
      default_prompt: |
        Evaluate this proposal:
        {{proposal}}
        
        Identify strengths and weaknesses.
      max_iteration: 3
      memory_profile: GOLDFISH  # Fresh perspective each time
      
  - label: Synthesize
    type: person_job
    props:
      person: Synthesizer
      default_prompt: |
        Given the proposal and criticism:
        Proposal: {{proposal}}
        Criticism: {{criticism}}
        
        Create a balanced synthesis.
      max_iteration: 1
      memory_profile: FULL
```

### 3. Error Handling and Retry Logic

```yaml
nodes:
  - label: API Call
    type: api_job
    props:
      url: https://api.example.com/data
      timeout: 10
      
  - label: Check Response
    type: code_job
    props:
      code: |
        try:
            data = json.loads(api_response)
            if data.get("status") == "success":
                result = {"success": True, "data": data}
            else:
                result = {"success": False, "error": data.get("error")}
        except:
            result = {"success": False, "error": "Invalid response"}
            
  - label: Should Retry
    type: condition
    props:
      condition_type: custom
      expression: not response["success"] and retry_count < 3
      
  - label: Increment Retry
    type: code_job
    props:
      code: |
        retry_count = retry_count + 1
        wait_time = 2 ** retry_count  # Exponential backoff
        time.sleep(wait_time)
        result = retry_count
```

### 4. Dynamic Batch Processing

```yaml
nodes:
  - label: Load Items
    type: db
    props:
      operation: read
      sub_type: file
      source_details: files/data/items.json
      
  - label: Parse Items
    type: code_job
    props:
      code: |
        items = json.loads(raw_json)
        # Create batch structure for sub_diagram
        result = {
            "items": [{"id": i, "data": item} for i, item in enumerate(items)]
        }
        
  - label: Process Batch
    type: sub_diagram
    props:
      diagram_name: workflows/process_single
      diagram_format: light
      batch: true
      batch_input_key: items
      batch_parallel: true  # Process all items concurrently
      
  - label: Aggregate Results
    type: code_job
    props:
      code: |
        # batch_results is array of outputs from each execution
        successful = [r for r in batch_results if r.get("status") == "success"]
        failed = [r for r in batch_results if r.get("status") != "success"]
        
        result = {
            "total": len(batch_results),
            "successful": len(successful),
            "failed": len(failed),
            "results": successful
        }
```

## Sub-Diagrams and Modular Composition

### Basic Sub-Diagram Usage

```yaml
# Parent diagram
nodes:
  - label: Prepare Data
    type: code_job
    props:
      code: |
        result = {
            "input_file": "data.csv",
            "config": {"quality_threshold": 80}
        }
        
  - label: Run Processor
    type: sub_diagram
    props:
      diagram_name: processors/data_quality_check
      diagram_format: light
      passInputData: true  # Pass all variables to sub-diagram
```

### Batch Processing with Sub-Diagrams

```yaml
# Parent diagram - processes multiple files
nodes:
  - label: List Files
    type: code_job
    props:
      code: |
        import glob
        files = glob.glob("files/input/*.csv")
        result = {"items": [{"file_path": f} for f in files]}
        
  - label: Process Files
    type: sub_diagram
    props:
      diagram_name: processors/single_file_processor
      diagram_format: light
      batch: true
      batch_input_key: items
      batch_parallel: true
```

### Conditional Sub-Diagram Execution

```yaml
nodes:
  - label: Check Environment
    type: code_job
    props:
      code: |
        env = os.environ.get("ENVIRONMENT", "dev")
        result = {"env": env, "is_production": env == "prod"}
        
  - label: Is Production
    type: condition
    props:
      condition_type: custom
      expression: is_production
      
  - label: Run Production Pipeline
    type: sub_diagram
    props:
      diagram_name: pipelines/production
      diagram_format: light
      passInputData: true
      
  - label: Run Dev Pipeline
    type: sub_diagram
    props:
      diagram_name: pipelines/development
      diagram_format: light
      passInputData: true
      
connections:
  - from: Is Production_condtrue
    to: Run Production Pipeline
  - from: Is Production_condfalse
    to: Run Dev Pipeline
```

## Error Handling and Resilience

### 1. Graceful Degradation

```yaml
nodes:
  - label: Primary API
    type: api_job
    props:
      url: https://primary.api.com/data
      timeout: 5
      
  - label: Check Primary
    type: code_job
    props:
      code: |
        try:
            data = json.loads(primary_response)
            result = {"success": True, "data": data, "source": "primary"}
        except:
            result = {"success": False, "source": "primary"}
            
  - label: Primary Failed
    type: condition
    props:
      condition_type: custom
      expression: not api_result["success"]
      
  - label: Fallback API
    type: api_job
    props:
      url: https://fallback.api.com/data
      timeout: 10
      
connections:
  - from: Primary Failed_condtrue
    to: Fallback API
  - from: Primary Failed_condfalse
    to: Process Data
```

### 2. Validation and Error Collection

```yaml
nodes:
  - label: Validate Input
    type: code_job
    props:
      code: |
        errors = []
        warnings = []
        
        # Validation logic
        if not data.get("required_field"):
            errors.append("Missing required_field")
            
        if len(data.get("items", [])) > 1000:
            warnings.append("Large dataset may take time")
            
        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "data": data
        }
        
  - label: Is Valid
    type: condition
    props:
      condition_type: custom
      expression: validation["valid"]
      
  - label: Log Errors
    type: endpoint
    props:
      file_format: json
      file_path: files/logs/validation_errors.json
```

### 3. Timeout and Circuit Breaker Pattern

```yaml
nodes:
  - label: Check Circuit State
    type: code_job
    props:
      code: |
        # Load circuit breaker state
        try:
            with open("temp/circuit_state.json", "r") as f:
                state = json.load(f)
        except:
            state = {"failures": 0, "last_failure": 0}
            
        # Check if circuit is open
        now = time.time()
        if state["failures"] >= 3:
            if now - state["last_failure"] < 300:  # 5 minute cooldown
                result = {"circuit_open": True}
            else:
                # Reset circuit
                state["failures"] = 0
                result = {"circuit_open": False, "state": state}
        else:
            result = {"circuit_open": False, "state": state}
```

## Performance Optimization

### 1. Parallel Execution Strategies

```yaml
# Parallel data fetching
nodes:
  - label: Start Parallel Fetch
    type: code_job
    props:
      code: |
        sources = [
            {"id": "users", "url": "/api/users"},
            {"id": "products", "url": "/api/products"},
            {"id": "orders", "url": "/api/orders"}
        ]
        result = {"items": sources}
        
  - label: Fetch Data
    type: sub_diagram
    props:
      diagram_name: utilities/fetch_single_source
      batch: true
      batch_input_key: items
      batch_parallel: true  # Fetch all sources concurrently
```

### 2. Caching Strategies

```yaml
nodes:
  - label: Check Cache
    type: code_job
    props:
      code: |
        import hashlib
        import os
        
        # Generate cache key
        cache_key = hashlib.md5(json.dumps(params).encode()).hexdigest()
        cache_file = f"temp/cache/{cache_key}.json"
        
        if os.path.exists(cache_file):
            # Check cache age
            age = time.time() - os.path.getmtime(cache_file)
            if age < 3600:  # 1 hour cache
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)
                result = {"hit": True, "data": cached_data}
            else:
                result = {"hit": False, "cache_file": cache_file}
        else:
            result = {"hit": False, "cache_file": cache_file}
```

### 3. Batch vs Sequential Processing

```yaml
# Choose strategy based on data size
nodes:
  - label: Analyze Workload
    type: code_job
    props:
      code: |
        item_count = len(items)
        avg_size = sum(len(str(item)) for item in items) / item_count
        
        # Use batch for large datasets, sequential for small
        use_batch = item_count > 100 or avg_size > 1000
        
        result = {
            "use_batch": use_batch,
            "items": items,
            "stats": {
                "count": item_count,
                "avg_size": avg_size
            }
        }
        
  - label: Should Batch
    type: condition
    props:
      condition_type: custom
      expression: use_batch
```

## Best Practices

### 1. Node Organization

- **Group related nodes visually**: Use x-coordinates to show flow progression
- **Use descriptive labels**: `Validate User Input` not `Step 3`
- **Consistent positioning**: Increment x by 200-400 for readability
- **Handle positions**: Use `flipped` property for cleaner layouts

### 2. Variable Naming

```yaml
connections:
  # Good: Descriptive, indicates content
  - from: Load User Data
    to: Process Users
    label: user_records
    
  # Bad: Generic, unclear
  - from: Node1
    to: Node2
    label: data
```

### 3. External Code Organization

**When to Use External Code Files:**
- Code longer than 10-15 lines
- Reusable functions across multiple diagrams
- Complex logic requiring imports and helper functions
- Code that needs testing independently
- Following DiPeO's codegen pattern (all code in external files)

**Directory Structure:**
```
files/
├── code/
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── user_validator.py
│   │   └── data_validator.py
│   ├── processors/
│   │   ├── __init__.py
│   │   └── data_processor.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── codegen/
│   └── code/
│       ├── models/
│       │   └── generate_python_models/
│       │       └── python_models_extractor_v2.py
│       └── shared/
│           └── parse_node_data/
│               └── parser_functions.py
```

**Example: Inline vs External Code**

```yaml
# Inline - Good for simple operations
- label: Simple Transform
  type: code_job
  props:
    code: |
      result = input_data.upper()

# External - Better for complex logic
- label: Complex Processing
  type: code_job
  props:
    code: files/code/processors/data_processor.py
    functionName: process_complex_data
    # OR using filePath:
    # filePath: files/code/processors/data_processor.py
```

### 4. Error Messages and Logging

```yaml
- label: Process with Logging
  type: code_job
  props:
    code: |
      import logging
      log = logging.getLogger(__name__)
      
      try:
          log.info(f"Processing {len(items)} items")
          processed = process_items(items)
          log.info(f"Successfully processed {len(processed)} items")
          result = {"success": True, "data": processed}
      except Exception as e:
          log.error(f"Processing failed: {str(e)}")
          result = {"success": False, "error": str(e)}
```

### 5. Testing Diagrams

```yaml
# Test harness diagram
nodes:
  - label: Load Test Cases
    type: db
    props:
      source_details: files/tests/test_cases.json
      
  - label: Run Tests
    type: sub_diagram
    props:
      diagram_name: main_workflow
      batch: true
      batch_input_key: test_cases
      
  - label: Validate Results
    type: code_job
    props:
      code: |
        failures = []
        for i, (result, expected) in enumerate(zip(results, test_cases)):
            if not validate_result(result, expected):
                failures.append({
                    "test": i,
                    "expected": expected,
                    "actual": result
                })
        
        if failures:
            raise AssertionError(f"{len(failures)} tests failed")
```

## Production Patterns

### 1. Configuration Management

```yaml
nodes:
  - label: Load Environment Config
    type: code_job
    props:
      code: |
        env = os.environ.get("ENVIRONMENT", "dev")
        config_file = f"files/config/{env}.json"
        
        with open(config_file, "r") as f:
            config = json.load(f)
            
        # Merge with environment variables
        for key, value in os.environ.items():
            if key.startswith("APP_"):
                config[key[4:].lower()] = value
                
        result = config
```

### 2. Monitoring and Metrics

```yaml
nodes:
  - label: Start Timer
    type: code_job
    props:
      code: |
        import time
        start_time = time.time()
        result = {"start_time": start_time}
        
  - label: Record Metrics
    type: code_job
    props:
      code: |
        duration = time.time() - timing["start_time"]
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "duration": duration,
            "items_processed": len(results),
            "success_rate": sum(1 for r in results if r["success"]) / len(results),
            "errors": [r["error"] for r in results if not r["success"]]
        }
        
        # Send to monitoring system
        send_metrics(metrics)
        result = metrics
```

### 3. Graceful Shutdown

```yaml
nodes:
  - label: Check Shutdown Signal
    type: code_job
    props:
      code: |
        import signal
        
        shutdown_requested = False
        
        def handle_shutdown(signum, frame):
            global shutdown_requested
            shutdown_requested = True
            
        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)
        
        result = {"shutdown": shutdown_requested}
        
  - label: Should Continue
    type: condition
    props:
      condition_type: custom
      expression: not status["shutdown"] and current_item < total_items
```

### 4. Deployment Patterns

```yaml
# Blue-green deployment checker
nodes:
  - label: Check Current Version
    type: api_job
    props:
      url: https://api.myapp.com/version
      
  - label: Compare Versions
    type: code_job
    props:
      code: |
        current = json.loads(version_response)["version"]
        target = os.environ.get("TARGET_VERSION")
        
        if current == target:
            result = {"deploy": False, "reason": "Already at target version"}
        else:
            result = {"deploy": True, "current": current, "target": target}
```

## Debugging and Troubleshooting

### 1. Debug Mode Execution

```bash
# Run with debug output
dipeo run my_diagram --light --debug

# With timeout for long-running diagrams
dipeo run my_diagram --light --debug --timeout=300

# With initial data
dipeo run my_diagram --light --debug --input-data '{"user_id": 123}'
```

### 2. Debugging Nodes

```yaml
- label: Debug State
  type: code_job
  props:
    code: |
      # Print all available variables
      print("=== Debug State ===")
      for key, value in locals().items():
          if not key.startswith("_"):
              print(f"{key}: {type(value)} = {repr(value)[:100]}")
      
      # Pass through data unchanged
      result = input_data
```

### 3. Execution Monitoring

```yaml
# Add monitoring nodes
- label: Log Execution
  type: code_job
  props:
    code: |
      with open("files/logs/execution.log", "a") as f:
          f.write(f"{datetime.now()}: Node {node_label} executed\n")
          f.write(f"  Input: {json.dumps(input_data)[:200]}\n")
      result = input_data
```

### 4. Common Issues and Solutions

**Issue: Variable not found in template**
```yaml
# Problem
default_prompt: "Process {{data}}"  # 'data' is undefined

# Solution: Ensure connection has label
connections:
  - from: Source
    to: Target
    label: data  # This creates the 'data' variable
```

**Issue: Sub-diagram not receiving inputs**
```yaml
# Problem
props:
  diagram_name: sub_workflow
  passInputData: false  # Inputs not passed

# Solution
props:
  diagram_name: sub_workflow
  passInputData: true  # Pass all variables
```

**Issue: Condition always false**
```yaml
# Problem
condition_type: custom
expression: score > 80  # 'score' might be string

# Solution
expression: float(score) > 80  # Explicit conversion
```

### 5. Performance Profiling

```yaml
nodes:
  - label: Profile Section
    type: code_job
    props:
      code: |
        import cProfile
        import pstats
        import io
        
        pr = cProfile.Profile()
        pr.enable()
        
        # Expensive operation
        result = expensive_function(input_data)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(10)  # Top 10 functions
        
        with open("files/logs/profile.txt", "w") as f:
            f.write(s.getvalue())
```

## Conclusion

DiPeO Light format provides a powerful, readable way to create complex workflows. By understanding the node types, data flow patterns, and best practices outlined in this guide, you can create efficient, maintainable, and production-ready diagrams.

Key takeaways:
1. **Always label connections** for variable access
2. **Use external code files** for complex logic
3. **Leverage sub-diagrams** for modularity
4. **Plan for errors** with conditions and validation
5. **Monitor execution** with debug nodes and logging
6. **Test thoroughly** with different input scenarios

The examples and patterns shown here are derived from DiPeO's own code generation system, demonstrating that Light format can handle sophisticated real-world workflows while remaining readable and maintainable.