# Complex DiPeO Diagram Examples

This document describes three complex diagram examples created for the DiPeO system.

## 1. Data Processing Pipeline (`data_processing_pipeline.yaml`)

A comprehensive data processing workflow that demonstrates:
- **Multi-source data loading**: Reads raw data CSV and configuration JSON
- **Data quality assessment**: AI-powered quality scoring with threshold checks
- **Conditional branching**: Routes to success or error paths based on quality
- **Data transformation**: AI-driven data cleaning and transformation
- **API enrichment**: External API integration for data enhancement
- **Pattern analysis**: AI analysis of processed data trends
- **Report generation**: Professional markdown reports with insights
- **Error handling**: Graceful failure paths with detailed error reports

**Key Features:**
- 4 specialized AI agents (Analyst, QualityChecker, Transformer, ReportWriter)
- Python code execution for data parsing and validation
- API integration for real-time exchange rates
- Multiple output formats (MD, JSON)
- Quality-based conditional routing

**Requirements:**
- `files/uploads/raw_data.csv` - Input data file
- `files/config/processing_rules.json` - Processing configuration

## 2. Research Assistant with Memory (`research_assistant_memory.yaml`)

An intelligent research workflow with iterative refinement:
- **User-driven topics**: Interactive topic input
- **Dynamic search query generation**: AI creates diverse search strategies
- **Web search integration**: Real-time information gathering
- **Fact verification**: Dedicated fact-checking with confidence ratings
- **Iterative improvement**: Up to 3 research iterations based on gaps
- **Memory management**: Different memory profiles for different stages
- **Critical review**: Identifies biases and missing information
- **Structured output**: Professional research reports with citations

**Key Features:**
- 4 specialized AI agents (Researcher, FactChecker, Synthesizer, Critic)
- Web search tool integration
- Sophisticated memory profiles (FULL, FOCUSED, MINIMAL)
- Iterative research loops with gap analysis
- Structured metadata output

**Requirements:**
- User input for research topic
- No file dependencies

## 3. Content Creation Workflow (`content_creation_workflow.yaml`)

A complete content production pipeline:
- **Requirements gathering**: Interactive input for content specifications
- **SEO optimization**: Keyword generation and optimization
- **Content brief creation**: Structured content planning
- **Iterative writing**: Up to 3 revision cycles for quality
- **Professional editing**: Grammar, style, and consistency checks
- **Quality assessment**: Automated scoring with multiple metrics
- **Image prompt generation**: AI-created prompts for visual content
- **Publishing packages**: Ready-to-publish content with metadata

**Key Features:**
- 5 specialized AI agents (Strategist, Writer, Editor, SEO Optimizer, Image Creator)
- Quality scoring system with thresholds
- Revision loops with maximum iteration limits
- Multiple output formats
- Manual review fallback for low-quality content

**Requirements:**
- User input for content requirements
- Optional SEO keywords input

## Running the Diagrams

### Basic execution:
```bash
dipeo run <diagram_name> --light --debug --no-browser
```

### With timeout:
```bash
dipeo run <diagram_name> --light --debug --no-browser --timeout=60
```

### View in browser:
```
http://localhost:3000/?diagram=<diagram_name>.light.yaml
```

## Testing Notes

1. **Data Processing Pipeline**: Requires test data files. Will fail quality check if data has errors (by design).

2. **Research Assistant**: Requires user input for research topic. Best tested interactively or with browser view.

3. **Content Creation**: Requires user input for content requirements. Supports revision loops based on quality.

All diagrams showcase advanced DiPeO features including:
- Multiple node types (person_job, condition, code_job, api_job, etc.)
- Complex connection patterns
- Variable passing between nodes
- Memory profile management
- Conditional execution flows
- Error handling
- File I/O operations