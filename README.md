# CloudPedagogy Course Engine (v1.2)

A Python-first, Quarto-backed **course compiler** that generates consistent, auditable learning artefacts from a single `course.yml` source of truth.

This tool is designed for **reproducible course production** in educator, learning design, QA, and governance contexts.

## What it does

- Treats `course.yml` as the **single source of truth**
- Validates course structure and metadata
- Generates publishable artefacts via templates
- Produces **auditable, reproducible outputs** with a machine-readable `manifest.json`
- Defaults to **non-destructive builds** (explicit `--overwrite` required)
- Supports optional **capability mapping metadata** for governance and audit (v1.1)

## Capability Mapping (v1.1)

Course Engine supports optional, **informational capability mapping metadata**.

This allows a course to declare how its content aligns to capability domains
(e.g. an AI capability framework) without enforcing compliance at build time.

In v1.1, capability mapping is:

- optional
- non-enforced (informational only)
- intended for governance, QA, and audit contexts

## Capability Coverage Reporting (v1.2)

In v1.2, Course Engine adds **capability coverage reporting**.

This moves capability mapping from *declared metadata* to a
**defensible, auditable view of coverage and gaps**.

The reporting system:

- reads capability mapping data from `manifest.json`
- summarises coverage and evidence per domain
- flags domains with no declared coverage or evidence
- produces **human-readable**, **verbose**, or **JSON** output

Coverage reporting supports review and assurance workflows but does not infer quality or completeness.


### Reporting examples (CLI)

```bash
course-engine report dist/ai-capability-foundations
course-engine report dist/ai-capability-foundations --verbose
course-engine report dist/ai-capability-foundations --json
```

### Capability mapping example (course.yml)

```yaml
capability_mapping:
  framework: "CloudPedagogy AI Capability Framework (2026 Edition)"
  version: "2026"
  domains:
    awareness:
      label: "AI Awareness & Orientation"
      intent: "Introduce foundational concepts and shared vocabulary."
      coverage: ["m1"]
      evidence: ["lesson:l1", "learning_objectives"]
```

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
- **`report`** – Generate a capability coverage report from build outputs (v1.2)
- **`clean`** – Remove generated artefacts safely
- **`check`** – Run dependency preflight checks (Quarto / TinyTeX where relevant)


## Alignment

This project is intended to be:

- **Framework-aligned** – Courses can declare framework and capability-domain alignment
- **Capability-Driven Development (CDD)-aligned** – Intent-first specifications, auditability, and non-destructive builds

Reports are informational by default and do not block builds or enforce compliance.

## Licensing & Scope

The CloudPedagogy Course Engine is open-source infrastructure released under the
MIT License.

CloudPedagogy frameworks, capability models, profiles, taxonomies, and training
materials are separate works and may be licensed differently.

This repository focuses on providing transparent, auditable tooling for course
production and review, without embedding or enforcing any specific framework.
