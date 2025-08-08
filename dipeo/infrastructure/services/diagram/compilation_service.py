"""Infrastructure compilation service for diagrams.

This service handles diagram compilation with infrastructure concerns like
logging, monitoring, caching, and error tracking while delegating the actual
compilation logic to the domain layer.
"""

import logging
import time

from dipeo.core import BaseService
from dipeo.core.ports.diagram_compiler import DiagramCompiler
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.diagram_generated import DomainDiagram
from dipeo.domain.diagram.compilation import (
    CompilationResult,
    DomainDiagramCompiler,
)

logger = logging.getLogger(__name__)


class CompilationService(BaseService, DiagramCompiler):
    """Infrastructure service for diagram compilation.
    
    This service provides:
    - Diagram compilation with proper error handling
    - Performance monitoring and metrics
    - Compilation result caching (future enhancement)
    - Detailed logging for debugging
    - Integration with the service registry pattern
    """
    
    def __init__(self):
        super().__init__()
        self._domain_compiler = DomainDiagramCompiler()
        self._initialized = False
        self._compilation_count = 0
        self._total_compilation_time = 0.0
        self._last_result: CompilationResult | None = None
    
    async def initialize(self) -> None:
        """Initialize the compilation service."""
        if self._initialized:
            return
        
        logger.debug("Initializing CompilationService")
        self._initialized = True
    
    def compile(self, domain_diagram: DomainDiagram) -> ExecutableDiagram:
        """Compile domain diagram with monitoring and error handling.
        
        Args:
            domain_diagram: The domain diagram to compile
            
        Returns:
            ExecutableDiagram: The compiled executable diagram
            
        Raises:
            ValueError: If compilation fails with validation errors
            RuntimeError: If service is not initialized
        """
        if not self._initialized:
            raise RuntimeError("CompilationService not initialized")
        
        diagram_name = domain_diagram.metadata.name if domain_diagram.metadata else "unnamed"
        start_time = time.time()
        
        try:
            # Delegate to domain compiler
            result = self._domain_compiler.compile(domain_diagram)
            
            # Track metrics
            compilation_time = time.time() - start_time
            self._compilation_count += 1
            self._total_compilation_time += compilation_time
            
            return result
            
        except ValueError as e:
            # Log compilation errors with context
            logger.error(f"Compilation failed for diagram '{diagram_name}': {e}")
            raise
            
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unexpected error during compilation of diagram '{diagram_name}': {e}",
                exc_info=True
            )
            raise
    
    def compile_with_diagnostics(self, domain_diagram: DomainDiagram) -> CompilationResult:
        """Compile with detailed diagnostics and metrics.
        
        This method provides rich compilation results including warnings,
        optimization suggestions, and performance metrics.
        
        Args:
            domain_diagram: The domain diagram to compile
            
        Returns:
            CompilationResult: Detailed compilation result with diagnostics
        """
        if not self._initialized:
            raise RuntimeError("CompilationService not initialized")
        
        diagram_name = domain_diagram.metadata.name if domain_diagram.metadata else "unnamed"
        logger.debug(f"Starting compilation with diagnostics for diagram: {diagram_name}")
        
        start_time = time.time()
        
        # Delegate to domain compiler
        result = self._domain_compiler.compile_with_diagnostics(domain_diagram)
        
        # Add infrastructure metrics
        compilation_time = time.time() - start_time
        result.metadata["compilation_time_ms"] = int(compilation_time * 1000)
        result.metadata["compiler_version"] = "1.0.0"
        
        # Track metrics
        self._compilation_count += 1
        self._total_compilation_time += compilation_time
        self._last_result = result
        
        # Log diagnostics
        if result.errors:
            logger.error(
                f"Compilation of '{diagram_name}' failed with {len(result.errors)} errors"
            )
            for error in result.errors:
                logger.error(f"  [{error.phase.name}] {error.message}")
        
        if result.warnings:
            logger.warning(
                f"Compilation of '{diagram_name}' produced {len(result.warnings)} warnings"
            )
            for warning in result.warnings:
                logger.warning(f"  [{warning.phase.name}] {warning.message}")
        
        if result.is_valid:
            logger.info(
                f"Diagram '{diagram_name}' compiled successfully in {compilation_time:.3f}s "
                f"with {len(result.warnings)} warnings"
            )
        
        return result
    
    def decompile(self, executable_diagram: ExecutableDiagram) -> DomainDiagram:
        """Convert executable diagram back to domain representation.
        
        Args:
            executable_diagram: The executable diagram to decompile
            
        Returns:
            DomainDiagram: The decompiled domain diagram
        """
        if not self._initialized:
            raise RuntimeError("CompilationService not initialized")
        
        logger.debug("Decompiling executable diagram")
        return self._domain_compiler.decompile(executable_diagram)
    
    def get_metrics(self) -> dict:
        """Get compilation service metrics.
        
        Returns:
            dict: Service metrics including compilation count and average time
        """
        avg_time = (
            self._total_compilation_time / self._compilation_count
            if self._compilation_count > 0
            else 0
        )
        
        return {
            "compilation_count": self._compilation_count,
            "total_compilation_time": self._total_compilation_time,
            "average_compilation_time": avg_time,
            "last_result": {
                "is_valid": self._last_result.is_valid if self._last_result else None,
                "error_count": len(self._last_result.errors) if self._last_result else 0,
                "warning_count": len(self._last_result.warnings) if self._last_result else 0,
            } if self._last_result else None
        }
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        logger.info(
            f"CompilationService shutting down. "
            f"Compiled {self._compilation_count} diagrams "
            f"in {self._total_compilation_time:.3f}s total"
        )
        self._initialized = False