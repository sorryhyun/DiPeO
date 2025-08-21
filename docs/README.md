# DiPeO User Guide: Building AI Workflows with Visual Diagrams

Welcome to DiPeO! This guide will help you create AI-powered workflows using the visual diagram editor in your browser. Since you've already installed DiPeO, let's jump right into building your first diagram.

> **Looking for other documentation?** Check out the [Documentation Index](index.md) for developer guides, technical specifications, and more.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [Your First Diagram](#your-first-diagram)
4. [Working with Nodes](#working-with-nodes)
5. [Managing AI Agents (Persons)](#managing-ai-agents-persons)
6. [Connecting Nodes](#connecting-nodes)
7. [Running Your Diagram](#running-your-diagram)
8. [Common Patterns](#common-patterns)
9. [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### Opening DiPeO

1. Make sure your servers are running:
   ```bash
   make dev-all
   ```

2. Open your browser and navigate to: `http://localhost:3000`

3. You'll see the DiPeO diagram editor interface with:
   - **Left sidebar**: Node palette and controls
   - **Center canvas**: Where you build your diagrams
   - **Right sidebar**: Properties panel for selected elements

## Core Concepts

Before building diagrams, let's understand the key concepts:

### 1. **Persons** (AI Agents)
- A "Person" is an LLM instance (like GPT-4)
- Each Person has its own memory and context
- Multiple nodes can use the same Person
- Think of them as team members with different roles

### 2. **Nodes** (Tasks)
- Nodes are the building blocks of your workflow
- Each node performs a specific task
- Common types: `person_job` (AI task), `code_job` (code execution), `condition` (branching)

### 3. **Connections** (Data Flow)
- Arrows that connect nodes
- Define how data flows through your diagram
- Can carry different types of content (text, variables, conversation state)

### 4. **Handles**
- Connection points on nodes
- **Left side**: Input handles (receive data)
- **Right side**: Output handles (send data)
- Special handles like `first` for initial-only inputs

## Your First Diagram

Let's build a simple Q&A assistant:

### Step 1: Set Up Your API Key

1. Click the **"API Keys"** button in the left sidebar
2. Add your OpenAI API key
3. Give it a memorable ID (e.g., "APIKEY_MAIN")

### Step 2: Create a Person

1. Click **"Add Person"** in the left sidebar
2. Configure:
   - **Name**: "Assistant"
   - **Service**: OpenAI
   - **Model**: gpt-4o-mini (or your preferred model)
   - **API Key**: Select your key
   - **System Prompt**: "You are a helpful assistant"
3. Click **Save**

### Step 3: Build the Diagram

1. **Add a Start Node**:
   - Drag "Start" from the left palette onto the canvas
   - This is your diagram's entry point

2. **Add a User Input Node**:
   - Drag "User Response" onto the canvas
   - Click on it and set:
     - **Prompt**: "What would you like to know?"
     - **Timeout**: 120 seconds

3. **Add an AI Response Node**:
   - Drag "Person Job" onto the canvas
   - Configure:
     - **Person**: Select "Assistant"
     - **Default Prompt**: "Answer this question: {{question}}"
     - **Max Iteration**: 1

4. **Add an Endpoint**:
   - Drag "Endpoint" onto the canvas
   - Configure:
     - **Save to File**: Yes
     - **File Format**: txt
     - **File Path**: `files/results/answer.txt`

### Step 4: Connect the Nodes

1. **Connect Start to User Response**:
   - Click and drag from Start's output handle to User Response's input handle

2. **Connect User Response to Person Job**:
   - Drag from User Response output to Person Job input
   - Click the connection line
   - Set **Label**: "question" (this creates the `{{question}}` variable)

3. **Connect Person Job to Endpoint**:
   - Complete the flow by connecting to the Endpoint

### Step 5: Save Your Diagram

Click **"Quicksave"** in the top toolbar to save your work.

## Working with Nodes

### Person Job (AI Tasks)
The most important node for AI workflows:

```yaml
Properties:
- Person: Which AI agent to use
- Default Prompt: Main instruction template
- First Only Prompt: Special prompt for first iteration only
- Max Iteration: How many times this can execute
- Memory Profile: How much context to remember
  - FULL: Remember everything
  - FOCUSED: Recent 20 exchanges
  - MINIMAL: Recent 5 messages
  - GOLDFISH: Only last 2 messages
```

### Code Job (Execute Code)
Run Python, JavaScript, or Bash code:

```python
# Access input variables
user_input = inputs.get('user_data', '')

# Process data
result = user_input.upper()

# IMPORTANT: Use 'result' variable or 'return' to pass data forward
result = f"Processed: {result}"
```

### Condition (Branching)
Create decision points:
- **Detect Max Iterations**: Check if loops should end
- **Custom Expression**: Use Python expressions like `score > 80`

### DB (File Operations)
Read data from files:
```yaml
Operation: read
Sub Type: file
Source: files/data/input.csv
```

## Managing AI Agents (Persons)

### Creating Specialized Agents

Create different Persons for different roles:

1. **Analyst**:
   ```yaml
   System Prompt: "You analyze data and identify patterns. Be objective and thorough."
   ```

2. **Writer**:
   ```yaml
   System Prompt: "You write clear, engaging content. Focus on readability."
   ```

3. **Critic**:
   ```yaml
   System Prompt: "You provide constructive criticism. Be specific about improvements."
   ```

### Memory Management

Control how agents remember conversations:

- **Debates**: Use GOLDFISH (agents argue without getting stuck on previous points)
- **Analysis**: Use FULL (maintain complete context)
- **Quick Tasks**: Use MINIMAL (just enough context)

## Connecting Nodes

### Connection Types

1. **raw_text**: Plain text output
2. **conversation_state**: Full conversation history
3. **object**: Complex data structures

### Using Labels

Labels create variables you can reference:

```yaml
Connection: User Input → AI Task
Label: user_question
Then use: {{user_question}} in prompts
```

### Special Handles

- **_first**: Only accepts data on first execution
- **_condtrue/_condfalse**: Condition node outputs

## Running Your Diagram

### Execution Mode

1. Switch to **"Execution Mode"** (top toolbar)
2. Click **"Run Diagram"**
3. Follow the prompts and watch execution in real-time

### Monitoring

- Green highlights show active nodes
- Click nodes to see their output
- Check the console for detailed logs

### Debugging

- Use **Debug Mode** for verbose output
- Add Code Job nodes to inspect data:
  ```python
  print(f"Current data: {inputs}")
  result = inputs  # Pass through for inspection
  ```

## Common Patterns

### 1. Simple Q&A
```
Start → User Input → AI Response → Save Result
```

### 2. Iterative Refinement
```
Start → Initial Draft → [Loop: Critique → Revise] → Final Output
```

### 3. Multi-Agent Debate
```
Topic → Agent A (argument) → Agent B (counter) → Judge → Result
```

### 4. Data Processing Pipeline
```
Load Data → Validate → Transform → AI Analysis → Report
```

### 5. Research Assistant
```
Query → Web Search → Fact Check → Synthesize → Output
```

## Tips and Best Practices

### 1. Start Simple
- Build basic flows first
- Test each section before adding complexity
- Use Save/Load frequently

### 2. Variable Naming
- Use clear, descriptive labels
- Keep consistent naming: `user_input`, `processed_data`
- Document complex variables in node descriptions

### 3. Error Handling
- Add condition nodes to check for errors
- Use validation before processing
- Include fallback paths

### 4. Performance
- Limit iterations to prevent infinite loops
- Use appropriate memory profiles
- Consider timeout settings

### 5. Organization
- Group related nodes visually
- Use consistent left-to-right flow
- Add descriptions to complex nodes

### 6. Testing
- Use small test data first
- Monitor execution logs
- Save successful patterns as templates

## Advanced Features

### Using Tools
Enable tools for Person Job nodes:
- **Web Search**: Real-time information
- **Image Generation**: Create visuals

### Templates
Create reusable patterns:
1. Build a diagram
2. Save with descriptive name
3. Load and modify for new use cases

### Multiple Outputs
Use condition nodes to create multiple paths:
```
Analysis → Condition (quality > 80) 
         ├─→ (true) → Publish
         └─→ (false) → Revise
```

## Troubleshooting

### Common Issues

1. **"No Person selected"**: Create and assign a Person first
2. **"Variable not found"**: Check connection labels
3. **"Timeout reached"**: Increase timeout or simplify prompts
4. **"Max iterations"**: Adjust max_iteration settings

### Getting Help

- Check example diagrams in `examples/`
- Review the logs in Execution Mode
- Experiment with memory profiles
- Start with working examples and modify

## Next Steps

1. **Explore Examples**: Load and study the example diagrams
2. **Build Templates**: Create your own reusable patterns
3. **Experiment**: Try different node combinations
4. **Share**: Export diagrams to share with others

Remember: DiPeO is about visual experimentation. Don't be afraid to try new combinations and see what works best for your use case!
