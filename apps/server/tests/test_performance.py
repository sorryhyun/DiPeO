"""Performance benchmarks and tests."""

import pytest
import time
import asyncio
from typing import Dict, Any, List
from unittest.mock import patch

from ..src.services.unified_execution_engine import UnifiedExecutionEngine
from .fixtures.diagrams import DiagramFixtures
from .fixtures.mocks import MockLLMService, MockAPIKeyService, MockMemoryService


@pytest.fixture
def performance_engine():
    """Create execution engine optimized for performance testing."""
    # Use faster mock services
    llm_service = MockLLMService({
        "openai": "Fast response",
        "claude": "Fast response", 
        "gemini": "Fast response"
    })
    
    return UnifiedExecutionEngine(
        llm_service=llm_service,
        api_key_service=MockAPIKeyService(),
        memory_service=MockMemoryService()
    )


class TestExecutionPerformance:
    """Performance benchmarks for diagram execution."""
    
    @pytest.mark.asyncio
    async def test_simple_diagram_performance(self, performance_engine):
        """Benchmark simple linear diagram execution."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # Warm up
        async for _ in performance_engine.execute_diagram(diagram):
            pass
        
        # Benchmark
        start_time = time.time()
        async for update in performance_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                break
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete within 1 second for simple diagram
        assert execution_time < 1.0
        print(f"Simple diagram execution time: {execution_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_complex_diagram_performance(self, performance_engine):
        """Benchmark complex diagram with branches and loops."""
        diagram = DiagramFixtures.iterating_diagram()
        
        start_time = time.time()
        async for update in performance_engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                break
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should complete within 5 seconds for complex diagram
        assert execution_time < 5.0
        print(f"Complex diagram execution time: {execution_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_executions(self, performance_engine):
        """Test performance with concurrent diagram executions."""
        diagram = DiagramFixtures.simple_linear_diagram()
        num_concurrent = 5
        
        async def execute_diagram():
            async for update in performance_engine.execute_diagram(diagram):
                if update.get('type') == 'execution_complete':
                    return update.get('data', {})
        
        start_time = time.time()
        
        # Run concurrent executions
        tasks = [execute_diagram() for _ in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All executions should complete
        assert len(results) == num_concurrent
        for result in results:
            assert 'context' in result
        
        # Should handle concurrency efficiently
        avg_time_per_execution = total_time / num_concurrent
        assert avg_time_per_execution < 2.0
        
        print(f"Concurrent executions ({num_concurrent}): {total_time:.3f}s total, {avg_time_per_execution:.3f}s avg")
    
    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self, performance_engine):
        """Test memory usage with increasing diagram complexity."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute diagrams of increasing complexity
        diagrams = [
            DiagramFixtures.simple_linear_diagram(),
            DiagramFixtures.branching_diagram(),
            DiagramFixtures.iterating_diagram()
        ]
        
        memory_usage = []
        
        for i, diagram in enumerate(diagrams):
            async for update in performance_engine.execute_diagram(diagram):
                if update.get('type') == 'execution_complete':
                    break
            
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = current_memory - baseline_memory
            memory_usage.append(memory_increase)
            
            print(f"Diagram {i+1} memory usage: +{memory_increase:.1f}MB")
        
        # Memory usage should not grow excessively
        max_memory_increase = max(memory_usage)
        assert max_memory_increase < 100  # Less than 100MB increase
    
    @pytest.mark.asyncio
    async def test_streaming_performance(self, performance_engine):
        """Test streaming update performance."""
        diagram = DiagramFixtures.simple_linear_diagram()
        
        start_time = time.time()
        update_count = 0
        first_update_time = None
        
        async for update in performance_engine.execute_diagram(diagram):
            update_count += 1
            
            if first_update_time is None:
                first_update_time = time.time() - start_time
            
            if update.get('type') == 'execution_complete':
                break
        
        total_time = time.time() - start_time
        
        # Should receive multiple updates
        assert update_count > 1
        
        # First update should come quickly (low latency)
        assert first_update_time < 0.5
        
        # Updates should be frequent
        avg_time_between_updates = total_time / update_count
        assert avg_time_between_updates < 1.0
        
        print(f"Streaming: {update_count} updates in {total_time:.3f}s, first update in {first_update_time:.3f}s")


