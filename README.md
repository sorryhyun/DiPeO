# DiPeO, Diagrammed People (agents) & Organizations (agent system)
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
make codegen
make dev-all
```

That's it! This will:
- Install dependencies if it's your first time
- Generate required code
- Start both frontend and backend services

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
```bash
# run diagram with automatically running server
dipeo run diagrams/examples/simple_iter --debug --light --timeout=10
# or, feed actual directory
dipeo run files/diagrams/examples/simple_iter.light.yaml --light --debug
```

### Documentation
- [Full Documentation Index](docs/index.md) - Complete list of guides and technical documentation
- [User Guide](docs/README.md) - Getting started with DiPeO diagram editor


## Requirements
- Node.js 22+ with pnpm 10+
- Python 3.13+
- tmux (optional, for better parallel execution)

- 0.3.0 Release will include
  - Light formatted diagram Pydantic model for automatic diagram generation
  - Example diagram for self-evolving LLMs
