# DiPeO Technical Stack & Architecture

## Overview
DiPeO (Diagrammed People & Organizations) is a monorepo-based visual programming environment for AI agent workflows, featuring real-time execution and monitoring capabilities.

## Tech Stack

### Frontend (React/TypeScript)
**Core Framework:**
- React 19.1.0 with TypeScript 5.8.3
- Vite 5.4.19 (build tool with HMR)
- pnpm workspace monorepo

**UI & Visualization:**
- @xyflow/react 12.6.4 - Flow diagram editor
- Tailwind CSS 3.4.17 - Utility-first styling
- Lucide React 0.511.0 - Icon library
- React Resizable Panels 3.0.2 - Panel layouts
- React Window 1.8.11 - Virtualization for performance

**State Management:**
- Zustand 5.0.5 - Global state management
- TanStack Query 5.79.0 - Server state & caching
- Apollo Client 3.13.8 - GraphQL client (underutilized)
- Immer 10.1.1 - Immutable state updates
- React Hook Form 7.57.0 + Zod 3.25.42 - Form handling & validation

**Communication:**
- Apollo Client 3.13.8 - GraphQL client
- GraphQL-WS 6.0.5 - WebSocket subscriptions
- TRPC 11.1.4 - Type-safe API layer

### Backend (Python/FastAPI)
**Core Framework:**
- FastAPI 0.115.13 - Modern async web framework
- Hypercorn 0.17.3 - ASGI server with multi-worker support
- Python 3.12+ with type hints

**GraphQL & API:**
- Strawberry GraphQL 0.274.2 - GraphQL server
- Pydantic 2.11.7 - Data validation
- WebSockets 15.0.1 - Real-time communication

**LLM Integrations:**
- OpenAI 1.88.0
- Anthropic 0.54.0
- Google GenAI 1.21.0
- Custom prompt management system

**Infrastructure:**
- Prometheus Client 0.22.1 - Metrics collection
- Structlog 24.4.0 - Structured logging
- Python-dotenv 1.1.0 - Environment management
