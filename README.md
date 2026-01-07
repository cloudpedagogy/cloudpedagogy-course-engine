# Course Engine (v0.1)

A Python-first, Quarto-backed course production engine designed to generate consistent, reproducible e-learning course artefacts from a structured `course.yml`.

## Why this exists
- **Consistency:** one course spec → deterministic outputs
- **Maintainability:** update once, regenerate cleanly
- **Extensibility:** plugin hooks for validation, lineage, adaptation (and later agentic workflows)

## Install (dev)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Quickstart
```bash
course-engine build examples/sample-course/course.yml --out dist
# optional (requires Quarto installed):
course-engine render dist/ai-capability-foundations
```

## Alignment
This project is intended to be:
- **AI Capability Framework-aligned** (capability outcomes and governance lenses)
- **Capability-Driven Development-aligned** (intent-first specs, validation, modularity, extensibility)
