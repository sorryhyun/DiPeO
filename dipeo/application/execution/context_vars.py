from typing import Any

RESERVED_LOCAL_KEYS = {"this", "@index", "@first", "@last"}

def build_template_context(ctx, inputs: dict[str, Any] | None = None,
                          locals_: dict[str, Any] | None = None,
                          globals_win: bool = True) -> dict[str, Any]:
    """Build a consistent template context merging globals, inputs, and locals.
    
    Args:
        ctx: Execution context with get_variables() method
        inputs: Input values from the node
        locals_: Local variables (e.g., foreach loop vars)
        globals_win: If True, globals override inputs/locals. If False, locals override.
    
    Returns:
        Merged context with both namespaced and flat access patterns
    """
    inputs = inputs or {}
    locals_ = locals_ or {}
    globals_ = ctx.get_variables() if hasattr(ctx, "get_variables") else {}
    
    # Namespaced copies to avoid collisions in templates if desired
    merged = {
        "globals": {k: v for k, v in globals_.items() if k not in RESERVED_LOCAL_KEYS},
        "inputs": inputs,
        "local": locals_,
    }
    
    # Flat root for ergonomic {{ var }} access:
    flat = {**inputs, **locals_, **globals_} if globals_win else {**globals_, **inputs, **locals_}
    
    merged.update(flat)
    return merged