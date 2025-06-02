# DiPeO Frontend to Backend Execution Engine Migration Plan

## Executive Summary

This document outlines a comprehensive plan to migrate DiPeO's diagram execution engine from the current hybrid client-server model to a fully backend-based architecture. The migration will consolidate all execution logic on the server side, simplifying the architecture while maintaining performance and functionality.

## 1. Current State Analysis

### 1.1 Hybrid Architecture Overview
- **Client-Side Execution**: Start, Condition, Job, Endpoint nodes
- **Server-Side Execution**: PersonJob, PersonBatchJob, DB nodes  
- **Execution Orchestrator**: Automatically detects environment and routes execution
- **CLI Integration**: Uses Node.js bundle to leverage frontend execution logic

### 1.2 Key Components
```
Frontend (TypeScript/React)
├── execution-orchestrator.ts    # Environment detection & routing
├── execution-engine.ts          # Core execution logic
├── executors/
│   ├── client-safe/            # Local executors
│   └── server-only/            # API call wrappers
└── flow/                       # Dependency resolution

Backend (Python/FastAPI)
├── execution_service.py         # Server-only node execution
├── node_operations.py          # Individual node endpoints
└── diagram.py                  # Full diagram execution
```

### 1.3 Current Benefits
- Reduced network overhead for simple operations
- Browser-based execution capability
- Optimized performance for client-safe nodes

### 1.4 Current Challenges
- Complex codebase maintenance (TypeScript + Python)
- Duplicate logic for variable substitution, dependency resolution
- Difficult debugging across environments
- Security concerns with client-side code execution

## 2. Migration Goals

### 2.1 Primary Objectives
- **Unified Execution**: All nodes execute on the backend
- **Simplified Architecture**: Single execution engine in Python
- **Enhanced Security**: No code execution in browser
- **Improved Maintainability**: One codebase for execution logic
- **Better Debugging**: Centralized logging and monitoring

### 2.2 Expected Benefits
- Reduced frontend bundle size
- Consistent execution behavior
- Easier feature additions
- Simplified testing
- Better performance monitoring
- Enhanced security posture

## 3. Technical Approach

### 3.1 Architecture Changes
```
Current:                          Target:
Frontend → Orchestrator          Frontend → API Client
    ↓           ↓                    ↓
Client Exec   Server API         Backend API
    ↓           ↓                    ↓
 Results    Backend Exec         Unified Execution Engine
```

### 3.2 Key Migration Areas

#### 3.2.1 Execution Engine Core
- Port TypeScript execution-engine.ts to Python
- Migrate dependency resolver logic
- Implement loop controller in Python
- Port skip manager functionality

#### 3.2.2 Node Executors
- Convert client-safe executors to Python:
  - StartExecutor → start_executor.py
  - ConditionExecutor → condition_executor.py  
  - JobExecutor → job_executor.py
  - EndpointExecutor (already has backend API)
- Consolidate with existing server-only executors

#### 3.2.3 Frontend Changes
- Replace execution orchestrator with API client
- Remove executor implementations
- Simplify to diagram editor + API calls
- Maintain SSE streaming for real-time updates

#### 3.2.4 API Enhancements
- Expand `/api/run-diagram` to handle all node types
- Add execution state management endpoints
- Enhance streaming capabilities
- Add execution history endpoints

## 4. Implementation Plan

### Phase 1: Backend Infrastructure (Week 1-2) ✅ COMPLETED

#### 4.1.1 Create Unified Execution Engine ✅
Created `apps/server/src/services/unified_execution_engine.py` with:
- Unified execution engine managing complete diagram execution lifecycle
- Integration with all core components
- Streaming execution updates via AsyncIterator
- Proper error handling and context management

#### 4.1.2 Port Core Components ✅
- ✅ Dependency resolver (flow/dependency-resolver.ts → `dependency_resolver.py`)
  - Handles dependency resolution, cycle detection, topological sorting
  - Special handling for first-only inputs and condition branches
- ✅ Execution planner (flow/execution-planner.ts → `execution_planner.py`)
  - Creates execution plans with parallelization opportunities
  - Handles cycles gracefully with alternative ordering
