# Diff/Patch Node Documentation

## Overview

The `diff_patch` node applies unified diff patches to files with comprehensive safety controls, validation, and rollback capabilities. It provides a safer alternative to direct file writes for edit-style operations, preserving semantic intent and supporting dry-run validation.

## Canonical Diff Format

The primary supported format is **Unified Diff** (also known as `unidiff`), which is the standard output format of `diff -u` and `git diff`.

### Unified Diff Structure

```diff
--- a/original_file.txt
+++ b/modified_file.txt
@@ -line_start,line_count +line_start,line_count @@ optional_context
 unchanged context line
-removed line
+added line
 unchanged context line
```

### Components

1. **File Headers**
   - `--- a/file`: Original file path
   - `+++ b/file`: Modified file path

2. **Hunk Headers**
   - `@@ -old_start,old_count +new_start,new_count @@`
   - Specifies line numbers and counts for the change

3. **Change Lines**
   - Lines starting with ` ` (space): Context lines (unchanged)
   - Lines starting with `-`: Lines to be removed
   - Lines starting with `+`: Lines to be added

## Node Configuration

### Required Fields

- **`target_path`** (string): Path to the file to patch
- **`diff`** (string): The diff content to apply

### Optional Fields

- **`format`** (enum): Diff format type
  - `unified` (default): Standard unified diff
  - `git`: Git-style diff
  - `context`: Context diff format
  - `ed`: Ed script format
  - `normal`: Normal diff format

- **`apply_mode`** (enum): How to apply the patch
  - `normal` (default): Standard application, fail on conflicts
  - `force`: Continue despite rejected hunks
  - `dry_run`: Validate without applying changes
  - `reverse`: Apply diff in reverse (undo changes)

- **`backup`** (boolean): Create backup before patching (default: true)
- **`validate`** (boolean): Validate patch before applying (default: true)
- **`backup_dir`** (string): Directory for backup files
- **`strip_level`** (number): Strip N leading path components (default: 1)
- **`fuzz_factor`** (number): Lines that can be ignored when matching (default: 2)
- **`reject_file`** (string): Path to save rejected hunks
- **`ignore_whitespace`** (boolean): Ignore whitespace when matching (default: false)
- **`create_missing`** (boolean): Create target file if it doesn't exist (default: false)

## Output Structure

The node returns an envelope with the following result structure:

```json
{
  "status": "success|partial|error|invalid",
  "target_path": "/path/to/file",
  "applied_hunks": 5,
  "rejected_hunks": [],
  "backup_path": "/path/to/backup",
  "file_hash": "sha256_hash",
  "dry_run": false,
  "errors": []
}
```

### Status Values

- `success`: All hunks applied successfully
- `partial`: Some hunks were rejected
- `error`: Fatal error during processing
- `invalid`: Diff validation failed

## Example Usage

### Basic Patch Application

```yaml
- id: patch_config
  type: diff_patch
  target_path: "/config/settings.json"
  diff: |
    --- a/settings.json
    +++ b/settings.json
    @@ -10,3 +10,4 @@
       "debug": false,
       "timeout": 30,
    +  "max_retries": 3,
       "enabled": true
```

### Dry Run Validation

```yaml
- id: validate_patch
  type: diff_patch
  target_path: "/src/main.py"
  diff: "..."
  apply_mode: dry_run
  validate: true
```

### Force Application with Rejected Hunks Saved

```yaml
- id: force_patch
  type: diff_patch
  target_path: "/app/module.js"
  diff: "..."
  apply_mode: force
  reject_file: "/tmp/rejected.patch"
  backup: true
```

### Reverse a Previously Applied Patch

```yaml
- id: undo_patch
  type: diff_patch
  target_path: "/data/file.txt"
  diff: "..."
  apply_mode: reverse
```

## Safety Features

1. **Automatic Backups**: Creates backups before modification (configurable)
2. **Validation**: Pre-validates diff structure and applicability
3. **Dry Run**: Test patch application without making changes
4. **Rejected Hunks**: Saves unapplicable portions for review
5. **Atomic Operations**: Restores from backup on partial failure
6. **File Hash**: Returns SHA256 hash for verification

## Error Handling

The handler provides comprehensive error handling:

- Missing target files (optionally creates them)
- Invalid diff format
- Partially applicable patches
- Conflict detection with fuzzing
- Automatic rollback on failure

## Integration with Claude Code Translator

The diff_patch node is designed to work seamlessly with the Claude Code translator, enabling:

- Preservation of edit semantics in diagrams
- Safe file modifications with rollback capability
- Preview of changes before application
- Conflict detection and resolution

## Best Practices

1. **Always validate first**: Use `dry_run` mode to test patches
2. **Keep backups**: Leave `backup: true` for production changes
3. **Handle rejections**: Check `rejected_hunks` in the output
4. **Use appropriate fuzz**: Adjust `fuzz_factor` for flexibility
5. **Version control**: Combine with git for additional safety

## Comparison with DB Write Node

| Feature | diff_patch | db (write mode) |
|---------|-----------|-----------------|
| Preserves edit intent | ✅ Yes | ❌ No |
| Validation before apply | ✅ Yes | ❌ No |
| Automatic backups | ✅ Yes | ❌ No |
| Partial application handling | ✅ Yes | ❌ No |
| Dry run support | ✅ Yes | ❌ No |
| Conflict detection | ✅ Yes | ❌ No |
| File creation | ✅ Optional | ✅ Always |

## Technical Implementation

The handler uses:
- Python's `difflib` for diff parsing
- SHA256 for file verification
- Atomic file operations with backup/restore
- Comprehensive logging for debugging
