import pathlib
import re
import pytest


class TestDuplicateEnums:
    """Test to check for duplicate Enum definitions in the codebase."""
    
    PATTERN = re.compile(r'class\s+([A-Za-z0-9_]+)\(.*Enum')
    
    def test_no_duplicate_enums(self):
        """Ensure no duplicate Enum classes exist in the codebase."""
        dupes = {}
        base_path = pathlib.Path('apps/server/src')
        
        for py in base_path.rglob('*.py'):
            if '__generated__' in str(py):
                continue
            
            txt = py.read_text()
            for m in self.PATTERN.finditer(txt):
                dupes.setdefault(m.group(1), []).append(py)
        
        # Find enums that appear in multiple files
        duplicate_enums = {
            name: files 
            for name, files in dupes.items() 
            if len(files) > 1
        }
        
        if duplicate_enums:
            error_msg = "Duplicate Enums detected:\n"
            for name, files in duplicate_enums.items():
                error_msg += f"\n{name} found in:\n"
                for file in files:
                    error_msg += f"  - {file}\n"
            
            pytest.fail(error_msg)