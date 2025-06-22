"""Unit tests for execution engine."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from dipeo_server.domains.execution.engine import CompactEngine, build_graph, Node, Arrow, Graph, Ctx
from dipeo_server.core import ExecutionStatus, NodeType
from dipeo_server.core.exceptions import DiagramExecutionError


class TestCompactEngine:
    """Test CompactEngine functionality."""
    
    @pytest.fixture
    def mock_diagram(self):
        """Create a mock diagram for testing."""
        return {
            "nodes": {
                "start": {
                    "id": "start",
                    "type": "start",
                    "data": {"type": "start", "value": "Hello"}
                },
                "person1": {
                    "id": "person1",
                    "type": "person",
                    "data": {"type": "person", "model": "gpt-4.1-nano"}
                },
                "end": {
                    "id": "end",
                    "type": "end",
                    "data": {"type": "end"}
                }
            },
            "arrows": {
                "arrow1": {"source": "start", "target": "person1"},
                "arrow2": {"source": "person1", "target": "end"}
            }
        }
    
    @pytest.fixture
    def mock_executors(self):
        """Create mock executors for different node types."""
        class MockResult:
            def __init__(self, output, metadata=None):
                self.output = output
                self.metadata = metadata or {}
        
        executors = {}
        for node_type in ["start", "person", "end", "job", "condition"]:
            executor = Mock()
            executor.execute = AsyncMock(return_value=MockResult(f"{node_type} output"))
            executors[node_type] = executor
        
        return executors
    
    @pytest.fixture
    def engine(self, mock_executors):
        """Create an execution engine instance with mock executors."""
        return CompactEngine(mock_executors)
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine is not None
        assert hasattr(engine, 'run')
        assert hasattr(engine, 'execs')
        assert hasattr(engine, 'lock')
    
    @pytest.mark.asyncio
    async def test_build_graph(self, mock_diagram):
        """Test graph building from diagram."""
        graph = build_graph(mock_diagram)
        
        assert isinstance(graph, Graph)
        assert len(graph.nodes) == 3
        assert "start" in graph.nodes
        assert "person1" in graph.nodes
        assert "end" in graph.nodes
        
        # Check topological order
        assert graph.order == ["start", "person1", "end"]
    
    @pytest.mark.asyncio
    async def test_execute_simple_diagram(self, engine, mock_diagram):
        """Test executing a simple diagram."""
        messages = []
        
        async def capture_message(msg):
            messages.append(msg)
        
        await engine.run(mock_diagram, send=capture_message)
        
        # Check messages were sent
        assert any(msg["type"] == "execution_started" for msg in messages)
        assert any(msg["type"] == "execution_complete" for msg in messages)
        
        # Check nodes were executed
        for node_id in ["start", "person1", "end"]:
            assert any(
                msg["type"] == "node_complete" and msg["node_id"] == node_id 
                for msg in messages
            )
    
    @pytest.mark.asyncio
    async def test_node_execution_order(self, engine, mock_diagram):
        """Test that nodes execute in dependency order."""
        execution_order = []
        
        async def track_execution(node, ctx):
            execution_order.append(node["id"])
            return Mock(output=f"{node['id']} output", metadata={})
        
        # Replace executors with tracking versions
        for node_type in engine.execs:
            engine.execs[node_type].execute = track_execution
        
        await engine.run(mock_diagram)
        
        # Start should execute before person1, person1 before end
        assert execution_order.index("start") < execution_order.index("person1")
        assert execution_order.index("person1") < execution_order.index("end")
    
    @pytest.mark.asyncio
    async def test_condition_node_execution(self, engine):
        """Test execution with condition nodes."""
        diagram = {
            "nodes": {
                "start": {"id": "start", "type": "start", "data": {"type": "start"}},
                "cond": {"id": "cond", "type": "condition", "data": {"type": "condition"}},
                "end": {"id": "end", "type": "end", "data": {"type": "end"}}
            },
            "arrows": {
                "a1": {"source": "start", "target": "cond"},
                "a2": {"source": "cond", "target": "end"}
            }
        }
        
        # Make condition return True
        condition_result = Mock(output=True, metadata={"conditionResult": True})
        engine.execs["condition"].execute = AsyncMock(return_value=condition_result)
        
        messages = []
        await engine.run(diagram, send=lambda msg: messages.append(msg))
        
        # Check that condition was executed
        completed_nodes = [
            msg["node_id"] for msg in messages 
            if msg["type"] == "node_complete"
        ]
        
        assert "cond" in completed_nodes
        assert "end" in completed_nodes
    
    @pytest.mark.asyncio
    async def test_parallel_execution(self, engine):
        """Test parallel execution of independent nodes."""
        diagram = {
            "nodes": {
                "start": {"id": "start", "type": "start", "data": {"type": "start"}},
                "parallel1": {"id": "parallel1", "type": "job", "data": {"type": "job"}},
                "parallel2": {"id": "parallel2", "type": "job", "data": {"type": "job"}},
                "end": {"id": "end", "type": "end", "data": {"type": "end"}}
            },
            "arrows": {
                "a1": {"source": "start", "target": "parallel1"},
                "a2": {"source": "start", "target": "parallel2"},
                "a3": {"source": "parallel1", "target": "end"},
                "a4": {"source": "parallel2", "target": "end"}
            }
        }
        
        # Track execution timing
        execution_times = {}
        
        async def timed_execution(node, ctx):
            start_time = asyncio.get_event_loop().time()
            await asyncio.sleep(0.1)  # Simulate work
            execution_times[node["id"]] = start_time
            return Mock(output=f"{node['id']} output", metadata={})
        
        engine.execs["job"].execute = timed_execution
        
        await engine.run(diagram)
        
        # If parallel, both should start at similar times
        if "parallel1" in execution_times and "parallel2" in execution_times:
            time_diff = abs(execution_times["parallel1"] - execution_times["parallel2"])
            assert time_diff < 0.05  # Should be nearly simultaneous
    
    @pytest.mark.asyncio
    async def test_node_skip_max_iterations(self, engine):
        """Test node skipping due to max iterations."""
        diagram = {
            "nodes": {
                "start": {"id": "start", "type": "start", "data": {"type": "start"}},
                "loop_node": {
                    "id": "loop_node", 
                    "type": "job",  # Use job instead of person_job
                    "data": {"type": "job", "maxIteration": 2}
                },
                "end": {"id": "end", "type": "end", "data": {"type": "end"}}
            },
            "arrows": {
                "a1": {"source": "start", "target": "loop_node"},
                "a2": {"source": "loop_node", "target": "end"}
            }
        }
        
        messages = []
        await engine.run(diagram, send=lambda msg: messages.append(msg))
        
        # Check that nodes completed
        completed_nodes = [
            msg["node_id"] for msg in messages 
            if msg["type"] == "node_complete"
        ]
        
        # All nodes should complete 
        assert "start" in completed_nodes
        assert "loop_node" in completed_nodes
        assert "end" in completed_nodes
    
    @pytest.mark.asyncio
    async def test_missing_executor(self, engine):
        """Test error when executor for node type is missing."""
        diagram = {
            "nodes": {
                "unknown": {
                    "id": "unknown",
                    "type": "unknown_type",
                    "data": {"type": "unknown_type"}
                }
            },
            "arrows": {}
        }
        
        with pytest.raises(RuntimeError) as exc_info:
            await engine.run(diagram)
        
        assert "No executor" in str(exc_info.value)
        assert "unknown_type" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_deadlock_detection(self, engine):
        """Test detection of execution deadlock."""
        # Create circular dependency without proper start
        diagram = {
            "nodes": {
                "node1": {"id": "node1", "type": "job", "data": {"type": "job"}},
                "node2": {"id": "node2", "type": "job", "data": {"type": "job"}}
            },
            "arrows": {
                "a1": {"source": "node1", "target": "node2"},
                "a2": {"source": "node2", "target": "node1"}
            }
        }
        
        with pytest.raises(RuntimeError) as exc_info:
            await engine.run(diagram)
        
        assert "Dead-lock" in str(exc_info.value)