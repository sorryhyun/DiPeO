"""Pipeline-based input resolution system.

This module provides a composable pipeline for resolving node inputs
during diagram execution, splitting concerns into focused stages.
"""

from .base import PipelineStage, PipelineContext
from .incoming_edges import IncomingEdgesStage
from .filter import FilterStage
from .provider_stage import ProviderStage
from .transform import TransformStage
from .defaults import DefaultsStage
from .pipeline import InputResolutionPipeline
from .providers import (
    Provider,
    ConversationProvider,
    VariablesProvider,
    FirstExecutionProvider,
    get_provider,
    register_provider,
    get_all_providers
)

__all__ = [
    'PipelineStage',
    'PipelineContext',
    'IncomingEdgesStage',
    'FilterStage',
    'ProviderStage',
    'TransformStage',
    'DefaultsStage',
    'InputResolutionPipeline',
    # Provider system
    'Provider',
    'ConversationProvider',
    'VariablesProvider',
    'FirstExecutionProvider',
    'get_provider',
    'register_provider',
    'get_all_providers',
]