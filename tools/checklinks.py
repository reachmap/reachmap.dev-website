#!/usr/bin/env python3
"""Check that every internal link and asset in the site resolves.

Broken internal links are the failure mode of a hand-maintained static site, and
they are silent: the page still deploys. This runs in CI so they are not.
"""

import os
import re
import sys
from urllib.parse import urldefrag

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

pages = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in (".git", ".github", "tools")]
    for fn in filenames:
        if fn.endswith(".html"):
            pages.append(os.path.join(dirpath, fn))

REF = re.compile(r'(?:href|src)="([^"]+)"')
problems = []
anchors_by_page = {}

for page in pages:
    with open(page, encoding="utf-8") as fh:
        text = fh.read()
    anchors_by_page[page] = set(re.findall(r'id="([^"]+)"', text))

for page in pages:
    rel_page = os.path.relpath(page, ROOT)
    with open(page, encoding="utf-8") as fh:
        text = fh.read()
    for ref in REF.findall(text):
        if ref.startswith(("http://", "https://", "mailto:", "data:", "#")):
            if ref.startswith("#") and ref[1:] and ref[1:] not in anchors_by_page[page]:
                problems.append(f"{rel_page}: missing anchor {ref}")
            continue
        target, frag = urldefrag(ref)
        if not target:
            continue
        dest = os.path.normpath(os.path.join(os.path.dirname(page), target))
        if not os.path.exists(dest):
            problems.append(f"{rel_page}: broken link -> {ref}")
            continue
        if frag and dest.endswith(".html"):
            if frag not in anchors_by_page.get(dest, set()):
                problems.append(f"{rel_page}: {ref} -> no such anchor")

if problems:
    print("\n".join(sorted(problems)), file=sys.stderr)
    print(f"\n{len(problems)} problem(s)", file=sys.stderr)
    sys.exit(1)

print(f"OK: {len(pages)} pages, every internal link resolves")
