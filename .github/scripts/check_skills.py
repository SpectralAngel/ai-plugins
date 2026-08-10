#!/usr/bin/env python3
"""Checks the plugin validator does not make.

1. Skill frontmatter parses as YAML and agrees with its directory name.
   The failure this exists for: an unquoted description containing "Triggers on: ..."
   is read by YAML as a nested mapping, and the whole frontmatter is dropped silently.
2. No local paths or private identifiers leaked into published text.
"""
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Substrings that must never appear in published files. Product names such as
# Nextcloud are fine in prose; these are machine- and client-specific.
LEAKS = ["spectrangel", "johndeere", "viral-rn-api", "/Users/"]

errors = []

skills = sorted(ROOT.glob("plugins/*/skills/*/SKILL.md"))
if not skills:
    errors.append("no SKILL.md files found under plugins/*/skills/*/")

for path in skills:
    rel = path.relative_to(ROOT)
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        errors.append(f"{rel}: no YAML frontmatter block")
        continue
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        first = str(exc).split("\n")[0]
        errors.append(f"{rel}: frontmatter is not valid YAML ({first})")
        continue
    if not isinstance(meta, dict):
        errors.append(f"{rel}: frontmatter is not a mapping")
        continue
    expected = path.parent.name
    if meta.get("name") != expected:
        errors.append(f"{rel}: name is {meta.get('name')!r}, expected {expected!r}")
    description = (meta.get("description") or "").strip()
    if not description:
        errors.append(f"{rel}: description is missing or empty")
    elif len(description) > 1024:
        errors.append(f"{rel}: description is {len(description)} chars (max 1024)")

for path in sorted(ROOT.glob("**/*")):
    if not path.is_file() or ".git/" in str(path.relative_to(ROOT)):
        continue
    if path.suffix not in {".md", ".json", ".sh", ".yml", ".yaml"}:
        continue
    if path == pathlib.Path(__file__):
        continue
    lowered = path.read_text(encoding="utf-8", errors="replace").lower()
    for leak in LEAKS:
        if leak.lower() in lowered:
            errors.append(f"{path.relative_to(ROOT)}: contains {leak!r}")

if errors:
    print("FAILED:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"OK: {len(skills)} skills, frontmatter valid, no leaked identifiers")
