"""Core immutable containers for static services and business logic."""

from .business_container import BusinessLogicContainer
from .static_container import StaticServicesContainer

__all__ = ["BusinessLogicContainer", "StaticServicesContainer"]