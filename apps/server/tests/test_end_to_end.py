"""End-to-end tests for the complete DiPeO system."""

import pytest
import json
import time
import asyncio
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch

from ..src.services.unified_execution_engine import UnifiedExecutionEngine
from ..src.services.llm_service import LLMService
from ..src.services.api_key_service import APIKeyService
from ..src.services.memory_service import MemoryService
from .fixtures.diagrams import DiagramFixtures
from .fixtures.mocks import MockLLMService, MockAPIKeyService, MockMemoryService


@pytest.fixture(scope="session")
def test_diagrams_dir():
    """Create temporary directory for test diagrams."""
    test_dir = Path("/tmp/dipeo_test_diagrams")
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def e2e_engine():
    """Create execution engine for end-to-end testing."""
    return UnifiedExecutionEngine(
        llm_service=MockLLMService({
            "openai": "I understand the task and will complete it.",
            "claude": "I'll help you with this request.",
            "gemini": "Certainly! I can assist with that."
        }),
        api_key_service=MockAPIKeyService(),
        memory_service=MockMemoryService()
    )


class TestCompleteExecutionFlows:
    """Test complete execution flows from start to finish."""
    
    @pytest.mark.asyncio
    async def test_content_creation_workflow(self, e2e_engine, test_diagrams_dir):
        """Test a complete content creation workflow."""
        # Create content creation diagram
        diagram = {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "id": "start1",
                        "label": "Topic Input",
                        "output": "AI and Machine Learning"
                    }
                },
                {
                    "id": "research1",
                    "type": "person_job",
                    "position": {"x": 200, "y": 0},
                    "data": {
                        "id": "research1",
                        "label": "Researcher",
                        "personId": "researcher",
                        "prompt": "Research the topic: {{topic}}. Provide key insights and current trends."
                    }
                },
                {
                    "id": "writer1",
                    "type": "person_job",
                    "position": {"x": 400, "y": 0},
                    "data": {
                        "id": "writer1",
                        "label": "Content Writer",
                        "personId": "writer",
                        "prompt": "Based on the research: {{research}}, write a comprehensive article about {{topic}}."
                    }
                },
                {
                    "id": "editor1",
                    "type": "person_job",
                    "position": {"x": 600, "y": 0},
                    "data": {
                        "id": "editor1",
                        "label": "Editor",
                        "personId": "editor",
                        "prompt": "Edit and improve this article: {{article}}. Make it more engaging and fix any issues."
                    }
                },
                {
                    "id": "save1",
                    "type": "endpoint",
                    "position": {"x": 800, "y": 0},
                    "data": {
                        "id": "save1",
                        "label": "Save Article",
                        "filename": "article.txt"
                    }
                }
            ],
            "arrows": [
                {
                    "id": "arrow-1",
                    "source": "start1",
                    "target": "research1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-1",
                        "sourceBlockId": "start1",
                        "targetBlockId": "research1",
                        "label": "topic",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-2",
                    "source": "research1",
                    "target": "writer1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-2",
                        "sourceBlockId": "research1",
                        "targetBlockId": "writer1",
                        "label": "research",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-3",
                    "source": "writer1",
                    "target": "editor1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-3",
                        "sourceBlockId": "writer1",
                        "targetBlockId": "editor1",
                        "label": "article",
                        "contentType": "variable"
                    }
                },
                {
                    "id": "arrow-4",
                    "source": "editor1",
                    "target": "save1",
                    "type": "customArrow",
                    "data": {
                        "id": "arrow-data-4",
                        "sourceBlockId": "editor1",
                        "targetBlockId": "save1",
                        "label": "final_article",
                        "contentType": "variable"
                    }
                }
            ],
            "persons": [
                {
                    "id": "researcher",
                    "name": "AI Researcher",
                    "service": "openai",
                    "model": "gpt-4",
                    "apiKeyId": "test-key-1"
                },
                {
                    "id": "writer",
                    "name": "Content Writer",
                    "service": "claude",
                    "model": "claude-3-sonnet",
                    "apiKeyId": "test-key-2"
                },
                {
                    "id": "editor",
                    "name": "Editor",
                    "service": "gemini",
                    "model": "gemini-pro",
                    "apiKeyId": "test-key-3"
                }
            ],
            "apiKeys": [
                {
                    "id": "test-key-1",
                    "name": "OpenAI Key",
                    "service": "openai"
                },
                {
                    "id": "test-key-2",
                    "name": "Claude Key",
                    "service": "claude"
                },
                {
                    "id": "test-key-3",
                    "name": "Gemini Key",
                    "service": "gemini"
                }
            ]
        }
        
        # Execute the workflow
        start_time = time.time()
        result = {}
        steps_completed = 0
        
        async for update in e2e_engine.execute_diagram(diagram):
            if update.get('type') == 'node_complete':
                steps_completed += 1
                node_data = update.get('data', {})
                print(f"✓ Completed: {node_data.get('nodeId', 'unknown')}")
            elif update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify workflow completion
        assert 'context' in result
        assert steps_completed == 5  # All 5 nodes should complete
        assert result['totalCost'] > 0  # Should have LLM costs
        
        # Verify execution order
        context = result['context']
        execution_order = context['executionOrder']
        assert execution_order == ['start1', 'research1', 'writer1', 'editor1', 'save1']
        
        # Verify all outputs exist
        assert 'start1' in context['nodeOutputs']
        assert 'research1' in context['nodeOutputs']
        assert 'writer1' in context['nodeOutputs']
        assert 'editor1' in context['nodeOutputs']
        assert 'save1' in context['nodeOutputs']
        
        print(f"Content creation workflow completed in {execution_time:.2f}s")
        print(f"Total cost: ${result['totalCost']:.4f}")
    
    @pytest.mark.asyncio
    async def test_decision_making_workflow(self, e2e_engine):
        """Test a workflow with decision making and branching."""
        diagram = {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "id": "start1",
                        "label": "Input",
                        "output": "urgent: Fix critical security vulnerability"
                    }
                },
                {
                    "id": "classifier1",
                    "type": "person_job",
                    "position": {"x": 200, "y": 0},
                    "data": {
                        "id": "classifier1",
                        "label": "Priority Classifier",
                        "personId": "classifier",
                        "prompt": "Classify this request as HIGH, MEDIUM, or LOW priority: {{request}}"
                    }
                },
                {
                    "id": "condition1",
                    "type": "condition",
                    "position": {"x": 400, "y": 0},
                    "data": {
                        "id": "condition1",
                        "label": "Check Priority",
                        "condition": "'HIGH' in priority"
                    }
                },
                {
                    "id": "urgent_handler",
                    "type": "person_job",
                    "position": {"x": 600, "y": -100},
                    "data": {
                        "id": "urgent_handler",
                        "label": "Urgent Handler",
                        "personId": "urgent",
                        "prompt": "Handle this urgent request immediately: {{request}}"
                    }
                },
                {
                    "id": "normal_handler",
                    "type": "person_job",
                    "position": {"x": 600, "y": 100},
                    "data": {
                        "id": "normal_handler",
                        "label": "Normal Handler",
                        "personId": "normal",
                        "prompt": "Process this request: {{request}}"
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "position": {"x": 800, "y": 0},
                    "data": {
                        "id": "end1",
                        "label": "Complete",
                        "filename": "result.txt"
                    }
                }
            ],
            "arrows": [
                {
                    "id": "arrow-1",
                    "source": "start1",
                    "target": "classifier1",
                    "data": {"label": "request"}
                },
                {
                    "id": "arrow-2",
                    "source": "classifier1",
                    "target": "condition1",
                    "data": {"label": "priority"}
                },
                {
                    "id": "arrow-3",
                    "source": "condition1",
                    "target": "urgent_handler",
                    "data": {"label": "true"}
                },
                {
                    "id": "arrow-4",
                    "source": "condition1",
                    "target": "normal_handler",
                    "data": {"label": "false"}
                },
                {
                    "id": "arrow-5",
                    "source": "urgent_handler",
                    "target": "end1",
                    "data": {"label": ""}
                },
                {
                    "id": "arrow-6",
                    "source": "normal_handler",
                    "target": "end1",
                    "data": {"label": ""}
                }
            ],
            "persons": [
                {
                    "id": "classifier",
                    "name": "Priority Classifier",
                    "service": "openai",
                    "model": "gpt-4",
                    "apiKeyId": "test-key-1"
                },
                {
                    "id": "urgent",
                    "name": "Urgent Handler",
                    "service": "openai",
                    "model": "gpt-4",
                    "apiKeyId": "test-key-1"
                },
                {
                    "id": "normal",
                    "name": "Normal Handler",
                    "service": "openai",
                    "model": "gpt-3.5-turbo",
                    "apiKeyId": "test-key-1"
                }
            ],
            "apiKeys": [
                {
                    "id": "test-key-1",
                    "name": "OpenAI Key",
                    "service": "openai"
                }
            ]
        }
        
        # Execute workflow
        result = {}
        branch_taken = None
        
        async for update in e2e_engine.execute_diagram(diagram):
            if update.get('type') == 'node_complete':
                node_data = update.get('data', {})
                node_id = node_data.get('nodeId')
                if node_id in ['urgent_handler', 'normal_handler']:
                    branch_taken = node_id
            elif update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify branching logic
        assert 'context' in result
        assert branch_taken is not None
        
        # Should have taken urgent branch due to "urgent" keyword
        assert branch_taken == 'urgent_handler'
        
        # Verify condition was evaluated
        context = result['context']
        assert 'condition1' in context['conditionValues']
    
    @pytest.mark.asyncio
    async def test_iterative_improvement_workflow(self, e2e_engine):
        """Test workflow with iterative improvement loops."""
        diagram = {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "id": "start1",
                        "label": "Initial Code",
                        "output": "def add(a, b): return a + b"
                    }
                },
                {
                    "id": "reviewer1",
                    "type": "person_job",
                    "position": {"x": 200, "y": 0},
                    "data": {
                        "id": "reviewer1",
                        "label": "Code Reviewer",
                        "personId": "reviewer",
                        "prompt": "Review this code and suggest improvements: {{code}}. Respond with 'GOOD' if acceptable, or specific improvements needed.",
                        "maxIterations": 3
                    }
                },
                {
                    "id": "condition1",
                    "type": "condition",
                    "position": {"x": 400, "y": 0},
                    "data": {
                        "id": "condition1",
                        "label": "Check Quality",
                        "condition": "'GOOD' in review or iteration_count >= 3"
                    }
                },
                {
                    "id": "improver1",
                    "type": "person_job",
                    "position": {"x": 200, "y": 200},
                    "data": {
                        "id": "improver1",
                        "label": "Code Improver",
                        "personId": "improver",
                        "prompt": "Improve this code based on the review: {{review}}. Original code: {{code}}"
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "position": {"x": 600, "y": 0},
                    "data": {
                        "id": "end1",
                        "label": "Final Code",
                        "filename": "improved_code.py"
                    }
                }
            ],
            "arrows": [
                {
                    "id": "arrow-1",
                    "source": "start1",
                    "target": "reviewer1",
                    "data": {"label": "code"}
                },
                {
                    "id": "arrow-2",
                    "source": "reviewer1",
                    "target": "condition1",
                    "data": {"label": "review"}
                },
                {
                    "id": "arrow-3",
                    "source": "condition1",
                    "target": "end1",
                    "data": {"label": "true"}
                },
                {
                    "id": "arrow-4",
                    "source": "condition1",
                    "target": "improver1",
                    "data": {"label": "false"}
                },
                {
                    "id": "arrow-5",
                    "source": "improver1",
                    "target": "reviewer1",
                    "data": {"label": "code"}
                }
            ],
            "persons": [
                {
                    "id": "reviewer",
                    "name": "Code Reviewer",
                    "service": "openai",
                    "model": "gpt-4",
                    "apiKeyId": "test-key-1"
                },
                {
                    "id": "improver",
                    "name": "Code Improver",
                    "service": "openai",
                    "model": "gpt-4",
                    "apiKeyId": "test-key-1"
                }
            ],
            "apiKeys": [
                {
                    "id": "test-key-1",
                    "name": "OpenAI Key",
                    "service": "openai"
                }
            ]
        }
        
        # Execute workflow
        result = {}
        reviewer_executions = 0
        
        async for update in e2e_engine.execute_diagram(diagram):
            if update.get('type') == 'node_complete':
                node_data = update.get('data', {})
                if node_data.get('nodeId') == 'reviewer1':
                    reviewer_executions += 1
            elif update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify iterative execution
        assert 'context' in result
        assert reviewer_executions <= 3  # Max iterations respected
        assert reviewer_executions >= 1   # At least one execution
        
        # Verify loop termination
        context = result['context']
        assert 'end1' in context['nodeOutputs']  # Should reach end
    
    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, e2e_engine):
        """Test workflow with error handling and recovery."""
        # Mock LLM service that simulates errors
        error_llm = MockLLMService({
            "error_service": "ERROR: Service unavailable",
            "backup_service": "Backup service response"
        })
        
        error_engine = UnifiedExecutionEngine(
            llm_service=error_llm,
            api_key_service=MockAPIKeyService(),
            memory_service=MockMemoryService()
        )
        
        diagram = {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "position": {"x": 0, "y": 0},
                    "data": {
                        "id": "start1",
                        "label": "Input",
                        "output": "Process this request"
                    }
                },
                {
                    "id": "primary1",
                    "type": "person_job",
                    "position": {"x": 200, "y": 0},
                    "data": {
                        "id": "primary1",
                        "label": "Primary Service",
                        "personId": "primary",
                        "prompt": "Process: {{input}}"
                    }
                },
                {
                    "id": "condition1",
                    "type": "condition",
                    "position": {"x": 400, "y": 0},
                    "data": {
                        "id": "condition1",
                        "label": "Check Success",
                        "condition": "'ERROR' not in output"
                    }
                },
                {
                    "id": "backup1",
                    "type": "person_job",
                    "position": {"x": 400, "y": 200},
                    "data": {
                        "id": "backup1",
                        "label": "Backup Service",
                        "personId": "backup",
                        "prompt": "Backup process: {{input}}"
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "position": {"x": 600, "y": 0},
                    "data": {
                        "id": "end1",
                        "label": "Result",
                        "filename": "result.txt"
                    }
                }
            ],
            "arrows": [
                {
                    "id": "arrow-1",
                    "source": "start1",
                    "target": "primary1",
                    "data": {"label": "input"}
                },
                {
                    "id": "arrow-2",
                    "source": "primary1",
                    "target": "condition1",
                    "data": {"label": "output"}
                },
                {
                    "id": "arrow-3",
                    "source": "condition1",
                    "target": "end1",
                    "data": {"label": "true"}
                },
                {
                    "id": "arrow-4",
                    "source": "condition1",
                    "target": "backup1",
                    "data": {"label": "false"}
                },
                {
                    "id": "arrow-5",
                    "source": "backup1",
                    "target": "end1",
                    "data": {"label": ""}
                }
            ],
            "persons": [
                {
                    "id": "primary",
                    "name": "Primary Service",
                    "service": "error_service",
                    "model": "error-model",
                    "apiKeyId": "test-key-1"
                },
                {
                    "id": "backup",
                    "name": "Backup Service",
                    "service": "backup_service",
                    "model": "backup-model",
                    "apiKeyId": "test-key-1"
                }
            ],
            "apiKeys": [
                {
                    "id": "test-key-1",
                    "name": "Test Key",
                    "service": "test"
                }
            ]
        }
        
        # Execute workflow
        result = {}
        backup_used = False
        
        async for update in error_engine.execute_diagram(diagram):
            if update.get('type') == 'node_complete':
                node_data = update.get('data', {})
                if node_data.get('nodeId') == 'backup1':
                    backup_used = True
            elif update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify error recovery
        assert 'context' in result
        assert backup_used  # Backup should have been used due to primary error
        
        # Verify final result
        context = result['context']
        assert 'end1' in context['nodeOutputs']


