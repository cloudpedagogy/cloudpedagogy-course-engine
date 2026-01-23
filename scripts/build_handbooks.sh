#!/usr/bin/env bash
set -euo pipefail

OUT="docs/handbook"
mkdir -p "$OUT"

# --------------------------------------------------
# Handbook A — Course Engine Handbook
# --------------------------------------------------

quarto render docs/course-engine-handbook.md --to docx
quarto render docs/course-engine-handbook.md --to pdf

mv docs/course-engine-handbook.docx "$OUT/"
mv docs/course-engine-handbook.pdf  "$OUT/"

# --------------------------------------------------
# Handbook B — Course Engine Design & Rationale
# --------------------------------------------------

quarto render docs/course-engine-design-rationale.md --to docx
quarto render docs/course-engine-design-rationale.md --to pdf

mv docs/course-engine-design-rationale.docx "$OUT/"
mv docs/course-engine-design-rationale.pdf  "$OUT/"

echo "✔ Handbooks regenerated from canonical Markdown"