- ✅ Loop controller (core/loop-controller.ts → `loop_controller.py`)
  - Manages iteration counts per node
  - Supports both global and node-specific max iterations
- ✅ Skip manager (core/skip-manager.ts → `skip_manager.py`)
  - Centralizes skip logic with reason tracking
  - Expression evaluation for conditions

#### 4.1.3 Create Base Executor Classes ✅
Created `apps/server/src/executors/base_executor.py` with:
- `BaseExecutor` abstract class with validation and execution methods
- `ClientSafeExecutor` and `ServerOnlyExecutor` subclasses
- `ExecutorFactory` for managing executor instances
- Common utilities for variable substitution and input handling

### Phase 2: Executor Migration (Week 2-3) ✅ COMPLETED

#### 4.2.1 Port Client-Safe Executors ✅
- ✅ StartExecutor: Static data initialization (`start_executor.py`)
- ✅ ConditionExecutor: Expression evaluation, max_iterations logic (`condition_executor.py`)
- ✅ JobExecutor: Safe code execution (sandboxed Python/JS/Bash) (`job_executor.py`)
- ✅ EndpointExecutor: Terminal nodes with file saving (`endpoint_executor.py`)

#### 4.2.2 Consolidate Server Executors ✅
- ✅ PersonJobExecutor: LLM API calls with person configuration (`person_job_executor.py`)
- ✅ PersonBatchJobExecutor: Batch processing variant (`person_job_executor.py`)
- ✅ DBExecutor: File operations and data sources (`db_executor.py`)
- ✅ ExecutorFactory: Unified registration and dependency injection

#### 4.2.3 Variable Substitution ✅
- ✅ Arrow label → variable mapping logic in base executor
- ✅ Unified substitution patterns ({{var}} handling)
- ✅ Input value processing from execution context

### Phase 3: API Enhancement (Week 3-4) ✅ COMPLETED

#### 4.3.1 Enhance Main Execution Endpoint ✅
Created `/api/v2/run-diagram` with:
- Unified backend execution using `UnifiedExecutionEngine`
- SSE streaming for real-time updates
- Comprehensive error handling and validation
- API key integration for LLM services

#### 4.3.2 Add State Management 🚧 PARTIAL
- 🔲 Execution state persistence (placeholder endpoints created)
- 🔲 Resume/pause capabilities (API structure ready)
- 🔲 Execution history API (basic framework in place)

#### 4.3.3 Enhanced Monitoring 🚧 PARTIAL
- ✅ `/api/v2/execution-capabilities` endpoint for feature discovery
- ✅ Cost tracking in executor results
- 🔲 Real-time execution metrics collection
- 🔲 Node-level performance analytics

### Phase 4: Frontend Simplification (Week 4-5) ✅ COMPLETED

#### 4.4.1 Replace Execution Logic ✅
- ✅ Remove execution-orchestrator.ts
- ✅ Remove execution-engine.ts
- ✅ Remove all executor implementations
- ✅ Create simple API client wrapper (`unified-execution-client.ts`)

#### 4.4.2 Update Diagram Runner ✅
```typescript
// Simplified diagram runner using unified backend execution
export function useDiagramRunner() {
  const executionClient = createUnifiedExecutionClient();
  
  const runDiagram = async (diagram: DiagramData) => {
    return await executionClient.execute(diagram, options, (update) => {
      // Handle real-time SSE updates for UI
      switch (update.type) {
        case 'node_start': setCurrentRunningNode(update.nodeId); break;
        case 'node_complete': removeRunningNode(update.nodeId); break;
        case 'conversation_update': /* stream to UI */; break;
      }
    });
  };
}
```

#### 4.4.3 Maintain UI Functionality ✅
- ✅ Keep real-time execution visualization via SSE streaming
- ✅ Preserve node running states through execution updates
- ✅ Maintain conversation streaming with update callbacks

### Phase 5: CLI Tool Update (Week 5)

#### 4.5.1 Remove Node.js Dependency
- [ ] Update tool.py to use backend API exclusively
- [ ] Remove esbuild configuration
- [ ] Delete cli-runner.ts and related files

