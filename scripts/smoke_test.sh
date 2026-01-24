#!/usr/bin/env bash
set -euo pipefail

# CloudPedagogy Course Engine — Smoke Test
# Purpose: quick, repeatable, low-risk validation of toolchain + CLI + core workflows.
# Run from repo root (recommended inside .venv).

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== Smoke test: repo = $ROOT =="

echo
echo "== 1) Python + env =="
python --version
python -c "import sys; print('executable:', sys.executable)"

echo
echo "== 2) Toolchain presence (minimal) =="
command -v quarto >/dev/null
quarto --version
command -v pandoc >/dev/null
pandoc --version | head -n 1

echo
echo "== 3) course-engine CLI entrypoint =="
command -v course-engine >/dev/null
course-engine --help >/dev/null
course-engine --version
course-engine check
course-engine check --json | python -m json.tool >/dev/null

echo
echo "== 4) Import sanity =="
python -c "import course_engine; print('course_engine:', course_engine.__file__)"
python -c "from course_engine.explain.text import explain_payload_to_text, explain_payload_to_summary; print('explain text imports OK')"

echo
echo "== 5) Unit tests =="
pytest -q

echo
echo "== 6) Build demo (writes to a temp dist folder) =="

DEMO_YML="demo/scenario-planning-environmental-scanning/course.yml"
COURSE_ID="scenario-planning-environmental-scanning"

if [[ ! -f "$DEMO_YML" ]]; then
  echo "ERROR: demo course.yml not found at: $DEMO_YML"
  exit 1
fi

# Use a temp-ish location to avoid repo clutter and the parent-dir trap
OUT="/tmp/ce-e2e"
rm -rf "$OUT"
mkdir -p "$OUT"

course-engine build "$DEMO_YML" --out "$OUT" --overwrite

# Prefer deterministic child path (avoids parent-dir trap)
ARTEFACT_DIR="$OUT/$COURSE_ID"

# Fallbacks: handle alternate --out semantics
if [[ ! -f "$ARTEFACT_DIR/manifest.json" ]]; then
  if [[ -f "$OUT/manifest.json" ]]; then
    ARTEFACT_DIR="$OUT"
  else
    SUBDIR="$(find "$OUT" -mindepth 1 -maxdepth 2 -type f -name manifest.json -print \
      | sed 's|/manifest.json$||' \
      | head -n 1 || true)"
    if [[ -z "${SUBDIR:-}" ]]; then
      echo "ERROR: build produced no manifest.json in $OUT."
      echo "Expected either:"
      echo "  - $OUT/$COURSE_ID/manifest.json"
      echo "  - $OUT/manifest.json"
      echo "  - another child artefact dir under $OUT containing manifest.json"
      exit 1
    fi
    ARTEFACT_DIR="$SUBDIR"
  fi
fi

echo "Artefact dir: $ARTEFACT_DIR"
test -f "$ARTEFACT_DIR/manifest.json" && echo "manifest OK"

echo
echo "== 7) Explain (source + artefact) =="

course-engine explain "$DEMO_YML" --json | python -m json.tool >/dev/null
course-engine explain "$DEMO_YML" --format text | sed -n '1,60p'

course-engine explain "$ARTEFACT_DIR" --json | python -m json.tool >/dev/null
course-engine explain "$ARTEFACT_DIR" --format text | sed -n '1,90p'

echo
echo "== 8) Inspect (artefact) =="
# If inspect exists, run it; otherwise skip.
if course-engine inspect --help >/dev/null 2>&1; then
  course-engine inspect "$ARTEFACT_DIR" | sed -n '1,200p'
else
  echo "(skip) course-engine inspect not available"
fi

echo
echo "== 9) Report + validate (informational; do not fail smoke) =="
if course-engine report --help >/dev/null 2>&1; then
  course-engine report "$ARTEFACT_DIR" || true
else
  echo "(skip) course-engine report not available"
fi

if course-engine validate --help >/dev/null 2>&1; then
  course-engine validate "$ARTEFACT_DIR" || true
else
  echo "(skip) course-engine validate not available"
fi

echo
echo "== 10) Pack (artefact) =="
rm -rf /tmp/ce-pack-test
course-engine pack "$ARTEFACT_DIR" --out /tmp/ce-pack-test --overwrite >/dev/null
test -f /tmp/ce-pack-test/manifest.json && echo "pack manifest OK"
test -f /tmp/ce-pack-test/explain.json && echo "pack explain.json OK"
test -f /tmp/ce-pack-test/summary.txt && echo "pack summary.txt OK"

echo
echo "== DONE: smoke test completed successfully =="
