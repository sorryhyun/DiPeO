# DiPeO Light Format Guide

The Light format is a simplified YAML syntax for creating DiPeO diagrams. It uses human-readable labels instead of IDs, making it easier to write and understand.

## Basic Structure

```yaml
version: light

persons:
  Writer:
    label: Writer
    service: openai
    model: gpt-4o-mini
    system_prompt: You are a creative writer.
    api_key_id: APIKEY_3A9F1D

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    
  - label: Process Data
    type: job
    position: {x: 250, y: 200}
    props:
      code_type: python
      code: |
        # Your Python code here
        result = input_data * 2
        return result

connections:
  - from: Start
    to: Process Data
  - from: Process Data
    to: End Result
```

## Node Types

### 1. **start** - Entry point
```yaml
- label: Start
  type: start
  position: {x: 50, y: 200}
```

### 2. **person_job** - AI-powered task
```yaml
- label: Story Writer
  type: person_job
  position: {x: 400, y: 200}
  props:
    person: Writer  # References person defined above
    default_prompt: 'Write a story about: {{topic}}'
    first_only_prompt: 'Initial prompt for first iteration'
    max_iteration: 3
    forgetting_mode: on_every_turn  # or no_forget, upon_request
```

### 3. **condition** - Branching logic
```yaml
- label: Check Quality
  type: condition
  position: {x: 600, y: 200}
  props:
    personId: Reviewer
    prompt: 'Is this story good enough?'
```

### 4. **job** - Code execution
```yaml
- label: Transform Data
  type: job
  position: {x: 400, y: 200}
  props:
    code_type: python  # or javascript, bash
    code: |
      # Process the input
      return {"result": input_data.upper()}
```

### 5. **endpoint** - Output/Save
```yaml
- label: Save Result
  type: endpoint
  position: {x: 800, y: 200}
  props:
    save_to_file: true
    file_path: files/results/output.txt
```

### 6. **db** - Database/File operations
```yaml
- label: Load Data
  type: db
  position: {x: 200, y: 200}
  props:
    operation: read
    sub_type: file
    source_details: files/data/input.json
```

### 7. **user_response** - User input
```yaml
- label: Ask User
  type: user_response
  position: {x: 400, y: 300}
  props:
    prompt: 'Please enter your choice:'
    timeout: 60
```

## Connections

### Simple Connection
```yaml
connections:
  - from: Node A
    to: Node B
```

### With Custom Handles
```yaml
connections:
  - from: Condition:True    # True branch of condition
    to: Success Node
  - from: Condition:False   # False branch
    to: Retry Node
```

### With Content Type and Label
```yaml
connections:
  - from: Source Node
    to: Target Node
    content_type: variable     # or raw_text, conversation_state
    label: user_input
```

## Variables and Data Flow

Variables can be passed between nodes using `{{variable_name}}` syntax:

```yaml
- label: Get Name
  type: user_response
  props:
    prompt: 'What is your name?'

- label: Greet User
  type: person_job
  props:
    person: Assistant
    default_prompt: 'Say hello to {{name}}'
```

## Complete Example

```yaml
version: light

persons:
  Assistant:
    label: Assistant
    service: openai
    model: gpt-4o-mini
    system_prompt: You are a helpful assistant.
    api_key_id: MY_API_KEY

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}

  - label: Load Topic
    type: db
    position: {x: 200, y: 200}
    props:
      operation: read
      sub_type: file
      source_details: files/prompts/topic.txt

  - label: Generate Content
    type: person_job
    position: {x: 400, y: 200}
    props:
      person: Assistant
      default_prompt: 'Write an article about: {{topic}}'
      max_iteration: 1

  - label: Save Article
    type: endpoint
    position: {x: 600, y: 200}
    props:
      save_to_file: true
      file_path: files/results/article.txt

connections:
  - from: Start
    to: Load Topic
    
  - from: Load Topic
    to: Generate Content
    label: topic
    
  - from: Generate Content
    to: Save Article
```

## Tips

1. **Labels are unique identifiers** - Each node must have a unique label
2. **Positions are optional** - If omitted, nodes will be auto-positioned
3. **Props contain node-specific data** - Different node types require different props
4. **Forgetting modes** control conversation memory in person_job nodes
5. **Use meaningful labels** - They make the diagram self-documenting

The light format prioritizes readability and ease of editing over completeness, making it ideal for quick prototyping and simple workflows.