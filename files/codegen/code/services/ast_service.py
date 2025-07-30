"""AST Service with Smart Caching

Centralized AST processing with multi-level caching to reduce redundant
file reads and AST processing across generators.
"""

import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
import pickle


@dataclass
class CacheEntry:
    """Entry in the AST cache"""
    content_hash: str
    data: Any
    timestamp: datetime
    file_paths: List[Path]
    processor_ids: List[str] = field(default_factory=list)


class ContentAddressableCache:
    """Content-addressed cache for raw AST data"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path('.dipeo_cache/ast')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, Any] = {}
    
    def _compute_content_hash(self, file_paths: List[Path]) -> str:
        """Compute hash based on file contents"""
        hasher = hashlib.sha256()
        
        for path in sorted(file_paths):
            if path.exists():
                hasher.update(str(path).encode())
                hasher.update(path.read_bytes())
                hasher.update(str(path.stat().st_mtime).encode())
        
        return hasher.hexdigest()
    
    def get(self, file_paths: List[Path]) -> Optional[Any]:
        """Get cached AST data for files"""
        content_hash = self._compute_content_hash(file_paths)
        
        # Check memory cache first
        if content_hash in self._memory_cache:
            return self._memory_cache[content_hash]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{content_hash}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self._memory_cache[content_hash] = data
                    return data
            except Exception:
                # Invalid cache file, remove it
                cache_file.unlink()
        
        return None
    
    def set(self, file_paths: List[Path], data: Any) -> str:
        """Cache AST data for files"""
        content_hash = self._compute_content_hash(file_paths)
        
        # Store in memory
        self._memory_cache[content_hash] = data
        
        # Store on disk
        cache_file = self.cache_dir / f"{content_hash}.pkl"
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
        
        return content_hash
    
    def invalidate(self, file_paths: Optional[List[Path]] = None) -> None:
        """Invalidate cache entries"""
        if file_paths:
            content_hash = self._compute_content_hash(file_paths)
            self._memory_cache.pop(content_hash, None)
            cache_file = self.cache_dir / f"{content_hash}.pkl"
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all caches
            self._memory_cache.clear()
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()


class ProcessedASTCache:
    """Cache for processed AST data with processor tracking"""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
    
    def _compute_cache_key(self, content_hash: str, processor_ids: List[str]) -> str:
        """Compute cache key for processed AST"""
        processor_str = ','.join(sorted(processor_ids))
        return f"{content_hash}:{processor_str}"
    
    def get(self, content_hash: str, processor_ids: List[str]) -> Optional[Any]:
        """Get processed AST from cache"""
        cache_key = self._compute_cache_key(content_hash, processor_ids)
        entry = self._cache.get(cache_key)
        return entry.data if entry else None
    
    def set(self, content_hash: str, processor_ids: List[str], data: Any, file_paths: List[Path]) -> None:
        """Cache processed AST"""
        cache_key = self._compute_cache_key(content_hash, processor_ids)
        self._cache[cache_key] = CacheEntry(
            content_hash=content_hash,
            data=data,
            timestamp=datetime.now(),
            file_paths=file_paths,
            processor_ids=processor_ids
        )
    
    def invalidate_by_content(self, content_hash: str) -> None:
        """Invalidate all entries for a content hash"""
        keys_to_remove = [
            key for key, entry in self._cache.items()
            if entry.content_hash == content_hash
        ]
        for key in keys_to_remove:
            del self._cache[key]


@dataclass
class ASTProcessor:
    """Base class for AST processors"""
    id: str
    name: str
    description: str
    process_func: Callable[[Any], Any]
    dependencies: List[str] = field(default_factory=list)


class ProcessorRegistry:
    """Registry for AST processors"""
    
    def __init__(self):
        self._processors: Dict[str, ASTProcessor] = {}
        self._register_default_processors()
    
    def register(self, processor: ASTProcessor) -> None:
        """Register an AST processor"""
        self._processors[processor.id] = processor
    
    def get(self, processor_id: str) -> Optional[ASTProcessor]:
        """Get processor by ID"""
        return self._processors.get(processor_id)
    
    def get_execution_order(self, processor_ids: List[str]) -> List[str]:
        """Get processors in dependency order"""
        # Simple topological sort
        visited = set()
        order = []
        
        def visit(pid: str):
            if pid in visited:
                return
            visited.add(pid)
            
            processor = self._processors.get(pid)
            if processor:
                for dep in processor.dependencies:
                    visit(dep)
                order.append(pid)
        
        for pid in processor_ids:
            visit(pid)
        
        return order
    
    def _register_default_processors(self) -> None:
        """Register default AST processors"""
        # Extract models processor
        self.register(ASTProcessor(
            id='extract_models',
            name='Extract Models',
            description='Extract model definitions from AST',
            process_func=self._extract_models
        ))
        
        # Extract enums processor
        self.register(ASTProcessor(
            id='extract_enums',
            name='Extract Enums',
            description='Extract enum definitions from AST',
            process_func=self._extract_enums
        ))
        
        # Resolve references processor
        self.register(ASTProcessor(
            id='resolve_refs',
            name='Resolve References',
            description='Resolve type references in AST',
            process_func=self._resolve_references,
            dependencies=['extract_models', 'extract_enums']
        ))
    
    @staticmethod
    def _extract_models(ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract model definitions"""
        # This would contain actual extraction logic
        # For now, returning a placeholder
        models = ast_data.get('models', {})
        return {**ast_data, 'extracted_models': models}
    
    @staticmethod
    def _extract_enums(ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract enum definitions"""
        enums = ast_data.get('enums', {})
        return {**ast_data, 'extracted_enums': enums}
    
    @staticmethod
    def _resolve_references(ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve type references"""
        # This would contain actual resolution logic
        return {**ast_data, 'references_resolved': True}


class ASTService:
    """Centralized AST processing with multi-level caching"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self._raw_cache = ContentAddressableCache(cache_dir)
        self._processed_cache = ProcessedASTCache()
        self._processor_registry = ProcessorRegistry()
        self._performance_stats: Dict[str, List[float]] = {}
    
    async def get_processed_ast(
        self,
        files: List[Path],
        processors: List[str]
    ) -> Dict[str, Any]:
        """Get AST data with requested processors applied"""
        # Get raw AST (from cache if available)
        raw_ast = await self._load_raw_ast(files)
        content_hash = self._raw_cache._compute_content_hash(files)
        
        # Check processed cache
        cached_processed = self._processed_cache.get(content_hash, processors)
        if cached_processed is not None:
            return cached_processed
        
        # Apply processors
        processed = await self._apply_processors(raw_ast, processors)
        
        # Cache the result
        self._processed_cache.set(content_hash, processors, processed, files)
        
        return processed
    
    async def _load_raw_ast(self, files: List[Path]) -> Dict[str, Any]:
        """Load raw AST data with caching"""
        # Check cache first
        cached = self._raw_cache.get(files)
        if cached is not None:
            return cached
        
        # Load AST data (this would use actual AST parsing)
        # For now, we'll simulate loading from the existing cache format
        ast_data = await self._parse_files(files)
        
        # Cache the result
        self._raw_cache.set(files, ast_data)
        
        return ast_data
    
    async def _parse_files(self, files: List[Path]) -> Dict[str, Any]:
        """Parse TypeScript/other files to AST"""
        # This would integrate with existing TypeScript parsing
        # For now, return a placeholder structure
        result = {
            'files': [str(f) for f in files],
            'timestamp': datetime.now().isoformat(),
            'models': {},
            'enums': {},
            'interfaces': {},
        }
        
        # Try to load from existing cache format if available
        cache_dir = Path('files/codegen/.cache')
        if cache_dir.exists():
            for cache_file in cache_dir.glob('*.json'):
                try:
                    with open(cache_file) as f:
                        cached_data = json.load(f)
                        if 'ast_data' in cached_data:
                            result.update(cached_data['ast_data'])
                            break
                except Exception:
                    pass
        
        return result
    
    async def _apply_processors(
        self,
        ast_data: Dict[str, Any],
        processor_ids: List[str]
    ) -> Dict[str, Any]:
        """Apply processors to AST data"""
        # Get execution order based on dependencies
        execution_order = self._processor_registry.get_execution_order(processor_ids)
        
        # Apply processors in order
        result = ast_data.copy()
        for processor_id in execution_order:
            processor = self._processor_registry.get(processor_id)
            if processor:
                import time
                start = time.time()
                result = processor.process_func(result)
                elapsed = time.time() - start
                
                # Track performance
                if processor_id not in self._performance_stats:
                    self._performance_stats[processor_id] = []
                self._performance_stats[processor_id].append(elapsed)
        
        return result
    
    def get_extractor(self, data_type: str) -> Optional[Callable]:
        """Get extractor function for specific data type"""
        extractors = {
            'models': lambda ast: ast.get('extracted_models', ast.get('models', {})),
            'enums': lambda ast: ast.get('extracted_enums', ast.get('enums', {})),
            'interfaces': lambda ast: ast.get('interfaces', {}),
        }
        return extractors.get(data_type)
    
    def get_extracted_data(self, data_type: str, ast_data: Dict[str, Any]) -> Any:
        """Extract specific data type from AST"""
        extractor = self.get_extractor(data_type)
        return extractor(ast_data) if extractor else None
    
    def invalidate_cache(self, files: Optional[List[Path]] = None) -> None:
        """Invalidate cache for files"""
        if files:
            self._raw_cache.invalidate(files)
            content_hash = self._raw_cache._compute_content_hash(files)
            self._processed_cache.invalidate_by_content(content_hash)
        else:
            self._raw_cache.invalidate()
            self._processed_cache._cache.clear()
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics"""
        stats = {}
        for processor_id, times in self._performance_stats.items():
            if times:
                stats[processor_id] = {
                    'count': len(times),
                    'total': sum(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                }
        return stats
    
    def register_processor(self, processor: ASTProcessor) -> None:
        """Register a custom AST processor"""
        self._processor_registry.register(processor)