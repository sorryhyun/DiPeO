"""Backward compatibility for jinja_template services - DEPRECATED."""

import warnings

warnings.warn(
    "Import from dipeo.infrastructure.shared.template.drivers.jinja_template instead",
    DeprecationWarning,
    stacklevel=2
)

from dipeo.infrastructure.shared.template.drivers.jinja_template import *
from dipeo.infrastructure.shared.template.drivers.jinja_template.template_service import *
from dipeo.infrastructure.shared.template.drivers.jinja_template.template_integration import *