#### 4.5.2 Simplify CLI Commands
```bash
# All execution through backend
python tool.py run diagram.json        # Backend execution
python tool.py monitor                 # Monitor executions
python tool.py run --stream diagram.json # With streaming
```

### Phase 6: Testing & Migration (Week 6)

#### 4.6.1 Comprehensive Testing
- [ ] Unit tests for all executors
- [ ] Integration tests for execution engine
- [ ] End-to-end diagram execution tests
- [ ] Performance benchmarks

#### 4.6.2 Migration Strategy
- [ ] Feature flag for v1/v2 execution
- [ ] Gradual rollout with monitoring
- [ ] Rollback plan

## 5. Risk Assessment & Mitigation

### 5.1 Performance Risks
**Risk**: Increased latency for simple operations
**Mitigation**: 
- Implement caching for repeated operations
- Optimize backend execution paths
- Use connection pooling

### 5.2 Compatibility Risks
**Risk**: Breaking changes for existing diagrams
**Mitigation**:
- Maintain backward compatibility layer
- Automated diagram migration tool
- Comprehensive testing suite

### 5.3 Feature Parity Risks
**Risk**: Missing functionality during migration
**Mitigation**:
- Detailed feature inventory
- Side-by-side testing
- Phased rollout

## 6. Success Metrics

### 6.1 Performance Metrics
- Execution latency (target: <100ms overhead)
- Throughput (target: 100 concurrent executions)
- Resource usage (target: <50MB per execution)

### 6.2 Quality Metrics
- Test coverage (target: >90%)
- Bug reduction (target: 50% fewer execution bugs)
- Code complexity (target: 30% reduction)

### 6.3 Developer Metrics
- Time to add new node type (target: 50% reduction)
- Debugging time (target: 40% reduction)
- Onboarding time (target: 30% reduction)

## 7. Timeline Summary

| Phase | Duration | Key Deliverables | Status |
|-------|----------|------------------|---------|
| Phase 1 | 2 weeks | Backend infrastructure, core components | ✅ COMPLETED |
| Phase 2 | 1 week | Executor migration | ✅ COMPLETED |
| Phase 3 | 1 week | API enhancements | ✅ COMPLETED |
| Phase 4 | 1 week | Frontend simplification | ✅ COMPLETED |
| Phase 5 | 3 days | CLI tool update | 🔲 Pending |
| Phase 6 | 1 week | Testing & migration | 🔲 Pending |
| **Total** | **6 weeks** | **Full migration** | **Phase 4/6 Complete** |

## 8. Post-Migration Benefits

### 8.1 Immediate Benefits
- Simplified architecture
- Reduced maintenance burden
- Improved security
- Better debugging capabilities

### 8.2 Long-term Benefits
- Easier feature development
- Better performance optimization opportunities
- Simplified deployment
- Enhanced monitoring capabilities

## 9. Conclusion

This migration represents a significant architectural simplification that will improve maintainability, security, and developer experience. While there are short-term risks around performance and compatibility, the long-term benefits justify the investment. The phased approach ensures minimal disruption while providing opportunities for validation and course correction.

## Appendix A: File Mapping

| Frontend File | Backend Target |
|--------------|----------------|
| execution-orchestrator.ts | unified_execution_engine.py |
| execution-engine.ts | unified_execution_engine.py |
| dependency-resolver.ts | dependency_resolver.py |
| loop-controller.ts | loop_controller.py |
| StartExecutor.ts | executors/start_executor.py |
| ConditionExecutor.ts | executors/condition_executor.py |
| JobExecutor.ts | executors/job_executor.py |
| PersonJobExecutor.ts | (existing) |
| DBExecutor.ts | (existing) |

## Appendix B: API Changes

### Deprecated Endpoints
- Individual node execution endpoints (will be internal)

### New Endpoints
- `POST /api/v2/run-diagram` - Unified execution
- `GET /api/v2/executions/{id}` - Execution details
- `GET /api/v2/executions/{id}/state` - Current state
- `POST /api/v2/executions/{id}/pause` - Pause execution
- `POST /api/v2/executions/{id}/resume` - Resume execution