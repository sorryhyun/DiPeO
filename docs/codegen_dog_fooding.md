
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

### Multi-language Model Generation (V2 Architecture)

* **Dynamic discovery**: System automatically finds all TypeScript files using glob patterns
* **AST caching**: Parsed TypeScript cached to `/temp/` for performance
* **Template-based generation**: V2 uses `template_job` nodes for direct rendering

**Generation flow**:
1. Parse all TypeScript → Cache AST
2. Generate Python models, enums, validations → Staged directory
3. Apply staged changes with syntax validation
4. Generate frontend using applied models
5. Export GraphQL schema and generate TypeScript types

**Custom Jinja2 filters**:
* `ts_to_python`, `ts_to_graphql` - Type conversions
* `snake_case`, `camel_case`, `pascal_case` - Naming conventions
* `pluralize` - Collection naming
* `get_graphql_type`, `get_zod_type` - Framework-specific types

**Key generators**:
* `/projects/codegen/code/models/` - Python model generation
* `/projects/codegen/code/frontend/` - React/TypeScript generation
* All use external files for testability and reuse

**Result**: **Single source of truth** (TS definitions) generating:
* Python Pydantic models with validation
* GraphQL schema and Strawberry types
* React components with Zod validation
* Fully typed GraphQL operations

### Dog‑fooding via Diagram‑Driven Codegen

* **All code generation is orchestrated through DiPeO diagrams** - no traditional code generators
* Located in `/projects/codegen/diagrams/` with sub-folders for models, frontend, and shared utilities
* **Direct execution**: `make codegen` runs `dipeo run codegen/diagrams/models/generate_all_models --light`
* **Staging approach**: Generated code goes to `/dipeo/diagram_generated_staged/` for validation before applying
* **External code**: All generation logic in `/projects/codegen/code/` matching diagram structure
* DiPeO's execution engine generates its own code—true *dog‑fooding* in action

### Extensible Node Specifications

* Node behavior defined in TypeScript specs: fields, UI config, execution, examples
* Example: Sub-Diagram node spec defines diagram selection, I/O mapping, timeouts, context options
* Specs power the codegen system: auto-generate backend models, GraphQL types, frontend forms
* UI metadata ensures consistency and extensibility

### Staging System and Validation

* **Staged generation**: All generated code goes to `/dipeo/diagram_generated_staged/` first
* **Syntax validation**: Python compilation check ensures generated code is valid
* **Preview changes**: `make diff-staged` shows what will change
* **Atomic updates**: Apply all changes or none - prevents partial updates
* **Rollback safety**: Easy to discard bad generations before applying

### Batch Processing and Parallelization

* **Batch sub-diagrams**: Generate multiple nodes in parallel using `batch: true`
* **Dynamic lists**: Discover files with glob patterns, process in batches
* **Error resilience**: Failed items don't stop other generations
* **Performance**: Parallel processing significantly reduces generation time
* Example: Frontend generation processes all node specs concurrently

---

## Strengths and Unique Value

* **Intuitive memory/context management:** Each LLM is a person with persistent memory; global convo model + per-agent views = fine‑grained control
* **Visual programming w/ YAML round‑tripping:** Export/import diagrams as JSON/YAML; edit in code editor; Light YAML for quick edits, Domain JSON for full fidelity
* **Self‑hosted operation & privacy:** All processing local, no external server
* **Advanced dog‑fooding meta‑codegen:** 
  * Platform uses itself for all code generation—proven robustness
  * Staging system ensures safe updates with validation
  * External code organization enables testing and reuse
  * V2 template jobs simplify generation flow
* **Cross‑language consistency:** TS models as single source of truth generating:
  * Python Pydantic models with full validation
  * GraphQL schema with Strawberry types
  * React components with TypeScript types
  * Zod validation schemas
* **Flexible agent collaboration:** Debate, pipeline, multi-agent patterns for complex workflows
* **Extensible node system:** 
  * Node specs define complete behavior
  * Auto-discovery of new specifications
  * Parallel generation for performance
  * UI metadata ensures consistency

---

## Conclusion

> **DiPeO** is more than a diagram editor.
> It's a full‑stack platform integrating visual programming, robust memory management, and automated code generation. By modelling LLMs as persistent "persons" with global conversations and per‑agent filters, DiPeO lets developers design complex multi‑agent workflows *intuitively*. 
>
> Its advanced dog‑fooding approach—where DiPeO diagrams orchestrate the generation of DiPeO's own code—demonstrates the platform's maturity and capabilities. The v2 architecture with staging directories, external code organization, and parallel batch processing shows how visual programming can handle sophisticated meta-programming tasks.
>
> With privacy‑preserving local execution, cross‑language type safety from a single TypeScript source of truth, and flexible pattern abstractions, DiPeO exemplifies the future of AI-driven development tools—where the platform builds itself.

---
