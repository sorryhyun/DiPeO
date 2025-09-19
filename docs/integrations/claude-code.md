# Claude Code Integration

DiPeO now supports Claude Code SDK as an LLM provider, enabling integration with Anthropic's Claude Code for advanced AI agent capabilities.

## Installation

### Prerequisites

The Claude Code SDK is already included in DiPeO's dependencies. No additional installation required.

## Configuration

### API Key Setup

Use your Anthropic API key (same as regular Claude):
```bash
export ANTHROPIC_API_KEY=your-api-key-here
```

### DiPeO Configuration

In your diagram YAML files, configure a person to use Claude Code:

```yaml
version: light

persons:
  Claude Code Agent:
    service: claude-code
    model: claude-code
    api_key_id: anthropic_api_key
    system_prompt: "You are a helpful assistant"
    max_turns: 5  # Maximum conversation turns
```

## Supported Models

- `claude-code` - Default Claude Code model
- `claude-code-sdk` - Alias for Claude Code

Note: Claude Code uses its own model endpoint and doesn't follow the typical model naming conventions used by other providers like `gpt-5-nano-2025-08-07`.

## Service Aliases

The following service names are recognized:
- `claude-code` (primary)
- `claude-sdk`
- `claude_code`

## Example Usage

```yaml
version: light

persons:
  Performance Analyzer:
    service: claude-code
    model: claude-code
    api_key_id: anthropic_api_key
    system_prompt: "You are a performance engineer"
    max_turns: 3

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    props:
      trigger_mode: manual
      custom_data:
        system: "web-server"
        metrics_file: "files/data/performance.json"

  - label: Analyze Performance
    type: person_job
    position: {x: 400, y: 200}
    props:
      person: Performance Analyzer
      default_prompt: |
        Analyze the performance data for {{system}}:
        {{metrics_data}}
        
        Provide insights on bottlenecks and optimization recommendations.
      max_iteration: 1
      memory_profile: FOCUSED

  - label: Load Metrics
    type: db
    position: {x: 200, y: 200}
    props:
      operation: read
      sub_type: file
      source_details: "{{metrics_file}}"
      serialize_json: true

  - label: Save Analysis
    type: endpoint
    position: {x: 600, y: 200}
    props:
      file_format: md
      save_to_file: true
      file_path: files/results/performance_analysis.md

connections:
  - from: Start
    to: Load Metrics
  - from: Load Metrics
    to: Analyze Performance
    label: metrics_data
  - from: Analyze Performance
    to: Save Analysis
```

## Key Differences from Regular Claude

1. **Streaming-First Architecture**: Claude Code uses streaming responses by default
2. **Context Manager Pattern**: Client lifecycle managed via async context managers
3. **Multi-Turn Support**: Built-in conversation management with configurable max turns
4. **Different API Pattern**: Uses `ClaudeSDKClient` instead of traditional API clients

## Memory Profiles for Claude Code

Claude Code agents support the same memory management strategies as other LLM providers:

```yaml
persons:
  Code Assistant:
    service: claude-code
    model: claude-code
    api_key_id: anthropic_api_key
    system_prompt: "You are a helpful coding assistant"

nodes:
  - label: Detailed Analysis
    type: person_job
    props:
      person: Code Assistant
      memory_profile: FULL      # Keep complete conversation history
      max_iteration: 5
      
  - label: Quick Review
    type: person_job
    props:
      person: Code Assistant  
      memory_profile: FOCUSED   # Last 20 conversation pairs (default)
      max_iteration: 3
      
  - label: Fresh Evaluation
    type: person_job
    props:
      person: Code Assistant
      memory_profile: GOLDFISH  # No memory - unbiased evaluation
      max_iteration: 1
      
  - label: Custom Memory
    type: person_job
    props:
      person: Code Assistant
      memory_profile: CUSTOM
      memory_settings:
        view: conversation_pairs
        max_messages: 10
        preserve_system: true
      max_iteration: 2
```

**Memory Profile Options:**
- `FULL`: Complete conversation history
- `FOCUSED`: Recent 20 conversation pairs (recommended for analysis tasks)
- `MINIMAL`: System + recent 5 messages  
- `GOLDFISH`: Only last 2 messages, no system preservation (good for objective evaluations)
- `CUSTOM`: User-defined settings via `memory_settings`

## Limitations

- Tool/function calling is not yet supported
- Response API pattern is not available
- Models list API is not available (returns predefined list)

## Advanced Example: Code Review Workflow

Here's a more comprehensive example showing Claude Code in a code review workflow:

