"""Tests for the new type-safe NodeOutput protocol hierarchy."""

import pytest
from datetime import datetime

from dipeo.models.models import Vec2
from dipeo.core.execution.execution_tracker import (
    CompletionStatus,
    ExecutionTracker,
    FlowStatus,
)
from dipeo.core.execution.node_output import (
    BaseNodeOutput,
    ConditionOutput,
    ConversationOutput,
    DataOutput,
    ErrorOutput,
    LegacyNodeOutput,
    TextOutput,
)
from dipeo.models import Message, NodeID


class TestNodeOutputTypes:
    """Test various NodeOutput implementations."""
    
    def test_text_output_creation(self):
        """Test TextOutput creation and access."""
        output = TextOutput(
            value="Hello, world!",
            node_id=NodeID("test-node"),
            metadata={"tokens": 10}
        )
        
        assert output.value == "Hello, world!"
        assert output.node_id == "test-node"
        assert output.metadata["tokens"] == 10
        assert not output.has_error()
        assert isinstance(output.timestamp, datetime)
    
    def test_text_output_type_validation(self):
        """Test TextOutput type validation."""
        with pytest.raises(TypeError, match="TextOutput value must be str"):
            TextOutput(
                value=123,  # Wrong type
                node_id=NodeID("test-node")
            )
    
    def test_condition_output_branch_access(self):
        """Test ConditionOutput branch handling."""
        output = ConditionOutput(
            value=True,
            node_id=NodeID("condition-node"),
            true_output="success_data",
            false_output="failure_data"
        )
        
        assert output.value is True
        assert output.get_output("condtrue") == "success_data"
        assert output.get_output("condfalse") == "failure_data"
        assert output.get_output("active_branch") == "condtrue"
        
        branch_name, branch_data = output.get_branch_output()
        assert branch_name == "condtrue"
        assert branch_data == "success_data"
    
    def test_condition_output_false_branch(self):
        """Test ConditionOutput with false result."""
        output = ConditionOutput(
            value=False,
            node_id=NodeID("condition-node"),
            true_output="success_data",
            false_output="failure_data"
        )
        
        branch_name, branch_data = output.get_branch_output()
        assert branch_name == "condfalse"
        assert branch_data == "failure_data"
        assert output.get_output("active_branch") == "condfalse"
    
    def test_data_output_access(self):
        """Test DataOutput dictionary access."""
        data = {"key1": "value1", "key2": 42, "nested": {"inner": "data"}}
        output = DataOutput(
            value=data,
            node_id=NodeID("data-node")
        )
        
        assert output.value == data
        assert output.get_output("key1") == "value1"
        assert output.get_output("key2") == 42
        assert output.get_output("nested") == {"inner": "data"}
        assert output.get_output("missing", "default") == "default"
    
    def test_error_output(self):
        """Test ErrorOutput behavior."""
        output = ErrorOutput(
            value="Something went wrong",
            node_id=NodeID("error-node"),
            error_type="RuntimeError"
        )
        
        assert output.value == "Something went wrong"
        assert output.has_error()
        assert output.error == "Something went wrong"
        assert output.metadata["error_type"] == "RuntimeError"
        assert output.metadata["is_error"] is True
    
    def test_conversation_output(self):
        """Test ConversationOutput with messages."""
        messages = [
            Message(
                id="msg1",
                from_person_id="system",
                to_person_id=NodeID("person1"),
                content="Hello",
                message_type="system_to_person"
            ),
            Message(
                id="msg2",
                from_person_id=NodeID("person1"),
                to_person_id=NodeID("person2"),
                content="Hi there",
                message_type="person_to_person"
            )
        ]
        
        output = ConversationOutput(
            value=messages,
            node_id=NodeID("conversation-node")
        )
        
        assert len(output.value) == 2
        last_msg = output.get_last_message()
        assert last_msg.content == "Hi there"
    
    def test_base_output_serialization(self):
        """Test output serialization and deserialization."""
        original = TextOutput(
            value="Test content",
            node_id=NodeID("test-node"),
            metadata={"key": "value"}
        )
        
        # Serialize
        data = original.to_dict()
        assert data["value"] == "Test content"
        assert data["node_id"] == "test-node"
        assert data["metadata"]["key"] == "value"
        assert "timestamp" in data
        
        # Deserialize
        restored = BaseNodeOutput.from_dict(data)
        assert restored.value == original.value
        assert restored.node_id == original.node_id
        assert restored.metadata == original.metadata
    
    def test_legacy_output_conversion(self):
        """Test converting legacy outputs to modern format."""
        # String value
        legacy = LegacyNodeOutput("Hello", {"tokens": 5})
        modern = legacy.to_modern(NodeID("test-node"))
        assert isinstance(modern, TextOutput)
        assert modern.value == "Hello"
        assert modern.metadata["tokens"] == 5
        
        # Boolean value with condition metadata
        legacy = LegacyNodeOutput(True, {"condtrue": "yes", "condfalse": "no"})
        modern = legacy.to_modern(NodeID("cond-node"))
        assert isinstance(modern, ConditionOutput)
        assert modern.value is True
        assert modern.true_output == "yes"
        assert modern.false_output == "no"
        
        # Dict value
        legacy = LegacyNodeOutput({"data": "value"}, {})
        modern = legacy.to_modern(NodeID("data-node"))
        assert isinstance(modern, DataOutput)
        assert modern.value == {"data": "value"}


