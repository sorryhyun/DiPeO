# DiPeO, Diagrammed People (agents) & Organizations (agent system)

> Start with `dipeo ask "the command you want to ask" --and-run`

![image info](/docs/actual_screenshot.png)



DiPeO(daɪpiːɔː) is a **monorepo** for building, executing, and monitoring AI‑powered agent workflows through an intuitive visual programming environment. The repository is composed of a feature-based React **frontend** (apps/web/), a domain-driven FastAPI **backend** (apps/server/), and a CLI **tool** (apps/cli/) that work together to deliver real‑time, multi‑LLM automation at scale.

## 핵심 기능

1. LLM과 작업 블록의 분리를 통한 직관적인 컨텍스트 관리
2. diagram의 yaml 형태 표현 및 실행 tool 제공
3. 다이어그램 엔드포인트를 활용한 A2A canvas 제공 (구현 예정)

For motivations, guide, details in Korean, read [Korean docs](docs/korean/index.md)

## Dev settings:

```bash
# clone github project first
make install
make graphql-schema  # Generate GraphQL types
make dev-all
```

That's it! This will:
- Install dependencies if it's your first time
- Generate GraphQL schema and TypeScript types
- Start both frontend and backend services

### Code Generation (For Development)

If you need to modify the codebase or add new features:

```bash
# After modifying TypeScript specifications
cd dipeo/models && pnpm build  # Build TypeScript models
dipeo run codegen/diagrams/generate_all --light --debug --timeout=90  # Generate code
make apply-syntax-only  # Apply staged changes
make graphql-schema  # Update GraphQL types
```

## ollama supports
- Now we support ollama. All you have to do is add random api key to the file and write the diagram as:
```yaml
persons:
  person 1:
    service: ollama
    model: gpt-oss:20b
    api_key_id: APIKEY_21A814
```
read [example](files/diagrams/examples/simple_iter_ollama.light.yaml)

## Integrated API supports
- We support Notion, custom LLM with curl, ... etc, any API services


### `dipeo` - Run Diagrams with CLI

#### Run existing diagrams
```bash
# run diagram with automatically running server
dipeo run diagrams/examples/simple_iter --debug --light --timeout=10
# or, feed actual directory
dipeo run files/diagrams/examples/simple_iter.light.yaml --light --debug
```

#### Generate diagrams from natural language
```bash
# Generate a diagram from natural language request
dipeo ask --to "create csv preprocessor" --timeout=90

# Generate and immediately run the created diagram
dipeo ask --to "create csv preprocessor" --and-run --timeout=90

# With additional options
dipeo ask --to "build data pipeline" --and-run --debug --timeout=120 --run-timeout=300
```

**Note**: The `dipeo ask` command uses AI to generate DiPeO diagrams from your natural language description. Generation typically takes 60-90 seconds due to multiple LLM calls. Use `--timeout 120` for complex requests.

### Documentation
- [Full Documentation Index](docs/index.md) - Complete list of guides and technical documentation
- [User Guide](docs/README.md) - Getting started with DiPeO diagram editor


## Requirements
- Node.js 22+ with pnpm 10+
- Python 3.13+
- tmux (optional, for better parallel execution)

## 0.4.0 Release will include
- Automatic dipeo diagram generation service
