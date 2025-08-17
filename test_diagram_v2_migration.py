#!/usr/bin/env python3
"""Test script to verify diagram services V2 migration."""

import os
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_v1_services():
    """Test with V1 services (default)."""
    logger.info("Testing V1 services...")
    
    # Ensure V2 is disabled
    os.environ.pop("DIAGRAM_PORT_V2", None)
    os.environ.pop("DIAGRAM_COMPILER_V2", None)
    os.environ.pop("DIAGRAM_SERIALIZER_V2", None)
    
    from dipeo.application.registry import ServiceRegistry
    from dipeo.application.bootstrap import ApplicationContainer
    from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter
    from dipeo.application.registry.keys import FILESYSTEM_ADAPTER, DIAGRAM_SERVICE
    
    # Create registry and wire services
    registry = ServiceRegistry()
    registry.register(FILESYSTEM_ADAPTER, LocalFileSystemAdapter())
    
    # This should use V1 services
    app_container = ApplicationContainer(registry)
    
    # Get the diagram service
    diagram_service = registry.resolve(DIAGRAM_SERVICE)
    assert diagram_service is not None, "DiagramService not registered"
    
    # Check it's using V1
    assert not diagram_service._using_v2_converter, "Should be using V1 converter"
    assert not diagram_service._using_v2_compiler, "Should be using V1 compiler"
    
    logger.info("✅ V1 services test passed")
    return True

async def test_v2_services():
    """Test with V2 services enabled."""
    logger.info("Testing V2 services...")
    
    # Enable V2
    os.environ["DIAGRAM_PORT_V2"] = "1"
    os.environ["DIAGRAM_COMPILER_V2"] = "1"
    os.environ["DIAGRAM_SERIALIZER_V2"] = "1"
    os.environ["DIAGRAM_USE_INTERFACE_COMPILER"] = "1"
    os.environ["DIAGRAM_COMPILER_CACHE"] = "1"
    
    # Clear any cached modules
    import sys
    modules_to_clear = [k for k in sys.modules.keys() if 'dipeo.application.wiring' in k]
    for module in modules_to_clear:
        del sys.modules[module]
    
    from dipeo.application.registry import ServiceRegistry
    from dipeo.application.bootstrap import ApplicationContainer
    from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter
    from dipeo.application.registry.keys import FILESYSTEM_ADAPTER, DIAGRAM_SERVICE
    
    # Create registry and wire services
    registry = ServiceRegistry()
    registry.register(FILESYSTEM_ADAPTER, LocalFileSystemAdapter())
    
    # This should use V2 services
    app_container = ApplicationContainer(registry)
    
    # Get the diagram service
    diagram_service = registry.resolve(DIAGRAM_SERVICE)
    assert diagram_service is not None, "DiagramService not registered"
    
    # Check it's using V2
    assert diagram_service._using_v2_converter, "Should be using V2 converter"
    assert diagram_service._using_v2_compiler, "Should be using V2 compiler"
    
    logger.info("✅ V2 services test passed")
    return True

async def test_compilation():
    """Test that compilation works with both V1 and V2."""
    logger.info("Testing compilation...")
    
    from dipeo.diagram_generated import DomainDiagram, DomainNode, NodeType, DiagramMetadata
    from dipeo.application.registry import ServiceRegistry
    from dipeo.application.bootstrap import ApplicationContainer
    from dipeo.infrastructure.adapters.storage import LocalFileSystemAdapter
    from dipeo.application.registry.keys import FILESYSTEM_ADAPTER, DIAGRAM_SERVICE
    
    # Create a simple test diagram
    from datetime import datetime
    
    test_diagram = DomainDiagram(
        metadata=DiagramMetadata(
            id="test_diagram",
            name="Test Diagram",
            version="1.0.0",
            created=datetime.now().isoformat(),
            modified=datetime.now().isoformat()
        ),
        nodes=[
            DomainNode(
                id="start",
                type=NodeType.START,
                position={"x": 0, "y": 0},
                data={"label": "Start"}
            ),
            DomainNode(
                id="end",
                type=NodeType.ENDPOINT,
                position={"x": 100, "y": 0},
                data={"label": "End"}
            )
        ],
        arrows=[],
        handles=[],
        persons=[]
    )
    
    # Test with V1
    os.environ.pop("DIAGRAM_PORT_V2", None)
    registry = ServiceRegistry()
    registry.register(FILESYSTEM_ADAPTER, LocalFileSystemAdapter())
    app_container = ApplicationContainer(registry)
    diagram_service = registry.resolve(DIAGRAM_SERVICE)
    
    await diagram_service.initialize()
    executable_v1 = diagram_service.compile(test_diagram)
    assert executable_v1 is not None, "V1 compilation failed"
    assert len(executable_v1.nodes) == 2, "V1 compilation incorrect"
    logger.info("✅ V1 compilation test passed")
    
    # Test with V2
    os.environ["DIAGRAM_PORT_V2"] = "1"
    
    # Clear cached modules
    import sys
    modules_to_clear = [k for k in sys.modules.keys() if 'dipeo.application.wiring' in k]
    for module in modules_to_clear:
        del sys.modules[module]
    
    registry = ServiceRegistry()
    registry.register(FILESYSTEM_ADAPTER, LocalFileSystemAdapter())
    app_container = ApplicationContainer(registry)
    diagram_service = registry.resolve(DIAGRAM_SERVICE)
    
    await diagram_service.initialize()
    executable_v2 = diagram_service.compile(test_diagram)
    assert executable_v2 is not None, "V2 compilation failed"
    assert len(executable_v2.nodes) == 2, "V2 compilation incorrect"
    logger.info("✅ V2 compilation test passed")
    
    return True

async def main():
    """Run all tests."""
    try:
        await test_v1_services()
        await test_v2_services()
        await test_compilation()
        logger.info("\n🎉 All tests passed! Migration is working correctly.")
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())