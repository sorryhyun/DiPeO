# Example Skill Configurations

Quick-start examples for common skill types. Use these as templates for your own skills.

## Simple Single-File Skills

### Commit Message Helper

```markdown
---
name: commit-helper
description: Generate clear, conventional commit messages from git diffs. Use when writing commit messages or when the user mentions commits, git messages, or version control.
---

# Commit Message Helper

## Instructions

1. Run `git diff --staged` to see changes
2. I'll generate a commit message following conventional commits format:
   - type(scope): summary (max 50 chars)
   - Blank line
   - Detailed description (72 char wrap)

## Commit Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation only
- **style**: Formatting changes
- **refactor**: Code restructuring
- **test**: Adding tests
- **chore**: Maintenance tasks

## Example

```
feat(auth): add OAuth2 login support

Implements OAuth2 authentication flow with Google and GitHub providers.
Users can now log in using their existing accounts instead of creating
new credentials.

- Added OAuth2 middleware
- Integrated with passport.js
- Updated login UI with provider buttons
```
```

### Code Reviewer

```markdown
---
name: code-reviewer  
description: Review code for best practices, security issues, and performance problems. Use when reviewing code, checking pull requests, or analyzing code quality.
allowed-tools: Read, Grep, Glob
---

# Code Reviewer

## Review Checklist

1. **Code Organization**
   - Clear structure and separation of concerns
   - Appropriate use of functions/classes
   - Good naming conventions

2. **Error Handling**
   - Comprehensive error catching
   - Meaningful error messages
   - Graceful degradation

3. **Security**
   - Input validation
   - SQL injection prevention
   - XSS protection
   - Secure authentication

4. **Performance**
   - Efficient algorithms
   - Minimal database queries
   - Proper caching
   - Resource cleanup

5. **Testing**
   - Test coverage
   - Edge cases handled
   - Integration tests

## Instructions

I'll review the code and provide:
- Specific issues found
- Severity rating (Critical/Major/Minor)
- Suggested improvements
- Code examples for fixes
```

## Task-Based Skills

### Image Processor

```markdown
---
name: image-processor
description: Resize, crop, convert, and optimize images for web use. Use when working with images, photos, or when the user mentions image processing, conversion, or optimization. Requires Pillow package.
---

# Image Processor

## Core Tasks

### 1. Resize Images

Resize images while maintaining aspect ratio.

**Usage:**
```python
from PIL import Image
img = Image.open('input.jpg')
img.thumbnail((800, 600))
img.save('output.jpg')
```

### 2. Convert Formats

Convert between PNG, JPEG, WebP.

**Usage:**
```python
img = Image.open('input.png')
img.save('output.jpg', 'JPEG', quality=90)
```

### 3. Optimize for Web

Reduce file size while maintaining quality.

**Usage:**
```python
img = Image.open('input.jpg')
img.save('optimized.jpg', optimize=True, quality=85)
```

### 4. Crop Images

Crop to specific dimensions or aspect ratios.

**Usage:**
```python
img = Image.open('input.jpg')
cropped = img.crop((100, 100, 400, 400))
cropped.save('cropped.jpg')
```

## Batch Processing

Process multiple images:
```python
from pathlib import Path
for img_file in Path('.').glob('*.jpg'):
    img = Image.open(img_file)
    img.thumbnail((800, 600))
    img.save(f'resized_{img_file.name}')
```

## Requirements

```bash
pip install Pillow
```
```

### API Client

```markdown
---
name: github-api-client
description: Interact with GitHub API to manage repositories, issues, pull requests, and workflows. Use when working with GitHub, automating GitHub tasks, or managing repositories programmatically.
---

# GitHub API Client

## Overview

Comprehensive GitHub API integration for repository management and automation.

## Core Tasks

### 1. Repository Operations

**List repositories:**
```python
import requests
headers = {'Authorization': f'token {GITHUB_TOKEN}'}
repos = requests.get('https://api.github.com/user/repos', headers=headers)
```

**Create repository:**
```python
data = {'name': 'new-repo', 'private': False}
response = requests.post('https://api.github.com/user/repos', 
                        headers=headers, json=data)
