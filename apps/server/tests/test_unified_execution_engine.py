"""Tests for the unified execution engine."""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, Mock, patch

from ..src.core.execution.engine import UnifiedExecutionEngine
from ..src.core.execution.executors.base_executor import ExecutorFactory
from ..src.services.llm_service import LLMService
from ..src.services.api_key_service import APIKeyService
from ..src.services.memory_service import MemoryService
from .fixtures.diagrams import DiagramFixtures
from .fixtures.mocks import MockLLMService, MockAPIKeyService, MockMemoryService


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    return {
        'llm_service': MockLLMService(),
        'api_key_service': MockAPIKeyService(),
        'memory_service': MockMemoryService(),
        'executor_factory': ExecutorFactory()
    }


@pytest.fixture
def execution_engine(mock_services):
    """Create execution engine with mock services."""
    return UnifiedExecutionEngine(
        llm_service=mock_services['llm_service'],
        api_key_service=mock_services['api_key_service'],
        memory_service=mock_services['memory_service']
    )


class TestUnifiedExecutionEngine:
    """Test cases for the unified execution engine."""
    
    @pytest.mark.asyncio
    async def test_simple_linear_execution(self, execution_engine):
        """Test execution of simple linear diagram."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # Execute diagram
        result = {}
        async for update in execution_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify execution completed
        assert 'context' in result
        assert 'totalCost' in result
        assert result['totalCost'] >= 0
        
        # Verify all nodes were processed
        context = result['context']
        assert 'nodeOutputs' in context
        assert len(context['nodeOutputs']) == 3  # start, person, endpoint
    
    @pytest.mark.asyncio
    async def test_branching_execution(self, execution_engine):
        """Test execution of diagram with conditional branching."""
        diagram = DiagramFixtures.branching_diagram()
        
        # Execute diagram
        result = {}
        async for update in execution_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify execution completed
        assert 'context' in result
        context = result['context']
        
        # Should have executed start, condition, one person node, and endpoint
        assert len(context['nodeOutputs']) >= 4
        
        # Verify condition node executed
        assert any(node_id.startswith('condition') for node_id in context['nodeOutputs'])
    
    @pytest.mark.asyncio
    async def test_iterating_execution(self, execution_engine):
        """Test execution with loops and max iterations."""
        diagram = DiagramFixtures.iterating_diagram()
        
        # Execute diagram
        result = {}
        node_executions = []
        
        async for update in execution_engine.execute_diagram(diagram):
            if update.get('type') == 'node_complete':
                node_executions.append(update.get('data', {}))
            elif update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify execution completed
        assert 'context' in result
        
        # Should have multiple executions of the person node (up to max iterations)
        person_executions = [ex for ex in node_executions if ex.get('nodeType') == 'person_job']
        assert len(person_executions) <= 3  # Max iterations = 3
    
    @pytest.mark.asyncio
    async def test_error_handling(self, execution_engine):
        """Test error handling during execution."""
        # Create invalid diagram (missing required fields)
        invalid_diagram = {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "data": {}  # Missing required fields
                }
            ],
            "arrows": [],
            "persons": [],
            "apiKeys": []
        }
        
        # Execute and expect error
        error_received = False
        async for update in execution_engine.execute_diagram(invalid_diagram):
            if update.get('type') == 'error':
                error_received = True
                break
        
        assert error_received
    
    @pytest.mark.asyncio
    async def test_execution_context_tracking(self, execution_engine):
        """Test that execution context is properly tracked."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # Execute diagram
        result = {}
        async for update in execution_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify context structure
        context = result['context']
        
        assert 'nodeOutputs' in context
        assert 'nodeExecutionCounts' in context
        assert 'conditionValues' in context
        assert 'executionOrder' in context
        assert 'totalCost' in context
        
        # Verify execution order is valid
        execution_order = context['executionOrder']
        assert len(execution_order) >= 3  # At least start, person, endpoint
        assert execution_order[0] == 'start1'  # Start node should be first
    
    @pytest.mark.asyncio
    async def test_streaming_updates(self, execution_engine):
        """Test that streaming updates are properly sent."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # Collect all streaming updates
        updates = []
        async for update in execution_engine.execute_diagram(diagram):
            updates.append(update)
            if update.get('type') == 'execution_complete':
                break
        
        # Verify we received different types of updates
        update_types = {update.get('type') for update in updates}
        
        assert 'execution_started' in update_types
        assert 'node_start' in update_types
        assert 'node_complete' in update_types
        assert 'execution_complete' in update_types
    
    @pytest.mark.asyncio
    async def test_cost_calculation(self, execution_engine):
        """Test that costs are properly calculated and aggregated."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # Execute diagram
        result = {}
        async for update in execution_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify cost tracking
        assert 'totalCost' in result
        assert result['totalCost'] >= 0
        
        # Should have some cost from LLM calls
        if 'person' in str(diagram):  # If diagram contains person nodes
            assert result['totalCost'] > 0
    
    @pytest.mark.asyncio
    async def test_memory_integration(self, execution_engine):
        """Test integration with memory service."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # Execute diagram
        result = {}
        async for update in execution_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify memory service was used
        memory_service = execution_engine.memory_service
        assert hasattr(memory_service, 'memory_data')
        
        # Should have created memory for person nodes
        if any(node.get('type') == 'person_job' for node in diagram.get('nodes', [])):
            assert len(memory_service.memory_data) > 0
    
    def test_execution_engine_initialization(self, mock_services):
        """Test proper initialization of execution engine."""
        engine = UnifiedExecutionEngine(
            llm_service=mock_services['llm_service'],
            api_key_service=mock_services['api_key_service'],
            memory_service=mock_services['memory_service']
        )
        
        assert engine.llm_service is not None
        assert engine.api_key_service is not None
        assert engine.memory_service is not None
        assert engine.executor_factory is not None