class TestResourceUtilization:
    """Test resource utilization efficiency."""
    
    @pytest.mark.asyncio
    async def test_cpu_utilization(self, performance_engine):
        """Test CPU utilization during execution."""
        import psutil
        import threading
        
        diagram = DiagramFixtures.branching_diagram()
        
        # Monitor CPU usage
        cpu_usage = []
        stop_monitoring = False
        
        def monitor_cpu():
            while not stop_monitoring:
                cpu_usage.append(psutil.cpu_percent(interval=0.1))
                time.sleep(0.1)
        
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        try:
            # Execute diagram
            async for update in performance_engine.execute_diagram(diagram):
                if update.get('type') == 'execution_complete':
                    break
        finally:
            stop_monitoring = True
            monitor_thread.join()
        
        if cpu_usage:
            avg_cpu = sum(cpu_usage) / len(cpu_usage)
            max_cpu = max(cpu_usage)
            
            print(f"CPU usage - Avg: {avg_cpu:.1f}%, Max: {max_cpu:.1f}%")
            
            # Should not consume excessive CPU
            assert avg_cpu < 80.0  # Average CPU usage below 80%
    
    def test_memory_leaks(self, performance_engine):
        """Test for memory leaks during repeated executions."""
        import psutil
        import os
        import gc
        
        process = psutil.Process(os.getpid())
        diagram = DiagramFixtures.simple_linear_diagram()
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run multiple executions
        for i in range(10):
            asyncio.run(self._execute_diagram_once(performance_engine, diagram))
            
            if i % 5 == 0:  # Check memory every 5 executions
                gc.collect()
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - baseline_memory
                
                print(f"After {i+1} executions: +{memory_increase:.1f}MB")
                
                # Memory shouldn't grow significantly
                assert memory_increase < 50  # Less than 50MB increase
    
    async def _execute_diagram_once(self, engine, diagram):
        """Helper to execute diagram once."""
        async for update in engine.execute_diagram(diagram):
            if update.get('type') == 'execution_complete':
                break


class TestScalabilityLimits:
    """Test scalability limits and thresholds."""
    
    @pytest.mark.asyncio
    async def test_large_diagram_nodes(self, performance_engine):
        """Test performance with large number of nodes."""
        # Create diagram with many nodes
        nodes = []
        arrows = []
        
        # Start node
        nodes.append({
            "id": "start1",
            "type": "start",
            "position": {"x": 0, "y": 0},
            "data": {"id": "start1", "label": "Start", "output": "Begin"}
        })
        
        # Chain of job nodes
        for i in range(20):  # 20 nodes should be manageable
            node_id = f"job{i}"
            nodes.append({
                "id": node_id,
                "type": "job",
                "position": {"x": (i+1)*100, "y": 0},
                "data": {
                    "id": node_id,
                    "label": f"Job {i}",
                    "language": "python",
                    "code": f"result = {i} + 1"
                }
            })
            
            # Connect to previous node
            prev_id = f"job{i-1}" if i > 0 else "start1"
            arrows.append({
                "id": f"arrow-{i}",
                "source": prev_id,
                "target": node_id,
                "type": "customArrow",
                "data": {
                    "id": f"arrow-data-{i}",
                    "sourceBlockId": prev_id,
                    "targetBlockId": node_id,
                    "label": "",
                    "contentType": "variable"
                }
            })
        
        # End node
        nodes.append({
            "id": "end1",
            "type": "endpoint",
            "position": {"x": 2100, "y": 0},
            "data": {"id": "end1", "label": "End"}
        })
        
        arrows.append({
            "id": "arrow-final",
            "source": "job19",
            "target": "end1",
            "type": "customArrow",
            "data": {
                "id": "arrow-data-final",
                "sourceBlockId": "job19",
                "targetBlockId": "end1",
                "label": "",
                "contentType": "variable"
            }
        })
        
        large_diagram = {
            "nodes": nodes,
            "arrows": arrows,
            "persons": [],
            "apiKeys": []
        }
        
        start_time = time.time()
        async for update in performance_engine.execute_diagram(large_diagram):
            if update.get('type') == 'execution_complete':
                result = update.get('data', {})
                break
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Should handle large diagrams
        assert 'context' in result
        assert len(result['context']['nodeOutputs']) == 22  # 20 jobs + start + end
        
        # Should complete within reasonable time
        assert execution_time < 30.0  # 30 seconds for 20 nodes
        
        print(f"Large diagram (22 nodes) execution time: {execution_time:.3f}s")
    
    @pytest.mark.asyncio
    async def test_deep_iteration_performance(self, performance_engine):
        """Test performance with deep iteration loops."""
        # Create diagram with high max iterations
        diagram = DiagramFixtures.iterating_diagram()
        
        # Increase max iterations for stress test
        for node in diagram["nodes"]:
            if node.get("type") == "person_job":
                node["data"]["maxIterations"] = 10  # Higher iteration count
        
        start_time = time.time()
        iteration_count = 0
        
        async for update in performance_engine.execute_diagram(diagram):
            if update.get('type') == 'node_complete':
                node_data = update.get('data', {})
                if node_data.get('nodeType') == 'person_job':
                    iteration_count += 1
            elif update.get('type') == 'execution_complete':
                break
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should handle iterations efficiently
        assert iteration_count <= 10  # Shouldn't exceed max iterations
        assert execution_time < 15.0  # Should complete within 15 seconds
        
        print(f"Deep iteration test: {iteration_count} iterations in {execution_time:.3f}s")


# Utility function to generate performance reports
def generate_performance_report():
    """Generate a performance report for the execution engine."""
    # This could be expanded to create detailed performance reports
    # Including metrics like throughput, latency, resource usage, etc.
    pass