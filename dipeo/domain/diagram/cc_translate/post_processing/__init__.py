"""Post-processing module for diagram optimization."""

from .config import PipelineConfig, ProcessingPreset, ReadDeduplicatorConfig
from .pipeline import PostProcessingPipeline
from .processors import ReadNodeDeduplicator

__all__ = [
    "PipelineConfig",
    "PostProcessingPipeline",
    "ProcessingPreset",
    "ReadDeduplicatorConfig",
    "ReadNodeDeduplicator",
]
