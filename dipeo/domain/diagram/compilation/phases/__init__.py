"""Compilation phases for diagram compilation.

This module contains the individual phases of diagram compilation:
1. ValidationPhase - Structural and semantic validation
2. NodeTransformationPhase - Convert domain nodes to typed nodes
3. ConnectionResolutionPhase - Resolve handle references to connections
4. EdgeBuildingPhase - Create executable edges with rules
5. OptimizationPhase - Optimize execution paths
6. AssemblyPhase - Create final ExecutableDiagram
"""

from .assembly_phase import AssemblyPhase
from .base import CompilationContext, PhaseInterface
from .connection_resolution_phase import ConnectionResolutionPhase
from .edge_building_phase import EdgeBuildingPhase
from .node_transformation_phase import NodeTransformationPhase
from .optimization_phase import OptimizationPhase
from .validation_phase import ValidationPhase

__all__ = [
    "AssemblyPhase",
    "CompilationContext",
    "ConnectionResolutionPhase",
    "EdgeBuildingPhase",
    "NodeTransformationPhase",
    "OptimizationPhase",
    "PhaseInterface",
    "ValidationPhase",
]
