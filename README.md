# DiPeO, Diagrammed People (agents) & Organizations (agent system)
![image info](/docs/image.png)

DiPeO(daɪpiːɔː) is a **monorepo** for building, executing, and monitoring AI‑powered agent workflows through an intuitive visual programming environment. The repository is composed of a feature-based React **frontend** (apps/web/), a domain-driven FastAPI **backend** (apps/server/), and a CLI **tool** (apps/cli/) that work together to deliver real‑time, multi‑LLM automation at scale.

## 핵심 기능

1. LLM과 작업 블록의 분리를 통한 직관적인 컨텍스트 관리
2. diagram의 yaml 형태 표현 및 실행 tool 제공
3. 다이어그램 엔드포인트를 활용한 A2A canvas 제공 (구현 예정)

## Quickstart

[windows installer](https://github.com/sorryhyun/DiPeO/releases/tag/betav6)

For Korean guide for quickstart, read [Korean docs](docs/korean_install_guide.md)

dev settings:

```bash
make install
make codegen
make dev-all
```

That's it! This will:
- Install dependencies if it's your first time
- Generate required code
- Start both frontend and backend services

## Essential Scripts

### Makefile Commands
```bash
make dev-server                   # Start backend server
make dev-web                      # Start frontend server
```

### `./dipeo` - Run Diagrams
```bash
# run diagram with automatically running server
dipeo run examples/simple_iter --debug --light --no-browser --timeout=10
# or, feed actual directory
dipeo run files/diagrams/native_examples/quicksave.native.json --debug
```

### Docs
Note [docs](docs)

## Requirements
- Node.js 22+ with pnpm 10+
- Python 3.13+
- tmux (optional, for better parallel execution)


## Next Release will be
- hook node for general event hooks. i.e. youtube subtitle generator
- gemini supports

## Near-future objectives
- Gemini, Claude support
- Custom LLM support
