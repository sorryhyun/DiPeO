"""Factory for creating template services with full filters."""

from pathlib import Path

from ..adapters import Jinja2Adapter
from .filter_registry import create_filter_registry
from .macro_library import MacroLibrary
from .template_service import CodegenTemplateService


def get_template_service(template_dirs: list[str] | None = None) -> CodegenTemplateService:
    """Create a template service with all filters enabled.

    Args:
        template_dirs: Optional list of template directories

    Returns:
        Configured CodegenTemplateService instance with all filters
    """
    if template_dirs is None:
        template_dirs = [
            "projects/codegen/templates",
            "projects/codegen/templates/models",
            "projects/codegen/templates/backend",
            "projects/codegen/templates/frontend",
        ]

    existing_dirs = [d for d in template_dirs if Path(d).exists()]

    adapter = Jinja2Adapter(template_dirs=existing_dirs)
    filter_registry = create_filter_registry()
    macro_library = MacroLibrary()

    service = CodegenTemplateService(
        adapter=adapter, filter_registry=filter_registry, macro_library=macro_library
    )

    all_filters = filter_registry.get_all_filters()
    for name, func in all_filters.items():
        adapter.register_filter(name, func)

    # Register filters as globals for multi-argument filter functions in templates
    if adapter._env:
        for name, func in all_filters.items():
            adapter._env.globals[name] = func

    return service
