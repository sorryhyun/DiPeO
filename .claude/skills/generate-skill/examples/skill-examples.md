# Example Skills

Quick-start examples. Copy and customize.

## Simple Single-File Skills

### Commit Helper
```yaml
---
name: commit-helper
description: Generate conventional commit messages from git diffs. Use when writing commits or mentions version control.
---

# Commit Helper

1. Run `git diff --staged`
2. Generate message: `type(scope): summary`

## Types
- feat, fix, docs, style, refactor, test, chore

## Example
```
feat(auth): add OAuth2 support

Implements OAuth2 with Google/GitHub providers.
```
```

### Code Reviewer
```yaml
---
name: code-reviewer
description: Review code for best practices, security, performance. Use when reviewing code or PRs.
allowed-tools: Read, Grep, Glob
---

# Code Reviewer

## Checklist
1. Code organization & naming
2. Error handling
3. Security (validation, injection, XSS)
4. Performance
5. Test coverage
```

## Task-Based Skills

### Image Processor
```yaml
---
name: image-processor
description: Resize, crop, convert images. Use when working with images. Requires Pillow.
---

# Image Processor

## Tasks

### 1. Resize
```python
from PIL import Image
img = Image.open('input.jpg')
img.thumbnail((800, 600))
img.save('output.jpg')
```

### 2. Convert
```python
img.save('output.jpg', 'JPEG', quality=90)
```

### 3. Optimize
```python
img.save('output.jpg', optimize=True, quality=85)
```
```

## Workflow Skills

### Data Pipeline
```yaml
---
name: data-pipeline
description: Extract, transform, load data from CSV to databases. Use for ETL tasks.
---

# Data Pipeline

## Workflow

### Step 1: Extract
```python
import pandas as pd
df = pd.read_csv('source.csv')
```

### Step 2: Transform
```python
df = df.drop_duplicates().fillna(0)
df['date'] = pd.to_datetime(df['date'])
```

### Step 3: Load
```python
from sqlalchemy import create_engine
engine = create_engine('postgresql://...')
df.to_sql('table', engine, if_exists='append')
```
```

## Reference Skills

### Brand Guidelines
```yaml
---
name: brand-guidelines
description: Company brand colors, typography, logo usage. Use when creating branded content.
---

# Brand Guidelines

## Colors
- Primary: #0066CC
- Accent: #FF6B35

## Typography
- H1: Open Sans Bold 48px
- Body: Open Sans Regular 16px

## Logo
- Min size: 120px width
- Clear space: 0.5× logo height
- No stretching, rotation, or effects
```

## Tips

1. Start simple - add complexity only if needed
2. Customize descriptions for your triggers
3. Keep under 200 lines
4. Test with real requests
