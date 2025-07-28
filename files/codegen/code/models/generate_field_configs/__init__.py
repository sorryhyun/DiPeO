"""Field configurations generator module."""

from .field_configs_generator import (
    extract_field_configs,
    prepare_template_data,
    render_field_configs,
    # Backward compatibility
    main,
    prepare_field_config_data
)

__all__ = [
    'extract_field_configs',
    'prepare_template_data', 
    'render_field_configs',
    'main',
    'prepare_field_config_data'
]