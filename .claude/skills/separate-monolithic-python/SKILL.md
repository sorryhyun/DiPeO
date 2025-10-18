---
name: separate-monolithic-python
description: Break large Python files (>500 LOC) into smaller, well-organized modules with proper package structure. Use when a Python file is too large, monolithic, or needs refactoring. Triggered by requests mentioning "too large", "separate", "split", "break up", or "refactor" for Python files.
---

# Separate Monolithic Python Code

## Overview

Refactor large Python files into smaller, maintainable modules following Python best practices. This skill analyzes code structure, identifies logical separation points, and creates a clean module hierarchy with proper imports.

## Workflow

Follow this systematic process to separate monolithic Python code:

### Step 1: Analyze the File

Before making any changes, understand the current structure:

1. **Read the entire file** to understand its contents
2. **Identify major components**:
   - Classes and their relationships
   - Function groups by purpose
   - Constants and configuration
   - Import dependencies
3. **Count lines of code** to confirm it needs separation (>500 LOC)
4. **Analyze cohesion**: Which code elements belong together?
5. **Map dependencies**: What depends on what?

**Analysis checklist:**
- [ ] File structure understood (classes, functions, constants)
- [ ] Logical groupings identified
- [ ] Dependencies mapped
- [ ] Separation strategy determined

### Step 2: Plan the Module Structure

Design the new module organization before splitting:

**Common separation patterns:**

**Pattern A: By Responsibility (Recommended)**
```
mypackage/
├── __init__.py       # Public API exports
├── models.py         # Data models/classes
├── services.py       # Business logic
├── utils.py          # Helper functions
└── constants.py      # Configuration/constants
```

**Pattern B: By Feature**
```
mypackage/
├── __init__.py
├── feature_a/
│   ├── __init__.py
│   ├── models.py
│   └── logic.py
└── feature_b/
    ├── __init__.py
    └── handlers.py
```

**Pattern C: By Layer**
```
mypackage/
├── __init__.py
├── domain/          # Core business models
├── application/     # Use cases/services
└── infrastructure/  # External dependencies
```

**Planning output:**
Present a clear plan to the user:
```
I'll separate this 1,200 line file into:
1. models.py (350 lines) - User, Product, Order classes
2. services.py (400 lines) - Business logic functions
3. utils.py (200 lines) - Helper functions
4. constants.py (100 lines) - Configuration
5. __init__.py (50 lines) - Public API

This follows the "By Responsibility" pattern.
Proceed? (y/n)
```

### Step 3: Create the Module Structure

Set up the new directory and files:

1. **Create package directory**: `mkdir mypackage/`
2. **Create module files**: One for each planned component
3. **Create `__init__.py`**: Start with empty file
4. **Preserve git history** (if applicable): Use `git mv` when possible

**Example:**
```bash
mkdir mypackage
touch mypackage/__init__.py
touch mypackage/models.py
touch mypackage/services.py
touch mypackage/utils.py
touch mypackage/constants.py
```

### Step 4: Extract Code

Move code systematically, starting with least dependent components:

**Extraction order:**
1. **Constants first** - no dependencies
2. **Models/data structures** - minimal dependencies
3. **Utilities** - depend on constants/models
4. **Services/logic** - depend on everything else
5. **Main/entry points** - orchestrate all components

**For each extraction:**
1. Copy relevant code to new module
2. Remove from original file
3. Add necessary imports to new module
4. Keep docstrings and comments
5. Maintain code style consistency

**Example extraction:**
```python
# Extract from monolith.py → models.py
class User:
    """User model."""
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
```

### Step 5: Update Imports

Fix all import statements throughout the codebase:

**In the new modules:**
```python
# models.py
from .constants import DEFAULT_ROLE
from .utils import validate_email
```

**In `__init__.py` (public API):**
```python
# Expose public interfaces
from .models import User, Product
from .services import create_user, process_order

__all__ = ['User', 'Product', 'create_user', 'process_order']
```

**In files using the old monolith:**
```python
# Before:
from monolith import User, create_user

# After:
from mypackage import User, create_user
```

**Import update checklist:**
- [ ] All new modules import what they need
- [ ] `__init__.py` exports public API
- [ ] External files updated to use new package
- [ ] Relative imports used within package (`.models`, `.utils`)
- [ ] No circular dependencies

### Step 6: Validate the Refactoring

Ensure everything works correctly:

1. **Check syntax**: Run linter/type checker
   ```bash
   ruff check mypackage/
   mypy mypackage/
   ```

2. **Verify imports**: Can all modules be imported?
   ```python
   python -c "from mypackage import User, create_user"
   ```

3. **Run tests**: If tests exist, ensure they pass
   ```bash
   pytest tests/
   ```

4. **Check for issues**:
   - [ ] No circular imports
   - [ ] All names resolve correctly
   - [ ] No missing imports
   - [ ] Code style maintained
   - [ ] Documentation preserved

5. **Clean up original file**:
   - If fully migrated: delete or archive
   - If partially migrated: keep remainder, update imports


