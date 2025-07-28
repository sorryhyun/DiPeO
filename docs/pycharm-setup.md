# PyCharm Configuration for DiPeO Diagrams

## 1. File Type Association

1. Go to **Settings → Editor → File Types**
2. Add a new file type or associate `*.light.yaml` with YAML

## 2. JSON Schema Mapping

1. Go to **Settings → Languages & Frameworks → Schemas and DTDs → JSON Schema Mappings**
2. Click **+** to add new mapping:
   - Name: `DiPeO Light Diagram`
   - Schema file: `/home/soryhyun/DiPeO/schemas/dipeo-light.schema.json`
   - File path pattern: `*.light.yaml`

## 3. External Tool for Validation

1. Go to **Settings → Tools → External Tools**
2. Click **+** to add:
   - Name: `Validate DiPeO Diagram`
   - Program: `python3`
   - Arguments: `$ProjectFileDir$/tools/validate_diagram.py $FilePath$`
   - Working directory: `$ProjectFileDir$`

## 4. File Watcher (Auto-validation)

1. Install **File Watchers** plugin if not already installed
2. Go to **Settings → Tools → File Watchers**
3. Click **+** to add:
   - Name: `DiPeO Diagram Validator`
   - File type: `YAML`
   - Scope: Pattern: `file:*.light.yaml`
   - Program: `python3`
   - Arguments: `$ProjectFileDir$/tools/validate_diagram.py $FilePath$`
   - Output filters: Configure to parse error format

## 5. Live Templates for Common Nodes

1. Go to **Settings → Editor → Live Templates**
2. Create a new group: `DiPeO`
3. Add templates like:

**Template: `dipeostart`**
```yaml
- label: Start
  type: start
  position: {x: $X$, y: $Y$}
```

**Template: `dipeocode`**
```yaml
- label: $LABEL$
  type: code_job
  position: {x: $X$, y: $Y$}
  props:
    language: python
    code: |
      $CODE$
```

## 6. Path Resolution

For better path completion in YAML files:

1. Mark directories as source roots:
   - Right-click `files/` → Mark Directory as → Sources Root
   - Right-click `apps/` → Mark Directory as → Sources Root

2. Use PyCharm's YAML plugin features for path completion

## 7. Python Code Inspection in YAML

For inline Python code validation:

1. Install **String Manipulation** plugin
2. Use **Language Injection**:
   - Place cursor in Python code block
   - Press **Alt+Enter** → Inject Language → Python

## 8. Custom Inspections

Create custom inspections via **Settings → Editor → Inspections**:
- Add patterns to detect missing start/endpoint nodes
- Check for unconnected nodes
- Validate prop requirements per node type

## 9. Keyboard Shortcuts

Assign shortcuts:
- **Validate Diagram**: `Ctrl+Shift+V`
- **Run Diagram**: `Ctrl+Shift+R`

## Usage

1. Open any `.light.yaml` file
2. PyCharm will automatically validate against schema
3. Use `Ctrl+Shift+V` to run full validation
4. Errors appear in the console and as annotations