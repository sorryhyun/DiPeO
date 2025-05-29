# AgentDiagram Backend – Essential Guide

## Purpose

A streamlined reference for setting up, running, and integrating the **AgentDiagram Backend**—a high‑performance FastAPI service for visual LLM workflows with real‑time streaming and conversation memory.

---

## Quick Start

```bash
# Clone & enter backend
cd apps/server

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy example config and edit as needed
cp .env.example .env

# Run the server
python main.py
# or. uvicorn main:app --reload --port 8000
```

Visit **[http://localhost:8000/docs](http://localhost:8000/docs)** for interactive Swagger UI.

---

## Directory Layout (trimmed)

```
src/
├── services/          # Business logic & integrations
├── utils/             # Helper utilities
├── run_graph.py       # Core execution engine
├── constants.py       # Enums & constants
└── exceptions.py      # Custom errors
```

---

## Execution Flow (high level)

1. **Diagram Validation** – checks structure & dependencies
2. **Scheduling** – topological sort with condition handling
3. **Node Execution** – processes nodes, streams updates (SSE)
4. **Memory Update** – persists conversation context
5. **Result Aggregation** – collects outputs, costs, and statuses

---

## Key API Endpoints

| Endpoint                | Method          | Description                 | Stream |
| ----------------------- | --------------- | --------------------------- | ------ |
| `/api/run-diagram`      | POST            | Execute diagram (streaming) | ✅      |
| `/api/run-diagram-sync` | POST            | Execute diagram (sync)      | ❌      |
| `/api/apikeys`          | GET/POST/DELETE | Manage API keys             | ❌      |
| `/api/models`           | GET             | List available models       | ❌      |
| `/api/conversations`    | GET             | Query conversation history  | ❌      |

### Example Streaming Payload

```json
{"type":"node_start","nodeId":"node-123"}
{"type":"node_complete","nodeId":"node-123","output_preview":"..."}
{"type":"execution_complete","total_cost":0.05}
```

---

## Core Environment Variables

| Variable               | Purpose                  | Default                     |
| ---------------------- | ------------------------ | --------------------------- |
| `BASE_DIR`             | Allowed file root        | `/app`                      |
| `MAX_CONCURRENT_NODES` | Parallel execution limit | `10`                        |
| `REQUEST_TIMEOUT`      | Seconds to wait for node | `300`                       |
| `ALLOWED_ORIGINS`      | CORS whitelist           | `["http://localhost:3000"]` |
| `MAX_FILE_SIZE`        | Upload limit (bytes)     | `10485760`                  |
| `LOG_LEVEL`            | Logging level            | `INFO`                      |

---

## Deployment (Docker)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Security Essentials

* **Validate paths** against `BASE_DIR` before any file I/O.
* **Never log** raw API keys or sensitive data.
* **Rate‑limit** endpoints and enable SSL/TLS in production.
* Use **sandboxed code execution** and Pydantic validation for all inputs.

---

## Need More?

For advanced features—custom node types, multi‑LLM adapters, testing, or observability—refer to the full documentation in the original `CLAUDE.md`.
