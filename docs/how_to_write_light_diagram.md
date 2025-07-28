# DiPeO Light Format Guide

The Light format is a simplified YAML syntax for creating DiPeO diagrams. It uses human-readable labels instead of IDs, making it easier to write and understand workflows.

## Basic Structure

Every Light diagram follows this structure:

```yaml
version: light

# Optional: Define persons (AI agents)
persons:
  Person 1:
    service: openai
    model: gpt-4.1-nano
    api_key_id: APIKEY_123456
    system_prompt: Optional system prompt

# Required: Define nodes
nodes:
  - label: Node Label
    type: node_type
    position: {x: 100, y: 200}
    props:
      # Node-specific properties

# Optional: Define connections
connections:
  - from: Source Node
    to: Target Node
    content_type: raw_text  # or conversation_state, object
    label: optional_label
```

## Node Types

### 1. **start** - Entry Point

Every diagram must have exactly one start node:

```yaml
- label: Start
  type: start
  position: {x: 50, y: 200}
  props:
    trigger_mode: manual  # or automatic
```

### 2. **person_job** - AI-Powered Tasks

Execute prompts with LLM agents:

```yaml
- label: Writer
  type: person_job
  position: {x: 400, y: 200}
  props:
    person: Person 1  # Reference to persons section
    default_prompt: 'Write a story about {{topic}}'
    first_only_prompt: 'Start a story about {{topic}}'  # Used only on first iteration
    max_iteration: 3
    memory_profile: FULL  # or FOCUSED, MINIMAL, GOLDFISH
    tools:  # Optional tools
    - type: web_search_preview
      enabled: true
```

Memory profiles control conversation history:
- **FULL**: All messages preserved
- **FOCUSED**: Recent 20 conversation pairs
- **MINIMAL**: System messages + recent 5 messages
- **GOLDFISH**: Only last 2 messages, no system preservation

### 3. **condition** - Branching Logic

Control flow based on conditions:

```yaml
- label: Check Iterations
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: detect_max_iterations  # Checks if all person_job nodes reached max
    flipped: true  # Optional: flip true/false outputs

# Custom expression condition
- label: Check Value
  type: condition
  position: {x: 600, y: 400}
  props:
    condition_type: custom
    expression: a > 10  # Python expression
```

### 4. **code_job** - Code Execution

Execute Python, TypeScript, Bash, or Shell code either inline or from external files:

#### Option 1: Inline Code

```yaml
- label: Process Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    code_type: python  # or typescript, bash, shell
    code: |
      # Access input variables from connections
      data = raw_data  # Variable from connection labeled 'raw_data'
      
      # Process data
      processed = data.upper()
      
      # IMPORTANT: To pass data to next nodes, use one of:
      # 1. Assign to 'result' variable
      result = processed
      
      # 2. Or use return statement
      # return processed
      
      # NOTE: print() is NOT supported in code_job nodes
      # Variables not assigned to 'result' won't be passed forward
```

#### Option 2: External Code File (Recommended for complex logic)

```yaml
- label: Process Data
  type: code_job
  position: {x: 400, y: 200}
  props:
    code_type: python  # or typescript, bash, shell
    filePath: files/code/my_functions.py  # Path to code file
    functionName: process_data  # Specific function to call

# The external file should contain:
# def process_data(raw_data, other_input):
#     processed = raw_data.upper()
#     return processed
```

**Important Notes for code_job:**
- Variables from incoming connections are available by their label names
- For inline code, you MUST either:
  - Assign the output to a variable named `result`
  - Use a `return` statement (the code will be wrapped in a function)
- For external files:
  - Specify the file path in the `code` field
  - Use `functionName` to specify which function to call
  - The function receives input variables as arguments
  - The function's return value is passed to subsequent nodes
- If neither `result` nor `return` is used (inline), the node outputs "Code executed successfully"
- The `print()` function is not supported and won't produce output

### 5. **endpoint** - Output/Save

Save results to files:

