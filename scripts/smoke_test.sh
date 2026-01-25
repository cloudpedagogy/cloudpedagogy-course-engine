#!/usr/bin/env bash
set -euo pipefail

# CloudPedagogy Course Engine — Smoke Test
# Purpose: quick, repeatable, low-risk validation of toolchain + CLI + core workflows.
# Run from repo root (recommended inside .venv).
#
# Design goals:
# - minimal external assumptions (no jq required)
# - writes to /tmp (keeps repo clean)
# - deterministic artefact discovery (avoids parent-dir trap)
# - exercises both source-level and artefact-level explain
# - exercises snapshot determinism (timestamp-normalised)
# - exercises pack output presence
#
# Optional:
# - if a scenario-planning demo course.yml exists, run a second build/explain pass

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
# Legacy flag still supported; keep it for backwards compatibility smoke coverage
course-engine check --json | python -m json.tool >/dev/null
# Preferred selector (v1.19+)
course-engine check --format json | python -m json.tool >/dev/null

echo
echo "== 4) Import sanity =="
python -c "import course_engine; print('course_engine:', course_engine.__file__)"
python -c "from course_engine.explain.text import explain_payload_to_text, explain_payload_to_summary; print('explain text imports OK')"

echo
echo "== 5) Unit tests =="
pytest -q

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

resolve_artefact_dir() {
  # Args: OUT_DIR, EXPECTED_COURSE_ID (may be empty)
  # Echoes: resolved artefact dir (contains manifest.json) or exits 1
  local out_dir="$1"
  local expected_id="${2:-}"

  # Preferred deterministic child path when expected_id provided
  if [[ -n "$expected_id" ]] && [[ -f "$out_dir/$expected_id/manifest.json" ]]; then
    echo "$out_dir/$expected_id"
    return 0
  fi

  # Alternate semantic: manifest at OUT root
  if [[ -f "$out_dir/manifest.json" ]]; then
    echo "$out_dir"
    return 0
  fi

  # Fallback: find first child manifest.json (stable enough for smoke)
  local subdir=""
  subdir="$(find "$out_dir" -mindepth 1 -maxdepth 3 -type f -name manifest.json -print \
    | sed 's|/manifest.json$||' \
    | head -n 1 || true)"

  if [[ -n "${subdir:-}" ]]; then
    echo "$subdir"
    return 0
  fi

  echo "ERROR: build produced no manifest.json in $out_dir." >&2
  if [[ -n "$expected_id" ]]; then
    echo "Expected either:" >&2
    echo "  - $out_dir/$expected_id/manifest.json" >&2
    echo "  - $out_dir/manifest.json" >&2
    echo "  - another child artefact dir under $out_dir containing manifest.json" >&2
  else
    echo "Expected either:" >&2
    echo "  - $out_dir/manifest.json" >&2
    echo "  - a child artefact dir under $out_dir containing manifest.json" >&2
  fi
  exit 1
}

snapshot_determinism_check() {
  # Args: ARTEFACT_DIR, OUT_DIR
  local artefact_dir="$1"
  local out_dir="$2"

  echo
  echo "== 8) Snapshot determinism (timestamp-normalised) =="

  course-engine snapshot "$artefact_dir" --format json > "$out_dir/snap1.json"
  course-engine snapshot "$artefact_dir" --format json > "$out_dir/snap2.json"

  python - "$out_dir/snap1.json" "$out_dir/snap2.json" "$out_dir/snap1.norm.json" "$out_dir/snap2.norm.json" <<'PY'
import json, sys, pathlib

snap1, snap2, out1, out2 = sys.argv[1:5]

def norm(path: str) -> dict:
    p = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    p["generated_at_utc"] = "<NORMALISED>"
    return p

p1 = norm(snap1)
p2 = norm(snap2)

pathlib.Path(out1).write_text(json.dumps(p1, sort_keys=True, indent=2), encoding="utf-8")
pathlib.Path(out2).write_text(json.dumps(p2, sort_keys=True, indent=2), encoding="utf-8")
PY

  diff "$out_dir/snap1.norm.json" "$out_dir/snap2.norm.json"
}

