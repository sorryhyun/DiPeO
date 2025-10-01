# Subagent Collaboration Example

This example demonstrates how multiple subagents collaborate to build a complete DiPeO workflow.

## Scenario: Building a Data Processing Pipeline

The user requests: "I need to create a workflow that fetches data from multiple APIs, validates it, processes it with AI, and stores the results in a database."

## Subagent Collaboration Flow

### 1. Initial Analysis (Claude Code Main Agent)
Claude Code analyzes the request and identifies the need for multiple specialized subagents:
- **diagram-architect**: Overall workflow design
- **integration-expert**: API configurations
- **prompt-engineer**: AI processing prompts
- **node-specialist**: Node selection and configuration

### 2. Workflow Architecture (diagram-architect)

The diagram-architect designs the high-level workflow:

```yaml
# High-level structure designed by diagram-architect
Flow: Start -> Fetch APIs (parallel) -> Validate -> AI Process -> Store -> End

Patterns identified:
- Parallel API fetching for efficiency
- Early validation to fail fast
- Batch processing for AI operations
- Transaction safety for database operations
```

### 3. API Integration (integration-expert)

The integration-expert configures the API integrations:

```yaml
# API configurations by integration-expert
apis:
  weather_api:
    type: api_job
    props:
      url: "https://api.weather.com/v1/current"
      method: GET
      headers:
        X-API-Key: "{{weather_api_key}}"
      retry_count: 3
      cache_duration: 300

  market_data_api:
    type: api_job
    props:
      url: "https://api.markets.com/v2/quotes"
      method: POST
      body: |
        {
          "symbols": ["AAPL", "GOOGL"],
          "fields": ["price", "volume"]
        }
      authentication: oauth2
      rate_limit:
        requests_per_second: 10
```

### 4. Prompt Optimization (prompt-engineer)

The prompt-engineer creates optimized prompts for AI processing:

```yaml
# Optimized prompts by prompt-engineer
persons:
  Data Analyzer:
    service: openai
    model: gpt-5-mini-2025-08-07
    system_prompt: |
      You are a data analysis expert specializing in correlation detection.

      Analyze multi-source data for:
      - Patterns and anomalies
      - Cross-dataset correlations
      - Predictive indicators

      Input format: JSON with 'weather' and 'market' keys
      Output format:
      {
        "correlations": [{"type": "", "strength": 0.0-1.0, "description": ""}],
        "anomalies": [{"dataset": "", "description": "", "severity": ""}],
        "predictions": [{"metric": "", "trend": "", "confidence": 0.0-1.0}]
      }
```

### 5. Node Configuration (node-specialist)

The node-specialist selects and configures appropriate nodes:

```yaml
# Node configurations by node-specialist
nodes:
  - label: Validate Data
    type: code_job  # Chosen for deterministic validation
    props:
      language: python
      code: |
        import json
        from typing import Dict, List, Any

        def validate_data(data: Dict[str, Any]) -> Dict[str, Any]:
            errors = []

            # Check required fields
            if 'weather' not in data:
                errors.append("Missing weather data")
            if 'market' not in data:
                errors.append("Missing market data")

            # Validate data structures
            if 'weather' in data:
                if not isinstance(data['weather'].get('temperature'), (int, float)):
                    errors.append("Invalid temperature format")

            return {
                'is_valid': len(errors) == 0,
                'errors': errors,
                'data': data if len(errors) == 0 else None
            }

        return validate_data(input)

  - label: Process with AI
    type: person_job  # AI processing with BALANCED memory
    props:
      person: Data Analyzer
      memory_profile: BALANCED
      enable_dynamic_prompt: true
      batch_mode: true
      batch_size: 10
```

## Complete Integrated Workflow

The result of all subagents working together:

