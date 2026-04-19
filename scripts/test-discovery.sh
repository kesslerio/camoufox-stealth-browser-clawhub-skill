#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CASES="$ROOT/tests/discovery-cases.txt"

python3 - "$ROOT" "$CASES" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
cases_path = Path(sys.argv[2])
skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
readme_text = (root / "README.md").read_text(encoding="utf-8")

match = re.search(r"(?ms)^---\n(.*?)\n---", skill_text)
if not match:
    raise SystemExit("frontmatter not found in SKILL.md")

description_match = re.search(r"(?m)^description:\s+(.+)$", match.group(1))
if not description_match:
    raise SystemExit("description not found in SKILL.md frontmatter")

description = description_match.group(1).strip().lower()
scopes = {
    "description": description,
    "skill": skill_text.lower(),
    "readme": readme_text.lower(),
}

failures = []
for raw_line in cases_path.read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue
    expectation, scope, label, terms = [part.strip() for part in line.split("|", 3)]
    haystack = scopes[scope]
    required_terms = [term.strip().lower() for term in terms.split(",") if term.strip()]
    present = all(term in haystack for term in required_terms)
    if expectation == "positive" and not present:
        failures.append(f"missing expected discovery signal: {label}")
    if expectation == "negative" and present:
        failures.append(f"unexpected discovery signal present: {label}")

if failures:
    raise SystemExit("\n".join(failures))
PY

echo "discovery checks passed"
