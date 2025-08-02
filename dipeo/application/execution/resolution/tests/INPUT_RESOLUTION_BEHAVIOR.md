# Input Resolution Expected Behavior Documentation

This document describes the expected behavior of the `TypedInputResolutionService` as validated by the test suite. It serves as a reference for understanding how inputs are resolved during diagram execution.

## Overview

The input resolution service is responsible for:
1. Gathering outputs from source nodes
2. Applying transformation rules
3. Routing values to target node inputs
4. Handling special cases for specific node types

## Core Behaviors

### Basic Input Resolution

1. **Simple Edge Connection**
   - When an edge connects two nodes, the output from the source node is passed as input to the target node
   - Default output key is "default" if not specified
   - Default input key is "default" if not specified

2. **Named Outputs and Inputs**
   - Edges can specify `source_output` to select a specific output from source node
   - Edges can specify `target_input` to route to a specific input on target node
   - Edge metadata `label` can override the target input key

3. **Missing Outputs**
   - If source node has no output, the edge is skipped
   - If requested output key doesn't exist, fallback to "default" key
   - If neither exists, the edge is skipped

### Node Output Formats

The service handles multiple output formats:

1. **NodeOutputProtocol Objects**
   - Extract value using `.value` property
   - Special handling for `ConditionOutput` (see below)

2. **Legacy Dictionary Format**
   - Looks for "value" key in dictionary
   - Supports backward compatibility

3. **Raw Values**
   - Non-dict values are wrapped as `{"default": value}`

### PersonJob Node Special Handling

PersonJob nodes have unique behavior for handling "first" inputs:

1. **First Execution (exec_count == 1)**
   - If any edges have `target_input` of "first" or ending with "_first":
     - Only process these "first" inputs
     - Ignore default inputs
   - If no "first" inputs exist:
     - Process default inputs normally

2. **Subsequent Executions (exec_count > 1)**
   - Ignore all "first" inputs
   - Process only default inputs

3. **Exception: conversation_state**
   - Edges with `content_type: "conversation_state"` are ALWAYS processed
   - This applies even on first execution when other inputs might be filtered

### Condition Node Output Handling

ConditionOutput objects produce special output structure:

1. **True Branch**
   - Output: `{"condtrue": true_output}`
   - Consumed by edges with `source_output: "condtrue"`

2. **False Branch**
   - Output: `{"condfalse": false_output}`
   - Consumed by edges with `source_output: "condfalse"`

## Data Transformation

### Content Type: object

When `data_transform.content_type` is "object":

1. **JSON String to Object**
   - Attempts to parse string values as JSON
   - Only processes strings starting with '{' or '['
   - On parse failure, keeps original string value

2. **Non-String Values**
   - Passed through without transformation
   - Already-parsed objects remain unchanged

3. **Special JSON Values**
   - Handles: null, true, false, numbers, quoted strings
   - Preserves Unicode characters
   - Handles large JSON structures

### Other Content Types

- Content types without special handling pass values through unchanged
- Currently supported: "object", "conversation_state"
- Future content types can be added with specific transformation logic

## Edge Processing Rules

### Should Process Edge Logic

For each edge, the service determines if it should be processed:

1. **Non-PersonJob Nodes**
   - All edges are always processed

2. **PersonJob Nodes**
   - First execution with "first" inputs available:
     - Process only "first" inputs (and conversation_state)
   - First execution without "first" inputs:
     - Process default inputs
   - Subsequent executions:
     - Skip "first" inputs
     - Process default inputs

## Integration Points

### ExecutionRuntime Integration

1. **Node Output Collection**
   - Runtime collects outputs from ExecutionTracker
   - Provides node execution counts for PersonJob logic

2. **Memory Configuration**
   - PersonJob memory settings passed through
   - Used for conversation management

### Error Handling

1. **Graceful Failures**
   - Missing source nodes: Skip edge
   - Missing output keys: Try fallback to "default"
   - JSON parse errors: Keep original value
   - No matching outputs: Skip edge

2. **Logging**
   - Debug logs for transformation attempts
   - Silent failures for missing outputs

## Test Coverage

The test suite validates:
- Basic input/output routing
- Multiple input sources
- All node output formats
- PersonJob first/default input logic
- Condition node branching
- Data transformation rules
- Edge cases and error scenarios
- Integration with ExecutionRuntime

This comprehensive test coverage ensures the input resolution mechanism behaves predictably and handles edge cases gracefully.