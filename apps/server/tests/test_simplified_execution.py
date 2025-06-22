"""Tests for the simplified execution engine."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from dipeo_domain.models import (
    Arrow,
    Diagram,
    Endpoint,
    NodeOutput,
    PersonJob,
    Start,
)

from dipeo_server.domains.execution.engine import SimplifiedEngine
from dipeo_server.domains.execution.handlers import get_handlers
from dipeo_server.domains.execution.context import ExecutionContext


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    return {
        "llm_service": AsyncMock(),
        "file_service": AsyncMock(),
        "memory_service": AsyncMock(),
        "notion_service": AsyncMock(),
        "state_store": AsyncMock(),
    }


@pytest.fixture
def simple_diagram():
    """Create a simple test diagram."""
    return Diagram(
        id="test-diagram",
        name="Test Diagram",
        nodes=[
            Start(id="start", label="Start"),
            PersonJob(
                id="person1",
                label="Test Person",
                person_id="person1",
                job="You are a helpful assistant",
                output="response",
                model="gpt-4o-mini",
            ),
            Endpoint(id="end", label="End", output="final_output"),
        ],
        arrows=[
            Arrow(id="a1", from_node="start", to_node="person1", label="input"),
            Arrow(id="a2", from_node="person1", to_node="end", label="response"),
        ],
    )


@pytest.mark.asyncio
async def test_simplified_engine_execution(mock_services, simple_diagram):
    """Test that the simplified engine can execute a diagram."""
    # Setup mocks
    mock_services["llm_service"].generate.return_value = "Hello, I'm a helpful assistant!"
    mock_services["state_store"].initialize_execution = AsyncMock()
    mock_services["state_store"].update_node_status = AsyncMock()
    mock_services["state_store"].add_node_output = AsyncMock()
    
    # Create engine
    engine = SimplifiedEngine(get_handlers())
    
    # Execute diagram
    ctx = await engine.execute_diagram(
        diagram=simple_diagram,
        api_keys={"openai": "test-key"},
        **mock_services
    )
    
    # Verify execution context
    assert ctx.execution_id
    assert len(ctx.node_outputs) == 3  # Start, PersonJob, Endpoint
    
    # Verify Start node executed
    start_output = ctx.get_node_output("start")
    assert start_output is not None
    assert start_output.status == "completed"
    
    # Verify PersonJob executed
    person_output = ctx.get_node_output("person1")
    assert person_output is not None
    assert person_output.status == "completed"
    assert person_output.outputs["response"] == "Hello, I'm a helpful assistant!"
    
    # Verify Endpoint collected the output
    end_output = ctx.get_node_output("end")
    assert end_output is not None
    assert end_output.status == "completed"
    assert "response" in end_output.outputs["final_output"]
    
    # Verify services were called
    mock_services["llm_service"].generate.assert_called_once()
    assert mock_services["state_store"].update_node_status.call_count >= 6  # 3 nodes × 2 status updates


@pytest.mark.asyncio
async def test_execution_context_methods():
    """Test ExecutionContext utility methods."""
    ctx = ExecutionContext(
        diagram=MagicMock(),
        edges=[
            Arrow(id="a1", from_node="n1", to_node="n2", label="data"),
            Arrow(id="a2", from_node="n2", to_node="n3", label="result"),
        ],
    )
    
    # Test edge finding
    edges_from_n1 = ctx.find_edges_from("n1")
    assert len(edges_from_n1) == 1
    assert edges_from_n1[0].to_node == "n2"
    
    edges_to_n2 = ctx.find_edges_to("n2")
    assert len(edges_to_n2) == 1
    assert edges_to_n2[0].from_node == "n1"
    
    # Test node output management
    output = NodeOutput(
        node_id="n1",
        exec_id="n1_1",
        status="completed",
        outputs={"data": "test"},
    )
    ctx.set_node_output("n1", output)
    assert ctx.get_node_output("n1") == output
    
    # Test execution counting
    assert ctx.increment_exec_count("n1") == 1
    assert ctx.increment_exec_count("n1") == 2
    
    # Test conversation history
    ctx.add_to_conversation("person1", {"role": "user", "content": "Hello"})
    ctx.add_to_conversation("person1", {"role": "assistant", "content": "Hi there"})
    history = ctx.get_conversation_history("person1")
    assert len(history) == 2
    assert history[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_topological_sort():
    """Test that the engine correctly sorts nodes in topological order."""
    diagram = Diagram(
        id="test",
        name="Test",
        nodes=[
            Start(id="s1", label="Start 1"),
            Start(id="s2", label="Start 2"),
            PersonJob(id="p1", label="Person 1", job="Job 1", output="out1"),
            PersonJob(id="p2", label="Person 2", job="Job 2", output="out2"),
            Endpoint(id="e1", label="End", output="final"),
        ],
        arrows=[
            Arrow(id="a1", from_node="s1", to_node="p1", label="in"),
            Arrow(id="a2", from_node="s2", to_node="p2", label="in"),
            Arrow(id="a3", from_node="p1", to_node="e1", label="data1"),
            Arrow(id="a4", from_node="p2", to_node="e1", label="data2"),
        ],
    )
    
    engine = SimplifiedEngine(get_handlers())
    levels = engine._topological_sort(diagram.nodes, diagram.arrows)
    
    # Should have 3 levels
    assert len(levels) == 3
    
    # Level 0: Both start nodes (can run in parallel)
    assert set(levels[0]) == {"s1", "s2"}
    
    # Level 1: Both person nodes (can run in parallel after starts complete)
    assert set(levels[1]) == {"p1", "p2"}
    
    # Level 2: Endpoint (runs after both persons complete)
    assert levels[2] == ["e1"]