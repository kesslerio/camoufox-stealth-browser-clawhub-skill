#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$ROOT/SKILL.md"
README="$ROOT/README.md"

test -f "$SKILL"
test -f "$README"
test -f "$ROOT/references/gotchas.md"
test -f "$ROOT/scripts/test-discovery.sh"
test -f "$ROOT/tests/discovery-cases.txt"

skill_lines="$(wc -l < "$SKILL" | tr -d ' ')"
if [[ "$skill_lines" -ge 500 ]]; then
  echo "SKILL.md too long: ${skill_lines} lines" >&2
  exit 1
fi

python3 - "$ROOT" <<'PY'
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
skill = root / "SKILL.md"
readme = root / "README.md"

skill_text = skill.read_text(encoding="utf-8")
readme_text = readme.read_text(encoding="utf-8")

required_frontmatter = [
    r"(?m)^name:\s+camoufox-stealth-browser$",
    r"(?m)^homepage:\s+https://github\.com/kesslerio/camoufox-stealth-browser-clawhub-skill$",
    r"(?m)^description:\s+.+$",
    r"(?m)^metadata:\s*$",
    r'(?m)^\s+emoji:\s+"🦊"$',
]

for pattern in required_frontmatter:
    if not re.search(pattern, skill_text):
        raise SystemExit(f"missing required frontmatter pattern: {pattern}")

local_targets = []
for text, source in ((skill_text, "SKILL.md"), (readme_text, "README.md")):
    for target in re.findall(r"\]\(([^)#]+)(?:#[^)]+)?\)", text):
        if target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:"):
            continue
        local_targets.append((source, target))

missing = []
for source, target in local_targets:
    path = (root / target).resolve()
    if not path.exists():
        missing.append(f"{source} -> {target}")

if missing:
    raise SystemExit("missing referenced files:\n" + "\n".join(missing))
PY

test -x "$ROOT/scripts/test-discovery.sh"

echo "skill lint passed"
