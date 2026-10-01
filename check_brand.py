"""Guard against the failure mode where the app doesn't import at all.

The app once shipped with 13 constants imported from brand.py but never defined,
so `import main` raised ImportError and nothing ran. This is a cheap, fast
regression guard for that whole class of breakage.

Run:  python check_brand.py     (exits non-zero if anything is missing)
"""
import pathlib
import re
import sys

SRC = pathlib.Path(__file__).resolve().parent / 'src'

imported = set()
for py in SRC.rglob('*.py'):
    text = py.read_text(encoding='utf-8', errors='replace')
    for m in re.finditer(r'from brand import \(([^)]*)\)', text):
        for name in m.group(1).replace('\n', ' ').split(','):
            name = name.strip().split('#')[0].strip()
            if name:
                imported.add(name)
    for m in re.finditer(r'from brand import ([^(]+)', text):
        for name in m.group(1).split(','):
            name = name.strip()
            if name and name.isidentifier():
                imported.add(name)

brand_src = (SRC / 'brand.py').read_text(encoding='utf-8')
defined = set(re.findall(r'^([A-Z][A-Z0-9_]*)\s*=', brand_src, re.M))

missing = sorted(imported - defined)
if missing:
    print(f'MISSING {len(missing)} brand constant(s):')
    for name in missing:
        print('  -', name)
    sys.exit(1)

print(f'all {len(imported)} brand constants resolve')
