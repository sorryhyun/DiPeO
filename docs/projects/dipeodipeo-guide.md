# DiPeO AI Diagram Generation Guide

## Overview {#overview}

The `dipeodipeo` project demonstrates DiPeO's ultimate dog-fooding capability - using DiPeO diagrams to generate new DiPeO diagrams through AI. This meta-programming approach leverages Large Language Models (LLMs) with structured output to automatically create executable workflows from natural language descriptions.

**Key Achievement**: DiPeO is mature enough to use itself to extend itself, creating a self-improving system where AI agents design new automation workflows.

## System Architecture {#system-architecture}

```
Natural Language Request → Prompt Engineering → AI Diagram Generation → Post-Processing → Executable Diagram
                                     ↓
                          Test Data Generation
```

The system orchestrates three specialized AI agents:
1. **Prompt Engineer** - Transforms user requirements into detailed generation prompts
2. **Diagram Designer** - Creates structured DiPeO diagrams following best practices
3. **Test Data Creator** - Generates realistic test data for diagram validation

## Core Components {#core-components}

### 1. Light Diagram Models (`light_diagram_models.py`) {#1-light-diagram-models-light_diagram_modelspy}

Defines Pydantic models that provide structured output schemas for LLMs:

```python
# Typed node classes for each DiPeO node type
class PersonJobNode(BaseModel):
    label: str
    type: Literal[LightNodeType.PERSON_JOB]
    position: Position
    props: PersonJobNodeData

# Complete diagram specification
class LightDiagram(BaseModel):
    version: Literal["light"] = "light"
    name: str
    description: str
    nodes: List[LightNode]
    connections: List[LightConnection]
    persons: Optional[Dict[str, LightPerson]]
```

**Key Features**:
- Inherits from DiPeO's generated domain models for consistency
- Excludes redundant fields (like `label` in props) for cleaner generation
- Includes validation to ensure diagram correctness
- Provides type safety for AI-generated outputs

### 2. Generation Pipeline (`test.light.yaml`) {#2-generation-pipeline-testlightyaml}

The main workflow that orchestrates the generation process:

```yaml
nodes:
  - label: load_request
    type: code_job
    # Loads user requirements from file or input
  
  - label: generate_prompt
    type: person_job
    # AI creates optimized prompt for diagram generation
    
  - label: generate_test_data
    type: person_job  
    # AI creates test data for the workflow
    
  - label: generate_diagram
    type: person_job
    # AI creates the actual DiPeO diagram
    
  - label: format_yaml
    type: code_job
    # Post-processes to clean YAML output
```

### 3. Post-Processing (`process.py`) {#3-post-processing-processpy}

Cleans and formats AI-generated diagrams:

```python
def process_diagram(inputs: Dict[str, Any]) -> str:
    # Remove null values and empty collections
    # Fix code field formatting for readability
    # Order keys logically (version, name, description, etc.)
    # Generate clean YAML with proper multiline strings
```

**Improvements Applied**:
- Removes AI-generated null fields
- Converts escaped newlines to proper multiline YAML
- Ensures consistent key ordering
- Uses literal scalar format (`|`) for code blocks

### 4. Prompt Templates (`prompts/`) {#4-prompt-templates-prompts}

#### `diagram_generator.txt` {#diagram_generatortxt}
Contains comprehensive instructions for AI diagram generation:
- Content type rules (never use 'empty')
- Node positioning guidelines (x increment by 200-300)
- Node selection best practices
- Code patterns for common tasks
- Error handling requirements

#### `prompt_generator.txt` {#prompt_generatortxt}
Guides the prompt engineer agent to create effective prompts

#### `test_data_generator.txt` {#test_data_generatortxt}
Instructions for creating realistic test data in various formats

## Generation Workflow {#generation-workflow}

### Step 1: Define Requirements {#step-1-define-requirements}

Create or update `request.txt` with your workflow description:
```text
Create a data processing pipeline that:
1. Loads CSV files from a directory
2. Validates the data format
3. Processes each file in parallel
4. Aggregates results
5. Saves to JSON output
```

### Step 2: Run Generation {#step-2-run-generation}

```bash
dipeo run projects/dipeodipeo/test --light --debug --timeout=60
```

### Step 3: Review Generated Files {#step-3-review-generated-files}

**Generated Diagram**: `projects/dipeodipeo/generated/diagram.light.yaml`
- Complete, executable DiPeO diagram
- Properly formatted with clean YAML
- Includes all necessary node configurations

**Test Data**: `projects/dipeodipeo/generated/test_data.csv`
- Realistic sample data for testing
- Matches the expected input format
- Can be used immediately with the generated diagram

### Step 4: Execute Generated Diagram {#step-4-execute-generated-diagram}

```bash
dipeo run projects/dipeodipeo/generated/diagram --light --debug
```

## Advanced Features {#advanced-features}

### Dynamic Input Support {#dynamic-input-support}

The system can accept runtime parameters instead of reading from files:

```bash
dipeo run projects/dipeodipeo/test --light \
  --input-data '{"user_requirements": "Create a web scraping workflow", "workflow_description": "Scrape product data from e-commerce sites"}'
```

### Custom AI Models {#custom-ai-models}

Configure different LLM providers and models in `test.light.yaml`:

```yaml
persons:
  diagram_designer:
    service: anthropic  # or openai, ollama
    model: claude-3-sonnet
    api_key_id: APIKEY_ANTHROPIC
```

