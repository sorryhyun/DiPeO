// Phase 4: Frontend Simplification - Unified Backend Execution
// All execution logic has been moved to the backend unified engine.
// Frontend now uses a simple API client for execution.

// Export unified execution client (replaces all legacy execution components)
export * from './unified-execution-client';

// Legacy execution components removed in Phase 4:
// - DependencyResolver (moved to backend)
// - ExecutionPlanner (moved to backend) 
// - SkipManager (moved to backend)
// - LoopController (moved to backend)
// - ExecutionEngine (replaced by backend unified engine)
// - All executors (moved to backend)
// - execution-orchestrator (replaced by unified-execution-client)
// - createExecutionContext (no longer needed on frontend)