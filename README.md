# CloudPedagogy Course Engine (v1.1)

A Python-first, Quarto-backed **course compiler** that generates consistent, auditable learning artefacts from a single `course.yml` source of truth.

This tool is designed for **reproducible course production** in educator, learning design, QA, and governance contexts.

## What it does

- Treats `course.yml` as the **single source of truth**
- Validates course structure and metadata
- Generates publishable artefacts via templates
- Produces **auditable, reproducible outputs** with a machine-readable (`manifest.json`)
- Defaults to **non-destructive builds** (explicit `--overwrite` required)

## Outputs

- Multi-page Quarto website
- Single-page HTML handout
- Print-ready PDF (via Quarto + TinyTeX/LaTeX)
- Markdown export package

## Install (dev)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
## Quickstart

Preflight checks (recommended):

```bash
course-engine check
```
Build a website:

```bash
course-engine build examples/sample-course/course.yml --out dist --overwrite
course-engine render dist/ai-capability-foundations
```

Build a PDF handout:

```bash
course-engine build examples/sample-course/course.yml --format pdf --out dist --overwrite
course-engine render dist/ai-capability-foundations-pdf
```

Inspect build metadata:
```bash
course-engine inspect dist/ai-capability-foundations-pdf
```

## CLI Commands

- **`init`** – Scaffold a new course project
- **`build`** – Compile `course.yml` into an output package
- **`render`** – Run Quarto to render the built package
- **`inspect`** – Show build metadata (manifest summary)
- **`clean`** – Remove generated artefacts safely
- **`check`** – Run dependency preflight checks (Quarto / TinyTeX where relevant)

## Alignment

This project is intended to be:

- **Framework-aligned** – Courses can declare framework and capability-domain alignment
- **Capability-Driven Development (CDD)-aligned** – Intent-first specifications, auditability, and non-destructive builds


