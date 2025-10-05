# Metrics Enhancement Analysis

## Current State

The `dipeo metrics --latest --breakdown` command provides:
- ✅ Node-level timing
- ✅ Phase breakdown with hierarchical structure (e.g., `memory_selection__api_call`)
- ✅ Token usage tracking
- ✅ Bottleneck identification
- ✅ System operations timing

### Current Instrumentation Coverage

#### Already Tracked:
1. **LLM Service** (`dipeo/infrastructure/llm/drivers/service.py:135`)
   - `{phase}__api_call` - API call latency
   - Metadata: model, service, execution_phase

2. **Person Job Handler** (`dipeo/application/execution/handlers/person_job/single_executor.py`)
   - `complete_with_memory` - Memory-based completion

3. **System Operations** (via MetricsObserver)
   - Node execution times
   - Total execution duration
   - Per-node duration and token usage

## Identified Gaps

### 1. Claude Code Adapter Session Management (High Priority)

**Missing latency measurements:**

#### Session Lifecycle Latencies
- ❌ **Template Session Creation** (`unified_client.py:138`)
  - First-time template creation for each execution phase
  - Connection establishment (`template_session.connect()`)
  - Impact: Cold start penalty, only once per phase

- ❌ **Session Forking** (`unified_client.py:169-196`)
  - Fork operation from template
  - Fallback to fresh session creation
  - Impact: Per-request overhead

- ❌ **Session Connection** (`unified_client.py:207`)
  - Fresh session `connect()` call
  - Impact: Significant when forking unavailable

- ❌ **Session Cleanup** (`unified_client.py:285-293`)
  - Disconnect and removal from active sessions
  - Impact: Resource cleanup overhead

#### Request Processing Latencies
- ❌ **Message Preparation** (`unified_client.py:314`)
  - System message extraction
  - Message formatting for Claude SDK

- ❌ **Tool Configuration** (`unified_client.py:321`)
  - MCP server setup based on execution phase

- ❌ **System Prompt Building** (`unified_client.py:324`)
  - Prompt assembly with phase-specific templates

- ❌ **Workspace Setup** (`unified_client.py:332`)
  - Directory creation and path resolution

- ❌ **Query Execution** (`unified_client.py:235`)
  - Actual query submission
  - Response collection loop

- ❌ **Response Parsing** (`unified_client.py:264-280`)
  - Tool invocation detection
  - Result text processing

### 2. Client Manager Pool Operations (Medium Priority)

**Missing latency measurements in** `dipeo/infrastructure/llm/drivers/client_manager.py`:

- ❌ **Client Pool Lookup** (`client_manager.py:106-112`)
  - Cache key creation
  - Pool lookup with lock acquisition

- ❌ **Client Creation** (`client_manager.py:114-137`)
  - API key retrieval
  - Provider-specific client instantiation
  - Pool insertion

- ❌ **SingleFlightCache Operations** (`client_manager.py:139`)
  - Deduplication logic
  - Concurrent request coalescing

### 3. Other LLM Infrastructure Gaps (Medium Priority)

#### All Unified Clients (OpenAI, Anthropic, Google, Ollama)
- ❌ **Request Preparation**
  - Message conversion to provider format
  - Tool/function schema translation
  - Response format setup

- ❌ **HTTP Client Operations**
  - Connection pooling effects
  - Request serialization
  - Response deserialization

- ❌ **Retry Logic**
  - Retry attempts and backoff delays
  - Fallback provider switches

### 4. Execution Pipeline Gaps (Low-Medium Priority)

#### State Store Operations
- ❌ **Cache vs DB Access** (already has some tracking but not comprehensive)
  - Cache hit/miss timing
  - DB write latency
  - Persistence manager flush operations

#### Input Resolution
- ❌ **Dependency Resolution** (`dipeo/domain/execution/resolution/api.py`)
  - Input variable extraction
  - Edge traversal for dependencies
  - Transformation application

#### Memory Selection (Partially Tracked)
- ✅ Already has `memory_selection__api_call`
- ❌ Missing: Memory candidate filtering, facet creation, result ranking

#### Orchestrator Operations
- ❌ **Person Management** (`dipeo/application/execution/orchestrators/person_orchestrator.py`)
  - Person creation/lookup
  - Conversation retrieval

- ❌ **Prompt Loading** (`dipeo/application/execution/orchestrators/prompt_orchestrator.py`)
  - Template loading from disk
  - Variable substitution
  - Cache operations

#### Node Handler Initialization
- ❌ **Handler Discovery and Registration**
  - Module import time
  - Handler class instantiation

#### Event System
- ❌ **Event Publishing Overhead**
  - Event serialization
  - Subscriber notification
  - Queue operations

## Recommended Enhancements

### Phase 1: Claude Code Session Profiling (Immediate)

**Locations to instrument:**

1. **Template Management** (`unified_client.py`)
```python
async def _get_or_create_template(self, options, execution_phase):
    async with self._template_lock:
        if self._template_sessions.get(execution_phase):
            return self._template_sessions[execution_phase]

        # ADD TIMING HERE
        async with atime_phase(trace_id, "claude_code", f"session__template_create__{execution_phase}"):
            template_session = ClaudeSDKClient(options=options)
            await template_session.connect(None)

        self._template_sessions[execution_phase] = template_session
        return template_session
```

