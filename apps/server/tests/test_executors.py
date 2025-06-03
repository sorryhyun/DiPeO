"""Tests for individual node executors."""

import pytest
from unittest.mock import patch

from ..src.engine.executors import StartExecutor
from ..src.engine.executors import ConditionExecutor
from ..src.engine.executors import JobExecutor
from ..src.engine.executors import EndpointExecutor
from ..src.engine.executors import PersonJobExecutor
from ..src.engine.executors import DBExecutor
from ..src.engine.executors import ExecutorFactory
from ..src.engine.engine import ExecutionContext
from .fixtures.mocks import MockLLMService, MockAPIKeyService, MockMemoryService


@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    return {
        'llm_service': MockLLMService(),
        'api_key_service': MockAPIKeyService(),
        'memory_service': MockMemoryService()
    }


@pytest.fixture
def execution_context():
    """Create basic execution context for testing."""
    return ExecutionContext(
        node_outputs={},
        node_execution_counts={},
        condition_values={},
        first_only_consumed={},
        execution_order=[],
        total_cost=0.0,
        nodes_by_id={},
        incoming_arrows={},
        outgoing_arrows={}
    )


class TestStartExecutor:
    """Test cases for StartExecutor."""
    
    @pytest.mark.asyncio
    async def test_start_executor_basic(self, mock_services, execution_context):
        """Test basic start node execution."""
        node = {
            "id": "start1",
            "type": "start",
            "data": {
                "id": "start1",
                "label": "Start",
                "output": "Hello World"
            }
        }
        
        executor = StartExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, {})
        
        assert result.success is True
        assert result.output == "Hello World"
        assert result.cost == 0.0
    
    @pytest.mark.asyncio
    async def test_start_executor_with_variables(self, mock_services, execution_context):
        """Test start node with variable substitution."""
        node = {
            "id": "start1",
            "type": "start",
            "data": {
                "id": "start1",
                "label": "Start",
                "output": "Welcome {{name}}"
            }
        }
        
        input_values = {"name": "Alice"}
        
        executor = StartExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, input_values)
        
        assert result.success is True
        assert result.output == "Welcome Alice"


class TestConditionExecutor:
    """Test cases for ConditionExecutor."""
    
    @pytest.mark.asyncio
    async def test_condition_executor_true(self, mock_services, execution_context):
        """Test condition executor returning true."""
        node = {
            "id": "condition1",
            "type": "condition",
            "data": {
                "id": "condition1",
                "label": "Check",
                "condition": "input == 'yes'"
            }
        }
        
        input_values = {"input": "yes"}
        
        executor = ConditionExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, input_values)
        
        assert result.success is True
        assert result.output is True
    
    @pytest.mark.asyncio
    async def test_condition_executor_false(self, mock_services, execution_context):
        """Test condition executor returning false."""
        node = {
            "id": "condition1",
            "type": "condition",
            "data": {
                "id": "condition1",
                "label": "Check",
                "condition": "input == 'yes'"
            }
        }
        
        input_values = {"input": "no"}
        
        executor = ConditionExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, input_values)
        
        assert result.success is True
        assert result.output is False
    
    @pytest.mark.asyncio
    async def test_condition_executor_max_iterations(self, mock_services, execution_context):
        """Test condition executor with max iterations logic."""
        node = {
            "id": "condition1",
            "type": "condition",
            "data": {
                "id": "condition1",
                "label": "Check Max Iterations",
                "conditionType": "max_iterations"
            }
        }
        
        # Set up context with iteration counts
        execution_context.node_execution_counts = {"person1": 2, "person2": 3}
        execution_context.nodes_by_id = {
            "person1": {"data": {"maxIterations": 3}},
            "person2": {"data": {"maxIterations": 3}}
        }
        
        executor = ConditionExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, {})
        
        assert result.success is True
        assert result.output is False  # Not all nodes have reached max iterations


class TestJobExecutor:
    """Test cases for JobExecutor."""
    
    @pytest.mark.asyncio
    async def test_job_executor_python(self, mock_services, execution_context):
        """Test job executor with Python code."""
        node = {
            "id": "job1",
            "type": "job",
            "data": {
                "id": "job1",
                "label": "Python Job",
                "language": "python",
                "code": "result = 2 + 2"
            }
        }
        
        executor = JobExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, {})
        
        assert result.success is True
        assert "result" in result.output
    
    @pytest.mark.asyncio
    async def test_job_executor_with_variables(self, mock_services, execution_context):
        """Test job executor with variable substitution."""
        node = {
            "id": "job1",
            "type": "job",
            "data": {
                "id": "job1",
                "label": "Python Job",
                "language": "python",
                "code": "result = {{x}} + {{y}}"
            }
        }
        
        input_values = {"x": 5, "y": 3}
        
        executor = JobExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, input_values)
        
        assert result.success is True
        assert "result" in result.output


class TestEndpointExecutor:
    """Test cases for EndpointExecutor."""
    
    @pytest.mark.asyncio
    async def test_endpoint_executor_basic(self, mock_services, execution_context):
        """Test basic endpoint execution."""
        node = {
            "id": "end1",
            "type": "endpoint",
            "data": {
                "id": "end1",
                "label": "End",
                "filename": "test_output.txt"
            }
        }
        
        input_values = {"content": "Test output content"}
        
        with patch('pathlib.Path.write_text') as mock_write:
            executor = EndpointExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
            result = await executor.execute(node, execution_context, input_values)
            
            assert result.success is True
            mock_write.assert_called_once()