class TestExecutionTracker:
    """Test execution tracking functionality."""
    
    def test_execution_counting(self):
        """Test proper execution counting."""
        tracker = ExecutionTracker()
        node_id = NodeID("test-node")
        
        # Initially no executions
        assert tracker.get_execution_count(node_id) == 0
        assert not tracker.has_executed(node_id)
        
        # Start first execution
        exec_num = tracker.start_execution(node_id)
        assert exec_num == 1  # 1-based counting
        assert tracker.get_execution_count(node_id) == 1
        
        # Complete execution
        output = TextOutput(value="result", node_id=node_id)
        tracker.complete_execution(node_id, CompletionStatus.SUCCESS, output)
        
        assert tracker.has_executed(node_id)
        assert tracker.get_last_output(node_id) is output
    
    def test_multiple_executions(self):
        """Test tracking multiple executions of same node."""
        tracker = ExecutionTracker()
        node_id = NodeID("iterative-node")
        
        # Execute three times
        outputs = []
        for i in range(3):
            exec_num = tracker.start_execution(node_id)
            assert exec_num == i + 1
            
            output = TextOutput(value=f"result_{i}", node_id=node_id)
            outputs.append(output)
            tracker.complete_execution(node_id, CompletionStatus.SUCCESS, output)
        
        assert tracker.get_execution_count(node_id) == 3
        assert tracker.get_last_output(node_id) is outputs[-1]
        
        # Check execution history
        history = tracker.get_node_execution_history(node_id)
        assert len(history) == 3
        assert all(record.was_successful() for record in history)
    
    def test_iteration_reset_preserves_history(self):
        """Test that iteration reset preserves execution history."""
        tracker = ExecutionTracker()
        node_id = NodeID("iterative-node")
        
        # Execute first time
        tracker.start_execution(node_id)
        output1 = TextOutput(value="first", node_id=node_id)
        tracker.complete_execution(node_id, CompletionStatus.SUCCESS, output1)
        
        # Reset for iteration
        tracker.reset_for_iteration(node_id)
        
        # History should be preserved
        assert tracker.get_execution_count(node_id) == 1
        assert tracker.has_executed(node_id)
        assert tracker.get_last_output(node_id) is output1
        
        # But should be ready for next execution
        runtime_state = tracker.get_runtime_state(node_id)
        assert runtime_state.flow_status == FlowStatus.READY
        assert runtime_state.can_execute()
    
    def test_failed_execution_tracking(self):
        """Test tracking failed executions."""
        tracker = ExecutionTracker()
        node_id = NodeID("failing-node")
        
        # Start and fail execution
        tracker.start_execution(node_id)
        error_output = ErrorOutput(
            value="Test error",
            node_id=node_id,
            error_type="TestError"
        )
        tracker.complete_execution(
            node_id,
            CompletionStatus.FAILED,
            error_output,
            "Test error"
        )
        
        # Node should be blocked after failure
        runtime_state = tracker.get_runtime_state(node_id)
        assert runtime_state.flow_status == FlowStatus.BLOCKED
        assert not runtime_state.can_execute()
        
        # But history should show it executed
        assert tracker.has_executed(node_id)  # It ran, just failed
        assert tracker.get_last_output(node_id) is error_output
    
    def test_execution_summary(self):
        """Test execution summary generation."""
        tracker = ExecutionTracker()
        
        # Execute several nodes
        for i in range(3):
            node_id = NodeID(f"node-{i}")
            tracker.start_execution(node_id)
            output = TextOutput(value=f"result-{i}", node_id=node_id)
            
            # Make one fail
            if i == 1:
                tracker.complete_execution(
                    node_id,
                    CompletionStatus.FAILED,
                    output,
                    "Simulated failure"
                )
            else:
                tracker.complete_execution(
                    node_id,
                    CompletionStatus.SUCCESS,
                    output,
                    token_usage={"input": 10, "output": 20, "cached": 5}
                )
        
        summary = tracker.get_execution_summary()
        assert summary["total_executions"] == 3
        assert summary["successful_executions"] == 2
        assert summary["failed_executions"] == 1
        assert summary["success_rate"] == 2/3
        assert summary["nodes_executed"] == 3
        assert summary["total_tokens"]["input"] == 20  # 2 successful * 10
        assert summary["total_tokens"]["output"] == 40  # 2 successful * 20
    
    def test_runtime_state_management(self):
        """Test runtime state transitions."""
        tracker = ExecutionTracker()
        node_id = NodeID("state-test-node")
        
        # Initial state
        state = tracker.get_runtime_state(node_id)
        assert state.flow_status == FlowStatus.WAITING
        assert not state.can_execute()  # Dependencies not met
        
        # Mark ready
        state.dependencies_met = True
        state.flow_status = FlowStatus.READY
        assert state.can_execute()
        
        # Start execution
        tracker.start_execution(node_id)
        assert state.flow_status == FlowStatus.RUNNING
        
        # Complete execution
        tracker.complete_execution(
            node_id,
            CompletionStatus.SUCCESS,
            TextOutput(value="done", node_id=node_id)
        )
        assert state.flow_status == FlowStatus.WAITING


