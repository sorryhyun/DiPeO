# DiPeO, Diagrammed People (agents) & Organizations (agent system)

> Start with `dipeo ask --to "the command you want to ask" --and-run`

![Watch Demo](./docs/pics/ad.webp)

* This will generate diagram and run it as you want to create.

### Why diagram?

* To show how it is **structured**, and how it works **in realtime**.
* For consistent outputs, rather than asking to code.

### Hmm, so can I tweak it?

<div style="text-align: center;"><img src="/docs/pics/img.png" width="85%" alt=""></div>


* Definitely. You can just run `make dev-web` and tweak it in `localhost:3000`
* The whole procedure works inside your computer. Nothing is in cloud or somewhere in network.

### How about the diagram file?

* You can see the diagram file in `.yaml`

<details>
    <summary>The diagram file content we created looks like...</summary>

```yaml
    version: light
    name: data_processor_pipeline_dipeo
    description: A robust, reusable data processor pipeline from ingestion to output, including validation, transformation, routing,
      error handling, and observability.
    nodes:
    - label: ObjectiveInput
      type: start
      position:
        x: 0
        y: 0
      props:
        trigger_mode: manual
        custom_data:
          user_prompt: create data processor diagram
        output_data_structure:
          type: object
    - label: DefineDataConfig
      type: code_job
      position:
        x: 260
        y: 0
      props:
        language: python
        code: |
          import json
    
          # Sample, compact DataSource and DataSink artifacts (small, concrete examples)
          data_sources = [
              {"id": "source_csv_1", "type": "csv", "location": "./data/input.csv", "schema": {"fields": {"id": "int", "name": "str", "value": "float", "timestamp": "str"}}},
              {"id": "source_api_1", "type": "api", "endpoint": "https://api.example.com/data", "schema": {"fields": {"id": "int", "category": "str", "amount": "float", "ts": "str"}}},
              {"id": "source_kafka_1", "type": "kafka", "topic": "events", "bootstrap_servers": ["localhost:9092"], "schema": {"fields": {"id": "str", "payload": "dict"}}}
          ]
    
          data_sinks = [
              {"id": "sink_dw", "type": "parquet_store", "destination": "./warehouse/parquet/", "schema": {"fields": {"id": "int", "name": "str", "value": "float", "timestamp": "str"}}},
              {"id": "sink_blob", "type": "filesystem", "destination": "./lake/csv/", "schema": {"fields": {"id": "int", "name": "str", "value": "float", "timestamp": "str"}}}
          ]
    
          transformation_plan = {"steps": ["clean_nulls", "normalize_fields", "enrich_with_metadata", "deduplicate"]}
    
```

</details>

* For example, the diagram you generated with `dipeo ask ...` will be placed in `projects/dipeodipeo/generated`
* We support `.light.yaml` format which will format the diagram in readable format.

### How can I start?

```bash
# Clone the repository first
make install          # Install all dependencies (installs uv if needed)
make graphql-schema   # Generate GraphQL types
make dev-all          # Start both frontend and backend servers
```

### Ok. So is there a rule for diagram? Or, would you explain more detail?

* Yes, here is the documentary in detail.
  - [Full Documentation Index](docs/index.md) - Complete list of guides and technical documentation
  - [User Guide](docs/README.md) - Getting started with DiPeO diagram editor
  - We are developing some interesting projects using `dipeo` itself. Take a look at [projects](docs/projects)

---

> DiPeO(daɪpiːɔː) is a **monorepo** for building, executing, and monitoring AI‑powered agent workflows through an intuitive visual programming environment. The repository is composed of a feature-based React **frontend** (apps/web/), a domain-driven FastAPI **backend** (apps/server/), and a CLI **tool** (apps/cli/) that work together to deliver real‑time, multi‑LLM automation at scale.

## 핵심 기능

1. LLM과 작업 블록의 분리를 통한 직관적인 컨텍스트 관리
2. diagram의 yaml 형태 표현 및 실행 tool 제공
3. 다이어그램 엔드포인트를 활용한 A2A canvas 제공 (구현 예정)

For motivations, guide, details in Korean, read [Korean docs](docs/index.md)