### Structured Output with Pydantic {#structured-output-with-pydantic}

The system uses OpenAI's structured output feature with Pydantic models to ensure:
- Valid diagram syntax
- Type-safe node properties
- Proper connection definitions
- No missing required fields

### Test Data Models (`test_data_models.py`) {#test-data-models-test_data_modelspy}

Defines Pydantic schemas for test data generation:

```python
class DataRecord(BaseModel):
    id: str
    name: str
    value: float
    timestamp: str

class TestDataResponse(BaseModel):
    records: List[DataRecord]
    metadata: Dict[str, Any]
```

## Best Practices and Guidelines {#best-practices-and-guidelines}

### 1. AI Agent Configuration {#1-ai-agent-configuration}

**Prompt Engineer**:
- Focuses on clarity and specificity
- Breaks down complex requirements
- Adds implementation hints

**Diagram Designer**:
- Follows DiPeO conventions strictly
- Ensures proper node positioning
- Never uses deprecated features

**Test Data Creator**:
- Generates meaningful, realistic data
- Follows the specified schema
- Includes edge cases

### 2. Content Type Rules {#2-content-type-rules}

The system enforces strict content type usage:
- `raw_text` - Plain text, CSV, unstructured data
- `object` - Structured data (JSON, dictionaries)
- `conversation_state` - LLM conversation contexts
- **Never** `empty` - Provides no value

### 3. Node Selection Strategy {#3-node-selection-strategy}

- **code_job** - All data processing and transformation
- **person_job** - Only when AI analysis is required
- **db** - File I/O operations
- **No sub_diagram** - Use asyncio in code_job instead

### 4. Error Handling {#4-error-handling}

Generated diagrams include:
- Validation nodes after data loading
- Condition nodes for error branching
- Try-except blocks in code
- Detailed logging

## Integration with DiPeO Ecosystem {#integration-with-dipeo-ecosystem}

### Relationship to Code Generation {#relationship-to-code-generation}

While `/projects/codegen/` generates DiPeO's internal code from TypeScript specs, `dipeodipeo` generates user-facing diagrams from natural language. Together they demonstrate:

- **codegen**: DiPeO building itself (infrastructure)
- **dipeodipeo**: DiPeO extending itself (user workflows)

### Dog-fooding Hierarchy {#dog-fooding-hierarchy}

```
Level 1: DiPeO executes diagrams (basic capability)
Level 2: DiPeO diagrams generate DiPeO code (codegen)
Level 3: DiPeO diagrams generate new DiPeO diagrams (dipeodipeo)
```

This recursive capability proves the platform's maturity and flexibility.

## Common Use Cases {#common-use-cases}

### 1. Rapid Prototyping {#1-rapid-prototyping}

Transform ideas into working diagrams in seconds:
```bash
echo "Create a workflow to analyze sentiment in customer reviews" > request.txt
dipeo run projects/dipeodipeo/test --light
```

### 2. Batch Diagram Creation {#2-batch-diagram-creation}

Generate multiple related diagrams programmatically:
```python
workflows = [
    "Data validation pipeline",
    "Report generation system",
    "API integration workflow"
]

for workflow in workflows:
    # Run generation with different inputs
    subprocess.run([
        "dipeo", "run", "projects/dipeodipeo/test",
        "--light", "--input-data", 
        json.dumps({"user_requirements": workflow})
    ])
```

### 3. Template Generation {#3-template-generation}

Use as a starting point for complex diagrams:
1. Generate basic structure with AI
2. Manually refine and extend
3. Add domain-specific logic

## Limitations and Considerations {#limitations-and-considerations}

### Current Limitations {#current-limitations}

1. **Complexity Ceiling**: Very complex multi-stage workflows may need manual refinement
2. **Domain Knowledge**: AI may not understand specialized business logic
3. **Performance Optimization**: Generated code may need optimization for large-scale data
4. **Security**: Always review generated code for security implications

### When to Use Manual Creation {#when-to-use-manual-creation}

- Mission-critical workflows requiring precise control
- Highly optimized performance requirements
- Complex integration with external systems
- Workflows with sensitive security requirements

## Troubleshooting {#troubleshooting}

### Generated Diagram Won't Execute {#generated-diagram-wont-execute}

1. Check for syntax errors:
   ```bash
   dipeo run projects/dipeodipeo/generated/diagram --light --validate-only
   ```

2. Verify all referenced files exist
3. Ensure API keys are configured
4. Check connection labels match node expectations

### AI Generation Quality Issues {#ai-generation-quality-issues}

1. Improve the prompt in `request.txt`
2. Add specific examples to prompt templates
3. Use more capable models (GPT-4, Claude)
4. Provide sample test data for context

### Post-Processing Errors {#post-processing-errors}

If `format_yaml` fails:
1. Check the raw AI output for malformed YAML
2. Verify Pydantic models match current DiPeO schema
3. Update `process.py` for new node types


## Conclusion {#conclusion}

The `dipeodipeo` project represents the pinnacle of DiPeO's self-referential capabilities. By using AI-powered DiPeO diagrams to generate new DiPeO diagrams, it creates a powerful feedback loop where the platform can extend and improve itself. This approach democratizes workflow automation, allowing users to describe what they want in natural language and receive executable solutions immediately.

The system's structured output approach, comprehensive validation, and post-processing ensure that generated diagrams are not just syntactically correct but follow best practices and are immediately executable. This makes DiPeO accessible to non-technical users while maintaining the power and flexibility that developers expect.