run_build_explain_pack() {
  # Args: LABEL, COURSE_YML, EXPECTED_COURSE_ID, OUT_DIR, PACK_DIR
  local label="$1"
  local course_yml="$2"
  local expected_id="$3"
  local out_dir="$4"
  local pack_dir="$5"

  echo
  echo "== 6) Build demo ($label) =="

  if [[ ! -f "$course_yml" ]]; then
    echo "ERROR: course.yml not found at: $course_yml"
    exit 1
  fi

  rm -rf "$out_dir"
  mkdir -p "$out_dir"

  course-engine build "$course_yml" --out "$out_dir" --overwrite

  local artefact_dir=""
  artefact_dir="$(resolve_artefact_dir "$out_dir" "$expected_id")"

  echo "Artefact dir: $artefact_dir"
  test -f "$artefact_dir/manifest.json" && echo "manifest OK"

  echo
  echo "== 7) Explain (source + artefact) [$label] =="

  course-engine explain "$course_yml" --json | python -m json.tool >/dev/null
  course-engine explain "$course_yml" --format text | sed -n '1,60p'

  course-engine explain "$artefact_dir" --json | python -m json.tool >/dev/null
  course-engine explain "$artefact_dir" --format text | sed -n '1,90p'

  snapshot_determinism_check "$artefact_dir" "$out_dir"

  echo
  echo "== 9) Inspect (artefact) [$label] =="
  if course-engine inspect --help >/dev/null 2>&1; then
    course-engine inspect "$artefact_dir" | sed -n '1,200p'
  else
    echo "(skip) course-engine inspect not available"
  fi

  echo
  echo "== 10) Report + validate (informational; do not fail smoke) [$label] =="
  if course-engine report --help >/dev/null 2>&1; then
    course-engine report "$artefact_dir" || true
  else
    echo "(skip) course-engine report not available"
  fi

  if course-engine validate --help >/dev/null 2>&1; then
    course-engine validate "$artefact_dir" || true
  else
    echo "(skip) course-engine validate not available"
  fi

  echo
  echo "== 11) Pack (artefact) [$label] =="
  rm -rf "$pack_dir"
  course-engine pack "$artefact_dir" --out "$pack_dir" --overwrite >/dev/null
  test -f "$pack_dir/manifest.json" && echo "pack manifest OK"
  test -f "$pack_dir/explain.json" && echo "pack explain.json OK"
  test -f "$pack_dir/summary.txt" && echo "pack summary.txt OK"
}

# ------------------------------------------------------------------------------
# Primary demo: stable sample course
# ------------------------------------------------------------------------------

DEMO_YML_PRIMARY="examples/sample-course/course.yml"
COURSE_ID_PRIMARY="ai-capability-foundations"

OUT_PRIMARY="/tmp/ce-smoke.sample-course.$$"
PACK_PRIMARY="/tmp/ce-smoke.pack.sample-course.$$"

run_build_explain_pack "sample-course" "$DEMO_YML_PRIMARY" "$COURSE_ID_PRIMARY" "$OUT_PRIMARY" "$PACK_PRIMARY"

# ------------------------------------------------------------------------------
# Optional secondary demo: scenario planning (if present)
# ------------------------------------------------------------------------------

DEMO_YML_SECONDARY="demo/scenario-planning-environmental-scanning/course.yml"
COURSE_ID_SECONDARY="scenario-planning-environmental-scanning"

if [[ -f "$DEMO_YML_SECONDARY" ]]; then
  OUT_SECONDARY="/tmp/ce-smoke.scenario.$$"
  PACK_SECONDARY="/tmp/ce-smoke.pack.scenario.$$"
  run_build_explain_pack "scenario-planning" "$DEMO_YML_SECONDARY" "$COURSE_ID_SECONDARY" "$OUT_SECONDARY" "$PACK_SECONDARY"
else
  echo
  echo "== (skip) Optional scenario demo not found: $DEMO_YML_SECONDARY =="
fi

echo
echo "== DONE: smoke test completed successfully =="
