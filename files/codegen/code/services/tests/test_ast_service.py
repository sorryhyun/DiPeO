"""Compact tests for AST Service."""

import pytest
import asyncio
from pathlib import Path
from ..ast_service import ASTService, ASTProcessor


@pytest.mark.asyncio
async def test_ast_caching():
    service = ASTService()
    files = [Path('test.ts')]
    
    # First load should parse
    ast1 = await service.get_processed_ast(files, ['extract_models'])
    
    # Second load should use cache
    ast2 = await service.get_processed_ast(files, ['extract_models'])
    assert ast1 == ast2
    
    # Different processors should create different cache entry
    ast3 = await service.get_processed_ast(files, ['extract_enums'])
    assert 'extracted_enums' in ast3


@pytest.mark.asyncio
async def test_processor_dependencies():
    service = ASTService()
    
    # resolve_refs depends on extract_models and extract_enums
    files = [Path('test.ts')]
    result = await service.get_processed_ast(files, ['resolve_refs'])
    
    # Should have run all dependencies
    assert 'extracted_models' in result
    assert 'extracted_enums' in result
    assert result.get('references_resolved') is True


def test_custom_processor():
    service = ASTService()
    
    # Register custom processor
    custom_processor = ASTProcessor(
        id='custom',
        name='Custom',
        description='Test processor',
        process_func=lambda ast: {**ast, 'custom_processed': True}
    )
    service.register_processor(custom_processor)
    
    # Should be able to use it
    assert service._processor_registry.get('custom') is not None


def test_performance_tracking():
    service = ASTService()
    
    # After processing, should have stats
    asyncio.run(service.get_processed_ast([Path('test.ts')], ['extract_models']))
    stats = service.get_performance_stats()
    
    assert 'extract_models' in stats
    assert stats['extract_models']['count'] >= 1
    assert 'average' in stats['extract_models']