**Migration note for users:**
```python
# Old usage:
from monolith import User, create_user

# New usage:
from mypackage import User, create_user
# API remains the same, just the import changed
```

## Best Practices

### Separation Principles

1. **High Cohesion**: Keep related code together
   - Group by purpose, not by type
   - Example: `user_service.py` not `all_services.py`

2. **Low Coupling**: Minimize dependencies between modules
   - Avoid circular imports
   - Use dependency injection when needed

3. **Single Responsibility**: Each module has one clear purpose
   - `models.py` - just data structures
   - `services.py` - just business logic

4. **Clear API**: Use `__init__.py` to define public interface
   ```python
   # Only expose what users need
   __all__ = ['User', 'create_user']
   ```

### Import Organization

Always organize imports in this order:
```python
# 1. Standard library
import os
from typing import List

# 2. Third-party packages
import requests
from sqlalchemy import Column

# 3. Local modules
from .models import User
from .utils import validate_email
```

### Handling Circular Dependencies

If you encounter circular imports:

**Solution 1: Move shared code**
```python
# Create shared.py for code both modules need
# models.py and services.py both import from shared.py
```

**Solution 2: Use TYPE_CHECKING**
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .services import UserService  # Only for type hints
```

**Solution 3: Late import**
```python
def process_user():
    from .services import create_user  # Import inside function
    create_user()
```

### File Size Guidelines

Target module sizes:
- ✅ **Ideal**: 100-300 lines per file
- ⚠️ **Warning**: 300-500 lines (consider splitting)
- ❌ **Too large**: >500 lines (should be split)

## Common Patterns

### Pattern 1: Django App Separation

```
myapp/
├── __init__.py
├── models.py        # Database models
├── views.py         # View logic
├── serializers.py   # API serializers
├── services.py      # Business logic
├── urls.py          # URL routing
└── utils.py         # Helpers
```

### Pattern 2: FastAPI Service

```
myservice/
├── __init__.py
├── models.py        # Pydantic models
├── routes.py        # API endpoints
├── services.py      # Business logic
├── dependencies.py  # Dependency injection
└── config.py        # Configuration
```

### Pattern 3: Data Processing

```
processor/
├── __init__.py
├── extractors.py    # Data extraction
├── transformers.py  # Data transformation
├── loaders.py       # Data loading
└── validators.py    # Data validation
```

## Troubleshooting

### Import Errors After Separation

**Problem**: `ImportError: cannot import name 'X'`

**Solutions**:
1. Check `__init__.py` exports the name
2. Verify the name exists in the target module
3. Look for circular import issues
4. Ensure relative imports use correct syntax (`.module`)

### Circular Import Detected

**Problem**: `ImportError: cannot import name 'X' from partially initialized module`

**Solutions**:
1. Identify the cycle: A imports B, B imports A
2. Apply one of the circular dependency solutions above
3. Restructure to break the cycle (extract shared code)

### Tests Failing After Split

**Problem**: Tests can't find modules or functions

**Solutions**:
1. Update test imports to use new package structure
2. Ensure `__init__.py` exports all test dependencies
3. Check if tests need to be reorganized too

## Examples

### Example 1: Simple API Service

**Before** (monolith.py - 800 lines):
```python
# All in one file
import os
from fastapi import FastAPI

DATABASE_URL = "sqlite:///./test.db"

class User:
    def __init__(self, name):
        self.name = name

def create_user(name):
    return User(name)

app = FastAPI()

@app.get("/users")
def get_users():
    return []
```

**After** (structured package):
```
api/
├── __init__.py
├── config.py      # DATABASE_URL
├── models.py      # User class
├── services.py    # create_user
└── routes.py      # FastAPI routes
```

### Example 2: Data Pipeline

**Before** (pipeline.py - 1200 lines):
```python
# Everything together
def extract_data(): ...
def clean_data(): ...
def transform_data(): ...
def validate_data(): ...
def load_data(): ...
def run_pipeline(): ...
```

**After**:
```
pipeline/
├── __init__.py       # run_pipeline
├── extractors.py     # extract_data
├── cleaners.py       # clean_data
├── transformers.py   # transform_data
├── validators.py     # validate_data
└── loaders.py        # load_data
```

## Quick Reference

### Workflow Checklist

- [ ] Step 1: Analyze file structure and dependencies
- [ ] Step 2: Plan module organization (get user approval)
- [ ] Step 3: Create package directory and files
- [ ] Step 4: Extract code in dependency order
- [ ] Step 5: Update all imports (internal and external)
- [ ] Step 6: Validate with linter/tests
- [ ] Step 7: Document the new structure

### Key Commands

```bash
# Create package structure
mkdir mypackage && cd mypackage
touch __init__.py models.py services.py utils.py

# Validate syntax
ruff check .
mypy .

# Test imports
python -c "from mypackage import MyClass"

# Run tests
pytest tests/
```

For more details on Python package structure, see [references/python-modules.md](references/python-modules.md).
