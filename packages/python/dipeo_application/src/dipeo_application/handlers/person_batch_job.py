"""Person batch job node handler - executes prompts across multiple persons."""

import warnings

# Deprecation warning
warnings.warn(
    "dipeo_application.handlers.person_batch_job is deprecated. "
    "Use dipeo.application.handlers.person_batch_job instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from new location for backward compatibility
from dipeo.application.handlers.person_batch_job import PersonBatchJobNodeHandler

__all__ = ["PersonBatchJobNodeHandler"]