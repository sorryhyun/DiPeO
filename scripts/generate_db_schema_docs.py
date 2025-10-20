#!/usr/bin/env python3
"""
Automated Database Schema Documentation Generator

Extracts SQL CREATE TABLE statements from Python source code and generates:
1. Markdown documentation with table structures
2. Mermaid ER diagram for visual representation
3. Index documentation
"""

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Column:
    name: str
    type: str
    constraints: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        constraints_str = " ".join(self.constraints) if self.constraints else ""
        return f"{self.name} {self.type} {constraints_str}".strip()


@dataclass
class Index:
    name: str
    columns: list[str]
    unique: bool = False

    def __str__(self) -> str:
        idx_type = "UNIQUE INDEX" if self.unique else "INDEX"
        cols = ", ".join(self.columns)
        return f"{idx_type} {self.name} ON ({cols})"


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)
    indexes: list[Index] = field(default_factory=list)
    source_file: str = ""

    @property
    def primary_key(self) -> str | None:
        for col in self.columns:
            if "PRIMARY KEY" in col.constraints:
                return col.name
        return None


class SQLSchemaExtractor:
    """Extracts SQL schemas from Python source files."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.tables: dict[str, Table] = {}
        self.debug = False

    def extract_from_files(self, pattern: str = "**/*.py") -> None:
        """Extract schemas from all Python files matching pattern."""
        exclude_dirs = [".venv/", "node_modules/", "__pycache__/", ".git/"]

        for py_file in self.base_dir.glob(pattern):
            if py_file.is_file():
                # Skip excluded directories (check for directory separator)
                rel_path = str(py_file.relative_to(self.base_dir))
                if any(excl in rel_path for excl in exclude_dirs):
                    continue
                self._process_file(py_file)

    def _process_file(self, file_path: Path) -> None:
        """Process a single Python file for SQL schemas."""
        try:
            content = file_path.read_text()

            # Find all triple-quoted strings that contain CREATE TABLE
            # Match complete triple-quoted blocks first, then check for SQL
            block_patterns = [
                r'"""(.*?)"""',
                r"'''(.*?)'''",
            ]

            for pattern in block_patterns:
                matches = re.finditer(pattern, content, re.DOTALL)
                for match in matches:
                    block = match.group(1)
                    # Only process if it contains SQL CREATE statements
                    if re.search(r"CREATE\s+TABLE", block, re.IGNORECASE):
                        self._parse_sql_block(block, str(file_path.relative_to(self.base_dir)))

        except Exception as e:
            print(f"Warning: Failed to process {file_path}: {e}")

    def _parse_sql_block(self, sql_block: str, source_file: str) -> None:
        """Parse SQL statements from a block of SQL code."""
        # Split by semicolon to get individual statements
        statements = [s.strip() for s in sql_block.split(";") if s.strip()]

        for stmt in statements:
            if re.search(r"CREATE\s+TABLE", stmt, re.IGNORECASE):
                self._parse_create_table(stmt, source_file)
            elif re.search(r"CREATE\s+(UNIQUE\s+)?INDEX", stmt, re.IGNORECASE):
                self._parse_create_index(stmt)

    def _parse_create_table(self, stmt: str, source_file: str) -> None:
        """Parse a CREATE TABLE statement."""
        # Extract table name
        table_match = re.search(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(", stmt, re.IGNORECASE
        )
        if not table_match:
            if self.debug:
                print(f"  [DEBUG] No table name match for statement: {stmt[:100]}")
            return

        table_name = table_match.group(1)
        if self.debug:
            print(f"  [DEBUG] Parsing table: {table_name} from {source_file}")
            print(f"    [DEBUG] Statement length: {len(stmt)} chars, first 200: {stmt[:200]}")

        # Extract column definitions - find content between outer parens
        # The regex matches up to and including the '(', so find it within the match
        start_paren = stmt.find("(", table_match.start())
        if start_paren == -1:
            if self.debug:
                print(f"    [DEBUG] No opening paren found for {table_name}")
            return

        paren_depth = 1  # Start at 1 because we've already counted the opening paren
        end_paren = -1

        for i in range(start_paren + 1, len(stmt)):  # Start after the opening paren
            if stmt[i] == "(":
                paren_depth += 1
            elif stmt[i] == ")":
                paren_depth -= 1
                if paren_depth == 0:
                    end_paren = i
                    break

        if end_paren == -1:
            if self.debug:
                print(f"    [DEBUG] Could not find closing paren for {table_name}")
            return

        content = stmt[start_paren + 1 : end_paren]

        if self.debug:
            print(f"    [DEBUG] Table content length: {len(content)} chars")

        # Split by comma but respect content in parentheses
        columns = []
        current_col = []
        paren_depth = 0

        for char in content + ",":
            if char == "(":
                paren_depth += 1
                current_col.append(char)
            elif char == ")":
                paren_depth -= 1
                current_col.append(char)
            elif char == "," and paren_depth == 0:
                col_def = "".join(current_col).strip()
                if col_def:
                    self._parse_column_definition(col_def, columns)
                current_col = []
            else:
                current_col.append(char)

        if self.debug:
            print(f"    [DEBUG] Parsed {len(columns)} columns for {table_name}")

        table = Table(name=table_name, columns=columns, source_file=source_file)
        self.tables[table_name] = table

        if self.debug:
            print(f"    [DEBUG] Stored table {table_name} (total tables now: {len(self.tables)})")

    def _parse_column_definition(self, col_def: str, columns: list[Column]) -> None:
        """Parse a single column definition."""
        # Skip constraint definitions
        if re.match(
            r"^\s*(CONSTRAINT|FOREIGN|CHECK|UNIQUE\s*\(|PRIMARY\s+KEY\s*\()", col_def, re.IGNORECASE
        ):
            if self.debug:
                print(f"      [DEBUG] Skipping constraint: {col_def[:50]}")
            return

        # Parse: column_name TYPE [constraints...]
        parts = col_def.split(None, 2)
        if len(parts) < 2:
            if self.debug:
                print(f"      [DEBUG] Skipping (not enough parts): {col_def[:50]}")
            return

        col_name = parts[0].strip()
        col_type = parts[1].strip()

        # Extract constraints (everything after the type)
        constraints_str = parts[2] if len(parts) > 2 else ""

        # Parse constraints into list
        constraints = []
        if constraints_str:
            # Handle special multi-word constraints
            constraints_str = constraints_str.strip()
            if re.search(r"PRIMARY\s+KEY", constraints_str, re.IGNORECASE):
                constraints.append("PRIMARY KEY")
                constraints_str = re.sub(r"PRIMARY\s+KEY", "", constraints_str, flags=re.IGNORECASE)
            if re.search(r"NOT\s+NULL", constraints_str, re.IGNORECASE):
                constraints.append("NOT NULL")
                constraints_str = re.sub(r"NOT\s+NULL", "", constraints_str, flags=re.IGNORECASE)
            if "UNIQUE" in constraints_str.upper():
                constraints.append("UNIQUE")
                constraints_str = re.sub(r"\bUNIQUE\b", "", constraints_str, flags=re.IGNORECASE)

            # Handle DEFAULT
            default_match = re.search(
                r"DEFAULT\s+([^,\s]+(?:\s*\([^)]*\))?)", constraints_str, re.IGNORECASE
            )
            if default_match:
                constraints.append(f"DEFAULT {default_match.group(1)}")
                constraints_str = re.sub(
                    r"DEFAULT\s+[^,\s]+(?:\s*\([^)]*\))?", "", constraints_str, flags=re.IGNORECASE
                )

            # Any remaining words
            remaining = [
                w.strip()
                for w in constraints_str.split()
                if w.strip() and w.upper() not in ["ON", "UPDATE", "DELETE", "CASCADE"]
            ]
            constraints.extend(remaining)

        col = Column(name=col_name, type=col_type, constraints=constraints)
        columns.append(col)

    def _parse_create_index(self, stmt: str) -> None:
        """Parse a CREATE INDEX statement."""
        # Extract index name and table
        idx_match = re.search(
            r"CREATE\s+(UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)\s*\((.*?)\)",
            stmt,
            re.IGNORECASE,
        )
        if not idx_match:
            return

        is_unique = bool(idx_match.group(1))
        idx_name = idx_match.group(2)
        table_name = idx_match.group(3)
        columns_str = idx_match.group(4)

        # Parse column list
        columns = [c.strip() for c in columns_str.split(",")]

        if table_name in self.tables:
            index = Index(name=idx_name, columns=columns, unique=is_unique)
            self.tables[table_name].indexes.append(index)


class SchemaDocGenerator:
    """Generates documentation from extracted schemas."""

    def __init__(self, extractor: SQLSchemaExtractor):
        self.extractor = extractor

    def generate_markdown(self) -> str:
        """Generate markdown documentation."""
        lines = [
            "# DiPeO Database Schema Documentation",
            "",
            "> **Auto-generated documentation** - DO NOT EDIT MANUALLY",
            "> Generated from SQL CREATE TABLE statements in Python source code",
            "> Run `make schema-docs` to regenerate",
            "",
            "## Overview",
            "",
            "DiPeO uses SQLite databases for persistence with the following schema:",
            "",
            f"- **Number of tables**: {len(self.extractor.tables)}",
            "- **Database location**: `.dipeo/data/dipeo_state.db`",
            "",
            "## Tables",
            "",
        ]

        for _table_name, table in sorted(self.extractor.tables.items()):
            lines.extend(self._generate_table_section(table))

        lines.extend(
            [
                "",
                "## Mermaid ER Diagram",
                "",
                "```mermaid",
                self.generate_mermaid_diagram(),
                "```",
                "",
            ]
        )

        return "\n".join(lines)

    def _generate_table_section(self, table: Table) -> list[str]:
        """Generate markdown section for a single table."""
        lines = [
            f"### `{table.name}`",
            "",
            f"**Source**: `{table.source_file}`",
            "",
        ]

        if table.primary_key:
            lines.append(f"**Primary Key**: `{table.primary_key}`")
            lines.append("")

        # Column table
        lines.extend(
            [
                "#### Columns",
                "",
                "| Column | Type | Constraints |",
                "|--------|------|-------------|",
            ]
        )

        for col in table.columns:
            constraints = " ".join(col.constraints) if col.constraints else "-"
            lines.append(f"| `{col.name}` | `{col.type}` | {constraints} |")

        # Indexes
        if table.indexes:
            lines.extend(
                [
                    "",
                    "#### Indexes",
                    "",
                ]
            )
            for idx in table.indexes:
                lines.append(f"- **{idx.name}**: {idx}")

        lines.append("")
        return lines

    def generate_mermaid_diagram(self) -> str:
        """Generate Mermaid ER diagram."""
        lines = ["erDiagram"]

        for table_name, table in sorted(self.extractor.tables.items()):
            lines.append(f"    {table_name} {{")

            for col in table.columns:
                # Determine if PK or FK
                key_indicator = ""
                if "PRIMARY" in " ".join(col.constraints):
                    key_indicator = " PK"
                elif "FOREIGN" in " ".join(col.constraints):
                    key_indicator = " FK"

                # Clean type
                col_type = col.type.upper()

                lines.append(f"        {col_type} {col.name}{key_indicator}")

            lines.append("    }")

        # Add relationships (if we can detect them from foreign keys)
        for table_name, table in self.extractor.tables.items():
            for col in table.columns:
                # Simple FK detection (could be enhanced)
                if col.name.endswith("_id") and col.name != "id":
                    ref_table = col.name.replace("_id", "") + "s"
                    if ref_table in self.extractor.tables:
                        lines.append(f"    {table_name} ||--o{{ {ref_table} : has")

        return "\n".join(lines)

    def generate_sql_reference(self) -> str:
        """Generate SQL DDL reference file."""
        lines = [
            "-- DiPeO Database Schema",
            "-- Auto-generated SQL DDL reference",
            "-- DO NOT EXECUTE - For reference only",
            "",
        ]

        for table_name, table in sorted(self.extractor.tables.items()):
            lines.append(f"-- Table: {table_name}")
            lines.append(f"-- Source: {table.source_file}")
            lines.append(f"CREATE TABLE IF NOT EXISTS {table_name} (")

            col_lines = []
            for col in table.columns:
                constraints = " ".join(col.constraints)
                col_lines.append(f"    {col.name} {col.type} {constraints}".rstrip())

            lines.append(",\n".join(col_lines))
            lines.append(");")
            lines.append("")

            # Add indexes
            for idx in table.indexes:
                unique = "UNIQUE " if idx.unique else ""
                cols = ", ".join(idx.columns)
                lines.append(
                    f"CREATE {unique}INDEX IF NOT EXISTS {idx.name} " f"ON {table_name}({cols});"
                )

            lines.append("")
            lines.append("")

        return "\n".join(lines)


def main():
    """Main entry point."""
    import sys

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Check for debug flag
    debug = "--debug" in sys.argv

    print("DiPeO Schema Documentation Generator")
    print("=" * 50)
    print()

    # Extract schemas
    print("Extracting schemas from Python files...")
    extractor = SQLSchemaExtractor(project_root)
    extractor.debug = debug
    extractor.extract_from_files()

    print(f"Found {len(extractor.tables)} tables:")
    for table_name in sorted(extractor.tables.keys()):
        table = extractor.tables[table_name]
        print(f"  - {table_name} ({len(table.columns)} columns)")
        if debug:
            print(f"    Source: {table.source_file}")
    print()

    # Generate documentation
    print("Generating documentation...")
    generator = SchemaDocGenerator(extractor)

    # Generate markdown docs in docs/ directory
    docs_dir = project_root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    schema_doc_path = docs_dir / "database-schema.md"
    schema_doc_path.write_text(generator.generate_markdown())
    print(f"✓ Generated: {schema_doc_path.relative_to(project_root)}")

    # Generate SQL reference
    sql_ref_path = docs_dir / "database-schema.sql"
    sql_ref_path.write_text(generator.generate_sql_reference())
    print(f"✓ Generated: {sql_ref_path.relative_to(project_root)}")

    print()
    print("Schema documentation generated successfully!")


if __name__ == "__main__":
    main()
