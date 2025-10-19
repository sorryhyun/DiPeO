-- DiPeO Database Schema
-- Auto-generated SQL DDL reference
-- DO NOT EXECUTE - For reference only

-- Table: executions
-- Source: dipeo/infrastructure/execution/state/persistence_manager.py
CREATE TABLE IF NOT EXISTS executions (
    execution_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    diagram_id TEXT,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    node_states TEXT NOT NULL,
    node_outputs TEXT NOT NULL,
    llm_usage TEXT NOT NULL,
    error TEXT,
    variables TEXT NOT NULL,
    exec_counts TEXT NOT NULL DEFAULT '{}',
    executed_nodes TEXT NOT NULL DEFAULT '[]',
    metrics TEXT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_started_at ON executions(started_at);
CREATE INDEX IF NOT EXISTS idx_diagram_id ON executions(diagram_id);
CREATE INDEX IF NOT EXISTS idx_access_count ON executions(access_count DESC);
CREATE INDEX IF NOT EXISTS idx_last_accessed ON executions(last_accessed DESC);


-- Table: messages
-- Source: apps/server/src/dipeo_server/infra/message_store.py
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL,
    node_id TEXT NOT NULL,
    person_id TEXT,
    content TEXT NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_execution ON messages(execution_id);
CREATE INDEX IF NOT EXISTS idx_node ON messages(node_id);


-- Table: transitions
-- Source: dipeo/infrastructure/execution/state/persistence_manager.py
CREATE TABLE IF NOT EXISTS transitions (
    id TEXT PRIMARY KEY,
    execution_id TEXT NOT NULL,
    node_id TEXT,
    phase TEXT NOT NULL,
    seq INTEGER NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_exec_seq ON transitions(execution_id, seq);
CREATE INDEX IF NOT EXISTS idx_exec_transitions ON transitions(execution_id);
CREATE INDEX IF NOT EXISTS idx_created_at ON transitions(created_at DESC);
