import sys
import ast
import pathlib
import re

PATTERN = re.compile(r'class\s+([A-Za-z0-9_]+)\(.*Enum')

dupes = {}
for py in pathlib.Path('apps/server/src').rglob('*.py'):
    if '__generated__' in str(py):
        continue
    txt = py.read_text()
    for m in PATTERN.finditer(txt):
        dupes.setdefault(m.group(1), []).append(py)

errors = [n for n, files in dupes.items() if len(files) > 1]
if errors:
    print("Duplicate Enums detected:", *errors, sep='\n')
    sys.exit(1)