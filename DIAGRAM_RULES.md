# AgentDiagram CLI Tool

Simple command-line interface for AgentDiagram workflows.

## Installation

```bash
cd apps/tools
pip install -r requirements.txt
```

## Usage

### Run a Workflow
```bash
# Execute a diagram and save results
python agentdiagram_tool.py run workflow.yaml
python agentdiagram_tool.py run workflow.json results.json
```


### View Statistics
```bash
python agentdiagram_tool.py stats workflow.yaml
```

### Save to Server
```bash
python agentdiagram_tool.py server-save workflow.yaml my-workflow.yaml
```

## Requirements

- Python 3.8+
- `requests` library
- `pyyaml` library
- AgentDiagram server running on `localhost:8000`


## AgentDiagram YAML Format Rules

### 1. **File Structure Rules**

```yaml
version: "1.0"  # Required - must be exactly "1.0"
metadata:       # Optional but recommended
  description: "Brief description of the workflow"
apiKeys:        # Required if persons use API services
persons:        # Required if using personjobNode
workflow:       # Required - contains all nodes
```

### 2. **API Keys Rules**
- Each API key must have a unique ID
- Required fields: `service`, `name`
- Valid services: `chatgpt`, `claude`, `gemini`, `grok`, `custom`
- Example:
```yaml
apiKeys:
  APIKEY_ABC123:
    service: chatgpt
    name: "Production OpenAI Key"
```

### 3. **Persons Rules**
- Each person represents an LLM agent configuration
- Required fields: `id`, `model`, `service`
- Optional fields: `apiKeyId`, `system`, `temperature`
- The `apiKeyId` must reference a valid key in the `apiKeys` section
- Example:
```yaml
persons:
  researcher:
    id: researcher
    model: gpt-4.1-nano
    service: chatgpt
    apiKeyId: APIKEY_ABC123
    system: "You are a helpful research assistant"
```

### 4. **Workflow Rules**

#### 4.1 **Node Connectivity Rules**
- **No isolated nodes**: Every node must have at least one connection (except endpoints)
- Start nodes must have outgoing connections only
- Endpoint nodes must have incoming connections only
- All other nodes should have both incoming and outgoing connections

#### 4.2 **Node ID Rules**
- Each node must have a unique `id`
- Use descriptive IDs (e.g., `analyze_data`, not `node_1`)
- IDs should be lowercase with underscores for consistency

#### 4.3 **Node Type Rules**
Valid node types and their required fields:

```yaml
# Start Node
- id: start
  type: startNode
    position:
      x: 0
      y: 0
  connections:
    - to: first_task

# Person Job Node
- id: analyze_data
  type: personjobNode
  position:
    x: 200
    y: 0
  person: researcher  # Must reference a valid person
  prompt: "Analyze {{data}}"  # Can use {{variables}}
  first_prompt: "Optional first-run prompt"
  forget: upon_request  # Options: upon_request, no_forget, on_every_turn
  max_iterations: 3
  mode: sync  # Options: sync, batch

# Condition Node
- id: check_result
  type: conditionNode
  position:
    x: 400
    y: 0
  condition_type: expression  # or max_iterations
  expression: "score > 0.8"  # Python expression
  connections:
    - to: success_path
      branch: "true"
    - to: retry_path
      branch: "false"

# DB Source Node
- id: load_data
  type: dbNode
  position:
    x: 200
    y: -100
  sub_type: file  # or fixed_prompt
  source: "data/input.txt"

# Job Node
- id: process_data
  type: jobNode
  position:
    x: 500
    y: 100
  sub_type: code  # or api_tool, diagram_link
  code: |
    result = inputs[0].upper()
    return result

# Endpoint Node
- id: save_result
  type: endpointNode
  position:
    x: 800
    y: 0
  file: "results/output.txt"  # Optional
  file_format: text  # Options: text, json, csv
```

### 5. **Connection Rules**

#### 5.1 **Basic Connection Structure**
```yaml
connections:
  - to: target_node_id  # Required
    label: variable_name  # Recommended for clarity
```

#### 5.2 **Content Type Rules**
- `raw_text`: Default, passes output as-is
- `conversation_state`: Passes entire conversation history
- `variable_in_object`: Extracts specific field from object

#### 5.3 **Handle Rules**
- PersonJob nodes have special handles:
  - `first`: Only used on first iteration
  - `default`: Used on all iterations
- Condition nodes have branch-specific handles:
  - `true`: When condition is true
  - `false`: When condition is false

Example with handles:
```yaml
connections:
  - to: personjob_node
    source_handle: node-output-default
    target_handle: personjob_node-input-first
```

### 6. **Variable Usage Rules**
- Use `{{variable_name}}` syntax in prompts
- Variables come from connection labels
- Example:
```yaml
- id: writer
  type: personjobNode
  prompt: "Write article about {{research_results}}"
  connections:
    - to: editor
      label: draft  # This creates {{draft}} variable for next node
```

### 7. **Validation Rules**

#### 7.1 **Required Validations**
- [ ] At least one `startNode` must exist
- [ ] All nodes must be reachable from a start node
- [ ] No circular dependencies without condition breaks
- [ ] All person references must exist in `persons` section
- [ ] All apiKeyId references must exist in `apiKeys` section

#### 7.2 **Graph Topology Rules**
- The workflow must form a directed acyclic graph (DAG) or have proper loop control
- Loops are allowed only with:
  - Condition nodes that can break the loop
  - Max iteration limits on PersonJob nodes

#### 7.3 **Position Rules**
- All nodes must have valid `position` with `x` and `y` coordinates
- Positions should be spaced to avoid overlap (recommended: 200-300 units apart)

### 8. **Best Practices**

#### 8.1 **Naming Conventions**
```yaml
# Good
- id: analyze_customer_feedback
  label: "Analyze Customer Feedback"

# Bad
- id: node1
  label: "Node 1"
```

#### 8.2 **Error Handling**
- Always include max_iterations for PersonJob nodes in loops
- Use condition nodes to handle edge cases
- Provide meaningful labels for debugging

#### 8.3 **Organization**
```yaml
workflow:
  # Group related nodes together
  # 1. Input/Start nodes first
  - id: start
    type: startNode
    
  # 2. Data source nodes
  - id: load_data
    type: dbNode
    
  # 3. Processing nodes
  - id: process_data
    type: personjobNode
    
  # 4. Decision/routing nodes
  - id: check_quality
    type: conditionNode
    
  # 5. Output/End nodes
  - id: save_result
    type: endpointNode
```

### 9. **Common Errors to Avoid**

```yaml
# ❌ Bad: Isolated node
- id: orphan_node
  type: personjobNode
  # No connections!

# ❌ Bad: Invalid person reference
- id: task
  type: personjobNode
  person: non_existent_person  # This person doesn't exist

# ❌ Bad: Circular dependency without break
- id: a
  connections:
    - to: b
- id: b
  connections:
    - to: a  # Infinite loop!

# ✅ Good: Loop with condition break
- id: a
  connections:
    - to: condition
- id: condition
  type: conditionNode
  connections:
    - to: b
      branch: "true"
    - to: end
      branch: "false"
```

