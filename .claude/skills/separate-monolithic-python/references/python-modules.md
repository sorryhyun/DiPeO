# Python Module Organization Best Practices

## Table of Contents
- [Module Design Principles](#module-design-principles)
- [Package Structure Patterns](#package-structure-patterns)
- [Import Best Practices](#import-best-practices)
- [Common Pitfalls](#common-pitfalls)

## Module Design Principles

### 1. Single Responsibility Principle

Each module should have one clear purpose:

```python
# Good: Focused modules
user_service.py      # User-related business logic
user_repository.py   # User data access
user_validator.py    # User validation logic

# Bad: Mixed responsibilities
user_stuff.py        # Everything user-related
```

### 2. High Cohesion, Low Coupling

**High Cohesion**: Related functionality stays together
```python
# user_service.py - all user operations
def create_user(): ...
def update_user(): ...
def delete_user(): ...
```

**Low Coupling**: Minimal dependencies between modules
```python
# Good: Clean dependencies
models.py → No dependencies
utils.py → Depends on models.py
services.py → Depends on models.py, utils.py

# Bad: Circular dependencies
services.py ⟷ models.py  # Avoid this
```

### 3. Clear Public API

Use `__init__.py` to define what users should import:

```python
# mypackage/__init__.py
from .models import User, Product
from .services import create_user, get_user

# Only expose these
__all__ = ['User', 'Product', 'create_user', 'get_user']
```

Users then import cleanly:
```python
from mypackage import User, create_user
# Not: from mypackage.models import User
```

## Package Structure Patterns

### Pattern 1: Flat Structure (Small Projects)

Best for: 5-10 modules, simple domain

```
myproject/
├── __init__.py
├── models.py
├── services.py
├── utils.py
└── config.py
```

**Pros**: Simple, easy to navigate
**Cons**: Doesn't scale beyond ~10 files

### Pattern 2: Feature-Based (Medium Projects)

Best for: Multiple features, 10-30 modules

```
myproject/
├── __init__.py
├── users/
│   ├── __init__.py
│   ├── models.py
│   ├── services.py
│   └── validators.py
├── products/
│   ├── __init__.py
│   ├── models.py
│   └── services.py
└── shared/
    ├── __init__.py
    └── utils.py
```

**Pros**: Scales well, clear feature boundaries
**Cons**: Shared code needs careful organization

### Pattern 3: Layered Architecture (Large Projects)

Best for: Complex domains, 30+ modules

```
myproject/
├── __init__.py
├── domain/           # Core business logic
│   ├── models.py
│   └── services.py
├── application/      # Use cases
│   ├── user_registration.py
│   └── order_processing.py
├── infrastructure/   # External dependencies
│   ├── database.py
│   └── api_client.py
└── presentation/     # UI/API layer
    └── routes.py
```

**Pros**: Clean separation of concerns, testable
**Cons**: More complex, requires discipline

### Pattern 4: Django-Style (Web Apps)

Best for: Django/Flask applications

```
myapp/
├── __init__.py
├── models.py         # Database models
├── views.py          # Request handlers
├── forms.py          # Form definitions
├── serializers.py    # API serializers
├── urls.py           # URL routing
├── admin.py          # Admin interface
├── tests.py          # Tests
└── migrations/       # Database migrations
```

## Import Best Practices

### Import Order (PEP 8)

Always use this order:
```python
# 1. Standard library
import os
import sys
from typing import List, Optional

# 2. Third-party packages
import requests
import numpy as np
from fastapi import FastAPI

# 3. Local application/library
from .models import User
from .utils import validate_email
from ..shared import constants
```

### Absolute vs Relative Imports

**Use relative imports within a package:**
```python
# Inside mypackage/services.py
from .models import User          # Same directory
from .utils import validate       # Same directory
from ..shared.utils import log    # Parent directory
```

**Use absolute imports from outside:**
```python
# In application code
from mypackage import User
from mypackage.services import create_user
```

### Avoid Star Imports

```python
# Bad
from mypackage import *

# Good
from mypackage import User, Product, create_user
```

Star imports:
- Hide what you're actually using
- Can cause name collisions
- Make static analysis harder

### Lazy Imports for Performance

For expensive imports only used sometimes:
```python
def process_large_data():
    import pandas as pd  # Only import when needed
    return pd.DataFrame(...)
```

## Common Pitfalls

### 1. Circular Imports

**Problem:**
```python
# models.py
from .services import validate_user

class User: ...

# services.py
from .models import User

def validate_user(): ...
```

**Solutions:**

A) Move shared code to new module:
```python
# validators.py
def validate_user(): ...

# models.py - import from validators
# services.py - import from validators
```

B) Use TYPE_CHECKING:
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .services import UserService  # Only for type hints
```

C) Import inside function:
```python
def my_function():
    from .services import validate_user  # Deferred import
    validate_user()
```

### 2. Deep Nesting

**Problem:**
```python
from myapp.features.users.services.authentication.handlers import login
```

**Solution:** Keep hierarchies shallow (max 3-4 levels):
```python
from myapp.users.auth import login
```

### 3. Missing `__init__.py`

Before Python 3.3, `__init__.py` was required. Still recommended for:
- Explicit package marking
- Defining public API with `__all__`
- Package initialization code

```python
# mypackage/__init__.py
from .models import User
from .services import create_user

__all__ = ['User', 'create_user']
```

### 4. Polluted Namespace

**Problem:**
```python
# __init__.py
from .models import *  # Imports everything
from .services import *  # Name collisions possible
```

**Solution:**
```python
# __init__.py
from .models import User, Product
from .services import create_user, get_user

__all__ = ['User', 'Product', 'create_user', 'get_user']
```

## File Size Guidelines

### Recommended Sizes

- **Functions**: 10-50 lines (max 100)
- **Classes**: 50-300 lines (max 500)
- **Modules**: 100-500 lines (max 1000)

### When to Split

Split a module when:
- ✅ Over 500 lines
- ✅ Multiple unrelated responsibilities
- ✅ Hard to find specific functions
- ✅ Many imports needed
- ✅ Difficult to test in isolation

## Module Naming Conventions

### File Naming
- Use `snake_case.py`
- Be descriptive: `user_service.py` not `us.py`
- Avoid generic names: `helpers.py`, `utilities.py`

### Package Naming
- Use `snake_case` directories
- Singular nouns: `user/` not `users/`
- Be specific: `authentication/` not `auth/`

### Examples

```
Good names:
✅ user_repository.py
✅ email_validator.py
✅ payment_processor.py

Bad names:
❌ utils.py (too generic)
❌ stuff.py (meaningless)
❌ userRepo.py (wrong case)
```

## Testing Implications

### Module Structure Affects Testing

**Good structure:**
```python
# Easy to test in isolation
from myapp.services import create_user
from myapp.models import User

def test_create_user():
    user = create_user("Alice")
    assert isinstance(user, User)
```

**Bad structure:**
```python
# Hard to test - too many dependencies
from myapp.monolith import everything
# Can't test one thing without initializing everything
```

### Test File Organization

Mirror your module structure:
```
myapp/
├── models.py
├── services.py
└── utils.py

tests/
├── test_models.py
├── test_services.py
└── test_utils.py
```

## Migration Strategies

### Strategy 1: Incremental Refactoring

1. Create new module structure alongside old code
2. Gradually move code piece by piece
3. Keep both working during transition
4. Remove old code when fully migrated

### Strategy 2: Big Bang Refactoring

1. Create complete new structure
2. Move all code at once
3. Fix all imports
4. Validate everything works

**Use incremental for:**
- Production code
- Large teams
- Critical systems

**Use big bang for:**
- Small projects
- Solo development
- Non-critical code

## Real-World Examples

### Example 1: FastAPI Application

```
myapi/
├── __init__.py
├── main.py              # App entry point
├── config.py            # Configuration
├── models/
│   ├── __init__.py
│   ├── user.py
│   └── product.py
├── routes/
│   ├── __init__.py
│   ├── users.py
│   └── products.py
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   └── product_service.py
└── database/
    ├── __init__.py
    └── session.py
```

### Example 2: Data Science Project

```
ml_project/
├── __init__.py
├── data/
│   ├── __init__.py
│   ├── loaders.py
│   └── preprocessors.py
├── features/
│   ├── __init__.py
│   └── engineering.py
├── models/
│   ├── __init__.py
│   ├── training.py
│   └── evaluation.py
└── utils/
    ├── __init__.py
    └── visualization.py
```

### Example 3: CLI Tool

```
mytool/
├── __init__.py
├── cli.py               # Click/argparse interface
├── commands/
│   ├── __init__.py
│   ├── init.py
│   ├── build.py
│   └── deploy.py
├── core/
│   ├── __init__.py
│   └── engine.py
└── utils/
    ├── __init__.py
    └── file_ops.py
```

## Tools for Refactoring

### Static Analysis

```bash
# Find unused imports
pylint mypackage/

# Type checking
mypy mypackage/

# Import order
isort mypackage/

# Code formatting
black mypackage/
```

### Dependency Analysis

```bash
# Visualize dependencies
pydeps mypackage/

# Find circular imports
python -m pytest --import-mode=importlib
```

## Summary Checklist

When separating monolithic code, ensure:

- [ ] Each module has a single, clear responsibility
- [ ] Module names are descriptive and follow conventions
- [ ] Import order follows PEP 8 (stdlib → third-party → local)
- [ ] No circular dependencies
- [ ] Public API defined in `__init__.py`
- [ ] File sizes are reasonable (<500 lines)
- [ ] Tests mirror module structure
- [ ] Documentation updated
- [ ] All imports working correctly
- [ ] Linting passes (ruff, pylint, mypy)