```yaml
version: light
description: Multi-source data processing pipeline with AI analysis

# Configurations from integration-expert
config:
  api_timeout: 30000
  retry_strategy: exponential_backoff
  database_pool_size: 10

# Personas from prompt-engineer
persons:
  Data Analyzer:
    service: openai
    model: gpt-5-mini-2025-08-07
    system_prompt: |
      [Optimized prompt from prompt-engineer]

  Quality Reviewer:
    service: openai
    model: gpt-5-nano-2025-08-07
    system_prompt: |
      [Secondary validation prompt]

# Nodes configured by node-specialist and diagram-architect
nodes:
  - label: Start
    type: start
    position: {x: 50, y: 300}
    props:
      trigger_mode: schedule
      schedule: "*/15 * * * *"  # Every 15 minutes

  # Parallel API fetching (diagram-architect pattern)
  - label: Fetch Weather
    type: api_job
    position: {x: 200, y: 200}
    props:
      [Weather API configuration from integration-expert]

  - label: Fetch Market Data
    type: api_job
    position: {x: 200, y: 400}
    props:
      [Market API configuration from integration-expert]

  - label: Merge Data
    type: code_job
    position: {x: 350, y: 300}
    props:
      language: javascript
      code: |
        return {
          weather: inputs.weather_data,
          market: inputs.market_data,
          timestamp: new Date().toISOString()
        };

  - label: Validate Data
    type: code_job
    position: {x: 500, y: 300}
    props:
      [Validation configuration from node-specialist]

  - label: Check Valid
    type: condition
    position: {x: 650, y: 300}
    props:
      condition_type: simple
      expression: "output.is_valid === true"

  - label: Analyze Data
    type: person_job
    position: {x: 800, y: 250}
    props:
      [AI processing configuration from node-specialist]

  - label: Store Results
    type: db
    position: {x: 950, y: 250}
    props:
      operation: insert
      table: analysis_results
      transaction: true

  - label: Handle Invalid
    type: code_job
    position: {x: 800, y: 400}
    props:
      language: python
      code: |
        import logging
        logging.error(f"Data validation failed: {input['errors']}")
        return {"status": "validation_failed", "errors": input['errors']}

# Edges designed by diagram-architect
edges:
  - source: Start
    target: Fetch Weather

  - source: Start
    target: Fetch Market Data

  - source: Fetch Weather
    target: Merge Data
    data_key: weather_data

  - source: Fetch Market Data
    target: Merge Data
    data_key: market_data

  - source: Merge Data
    target: Validate Data

  - source: Validate Data
    target: Check Valid

  - source: Check Valid
    target: Analyze Data
    condition: true

  - source: Check Valid
    target: Handle Invalid
    condition: false

  - source: Analyze Data
    target: Store Results

# Metadata showing subagent contributions
metadata:
  subagent_contributions:
    diagram-architect:
      - Overall workflow structure
      - Parallel processing pattern
      - Error handling flow

    integration-expert:
      - API authentication setup
      - Retry strategies
      - Caching configuration
      - Rate limiting

    prompt-engineer:
      - Data Analyzer prompt optimization
      - Output format specification
      - Token efficiency

    node-specialist:
      - Node type selection
      - Memory profile configuration
      - Batch processing setup
      - Validation logic

  optimization_notes:
    - "Parallel API fetching reduces total execution time by 50%"
    - "Early validation prevents expensive AI operations on bad data"
    - "Batch processing for AI reduces API calls by 10x"
    - "Transaction safety ensures database consistency"
```

## Benefits of Subagent Collaboration

1. **Specialized Expertise**: Each subagent brings deep knowledge in their domain
2. **Consistent Patterns**: Subagents apply best practices consistently
3. **Faster Development**: Parallel subagent work speeds up workflow creation
4. **Higher Quality**: Specialized optimization at each layer
5. **Maintainability**: Well-structured, documented workflows

## Triggering Subagents

### Automatic Delegation
When Claude Code sees certain patterns, it automatically delegates:
- "design a workflow" → diagram-architect
- "integrate with API" → integration-expert
- "optimize this prompt" → prompt-engineer
- "which node should I use" → node-specialist

### Explicit Request
Users can explicitly request specific subagents:
```
"Use the diagram-architect subagent to optimize this workflow for parallel processing"
```

## Conclusion

This example demonstrates how DiPeO's subagent system enables sophisticated workflow creation through specialized, collaborative AI agents. Each subagent contributes their expertise, resulting in production-ready, optimized workflows.