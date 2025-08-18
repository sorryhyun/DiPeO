"""Backward compatibility for template_integration - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.shared.template.drivers.jinja_template.template_integration instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.shared.template.drivers.jinja_template.template_integration import *