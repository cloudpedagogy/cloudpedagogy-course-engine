#!/usr/bin/env bash
set -euo pipefail

# CloudPedagogy Course Engine — Verify Release
#
# Purpose:
# Maintainer-facing pre-release verification.
# Run before merging to master or tagging a release.
# Not intended for routine development use.
#
# What this checks:
# - Environment + package version alignment
# - Preflight contract (check, strict, json validity)
# - Static analysis (ruff, mypy) + unit tests (pytest)
# - End-to-end build + render (sample course) into a temp dir
# - Explain + snapshot determinism (timestamp-normalised)
# - Pack profile sanity (audit)
# - Optional scenario artefact checks (source if present, otherwise dist artefact)
# - Policy explain sanity (validate --explain --json)

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==[ 0. Environment check ]=============================="
echo "repo root: $ROOT"

# Ensure key tooling exists
for cmd in course-engine python ruff mypy pytest; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: required command not found: $cmd"
    exit 1
  fi
done

which course-engine
python --version

ENGINE_VERSION="$(course-engine --version | tr -d '[:space:]')"
echo "course-engine version: $ENGINE_VERSION"

PKG_VERSION="$(python -c "import course_engine; print(course_engine.__version__)")"
echo "python package version: $PKG_VERSION"

if [[ "$ENGINE_VERSION" != "$PKG_VERSION" ]]; then
  echo "ERROR: version mismatch (CLI vs python package)"
  echo "  CLI:  $ENGINE_VERSION"
  echo "  PKG:  $PKG_VERSION"
  echo "Tip: ensure you're in the correct .venv and (re)install with: pip install -e ."
  exit 1
fi

echo
echo "==[ 0.1 Preflight check contract ]======================"
course-engine check
course-engine check --format json | python -m json.tool >/dev/null
course-engine check --strict

echo
echo "==[ 1. Static analysis & tests ]========================"
ruff check .
mypy src
pytest -q

# Prefer temp output to avoid repo clutter / parent-dir ambiguity.
OUT_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/ce-verify.XXXXXX")"
cleanup() { rm -rf "$OUT_ROOT"; }
trap cleanup EXIT

echo
echo "==[ 2. Build + render: sample course ]=================="
SAMPLE_YML="examples/sample-course/course.yml"
SAMPLE_ID="ai-capability-foundations"

if [[ ! -f "$SAMPLE_YML" ]]; then
  echo "ERROR: sample course.yml not found at: $SAMPLE_YML"
  exit 1
fi

course-engine build "$SAMPLE_YML" --out "$OUT_ROOT" --overwrite

SAMPLE_ARTEFACT="$OUT_ROOT/$SAMPLE_ID"
if [[ ! -f "$SAMPLE_ARTEFACT/manifest.json" ]]; then
  echo "ERROR: expected manifest at $SAMPLE_ARTEFACT/manifest.json"
  echo "OUT_ROOT contents:"
  find "$OUT_ROOT" -maxdepth 2 -type f -name manifest.json -print || true
  exit 1
fi

course-engine render "$SAMPLE_ARTEFACT"

echo
echo "==[ 3. Explain + snapshot: sample artefact ]============"
course-engine explain "$SAMPLE_ARTEFACT" --summary
course-engine explain "$SAMPLE_ARTEFACT" --format json > "$OUT_ROOT/sample.explain.json"

# Print key blocks (jq if available; fallback to python)
if command -v jq >/dev/null 2>&1; then
  jq '.design_intent, .ai_scoping, .declared' "$OUT_ROOT/sample.explain.json"
else
  python - <<PY
import json
p=json.load(open("$OUT_ROOT/sample.explain.json"))
print(json.dumps(p.get("design_intent"), indent=2))
print(json.dumps(p.get("ai_scoping"), indent=2))
print(json.dumps(p.get("declared"), indent=2))
PY
fi

echo
echo "==[ 3.1 Snapshot determinism (timestamp-normalised) ]===="
course-engine snapshot "$SAMPLE_ARTEFACT" --format json > "$OUT_ROOT/snap1.json"
course-engine snapshot "$SAMPLE_ARTEFACT" --format json > "$OUT_ROOT/snap2.json"

# Determinism guarantee: everything except runtime timestamps should be identical.
# Normalise generated_at_utc (and command for cross-machine stability) to avoid false diffs.
python - <<PY
import json, pathlib

