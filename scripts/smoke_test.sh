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
echo "== 2) Quarto toolchain =="
command -v quarto >/dev/null
quarto --version
quarto check

echo
echo "== 3) course-engine CLI entrypoint =="
command -v course-engine >/dev/null
course-engine --help >/dev/null
course-engine check

echo
echo "== 3A) course-engine version =="
course-engine --version

echo
echo "== 4) Import sanity =="
python -c "import course_engine; print('course_engine:', course_engine.__file__)"

echo
echo "== 5) Unit tests =="
pytest -q

echo
echo "== 6) Build + render demo (non-destructive except a temp dist folder) =="

DEMO_YML="demo/scenario-planning-environmental-scanning/course.yml"
if [[ ! -f "$DEMO_YML" ]]; then
  echo "ERROR: demo course.yml not found at: $DEMO_YML"
  exit 1
fi

OUT="dist/_smoke_demo"
rm -rf "$OUT"

course-engine build "$DEMO_YML" --out "$OUT" --overwrite

# Resolve expected course slug folder name by reading the first directory created under OUT.
# This avoids hard-coding the course slug.
COURSE_DIR="$(find "$OUT" -mindepth 1 -maxdepth 1 -type d | head -n 1 || true)"
if [[ -z "${COURSE_DIR:-}" ]]; then
  echo "ERROR: build produced no course directory under $OUT"
  exit 1
fi

course-engine render "$COURSE_DIR"
course-engine inspect "$COURSE_DIR" | sed -n '1,160p'

echo
echo "== 7) Report + validate (may be informative-only depending on mapping) =="
course-engine report "$COURSE_DIR" || true
course-engine validate "$COURSE_DIR" || true

echo
echo "== 8) Explain-only policy resolution (no manifest required) =="
course-engine validate /tmp --policy preset:baseline --profile baseline --explain --json | head -n 60

echo
echo "== DONE: smoke test completed successfully =="