```yaml
- label: Save Result
  type: endpoint
  position: {x: 800, y: 200}
  props:
    file_format: txt  # or json, yaml, md
    save_to_file: true
    file_path: files/results/output.txt
```

### 6. **db** - Database/File Operations

Read data from files:

```yaml
- label: Load Data
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details: files/data/input.txt
```

### 7. **api_job** - HTTP Requests

Make API calls:

```yaml
- label: Call API
  type: api_job
  position: {x: 400, y: 200}
  props:
    url: https://api.example.com/data
    method: GET
    headers:
      Authorization: Bearer {{api_token}}
```

### 8. **user_response** - User Input

Get input from users:

```yaml
- label: Ask Question
  type: user_response
  position: {x: 400, y: 200}
  props:
    prompt: 'Please enter your name:'
    timeout: 60
```

## Connections

### Basic Connections

Simple flow between nodes:

```yaml
connections:
  - from: Start
    to: Process Data
```

### Condition Branches

Conditions have two output handles:

```yaml
connections:
  - from: Check Value_condtrue   # When condition is true
    to: Success Node
  - from: Check Value_condfalse  # When condition is false
    to: Retry Node
```

### Content Types

Specify how data flows between nodes:

```yaml
connections:
  - from: Source
    to: Target
    content_type: raw_text         # Plain text output
    
  - from: Person Job
    to: Another Person
    content_type: conversation_state  # Full conversation history
    
  - from: Code Job
    to: Person Job
    content_type: object          # Structured data from code execution
```

### Named Connections (Important!)

**Labels are REQUIRED for passing data between nodes.** Without labels, the receiving node cannot access the data:

```yaml
connections:
  # Without label - data is NOT accessible
  - from: Load Data
    to: Process Data
    
  # With label - data is accessible as 'raw_data' variable
  - from: Load Data
    to: Process Data
    label: raw_data    # In code_job: access as raw_data
                      # In templates: access as {{raw_data}}
    
  # Multiple inputs with different labels
  - from: Load Config
    to: Process Data
    label: config     # Accessible as separate 'config' variable
```

**Key Points:**
- DB nodes (file operations) return the file content
- The label becomes the variable name in the receiving node
- Without a label, the data is passed but not accessible by name

## Variables and Data Flow

### Template Variables

Use `{{variable_name}}` syntax in prompts:

```yaml
# Node that provides data
- label: Get User Name
  type: user_response
  props:
    prompt: 'What is your name?'

# Node that uses the data
- label: Greet User
  type: person_job
  props:
    person: Assistant
    default_prompt: 'Hello {{name}}! How can I help you today?'

connections:
  - from: Get User Name
    to: Greet User
    label: name  # Makes the output available as {{name}}
```

### Code Variables

Variables set in code are automatically available to subsequent nodes:

```yaml
- label: Calculate
  type: code_job
  props:
    code: |
      a = 10
      b = 20
      result = a + b  # 'result' is passed to next nodes

- label: Check Result
  type: condition
  props:
    condition_type: custom
    expression: result > 25  # Uses 'result' from previous code
```

## Iteration Patterns

### Simple Loop

```yaml
nodes:
  - label: Counter
    type: person_job
    props:
      person: Assistant
      default_prompt: 'Count iteration'
      max_iteration: 5
      
  - label: Check Complete
    type: condition
    props:
      condition_type: detect_max_iterations
      
connections:
  - from: Counter
    to: Check Complete
    content_type: conversation_state
    
  - from: Check Complete_condfalse
    to: Counter  # Loop back
    
  - from: Check Complete_condtrue
    to: End  # Exit loop
```

### Debate Pattern

Multiple agents interacting:

