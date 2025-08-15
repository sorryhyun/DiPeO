"""Pipeline-based input resolution system.

This module provides a composable pipeline for resolving node inputs
during diagram execution, splitting concerns into focused stages.
"""

from .base import PipelineStage, PipelineContext
from .incoming_edges import IncomingEdgesStage
from .filter import FilterStage
from .special_inputs import SpecialInputsStage
from .transform import TransformStage
from .defaults import DefaultsStage
from .pipeline import InputResolutionPipeline

__all__ = [
    'PipelineStage',
    'PipelineContext',
    'IncomingEdgesStage',
    'FilterStage',
    'SpecialInputsStage',
    'TransformStage',
    'DefaultsStage',
    'InputResolutionPipeline',
]