```

### 2. Issue Management

**Create issue:**
```python
data = {
    'title': 'Bug: Login fails',
    'body': 'Description of the bug',
    'labels': ['bug']
}
response = requests.post(
    'https://api.github.com/repos/owner/repo/issues',
    headers=headers, json=data
)
```

**List issues:**
```python
issues = requests.get(
    'https://api.github.com/repos/owner/repo/issues',
    headers=headers
)
```

### 3. Pull Request Handling

**Create pull request:**
```python
data = {
    'title': 'Feature: Add authentication',
    'body': 'Implements OAuth2 auth',
    'head': 'feature-branch',
    'base': 'main'
}
response = requests.post(
    'https://api.github.com/repos/owner/repo/pulls',
    headers=headers, json=data
)
```

## Authentication

Set your GitHub token:
```bash
export GITHUB_TOKEN='your_token_here'
```

Get token at: https://github.com/settings/tokens

## Rate Limiting

GitHub API limits:
- Authenticated: 5,000 requests/hour
- Unauthenticated: 60 requests/hour

Check rate limit:
```python
limit = requests.get('https://api.github.com/rate_limit', headers=headers)
```

## References

See [references/github-api.md](references/github-api.md) for complete API documentation.
```

## Workflow-Based Skills

### Data Pipeline

```markdown
---
name: data-pipeline
description: Extract, transform, and load data from CSV/Excel files to databases. Use when processing data, building ETL pipelines, or migrating data between systems.
---

# Data Pipeline

## Overview

End-to-end ETL workflow for data processing and migration.

## Workflow

### Step 1: Extract Data

Load data from source files.

**Supported formats:**
- CSV
- Excel (.xlsx, .xls)
- JSON
- Parquet

**Example:**
```python
import pandas as pd

# CSV
df = pd.read_csv('source.csv')

# Excel
df = pd.read_excel('source.xlsx', sheet_name='Sheet1')

# JSON
df = pd.read_json('source.json')
```

### Step 2: Transform Data

Clean and normalize the data.

**Operations:**
1. Remove duplicates
2. Handle missing values
3. Normalize formats
4. Apply business rules
5. Validate data quality

**Example:**
```python
# Remove duplicates
df = df.drop_duplicates()

# Handle missing values
df['col'] = df['col'].fillna(0)

# Normalize dates
df['date'] = pd.to_datetime(df['date'])

# Validate
assert df['amount'].min() >= 0, "Negative amounts found"
```

### Step 3: Load Data

Insert into target database.

**Example:**
```python
from sqlalchemy import create_engine

engine = create_engine('postgresql://user:pass@host/db')
df.to_sql('target_table', engine, 
          if_exists='append', index=False)
```

## Error Handling

- **Extract errors**: Skip corrupted rows, log to error file
- **Transform errors**: Quarantine invalid records
- **Load errors**: Rollback transaction, alert operator

## Best Practices

- Always validate before transform
- Use database transactions
- Log all operations
- Implement retry logic
- Monitor data quality

## Requirements

```bash
pip install pandas sqlalchemy psycopg2
```
```

## Reference-Based Skills

### Brand Guidelines