```yaml
version: light

persons:
  Code Reviewer:
    service: claude-code
    model: claude-code
    api_key_id: anthropic_api_key
    system_prompt: |
      You are a senior software engineer conducting code reviews.
      Focus on code quality, security, performance, and best practices.
    max_turns: 3

  Security Analyst:
    service: claude-code
    model: claude-code
    api_key_id: anthropic_api_key
    system_prompt: |
      You are a security specialist reviewing code for vulnerabilities.
      Look for security issues, potential exploits, and compliance violations.
    max_turns: 2

nodes:
  - label: Start
    type: start
    position: {x: 50, y: 200}
    props:
      trigger_mode: manual
      custom_data:
        repo_path: "files/code/my-project"
        review_files:
          - "src/auth/login.py"
          - "src/api/endpoints.py"
          - "src/utils/validators.py"

  - label: Load Code Files
    type: db
    position: {x: 200, y: 200}
    props:
      operation: read
      sub_type: file
      source_details: "{{review_files}}"

  - label: Initial Code Review
    type: person_job
    position: {x: 400, y: 150}
    props:
      person: Code Reviewer
      default_prompt: |
        Review the following code files for quality, maintainability, and best practices:
        
        {{#each code_files}}
        ## {{@key}}
        ```python
        {{this}}
        ```
        {{/each}}
        
        Provide specific feedback on:
        1. Code quality and structure
        2. Performance considerations
        3. Error handling
        4. Documentation and readability
      max_iteration: 1
      memory_profile: FOCUSED

  - label: Security Review
    type: person_job
    position: {x: 400, y: 250}
    props:
      person: Security Analyst
      default_prompt: |
        Perform a security review of these code files:
        
        {{#each code_files}}
        ## {{@key}}
        ```python
        {{this}}
        ```
        {{/each}}
        
        Look for:
        1. SQL injection vulnerabilities
        2. XSS prevention
        3. Authentication and authorization issues
        4. Input validation problems
        5. Data exposure risks
      max_iteration: 1
      memory_profile: GOLDFISH

  - label: Quality Gate
    type: condition
    position: {x: 600, y: 200}
    props:
      condition_type: llm_decision
      person: Code Reviewer
      memorize_to: "MINIMAL"
      judge_by: |
        Based on the code review and security analysis:
        
        Code Review: {{code_review_feedback}}
        Security Review: {{security_feedback}}
        
        Are there any CRITICAL issues that would block deployment?
        Respond with YES if there are blocking issues, NO if approved for deployment.

  - label: Generate Report
    type: template_job
    position: {x: 800, y: 150}
    props:
      engine: jinja2
      template_path: files/templates/code_review_report.j2
      output_path: files/results/code_review_report.md
      variables:
        code_review: "{{code_review_feedback}}"
        security_review: "{{security_feedback}}"
        approved: true
        timestamp: "{{current_timestamp}}"

  - label: Block Deployment
    type: endpoint
    position: {x: 800, y: 250}
    props:
      file_format: json
      save_to_file: true
      file_path: files/results/deployment_blocked.json

connections:
  - from: Start
    to: Load Code Files
  - from: Load Code Files
    to: Initial Code Review
    label: code_files
  - from: Load Code Files
    to: Security Review
    label: code_files
  - from: Initial Code Review
    to: Quality Gate
    label: code_review_feedback
  - from: Security Review
    to: Quality Gate
    label: security_feedback
  - from: Quality Gate_condfalse
    to: Generate Report
  - from: Quality Gate_condtrue
    to: Block Deployment
```

This example demonstrates:
- Multiple Claude Code agents with different specializations
- Parallel code review and security analysis
- LLM-based quality gate decision making using the new `llm_decision` condition type
- Conditional workflow based on review results
- Template-based report generation
- Modern light diagram format with proper node positioning and connections

## Running Diagrams

Execute diagrams with Claude Code agents:
```bash
dipeo run examples/test_claude_code --light --debug
```

## Best Practices for Claude Code Integration

### 1. Optimal Memory Profile Selection

Choose memory profiles based on your use case:

```yaml
# For code analysis requiring context
- label: Iterative Code Improvement
  type: person_job
  props:
    person: Code Assistant
    memory_profile: FOCUSED  # Maintains context across iterations
    max_iteration: 5

# For objective code evaluation
- label: Code Quality Check
  type: condition
  props:
    condition_type: llm_decision
    person: Code Reviewer
    memorize_to: "GOLDFISH"  # Fresh evaluation without bias
```

### 2. Leveraging Max Turns

Claude Code's `max_turns` configuration helps prevent excessive API calls:

```yaml
persons:
  Efficient Agent:
    service: claude-code
    model: claude-code
    api_key_id: anthropic_api_key
    max_turns: 3  # Limit conversation length
    system_prompt: "Be concise and focused in your responses"
```

### 3. Streaming Response Handling

Claude Code uses streaming by default, which is automatically handled by DiPeO. Monitor execution in real-time:

```bash
# Watch execution progress with debug output
dipeo run my_claude_diagram --light --debug

# Monitor in web UI
# Navigate to http://localhost:3000/?monitor=true
```

### 4. Error Recovery Patterns

Handle Claude Code specific errors gracefully:

```yaml
nodes:
  - label: Robust LLM Call
    type: person_job
    props:
      person: Claude Agent
      default_prompt: "{{task_description}}"
      max_iteration: 2  # Allow retry on failure
      
  - label: Validate Response
    type: code_job
    props:
      code: |
        # Check if Claude Code response is valid
        if not llm_response or len(llm_response.strip()) < 10:
            result = {"valid": False, "error": "Empty or too short response"}
        else:
            result = {"valid": True, "response": llm_response}
            
  - label: Fallback Handler
    type: condition
    props:
      condition_type: custom
      expression: not response_check["valid"]
```

## Troubleshooting

### Import Error
If you see `ImportError: claude-code-sdk is required`:
```bash
make install  # Reinstall dependencies
```

### Service Not Available
If Claude Code service is not available, check that the ANTHROPIC_API_KEY is configured properly in your environment.

### Rate Limiting
The adapter includes automatic retry logic with exponential backoff for rate limit errors.

## Claude Code Session Conversion

DiPeO can convert Claude Code conversation sessions into executable diagrams using the `dipeocc` command.

### What are Claude Code Sessions?

Claude Code automatically saves all conversations as JSONL files in:
```
~/.claude/projects/-home-{username}-DiPeO/
```

These sessions contain:
- User prompts and AI responses
- Tool usage (Read, Write, Edit, Bash, etc.)
- Timestamps and conversation flow
- Complete context for replay and analysis

### Converting Sessions to Diagrams

Use the `dipeocc` command to convert sessions:

```bash
# List available sessions
dipeocc list

# Convert the latest session
dipeocc convert --latest

# Convert and execute immediately
dipeocc convert --latest --auto-execute

# Watch for new sessions
dipeocc watch --interval 30
```

### Tool Mapping

Claude Code tools are automatically mapped to DiPeO nodes:

| Claude Code Tool | DiPeO Node | Purpose |
|-----------------|------------|---------|
| User message | Start node | Initial request |
| Assistant response | Person job (claude_code) | AI reasoning |
| Read tool | DB node (SELECT) | File reading |
| Write tool | DB node (INSERT) | File creation |
| Edit tool | DB node (UPDATE) | File modification |
| Bash tool | Code job (bash) | Command execution |
| TodoWrite | DB node | Task tracking |
| WebFetch | API job | Web content retrieval |

### Example Converted Diagram

A typical Claude Code session converts to:

```yaml
version: light

persons:
  Claude Code Agent:
    service: claude-code
    model: claude-code-custom
    max_turns: 10

nodes:
  - label: User Request
    type: start
    position: {x: 100, y: 200}
    props:
      trigger_mode: manual
      custom_data:
        request: "Help me refactor this code"

  - label: Analyze Code
    type: person_job
    position: {x: 300, y: 200}
    props:
      person: Claude Code Agent
      default_prompt: "{{request}}"
      memory_profile: FOCUSED

  - label: Read Source File
    type: db
    position: {x: 500, y: 200}
    props:
      operation: read
      sub_type: file
      source_details: "src/main.py"

connections:
  - from: User Request
    to: Analyze Code
  - from: Analyze Code
    to: Read Source File
```

### Benefits of Session Conversion

1. **Replay Workflows**: Re-execute past Claude Code sessions
2. **Share Solutions**: Convert successful sessions to shareable diagrams
3. **Modify and Enhance**: Edit converted diagrams to improve workflows
4. **Build Libraries**: Create reusable patterns from common tasks
5. **Analyze Performance**: Review execution patterns and optimize

### Advanced Usage

#### Optimizations

```bash
# Merge consecutive file reads
dipeocc convert --latest --merge-reads

# Simplify by removing intermediate results
dipeocc convert --latest --simplify

# Custom output directory
dipeocc convert --latest --output-dir projects/my_workflows
```

#### Batch Processing

```bash
# Convert multiple sessions
for session in $(dipeocc list | grep Session | awk '{print $3}'); do
  dipeocc convert $session
done
```

#### Continuous Integration

```bash
# Watch and auto-convert new sessions
dipeocc watch --auto-execute --interval 60
```

### Output Structure

Converted sessions are saved as:
```
projects/claude_code/
├── sessions/
│   ├── {session-id}/
│   │   ├── diagram.light.yaml  # Executable diagram
│   │   └── metadata.json       # Session metadata
│   └── ...
└── latest.light.yaml -> sessions/{latest}/diagram.light.yaml
```

### Full Documentation

For complete details on session conversion, see the [DiPeOCC Guide](../projects/dipeocc-guide.md).
