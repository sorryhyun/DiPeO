# Skill Structure Templates

## Workflow-Based (Sequential Steps)

```yaml
---
name: skill-name
description: [End-to-end process]. Use when [workflow keywords]
---

# Skill Title

[1-2 sentence overview]

## Workflow

### Step 1: [Action]
[What to do + example]

### Step 2: [Process]
[What to do + example]

### Step 3: [Output]
[What to do + example]
```

**Example:**
```yaml
---
name: data-pipeline
description: Extract, transform, load data from CSV to databases. Use when processing data, ETL, or data migration.
---

# Data Pipeline

Automated ETL workflow for processing data sources.

## Workflow

### Step 1: Extract
Load data using pandas: `pd.read_csv('source.csv')`

### Step 2: Transform
Clean and normalize: `df.drop_duplicates().fillna()`

### Step 3: Load
Insert to database: `df.to_sql('table', engine)`
```

## Task-Based (Distinct Operations)

```yaml
---
name: skill-name
description: [Tasks it performs]. Use when [task keywords]
---

# Skill Title

[Overview]

## Tasks

### 1. [Task Name]
[Description + example]

### 2. [Task Name]
[Description + example]
```

**Example:**
```yaml
---
name: pdf-toolkit
description: Extract text, merge, split PDFs. Use when working with PDF files.
---

# PDF Toolkit

## Tasks

### 1. Extract Text
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

### 2. Merge PDFs
```python
from PyPDF2 import PdfMerger
merger = PdfMerger()
merger.append('file1.pdf')
merger.write('combined.pdf')
```
```

## Reference/Guidelines (Standards)

```yaml
---
name: skill-name
description: [Standards it provides]. Use when [compliance scenarios]
---

# Skill Title

[Overview]

## Guidelines

### [Category]
[Standard + example]

### [Category]
[Standard + example]
```

**Example:**
```yaml
---
name: brand-guidelines
description: Company brand colors, typography, logo usage. Use when creating branded content.
---

# Brand Guidelines

## Standards

### Colors
- Primary: #0066CC
- Secondary: #FF6B35

### Typography
- Heading: Open Sans Bold 48px
- Body: Open Sans Regular 16px
```

## Capabilities-Based (Integrated System)

```yaml
---
name: skill-name
description: [System capabilities]. Use when [domain scenarios]
---

# Skill Title

[Overview]

## Capabilities

### 1. [Capability]
[Description + example]

### 2. [Capability]
[Description + example]
```

## Selection Guide

| Use Case | Structure | Indicator |
|----------|-----------|-----------|
| Sequential steps | Workflow | "First X, then Y, then Z" |
| Independent ops | Task | "Merge, split, rotate" |
| Standards/specs | Reference | "Guidelines, standards" |
| Related features | Capabilities | "Integrated system" |