### Code Generation (For Development)

If you need to modify the codebase or add new features:

```bash
# After modifying TypeScript specifications in /dipeo/models/src/
cd dipeo/models && pnpm build     # Build TypeScript models
make codegen                      # Generate code (includes parse-typescript)
make diff-staged                  # Review changes
make apply-syntax-only            # Apply staged changes
make graphql-schema              # Update GraphQL types
```

## Major Features

### 1. Claude Code Integration

DiPeO features built-in support for Anthropic's Claude Code SDK, enabling seamless integration with Claude's advanced AI capabilities. Simply configure your diagram with Claude Code agents:

```yaml
persons:
  Frontend Generator:
    service: claude-code
    model: claude-code
    api_key_id: APIKEY_CLAUDE
    system_prompt: |
        You are an expert React/TypeScript engineer.
        Generate clean, production-ready code.
```

**Key Benefits:**
- Streaming-first architecture for real-time responses
- Built-in conversation management
- Automatic retry logic with exponential backoff
- Context manager pattern for efficient resource usage

For detailed setup and usage, see [Claude Code Integration Guide](docs/integrations/claude-code.md).

### 2. Frontend Auto - Rapid Application Generation

Generate complete, production-ready React applications in 30 minutes with Frontend Auto. This streamlined system creates fully deployable frontends with modern tech stack:

```bash
# Generate a complete chat application
dipeo run projects/frontend_auto/consolidated_generator --light --debug --timeout=120

# Generate with specific variant (e.g., e-commerce, analytics, banking)
dipeo run projects/frontend_auto/consolidated_generator --light --debug --timeout=120 \
  --input-data '{"config_file": "variants/ecommerce_config.json"}'
```

**Generated Features:**
- React 18 + TypeScript + Vite
- Tailwind CSS styling
- TanStack Query for data fetching
- React Router v6 navigation
- Complete component architecture (atoms/molecules/organisms)
- Mock API with real-time features
- Vercel-ready deployment configuration

**Available Variants:** Chat applications, e-commerce stores, analytics dashboards, banking portals, CMS systems, healthcare portals, learning platforms, project management tools, and more.

For comprehensive details, see the Frontend Auto project files in `projects/frontend_auto/`.

### 3. Multi-LLM Support

Beyond Claude Code, DiPeO supports multiple LLM providers:

**Ollama (Local Models):**
```yaml
persons:
  Frontend Generator:
    service: ollama
    model: gpt-oss:20b
    api_key_id: APIKEY_OLLAMA
    system_prompt: |
        You are an expert React/TypeScript engineer.
        Generate clean, production-ready code.
```

**Custom APIs and Services:**
- Notion integration
- Custom LLM endpoints via cURL
- Any RESTful API service

Thanks to our schema-driven integration system, adding new external API features is straightforward. See `integrations/` directory for examples.

For local model examples, see [Ollama example](examples/simple_diagrams/simple_iter_ollama.light.yaml).


### `dipeo` - Run Diagrams with CLI

#### Run existing diagrams
```bash
# Run diagram with automatic server startup
dipeo run examples/simple_diagrams/simple_iter --light --debug --timeout=25
# Run with specific diagram file
dipeo run examples/simple_diagrams/simple_iter.light.yaml --light --debug
# Run with input data
dipeo run [diagram] --input-data '{"key": "value"}' --light --debug
```

#### Generate diagrams from natural language
```bash
# Generate a diagram from natural language request
dipeo ask --to "create csv preprocessor" --timeout=90

# Generate and immediately run the created diagram
dipeo ask --to "create csv preprocessor" --and-run --timeout=90

# With additional options
dipeo ask --to "build data pipeline" --and-run --timeout=120
```

**Note**: The `dipeo ask` command uses AI to generate DiPeO diagrams from your natural language description. Generation typically takes 150-250 seconds due to multiple LLM calls.

## Requirements
- **Python 3.13+** (required for uv support)
- **Node.js 22+** with **pnpm 10+** (not npm/yarn)
- **uv** package manager (auto-installed via `make install`)
- Default LLM: `gpt-5-nano-2025-08-07`
