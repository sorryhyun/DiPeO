"""Backward compatibility for template_service - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.shared.template.drivers.jinja_template.template_service instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.shared.template.drivers.jinja_template.template_service import *