class TestPersonJobExecutor:
    """Test cases for PersonJobExecutor."""
    
    @pytest.mark.asyncio
    async def test_person_job_executor_basic(self, mock_services, execution_context):
        """Test basic person job execution."""
        node = {
            "id": "person1",
            "type": "person_job",
            "data": {
                "id": "person1",
                "label": "AI Assistant",
                "personId": "assistant1",
                "prompt": "Respond to the user."
            }
        }
        
        input_values = {"message": "Hello"}
        
        executor = PersonJobExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, input_values)
        
        assert result.success is True
        assert result.cost > 0  # Should have LLM cost
        assert isinstance(result.output, str)
    
    @pytest.mark.asyncio
    async def test_person_job_executor_with_memory(self, mock_services, execution_context):
        """Test person job executor with memory integration."""
        node = {
            "id": "person1",
            "type": "person_job",
            "data": {
                "id": "person1",
                "label": "AI Assistant",
                "personId": "assistant1",
                "prompt": "Respond to the user."
            }
        }
        
        input_values = {"message": "Hello"}
        
        executor = PersonJobExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        
        # Execute twice to test memory
        result1 = await executor.execute(node, execution_context, input_values)
        result2 = await executor.execute(node, execution_context, {"message": "How are you?"})
        
        assert result1.success is True
        assert result2.success is True
        
        # Memory service should have recorded interactions
        memory_service = mock_services['memory_service']
        assert len(memory_service.memory_data) > 0


class TestDBExecutor:
    """Test cases for DBExecutor."""
    
    @pytest.mark.asyncio
    async def test_db_executor_read_file(self, mock_services, execution_context):
        """Test DB executor reading a file."""
        node = {
            "id": "db1",
            "type": "db",
            "data": {
                "id": "db1",
                "label": "Read File",
                "operation": "read_file",
                "filename": "test.txt"
            }
        }
        
        with patch('pathlib.Path.read_text', return_value="Test content"):
            executor = DBExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
            result = await executor.execute(node, execution_context, {})
            
            assert result.success is True
            assert result.output == "Test content"
    
    @pytest.mark.asyncio
    async def test_db_executor_fixed_prompt(self, mock_services, execution_context):
        """Test DB executor with fixed prompt."""
        node = {
            "id": "db1",
            "type": "db",
            "data": {
                "id": "db1",
                "label": "Fixed Output",
                "operation": "fixed_prompt",
                "prompt": "This is a fixed response."
            }
        }
        
        executor = DBExecutor(mock_services['llm_service'], mock_services['api_key_service'], mock_services['memory_service'])
        result = await executor.execute(node, execution_context, {})
        
        assert result.success is True
        assert result.output == "This is a fixed response."


class TestExecutorFactory:
    """Test cases for ExecutorFactory."""
    
    def test_executor_factory_creation(self, mock_services):
        """Test executor factory creates correct executors."""
        factory = ExecutorFactory()
        
        # Register services
        factory.register_services(
            mock_services['llm_service'],
            mock_services['api_key_service'],
            mock_services['memory_service']
        )
        
        # Test creating different executor types
        start_executor = factory.get_executor("start")
        assert isinstance(start_executor, StartExecutor)
        
        condition_executor = factory.get_executor("condition")
        assert isinstance(condition_executor, ConditionExecutor)
        
        job_executor = factory.get_executor("job")
        assert isinstance(job_executor, JobExecutor)
        
        person_executor = factory.get_executor("person_job")
        assert isinstance(person_executor, PersonJobExecutor)
    
    def test_executor_factory_invalid_type(self, mock_services):
        """Test executor factory with invalid type."""
        factory = ExecutorFactory()
        factory.register_services(
            mock_services['llm_service'],
            mock_services['api_key_service'],
            mock_services['memory_service']
        )
        
        with pytest.raises(ValueError):
            factory.get_executor("invalid_type")


class TestExecutionContext:
    """Test cases for ExecutionContext."""
    
    def test_execution_context_initialization(self):
        """Test proper initialization of execution context."""
        context = ExecutionContext(
            node_outputs={},
            node_execution_counts={},
            condition_values={},
            first_only_consumed={},
            execution_order=[],
            total_cost=0.0,
            nodes_by_id={},
            incoming_arrows={},
            outgoing_arrows={}
        )
        
        assert isinstance(context.node_outputs, dict)
        assert isinstance(context.node_execution_counts, dict)
        assert isinstance(context.condition_values, dict)
        assert isinstance(context.first_only_consumed, dict)
        assert isinstance(context.execution_order, list)
        assert context.total_cost == 0.0
        assert isinstance(context.nodes_by_id, dict)
        assert isinstance(context.incoming_arrows, dict)
        assert isinstance(context.outgoing_arrows, dict)
    
    def test_execution_context_cost_tracking(self):
        """Test cost tracking in execution context."""
        context = ExecutionContext(
            node_outputs={},
            node_execution_counts={},
            condition_values={},
            first_only_consumed={},
            execution_order=[],
            total_cost=0.0,
            nodes_by_id={},
            incoming_arrows={},
            outgoing_arrows={}
        )
        
        # Simulate adding costs
        context.total_cost += 0.01
        context.total_cost += 0.02
        
        assert context.total_cost == 0.03