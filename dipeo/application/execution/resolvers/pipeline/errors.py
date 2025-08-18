"""Resolution error classes for pipeline stages."""


class ResolutionError(Exception):
    """Base class for resolution errors."""
    pass


class InputResolutionError(ResolutionError):
    """Error when inputs cannot be resolved."""
    pass


class TransformationError(ResolutionError):
    """Error during value transformation."""
    pass


class SpreadCollisionError(TransformationError):
    """Error when spread operations collide."""
    pass