```markdown
---
name: brand-guidelines
description: Company brand visual identity standards including colors, typography, logo usage, and design principles. Use when creating branded content, marketing materials, or presentations.
---

# Brand Guidelines

## Overview

Ensure all created content follows company brand identity.

## Color Palette

### Primary Colors
- **Brand Blue**: #0066CC (RGB: 0, 102, 204)
  - Use for: Primary CTAs, headers, key elements
  
- **Brand Black**: #1A1A1A (RGB: 26, 26, 26)
  - Use for: Body text, secondary elements

### Secondary Colors
- **Accent Orange**: #FF6B35 (RGB: 255, 107, 53)
  - Use for: Highlights, accents, alerts
  
- **Light Gray**: #F5F5F5 (RGB: 245, 245, 245)
  - Use for: Backgrounds, subtle sections

### Accessibility
Maintain 4.5:1 contrast ratio minimum.

## Typography

### Fonts
- **Primary**: Open Sans
  - Headings: Open Sans Bold
  - Body: Open Sans Regular
  - UI: Open Sans SemiBold

### Hierarchy
- H1: 48px / 3rem (Bold)
- H2: 36px / 2.25rem (Bold)
- H3: 24px / 1.5rem (SemiBold)
- Body: 16px / 1rem (Regular)
- Small: 14px / 0.875rem (Regular)

### Line Height
- Headings: 1.2
- Body: 1.6

## Logo Usage

### Requirements
- Minimum size: 120px width
- Clear space: Logo height × 0.5
- Always use SVG when possible
- PNG backup: 300 DPI minimum

### Prohibited
❌ No stretching or distortion
❌ No color modifications
❌ No rotation
❌ No effects (shadows, outlines, glows)
❌ No placement on busy backgrounds

### Examples

**Correct:**
```html
<img src="logo.svg" alt="Company" width="200">
```

**Incorrect:**
```html
<!-- Don't do this -->
<img src="logo.png" style="filter: drop-shadow(2px 2px 4px #000)">
```

## Templates

### Presentations
Use `assets/presentation_template.pptx`
- Title slide: Logo top-right
- Section headers: Brand Blue background
- Content slides: Light Gray background

### Documents
- Cover page: Full logo centered
- Headers: Brand Blue
- Body: Brand Black on white

## Validation Checklist

Before publishing, verify:
- [ ] Colors match exact hex codes
- [ ] Typography uses approved fonts
- [ ] Logo has adequate clear space
- [ ] Contrast ratios meet standards
- [ ] Layout follows template

## Assets

Brand assets available in `assets/`:
- `logo.svg` - Primary logo
- `logo-white.svg` - White logo for dark backgrounds
- `presentation_template.pptx` - PowerPoint template
- `colors.ase` - Adobe Swatch Exchange file
```

## Skill with Scripts and References

### PDF Toolkit (Complete Example)

**Directory structure:**
```
pdf-toolkit/
├── SKILL.md
├── references/
│   ├── api-reference.md
│   └── examples.md
└── scripts/
    ├── fill_form.py
    ├── merge_pdfs.py
    └── extract_text.py
```

**SKILL.md:**
```markdown
---
name: pdf-toolkit
description: Extract text and tables from PDFs, fill forms, merge/split documents. Use when working with PDF files or when the user mentions PDFs, document processing, or form filling. Requires pypdf and pdfplumber packages.
---

# PDF Toolkit

## Quick Start

### Extract Text
```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

### Merge PDFs
```bash
python scripts/merge_pdfs.py file1.pdf file2.pdf -o combined.pdf
```

### Fill Forms
```bash
python scripts/fill_form.py template.pdf -d data.json -o filled.pdf
```

## Core Operations

1. **Text Extraction**: See usage above
2. **Form Filling**: Use `scripts/fill_form.py`
3. **Merging**: Use `scripts/merge_pdfs.py`
4. **Splitting**: Extract pages by range

## Advanced Usage

For detailed API documentation, see [references/api-reference.md](references/api-reference.md).
For more examples, see [references/examples.md](references/examples.md).

## Requirements

```bash
pip install pypdf pdfplumber
```

## Scripts

All scripts support `--help` for usage information:
```bash
python scripts/fill_form.py --help
```
```

## Tips for Using These Examples

1. **Start with the simplest example** that matches your use case
2. **Customize the description** to match your specific triggers
3. **Add your own operations** to the task lists
4. **Keep it focused** - each skill should do one thing well
5. **Test with real requests** to ensure activation works

## Next Steps

After choosing an example:
1. Copy the structure
2. Modify the description for your use case
3. Fill in your specific operations
4. Add scripts/references if needed
5. Test and iterate
