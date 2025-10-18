# Detailed Python Module Separation Guide

Comprehensive reference for breaking monolithic Python files into well-organized modules.

## Analysis Checklist

Before starting:
- [ ] File structure understood (classes, functions, constants)
- [ ] Logical groupings identified
- [ ] Dependencies mapped
- [ ] Separation strategy determined

## Common Separation Patterns

### Pattern 1: Django App
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

## Import Organization

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

## Detailed Examples

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

## Circular Dependency Solutions

### Solution 1: Move shared code
```python
# Create shared.py for code both modules need
# models.py and services.py both import from shared.py
```

### Solution 2: Use TYPE_CHECKING
```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .services import UserService  # Only for type hints
```

### Solution 3: Late import
```python
def process_user():
    from .services import create_user  # Import inside function
    create_user()
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

## Import Update Checklist

After extraction:
- [ ] All new modules import what they need
- [ ] `__init__.py` exports public API
- [ ] External files updated to use new package
- [ ] Relative imports used within package (`.models`, `.utils`)
- [ ] No circular dependencies

## Validation Checklist

Before completing:
- [ ] No circular imports
- [ ] All names resolve correctly
- [ ] No missing imports
- [ ] Code style maintained
- [ ] Documentation preserved
- [ ] Tests pass
- [ ] Linter checks pass

## Migration Note

**Migration note for users:**
```python
# Old usage:
from monolith import User, create_user

# New usage:
from mypackage import User, create_user
# API remains the same, just the import changed
```

## Key Commands

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
