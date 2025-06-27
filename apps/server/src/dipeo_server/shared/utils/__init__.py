"""Shared utilities."""

from .errors import (
    ErrorHandler,
    ResponseFormatter,
    handle_api_errors,
    handle_internal_errors,
    handle_service_exceptions,
    normalize_service_name,
)
from .features import (
    FeatureFlag,
    FeatureFlagManager,
    configure_features,
    disable_feature,
    enable_feature,
    get_feature_flags,
    get_feature_status,
    is_feature_enabled,
)

__all__ = [
    # Error handling
    "ErrorHandler",
    # Feature flags
    "FeatureFlag",
    "FeatureFlagManager",
    "ResponseFormatter",
    "configure_features",
    "disable_feature",
    "enable_feature",
    "get_feature_flags",
    "get_feature_status",
    "handle_api_errors",
    "handle_internal_errors",
    "handle_service_exceptions",
    "is_feature_enabled",
    "normalize_service_name",
]