class TestConditionHandling:
    """Test condition node scenarios with the new system."""
    
    @pytest.mark.asyncio
    async def test_condition_with_preserved_outputs(self):
        """Test condition evaluation with execution history."""
        from dipeo.application.execution.handlers.modern_condition import ModernConditionHandler
        from dipeo.core.static.generated_nodes import ConditionNode
        
        tracker = ExecutionTracker()
        
        # Setup: PersonJobNode executes and gets reset for iteration
        person_node_id = NodeID("person-1")
        tracker.start_execution(person_node_id)
        person_output = TextOutput(value="Generated text", node_id=person_node_id)
        tracker.complete_execution(person_node_id, CompletionStatus.SUCCESS, person_output)
        
        # Reset for iteration (like current bug scenario)
        tracker.reset_for_iteration(person_node_id)
        
        # Create condition node that checks if person node executed
        condition_node = ConditionNode(
            id=NodeID("condition-1"),
            label="Check execution",
            condition_type="has_executed",
            node_indices=[person_node_id],
            position=Vec2(x=0, y=0)  # Required position field
        )
        
        # Create mock context with tracker
        class MockContext:
            def __init__(self):
                self.metadata = {"execution_tracker": tracker}
                self.variables = {}
        
        # Execute condition handler
        handler = ModernConditionHandler()
        context = MockContext()
        
        # This should not fail even though person node was reset
        condition_output = await handler.execute(
            node=condition_node,
            context=context,
            inputs={},
            services={}
        )
        
        assert isinstance(condition_output, ConditionOutput)
        assert condition_output.value is True  # Person node HAS executed
        assert condition_output.metadata["condition_type"] == "has_executed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])