class TestSystemIntegration:
    """Test integration between different system components."""
    
    @pytest.mark.asyncio
    async def test_memory_persistence_across_executions(self, e2e_engine):
        """Test that memory persists correctly across multiple executions."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # First execution
        async for update in e2e_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                break
        
        # Second execution - should use memory from first
        result = {}
        async for update in e2e_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify execution completed successfully
        assert 'context' in result
        
        # Check memory service has recorded interactions
        memory_service = e2e_engine.memory_service
        assert len(memory_service.memory_data) > 0
    
    @pytest.mark.asyncio
    async def test_cost_tracking_accuracy(self, e2e_engine):
        """Test that cost tracking is accurate across different services."""
        diagram = {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "data": {"output": "Test input"}
                },
                {
                    "id": "openai1",
                    "type": "person_job",
                    "data": {
                        "personId": "openai_person",
                        "prompt": "Process with OpenAI: {{input}}"
                    }
                },
                {
                    "id": "claude1",
                    "type": "person_job",
                    "data": {
                        "personId": "claude_person",
                        "prompt": "Process with Claude: {{openai_output}}"
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "data": {"filename": "result.txt"}
                }
            ],
            "arrows": [
                {"source": "start1", "target": "openai1", "data": {"label": "input"}},
                {"source": "openai1", "target": "claude1", "data": {"label": "openai_output"}},
                {"source": "claude1", "target": "end1", "data": {"label": ""}}
            ],
            "persons": [
                {
                    "id": "openai_person",
                    "service": "openai",
                    "model": "gpt-4",
                    "apiKeyId": "key1"
                },
                {
                    "id": "claude_person",
                    "service": "claude",
                    "model": "claude-3",
                    "apiKeyId": "key2"
                }
            ],
            "apiKeys": [
                {"id": "key1", "service": "openai"},
                {"id": "key2", "service": "claude"}
            ]
        }
        
        # Execute and track costs
        result = {}
        node_costs = []
        
        async for update in e2e_engine.execute_diagram(diagram):
            if update.get('type') == 'node_complete':
                node_data = update.get('data', {})
                if 'cost' in node_data:
                    node_costs.append(node_data['cost'])
            elif update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify cost tracking
        assert 'totalCost' in result
        assert result['totalCost'] > 0
        
        # Sum of individual costs should equal total
        expected_total = sum(node_costs)
        assert abs(result['totalCost'] - expected_total) < 0.001  # Allow for floating point precision
    
    def test_diagram_validation_integration(self, e2e_engine):
        """Test integration with diagram validation."""
        # Invalid diagram (missing required fields)
        invalid_diagram = {
            "nodes": [
                {"id": "node1"}  # Missing type and data
            ],
            "arrows": [],
            "persons": [],
            "apiKeys": []
        }
        
        # Should handle validation gracefully
        async def execute_invalid():
            async for update in e2e_engine.execute_diagram(invalid_diagram):
                if update.get('type') in ['error', 'execution_complete']:
                    return update
        
        # Should either return error or handle gracefully
        result = asyncio.run(execute_invalid())
        assert result is not None


class TestDataFlowIntegrity:
    """Test data flow integrity throughout execution."""
    
    @pytest.mark.asyncio
    async def test_variable_substitution_chain(self, e2e_engine):
        """Test variable substitution through a chain of nodes."""
        diagram = {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "data": {"output": "Initial Value: 42"}
                },
                {
                    "id": "processor1",
                    "type": "job",
                    "data": {
                        "language": "python",
                        "code": "result = '{{input}}'.replace('42', '100')"
                    }
                },
                {
                    "id": "processor2",
                    "type": "job",
                    "data": {
                        "language": "python",
                        "code": "result = '{{processed}}' + ' - Final'"
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "data": {"filename": "chain_result.txt"}
                }
            ],
            "arrows": [
                {"source": "start1", "target": "processor1", "data": {"label": "input"}},
                {"source": "processor1", "target": "processor2", "data": {"label": "processed"}},
                {"source": "processor2", "target": "end1", "data": {"label": ""}}
            ],
            "persons": [],
            "apiKeys": []
        }
        
        # Execute and verify data flow
        result = {}
        async for update in e2e_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify data transformations
        context = result['context']
        node_outputs = context['nodeOutputs']
        
        assert 'start1' in node_outputs
        assert 'processor1' in node_outputs  
        assert 'processor2' in node_outputs
        
        # Verify the chain of transformations
        start_output = node_outputs['start1']
        assert "42" in start_output
        
        final_output = node_outputs['processor2']
        assert "100" in final_output  # Should have been transformed
        assert "Final" in final_output  # Should have been appended
    
    @pytest.mark.asyncio
    async def test_complex_variable_mapping(self, e2e_engine):
        """Test complex variable mapping scenarios."""
        diagram = {
            "nodes": [
                {
                    "id": "start1",
                    "type": "start",
                    "data": {"output": "Name: Alice, Age: 30"}
                },
                {
                    "id": "parser1",
                    "type": "job",
                    "data": {
                        "language": "python",
                        "code": "import re; match = re.search(r'Name: (\\w+), Age: (\\d+)', '{{user_info}}'); result = {'name': match.group(1), 'age': int(match.group(2))} if match else {}"
                    }
                },
                {
                    "id": "formatter1",
                    "type": "job",
                    "data": {
                        "language": "python",
                        "code": "result = f'Hello {{name}}, you are {{age}} years old.'.format(name='{{parsed.name}}', age='{{parsed.age}}')"
                    }
                },
                {
                    "id": "end1",
                    "type": "endpoint",
                    "data": {"filename": "formatted.txt"}
                }
            ],
            "arrows": [
                {"source": "start1", "target": "parser1", "data": {"label": "user_info"}},
                {"source": "parser1", "target": "formatter1", "data": {"label": "parsed"}},
                {"source": "formatter1", "target": "end1", "data": {"label": ""}}
            ],
            "persons": [],
            "apiKeys": []
        }
        
        # Execute workflow
        result = {}
        async for update in e2e_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        
        # Verify complex variable handling
        assert 'context' in result
        context = result['context']
        
        # Should have processed all nodes
        assert len(context['nodeOutputs']) == 4  # start, parser, formatter, end