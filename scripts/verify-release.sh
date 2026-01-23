# Purpose:
# Maintainer-facing pre-release verification.
# Run before merging to master or tagging a release.
# Not intended for routine development use.


#!/usr/bin/env bash
set -e

echo "==[ 0. Environment check ]=============================="
which course-engine
ENGINE_VERSION="$(course-engine --version | tr -d '[:space:]')"
echo "course-engine version: $ENGINE_VERSION"
python -c "import course_engine; print('python package version:', course_engine.__version__)"

echo
echo "==[ 1. Static analysis & tests ]========================"
ruff check .
mypy src
pytest -q

echo
echo "==[ 2. Build demo course ]=============================="
course-engine build demo/scenario-planning-environmental-scanning/course.yml \
  --out dist --overwrite

echo
echo "==[ 3. Inspect build artefact ]========================="
course-engine inspect dist/scenario-planning-environmental-scanning

echo
echo "==[ 4. Explain (source, default JSON) ]================="
course-engine explain demo/scenario-planning-environmental-scanning/course.yml \
  | head -n 40

echo
echo "==[ 5. Explain (source, text) ]========================="
course-engine explain demo/scenario-planning-environmental-scanning/course.yml \
  --format text | head -n 60

echo
echo "==[ 6. Explain (artefact, text) ]======================="
course-engine explain dist/scenario-planning-environmental-scanning \
  --format text | head -n 60

echo
echo "==[ 7. Legacy --json compatibility check ]=============="
course-engine explain demo/scenario-planning-environmental-scanning/course.yml \
  --json | head -n 20

echo
echo "==[ 8. Policy explain sanity check ]===================="
course-engine validate /tmp \
  --policy preset:baseline \
  --profile baseline \
  --explain \
  --json | head -n 40

echo
echo "==[ 9. Git status check (informational) ]==============="
git status

echo
echo "✅ ALL CHECKS COMPLETED SUCCESSFULLY"
echo "Course Engine v${ENGINE_VERSION} is verified, stable, and governance-ready."
