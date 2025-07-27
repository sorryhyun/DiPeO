
---

# Dog‑fooding DiPeO’s Code‑Generation System

## Overview of DiPeO

**DiPeO** (pronounced *daɪpiːɔː*) is a monorepo enabling users to build, execute, and monitor agent‑driven workflows through an intuitive visual programming environment.

* **Frontend:** Feature-based React UI
* **Backend:** Domain-driven FastAPI
* **CLI Tool:** For automation at scale (multi‑LLM, real‑time)
* **Key Features:**

  * Intuitive separation of LLM agents from work blocks for improved context management
  * YAML-based representation of diagrams + execution tooling
  * Plans for *A2A* (agent‑to‑agent) canvases
  * Local execution: all operations run on the user’s machine for privacy
  * Quick installation and launch: `make` commands to start frontend/backend

---

## Motivation and Philosophy

* DiPeO was created after observing that **existing diagram-based agent tools weren’t intuitive for developers**.
* Difficulties included:

  * Understanding context, memory, sandboxing
  * Distinguishing loops, conditionals, and agent tasks in diagrams
* **LLM agents as "persons"**:

  * Each LLM instance is a "person" with persistent memory
  * Memory is retained across tasks
  * Agents can share a global memory but selectively forget parts (per-agent policies)
* **Explicit diagrams:**

  * Loops and conditions are made explicit (e.g. `first_only`, max iterations, condition blocks)
  * The canvas acts as a sandboxed space; diagrams can form agent-to-agent networks
  * Conversations are globally stored, with memory governed by policies (e.g. `no_forget`, `on_every_turn`)

---

## Memory System Design

* **Global conversation model:** All messages from every agent are stored in a single, immutable, shared conversation
* **Memory views:** Agents view the conversation through filters:

  * `ALL_INVOLVED`, `SENT_BY_ME`, `SENT_TO_ME`, `SYSTEM_AND_ME`, `CONVERSATION_PAIRS`
* **Sliding window:** Limit messages (e.g., last *n* messages)
* **Job-level config:** Memory settings are at the job, not the person, level

### Memory Patterns

* **Debate:** Agents focus on current exchanges, judges maintain full context
* **Pipeline:** Context decreases through stages (analysis → summarization → extraction)
* **Multi-agent collaboration:** Different agents perceive the conversation differently (researcher, critic, moderator)

**Timing:**

* `on_every_turn`, `upon_request`, `no_forget`
* Forgetting is non-destructive; messages are hidden, not deleted

**Best practices:**

* Choose the right memory view for each task
* Set reasonable message limits
* Design memory flow from full to minimal context
* Always preserve system prompts

---

## Diagram Formats and Node Types

DiPeO diagrams can be represented as:

1. **Domain JSON:** Canonical, persistent, full structure/layout data
2. **Light YAML:** Simplified for readability, positions rounded, IDs removed
3. **Readable YAML:** Optimized for workflow comprehension; flows as lines, definitions separated

**Node Types:**

* `start`: Entry point, with trigger mode
* `person_job`: LLM-powered task for a person; supports prompts, iterations, memory profiles (FULL, FOCUSED, MINIMAL, GOLDFISH)
* `condition`: Branching logic, can trigger on all jobs or custom expressions
* `code_job`: Executes code (Python, TypeScript, Bash, Shell) inline or from files (inline code must output to a result variable; `print()` unsupported)
* `endpoint`: Saves results to files (text, JSON, YAML)
* `db`: Reads from files or databases
* `api_job`: Performs HTTP requests
* `user_response`: Captures user input

**Memory Profiles:**

* **FULL:** All messages
* **FOCUSED:** Last 20 pairs
* **MINIMAL:** System + last 5 messages
* **GOLDFISH:** Last 2 messages only (no system preservation)

*Light guide available in Korean, too*.

---

## Cutting‑Edge Code‑Generation and Meta‑Coding Features

### Automatic GraphQL Type Generation

* Generator produces Strawberry GraphQL types directly from `domain-schema.graphql`
* Reduces boilerplate (\~70%), enforces consistency
* Converts TypeScript models → GraphQL schema → Strawberry types
* Triggered via `dipeo run` or `make codegen`
* Types are imported into the server automatically
* Proof of self-hosting: DiPeO uses its own execution engine to build its API layer

### Multi-language Model Generation

* System consumes TypeScript ASTs, produces Python Pydantic models, and other artifacts
* Custom Jinja2 filters:

  * snake/camel/pascal conversion
  * pluralization
  * type conversion (e.g., `str` ↔ `string`)
  * default value mapping
* Template environment loads templates from strings, registers filters
* `python_models.py` generator:

  * Handles optional types, arrays, maps, unions, branded IDs
  * Mappings define node→UI fields, Zod schemas, Pydantic defaults
* Result: **Single source of truth** (TS definitions) across backend (Pydantic), frontend (React), API types

### Dog‑fooding via Diagram‑Driven Codegen

* Code generation is orchestrated through diagrams
* `run_codegen.py` creates a temporary diagram, runs it via the DiPeO CLI (`dipeo run <diagram>`)
* DiPeO’s visual engine generates code for new nodes/UI—*dog‑fooding* in action

### Extensible Node Specifications

* Node behavior defined in TypeScript specs: fields, UI config, execution, examples
* Example: Sub-Diagram node spec defines diagram selection, I/O mapping, timeouts, context options
* Specs power the codegen system: auto-generate backend models, GraphQL types, frontend forms
* UI metadata ensures consistency and extensibility

---

## Strengths and Unique Value

* **Intuitive memory/context management:** Each LLM is a person with persistent memory; global convo model + per-agent views = fine‑grained control
* **Visual programming w/ YAML round‑tripping:** Export/import diagrams as JSON/YAML; edit in code editor; Light YAML for quick edits, Domain JSON for full fidelity
* **Self‑hosted operation & privacy:** All processing local, no external server
* **Dog‑fooding meta‑codegen:** Platform uses itself for codegen—robustness, less manual work
* **Cross‑language consistency:** TS models as single source of truth for Python types, Zod schemas, UI
* **Flexible agent collaboration:** Debate, pipeline, multi-agent patterns for complex workflows
* **Extensible node system:** Node specs w/ UI metadata and execution rules → new nodes via diagrams

---

## Conclusion

> **DiPeO** is more than a diagram editor.
> It’s a full‑stack platform integrating visual programming, robust memory management, and automated code generation. By modelling LLMs as persistent "persons" with global conversations and per‑agent filters, DiPeO lets developers design complex multi‑agent workflows *intuitively*. Its dog‑fooding approach—diagrams generating Pydantic models and GraphQL types—showcases a forward‑looking meta‑coding paradigm. With privacy‑preserving local execution, cross‑language codegen, and flexible pattern abstractions, DiPeO stands out for building and experimenting with AI-driven agents.

---