```yaml
persons:
  Optimist:
    service: openai
    model: gpt-4.1-nano
    system_prompt: Always look on the bright side
    
  Pessimist:
    service: openai
    model: gpt-4.1-nano
    system_prompt: Point out potential problems

nodes:
  - label: Optimist View
    type: person_job
    props:
      person: Optimist
      first_only_prompt: 'Propose a solution for: {{problem}}'
      default_prompt: 'Respond to the criticism'
      max_iteration: 3
      memory_profile: GOLDFISH  # Forget previous rounds
      
  - label: Pessimist View
    type: person_job
    props:
      person: Pessimist
      default_prompt: 'Critique this solution'
      max_iteration: 3
      memory_profile: GOLDFISH
      
connections:
  - from: Optimist View
    to: Pessimist View
    content_type: conversation_state
    
  - from: Pessimist View
    to: Optimist View
    content_type: raw_text
```

## Complete Examples

### Example 1: Simple Q&A Bot

```yaml
version: light

persons:
  Assistant:
    service: openai
    model: gpt-4.1-nano
    api_key_id: APIKEY_123456

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    
  - label: Ask Question
    type: user_response
    position: {x: 200, y: 200}
    props:
      prompt: 'What would you like to know?'
      
  - label: Answer
    type: person_job
    position: {x: 400, y: 200}
    props:
      person: Assistant
      default_prompt: 'Answer this question: {{question}}'
      max_iteration: 1
      
  - label: Save Answer
    type: endpoint
    position: {x: 600, y: 200}
    props:
      file_format: txt
      save_to_file: true
      file_path: files/results/answer.txt

connections:
  - from: Start
    to: Ask Question
  - from: Ask Question
    to: Answer
    label: question
  - from: Answer
    to: Save Answer
```

### Example 2: Iterative Code Execution with External Files

```yaml
version: light

# The external file (files/code/iteration_functions.py) would contain:
# def initialize_counter():
#     return {"counter": 0, "status": "Starting..."}
#
# def increment_counter(counter, status):
#     new_counter = counter + 1
#     return {"counter": new_counter, "status": f"Processed {new_counter} times"}

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    
  - label: Initialize
    type: code_job
    position: {x: 200, y: 200}
    props:
      code_type: python
      code: files/code/iteration_functions.py
      functionName: initialize_counter
        
  - label: Process
    type: code_job
    position: {x: 400, y: 200}
    props:
      code_type: python
      code: files/code/iteration_functions.py
      functionName: increment_counter
        
  - label: Check Done
    type: condition
    position: {x: 400, y: 400}
    props:
      condition_type: custom
      expression: counter >= 5
      
  - label: End
    type: endpoint
    position: {x: 600, y: 400}
    props:
      file_format: txt
      save_to_file: true
      file_path: files/results/iterations.txt

connections:
  - from: Start
    to: Initialize
  - from: Initialize
    to: Process
  - from: Process
    to: Check Done
  - from: Check Done_condfalse
    to: Process  # Loop back
  - from: Check Done_condtrue
    to: End
```

## Best Practices

1. **Use Descriptive Labels** - Labels are unique identifiers, make them meaningful
2. **Set Appropriate Memory Profiles** - Use GOLDFISH for debate patterns, FULL for context-aware conversations
3. **Handle Errors Gracefully** - Add condition nodes to check for errors
4. **Test Iteratively** - Start simple and add complexity gradually
5. **Use Comments** - YAML supports # comments for documentation
6. **Variable Naming** - Use clear, consistent variable names in templates
7. **Position Nodes Logically** - Left-to-right flow improves readability
8. **Code Organization** - Use external files for complex logic (10+ lines) or reusable functions

## Running Light Diagrams

Execute your diagram with:

```bash
dipeo run your_diagram --light --debug
```

Or view in the web interface:
```
http://localhost:3000/?diagram=light/your_diagram.yaml
```

## Tips

- Labels with spaces work fine: `label: My Complex Node`
- Duplicate labels get auto-numbered: `Process` → `Process~1`
- The `flipped` property on nodes reverses their handle positions visually
- Use `first_only_prompt` for initialization, `default_prompt` for iterations
- Tools like `web_search_preview` enable extended capabilities
- The `_first` handle suffix allows special first-time inputs

Light format prioritizes readability and ease of editing over completeness, making it ideal for rapid prototyping and simple workflows.