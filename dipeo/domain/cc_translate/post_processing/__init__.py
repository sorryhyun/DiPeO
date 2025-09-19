"""Post-processing module for diagram optimization."""

from .config import PipelineConfig, ProcessingPreset, ReadDeduplicatorConfig
from .post_processor import PostProcessor
from .read_deduplicator import ReadNodeDeduplicator

__all__ = [
    "PipelineConfig",
    "PostProcessor",
    "ProcessingPreset",
    "ReadDeduplicatorConfig",
    "ReadNodeDeduplicator",
]