def norm(path: str) -> dict:
    p = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    p["generated_at_utc"] = "<NORMALISED>"
    if "command" in p:
        p["command"] = "<NORMALISED>"
    return p

p1 = norm("$OUT_ROOT/snap1.json")
p2 = norm("$OUT_ROOT/snap2.json")

pathlib.Path("$OUT_ROOT/snap1.norm.json").write_text(json.dumps(p1, sort_keys=True, indent=2), encoding="utf-8")
pathlib.Path("$OUT_ROOT/snap2.norm.json").write_text(json.dumps(p2, sort_keys=True, indent=2), encoding="utf-8")
PY

diff "$OUT_ROOT/snap1.norm.json" "$OUT_ROOT/snap2.norm.json"

echo
echo "==[ 4. Pack (sample artefact) ]========================="
PACK_OUT="$OUT_ROOT/packs/$SAMPLE_ID-audit"
mkdir -p "$(dirname "$PACK_OUT")"
course-engine pack "$SAMPLE_ARTEFACT" --out "$PACK_OUT" --profile audit --overwrite >/dev/null
test -f "$PACK_OUT/manifest.json" && echo "pack manifest OK"
test -f "$PACK_OUT/explain.json" && echo "pack explain.json OK"
test -f "$PACK_OUT/summary.txt" && echo "pack summary.txt OK"

echo
echo "==[ 5. Optional: scenario planning course checks ]======="
SCENARIO_SRC="demo/scenario-planning-environmental-scanning/course.yml"
SCENARIO_ID="scenario-planning-environmental-scanning"

SCENARIO_ARTEFACT=""

if [[ -f "$SCENARIO_SRC" ]]; then
  echo "Found scenario source: $SCENARIO_SRC"
  course-engine build "$SCENARIO_SRC" --out "$OUT_ROOT" --overwrite
  SCENARIO_ARTEFACT="$OUT_ROOT/$SCENARIO_ID"
  test -f "$SCENARIO_ARTEFACT/manifest.json"
  course-engine render "$SCENARIO_ARTEFACT"
elif [[ -f "dist/$SCENARIO_ID/manifest.json" ]]; then
  echo "Scenario source not found; using existing artefact: dist/$SCENARIO_ID"
  SCENARIO_ARTEFACT="dist/$SCENARIO_ID"
else
  echo "(skip) scenario planning course not available as source or artefact"
fi

if [[ -n "${SCENARIO_ARTEFACT:-}" ]]; then
  course-engine explain "$SCENARIO_ARTEFACT" --summary
  course-engine explain "$SCENARIO_ARTEFACT" --format json > "$OUT_ROOT/scenario.explain.json"
  if command -v jq >/dev/null 2>&1; then
    jq '.design_intent, .ai_scoping, .declared' "$OUT_ROOT/scenario.explain.json"
  else
    python - <<PY
import json
p=json.load(open("$OUT_ROOT/scenario.explain.json"))
print(json.dumps(p.get("design_intent"), indent=2))
print(json.dumps(p.get("ai_scoping"), indent=2))
print(json.dumps(p.get("declared"), indent=2))
PY
  fi
fi

echo
echo "==[ 6. Explain (source) + legacy --json ]==============="
if [[ -f "$SCENARIO_SRC" ]]; then
  course-engine explain "$SCENARIO_SRC" --format json | python -m json.tool >/dev/null
  course-engine explain "$SCENARIO_SRC" --format text | head -n 60
  course-engine explain "$SCENARIO_SRC" --json | python -m json.tool >/dev/null
else
  echo "(skip) source explain: demo scenario course.yml not present"
fi

echo
echo "==[ 7. Policy explain sanity check ]===================="
# NOTE: validate uses --json (no --format flag in v1.21.0).
# This is a schema/parse sanity check only; output is discarded.
course-engine validate "$SAMPLE_ARTEFACT" \
  --policy preset:baseline \
  --profile baseline \
  --explain \
  --json | python -m json.tool >/dev/null

echo
echo "==[ 8. Git status check (informational) ]==============="
git status

echo
echo "==[ 8.1 Working tree clean? (informational) ]==========="
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "NOTE: working tree has uncommitted changes."
fi

echo
echo "✅ ALL CHECKS COMPLETED SUCCESSFULLY"
echo "Course Engine v${ENGINE_VERSION} is verified, stable, and governance-ready."
