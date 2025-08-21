"""Domain-level resolution error classes.

These errors define the business-level exceptions that can occur during
input resolution, independent of any application-layer implementation.
"""


class ResolutionError(Exception):
    """Base class for all resolution-related errors."""
    pass


class InputResolutionError(ResolutionError):
    """Error when inputs cannot be resolved for a node."""
    pass


class TransformationError(ResolutionError):
    """Error during value transformation between nodes."""
    pass


class SpreadCollisionError(TransformationError):
    """Error when spread operations collide or conflict."""
    pass