2. **Session Forking** (`unified_client.py`)
```python
async def _create_forked_session(self, options, execution_phase):
    if FORK_SESSION_ENABLED:
        try:
            template = await self._get_or_create_template(options, execution_phase)

            # ADD TIMING HERE
            async with atime_phase(trace_id, "claude_code", f"session__fork__{execution_phase}"):
                fork_options = ClaudeAgentOptions(...)
                forked_session = ClaudeSDKClient(options=fork_options)
                await forked_session.connect(None)

            return forked_session
```

3. **Request Processing Phases** (`unified_client.py`)
```python
async def async_chat(self, messages, ...):
    # Message preparation
    async with atime_phase(trace_id, "claude_code", "request__prepare_messages"):
        system_message, formatted_messages = self._processor.prepare_message(messages)

    # Tool configuration
    async with atime_phase(trace_id, "claude_code", "request__configure_tools"):
        use_tools = execution_phase in (...)
        tool_options = self._processor.create_tool_options(execution_phase, use_tools)

    # System prompt
    async with atime_phase(trace_id, "claude_code", "request__build_system_prompt"):
        system_prompt = self._processor.build_system_prompt(...)

    # Query execution
    async with atime_phase(trace_id, "claude_code", f"request__query__{execution_phase}"):
        return await self._execute_query(session, query_input, execution_phase, session_id)
```

### Phase 2: Client Manager Profiling

Add timing to `client_manager.py`:
```python
async def get_client(self, service_name, model, api_key_id):
    cache_key = self._create_cache_key(provider, model, api_key_id)

    # Pool lookup
    async with self._client_pool_lock:
        async with atime_phase(trace_id, "client_manager", "pool__lookup"):
            if cache_key in self._client_pool:
                ...

    # Client creation
    async def create_new_client():
        async with atime_phase(trace_id, "client_manager", f"pool__create__{provider}"):
            raw_key = self._get_api_key(api_key_id)
            client = self._create_provider_client(...)
        return client
```

### Phase 3: Execution Pipeline Profiling

1. **Input Resolution** (`dipeo/domain/execution/resolution/api.py`)
2. **Memory Selection** (enhance existing)
3. **State Store Operations** (selective instrumentation)
4. **Orchestrator Operations** (person/prompt management)

### Phase 4: Enhanced Metrics Display

Update `display.py` to show:
```
🔧 Claude Code Session Management:
  session__template_create__memory_selection    1200ms (1 time)   - Cold start
  session__fork__memory_selection                 50ms (5 times)  - Avg: 10ms
  session__fork__direct_execution                 45ms (3 times)  - Avg: 15ms
  request__prepare_messages                       15ms (8 times)  - Avg: 2ms
  request__configure_tools                         8ms (8 times)  - Avg: 1ms
  request__build_system_prompt                    40ms (8 times)  - Avg: 5ms
  request__query__memory_selection              2500ms (5 times)  - Avg: 500ms
  request__query__direct_execution              1200ms (3 times)  - Avg: 400ms

🔄 Client Manager:
  pool__lookup                                    25ms (15 times) - Avg: 2ms (13 hits, 2 misses)
  pool__create__claude_code                      800ms (2 times)  - Avg: 400ms
  pool__create__openai                           120ms (1 time)   - Avg: 120ms
```

## Implementation Priority

### High Priority (Do First)
1. ✅ Claude Code session management (templates, forks, connections)
2. ✅ Request processing phases (prepare, configure, query)
3. ✅ Client pool operations

### Medium Priority (Do Second)
4. ⏺️ Other unified clients (OpenAI, Anthropic, etc.)
5. ⏺️ State store detailed profiling
6. ⏺️ Orchestrator operations

### Low Priority (Do Later)
7. ⏺️ Event system overhead
8. ⏺️ Handler initialization timing
9. ⏺️ Input resolution details

## Expected Impact

### What We'll Learn:

1. **Session Pool Efficiency**
   - Template reuse vs cold starts
   - Fork success rate and fallback frequency
   - Connection establishment overhead

2. **Request Processing Breakdown**
   - Message preparation overhead
   - Tool configuration cost
   - System prompt building time
   - Actual API call time vs overhead

3. **Cache Effectiveness**
   - Client pool hit rate
   - Session template reuse
   - SingleFlightCache deduplication benefits

4. **Bottleneck Identification**
   - Is it Claude Code SDK initialization?
   - Is it network/API latency?
   - Is it message/tool preparation?
   - Is it response parsing?

### Metrics We Can Derive:

- **Cold Start Penalty**: Template creation time
- **Warm Path Efficiency**: Fork time vs fresh session
- **Request Overhead**: Preparation + config + prompt vs actual query
- **Cache ROI**: Pool lookup time vs creation time
- **SDK Overhead**: SDK operations vs network time

## Next Steps

1. Implement Phase 1 (Claude Code) instrumentation
2. Run test diagrams with `--timing` flag
3. Analyze `dipeo metrics --latest --breakdown` output
4. Identify top bottlenecks
5. Implement targeted optimizations
6. Iterate on Phases 2-4 based on findings
