# Skill Structure Templates

This reference provides complete templates for different skill structures.

## Table of Contents

- [Workflow-Based Skills](#workflow-based-skills)
- [Task-Based Skills](#task-based-skills)
- [Reference/Guidelines Skills](#referenceguidelines-skills)
- [Capabilities-Based Skills](#capabilities-based-skills)

## Workflow-Based Skills

Best for sequential, step-by-step processes.

### Template

```markdown
---
name: [skill-name]
description: [What it does and when to use it, including workflow keywords]
---

# [Skill Title]

## Overview

[Brief description of the workflow this skill enables]

## Workflow

Follow this sequential process:

### Step 1: [Initial Phase]

**Purpose:** [What this step accomplishes]

**Actions:**
1. [First action]
2. [Second action]
3. [Third action]

**Example:**
```[language]
[Code or command example]
```

### Step 2: [Processing Phase]

**Purpose:** [What this step accomplishes]

**Actions:**
1. [First action]
2. [Second action]

**Example:**
```[language]
[Code or command example]
```

### Step 3: [Output Phase]

**Purpose:** [What this step accomplishes]

**Actions:**
1. [First action]
2. [Second action]

**Example:**
```[language]
[Code or command example]
```

## Error Handling

[How to handle errors at each step]

## Best Practices

- [Practice 1]
- [Practice 2]
- [Practice 3]
```

### Real-World Example

```markdown
---
name: data-pipeline
description: Extract, transform, and load data from CSV files to databases. Use when processing data files, ETL tasks, or when the user mentions data pipeline, ETL, or data migration.
---

# Data Pipeline

## Overview

Automated ETL workflow for processing data from various sources into target databases.

## Workflow

### Step 1: Extract Data

**Purpose:** Load data from source files

**Actions:**
1. Identify source file format (CSV, JSON, Excel)
2. Validate file structure
3. Load data into pandas DataFrame

**Example:**
```python
import pandas as pd
df = pd.read_csv('source.csv')
```

### Step 2: Transform Data

**Purpose:** Clean and normalize data

**Actions:**
1. Remove duplicates
2. Handle missing values
3. Normalize formats
4. Apply business rules

**Example:**
```python
df = df.drop_duplicates()
df = df.fillna(method='ffill')
df['date'] = pd.to_datetime(df['date'])
```

### Step 3: Load Data

**Purpose:** Insert transformed data into target database

**Actions:**
1. Establish database connection
2. Create or validate table schema
3. Insert data in batches
4. Verify insertion

**Example:**
```python
from sqlalchemy import create_engine
engine = create_engine('postgresql://...')
df.to_sql('target_table', engine, if_exists='append')
```

## Error Handling

- **Extract failures:** Log error, skip corrupted rows, continue
- **Transform errors:** Quarantine invalid records for review
- **Load failures:** Rollback transaction, alert operator

## Best Practices

- Always validate data before transformation
- Use transactions for database operations
- Log all operations for audit trail
- Implement retry logic for transient failures
```

## Task-Based Skills

Best for collections of distinct operations.

### Template

```markdown
---
name: [skill-name]
description: [What tasks it performs and when to use it]
---

# [Skill Title]

## Overview

[What this collection of tasks enables]

## Core Tasks

### 1. [Task Name]

[Brief description of what this task does]

**Usage:**
```[language]
[Usage example]
```

**Parameters:**
- `param1`: [Description]
- `param2`: [Description]

**Example:**
```[language]
[Complete example]
```

### 2. [Task Name]

[Description]

**Usage:**
[Usage pattern]

**Example:**
[Example]

### 3. [Task Name]

[Description and examples]

## Combining Tasks

[How tasks can be used together]

## Common Patterns

### Pattern 1: [Pattern Name]
[When to use this pattern and example]

### Pattern 2: [Pattern Name]
[When to use this pattern and example]
```

### Real-World Example

```markdown
---
name: pdf-toolkit
description: Extract text, fill forms, merge, split, and rotate PDF documents. Use when working with PDF files or when the user mentions PDFs, document processing, or form filling.
---

# PDF Toolkit

## Overview

Comprehensive PDF manipulation toolkit for common document operations.

## Core Tasks

### 1. Extract Text

Extract text content from PDF files.

**Usage:**
```python
import pdfplumber
with pdfplumber.open("document.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

**Parameters:**
- `pdf_path`: Path to the PDF file
- `page_num`: Page number to extract (0-indexed)

**Example:**
```python
# Extract all text from all pages
all_text = []
with pdfplumber.open("report.pdf") as pdf:
    for page in pdf.pages:
        all_text.append(page.extract_text())
```

### 2. Merge PDFs

Combine multiple PDF files into a single document.

**Usage:**
```python
from PyPDF2 import PdfMerger
merger = PdfMerger()
for pdf in ['file1.pdf', 'file2.pdf']:
    merger.append(pdf)
merger.write('combined.pdf')
```

**Example:**
```python
# Merge all PDFs in a directory
from pathlib import Path
merger = PdfMerger()
for pdf_file in Path('.').glob('*.pdf'):
    merger.append(pdf_file)
merger.write('all_combined.pdf')
```

### 3. Fill Form Fields

Programmatically fill PDF form fields.

**Usage:**
See [scripts/fill_form.py](scripts/fill_form.py)

**Example:**
```python
# Fill form fields
python scripts/fill_form.py template.pdf output.pdf --data form_data.json
```

## Combining Tasks

Common workflow: Extract → Modify → Merge
```python
# Extract pages from multiple PDFs
# Combine extracted pages
# Output new PDF
```

## Common Patterns

### Pattern 1: Report Generation
1. Extract data from source PDFs
2. Process and analyze
3. Generate new report PDF

### Pattern 2: Form Processing
1. Fill form template
2. Merge with attachments
3. Output completed packet
```

## Reference/Guidelines Skills

Best for standards, specifications, and guidelines.

### Template

```markdown
---
name: [skill-name]
description: [What standards or guidelines it provides and when to use]
---

# [Skill Title]

## Overview

[What these guidelines enable]

## Standards

### [Standard Category 1]

[Definition and requirements]

**Examples:**
- [Example 1]
- [Example 2]

### [Standard Category 2]

[Definition and requirements]

## Specifications

### [Specification 1]

**Required:**
- [Requirement 1]
- [Requirement 2]

**Optional:**
- [Option 1]
- [Option 2]

**Example:**
[Example following specification]

## Best Practices

### [Practice 1]
[Description and rationale]

### [Practice 2]
[Description and rationale]

## Validation

[How to verify compliance with guidelines]
```

### Real-World Example

```markdown
---
name: brand-guidelines
description: Company brand visual identity standards including colors, typography, and logo usage. Use when creating branded content, marketing materials, or presentations.
---

# Brand Guidelines

## Overview

Ensure all created content follows company brand identity standards.

## Standards

### Color Palette

**Primary Colors:**
- Brand Blue: #0066CC (RGB: 0, 102, 204)
- Brand Black: #1A1A1A (RGB: 26, 26, 26)

**Secondary Colors:**
- Accent Orange: #FF6B35 (RGB: 255, 107, 53)
- Light Gray: #F5F5F5 (RGB: 245, 245, 245)

**Usage:**
- Primary colors for main brand elements
- Secondary for accents and highlights
- Maintain 4.5:1 contrast ratio for accessibility

**Examples:**
- Headers: Brand Blue on white
- CTAs: Brand Blue background with white text
- Backgrounds: Light Gray for sections

### Typography

**Primary Font:** Open Sans
- Headings: Open Sans Bold
- Body: Open Sans Regular
- UI: Open Sans SemiBold

**Font Sizes:**
- H1: 48px / 3rem
- H2: 36px / 2.25rem
- H3: 24px / 1.5rem
- Body: 16px / 1rem

**Line Height:** 1.6 for body text

## Specifications

### Logo Usage

**Required:**
- Minimum size: 120px width
- Clear space: Logo height × 0.5 on all sides
- Use SVG format when possible

**Prohibited:**
- No stretching or distortion
- No color modifications
- No rotation
- No effects (shadows, glows, etc.)

**Example:**
```html
<!-- Correct logo usage -->
<img src="logo.svg" alt="Company Logo" width="200">
```

### Document Templates

**Presentations:**
Use `assets/presentation_template.pptx`
- Title slide with logo top-right
- Section headers in Brand Blue
- Body slides with Light Gray backgrounds

**Reports:**
- Cover page with full logo
- Headers in Brand Blue
- Body text in Brand Black

## Best Practices

### Consistency
Maintain visual consistency across all materials:
- Use approved color palette only
- Apply typography hierarchy consistently
- Follow spacing and layout guidelines

### Accessibility
Ensure all branded content is accessible:
- Maintain proper contrast ratios
- Use alt text for images
- Provide text alternatives for color-coded information

## Validation

Check your work:
- [ ] Colors match exact hex codes
- [ ] Typography uses approved fonts and sizes
- [ ] Logo has adequate clear space
- [ ] Contrast ratios meet accessibility standards
- [ ] Layout follows template structure
```

## Capabilities-Based Skills

Best for integrated systems with multiple interrelated features.

### Template

```markdown
---
name: [skill-name]
description: [What the integrated system provides and when to use]
---

# [Skill Title]

## Overview

[What this integrated system enables]

## Core Capabilities

### 1. [Capability Name]

[What this capability enables]

**Key Features:**
- [Feature 1]
- [Feature 2]
- [Feature 3]

**Usage:**
[How to use this capability]

**Example:**
[Example]

### 2. [Capability Name]

[Description and usage]

### 3. [Capability Name]

[Description and usage]

## Integration Patterns

[How capabilities work together]

## Advanced Features

[Additional capabilities for power users]
```

### Real-World Example

```markdown
---
name: product-management
description: Manage product lifecycle including roadmapping, stakeholder communication, and progress tracking. Use when planning features, communicating with stakeholders, or managing product development.
---

# Product Management

## Overview

Comprehensive product management capabilities for planning, communication, and execution.

## Core Capabilities

### 1. Context Gathering

Build comprehensive understanding of product requirements.

**Key Features:**
- Stakeholder interview templates
- User research synthesis
- Competitive analysis frameworks
- Market data collection

**Usage:**
Use this when starting new initiatives or needing to understand requirements deeply.

**Example:**
```markdown
## Stakeholder Interview Framework

### Business Goals
- What problem are we solving?
- What does success look like?
- What are the constraints?

### User Needs
- Who are the users?
- What are their pain points?
- What outcomes do they need?
```

### 2. Strategic Planning

Create product roadmaps and prioritize features.

**Key Features:**
- Roadmap templates
- Prioritization frameworks (RICE, Value vs Effort)
- Dependency mapping
- Resource planning

**Usage:**
Apply when planning releases or prioritizing backlog.

**Example:**
```markdown
## RICE Prioritization

| Feature | Reach | Impact | Confidence | Effort | Score |
|---------|-------|--------|------------|--------|-------|
| Feature A | 1000 | 3 | 80% | 4 | 600 |
| Feature B | 500 | 2 | 100% | 2 | 500 |
```

### 3. Stakeholder Communication

Maintain clear communication with all stakeholders.

**Key Features:**
- Status update templates
- Release notes generation
- Presentation frameworks
- Decision documentation

**Usage:**
Use for regular updates and major announcements.

**Example:**
See [references/communication.md](references/communication.md) for detailed templates.

## Integration Patterns

**Full Product Cycle:**
1. Gather context (Capability 1)
2. Create roadmap (Capability 2)
3. Communicate plan (Capability 3)
4. Track progress (implied capability)
5. Iterate based on feedback

## Advanced Features

- Automated metrics dashboard generation
- Competitive analysis reports
- User story mapping
- OKR tracking and alignment
```

## Selection Guide

Use this guide to choose the right structure:

| Your Skill Needs | Best Structure | Key Indicator |
|------------------|----------------|---------------|
| Sequential steps that must follow order | Workflow | "First X, then Y, finally Z" |
| Collection of independent operations | Task | "Merge PDFs, split PDFs, rotate PDFs" |
| Standards or specifications to follow | Reference | "Brand guidelines, coding standards" |
| Integrated system with related features | Capabilities | "Product management, CRM system" |

## Tips for Each Structure

### Workflow Tips
- Make steps clearly numbered and sequential
- Show what happens between steps
- Provide error handling for each step
- Include checkpoint validation

### Task Tips
- Keep tasks independent and modular
- Provide clear usage examples for each
- Show how tasks can combine
- Include parameters and return values

### Reference Tips
- Organize by category or domain
- Provide concrete examples for each standard
- Include validation checklists
- Make it scannable with clear headers

### Capabilities Tips
- Group related features logically
- Show how capabilities integrate
- Provide both basic and advanced usage
- Include real-world scenarios
