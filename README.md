# CloudPedagogy Course Engine (v1.5)

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
Coverage reporting supports review and assurance workflows but does not infer quality or completeness.

## Capability Validation (v1.3)

In v1.3, Course Engine introduces **capability mapping defensibility validation**.

This allows declared capability mappings to be checked against explicit rules,
supporting assurance, audit, and governance workflows.

Validation operates on the generated `manifest.json` and does **not modify builds**.

Validation rules focus on presence, traceability, and consistency, not pedagogical quality or effectiveness.

## Policy Explain Mode (v1.5)

In v1.5, Course Engine introduces an **explain-only policy resolution mode**.

This allows policies and profiles to be resolved, inspected, and consumed by
external tools **without requiring a built course or `manifest.json`**.

Explain mode is:

- explain-only (no validation executed)
- safe for CI, dashboards, and automation
- machine-readable via JSON output
- compatible with preset and file-based policies

### Explain examples (CLI)

Explain a preset policy and profile:

```bash
course-engine validate /tmp \
  --policy preset:baseline \
  --profile baseline \
  --explain \
  --json
```


### Validation modes

- **Non-strict (default)**  
  Reports warnings and informational issues without failing.
  Suitable for review, QA, and iterative design.

- **Strict mode**  
  Treats unmet rules as errors and exits with a non-zero status.
  Suitable for automated QA, compliance checks, or CI pipelines.

### Validation examples (CLI)

```bash
course-engine validate dist/ai-capability-foundations
```
Strict validation:

```bash
course-engine validate dist/ai-capability-foundations --strict
```

Validation results are human-readable by default and designed to support
transparent, defensible review rather than automated grading or scoring.

For guidance on configuring validation thresholds using policy files and profiles,
see [`docs/POLICY_FILES.md`](docs/POLICY_FILES.md).

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
- **`validate`** – Validate or explain capability policy resolution (v1.3 / v1.5)
- **`clean`** – Remove generated artefacts safely
- **`check`** – Run dependency preflight checks (Quarto / TinyTeX where relevant)


## Alignment

This project is intended to be:

- **Framework-aligned** – Courses can declare framework and capability-domain alignment
- **Capability-Driven Development (CDD)-aligned** – Intent-first specifications, auditability, and non-destructive builds

Reports and validation are informational by default and do not block builds unless strict validation is explicitly enabled.

---

## Versioning and Evolution

The Course Engine evolves incrementally through minor and patch releases.

New capabilities are added conservatively, with an emphasis on:
- backward compatibility
- non-destructive defaults
- preserving human judgement and governance boundaries

Versioned features are documented inline (e.g. v1.1, v1.2, v1.5), while detailed change history is maintained in `CHANGELOG.md`.

The design principles described in this README are intended to remain stable, even as capabilities expand.

---

## Course Builder Handbook

A detailed, governance-aware guide to the intent, design principles, capabilities, boundaries, and responsible use of the Course Engine is available in:

`docs/course-builder-handbook.md`

This Markdown file is the **canonical source** of the handbook.

Derived versions for distribution and reference are also available in:

`docs/handbook/`

These include Word and PDF formats generated from the Markdown source.

The handbook is intended for educators, learning designers, technologists, and institutions who are accountable for AI-supported course and curriculum design decisions.


---

## Disclaimer

The CloudPedagogy Course Engine is a technical tool for compiling, inspecting,
and reviewing course artefacts in a transparent and reproducible manner.

It does not evaluate pedagogical quality, academic merit, or educational
effectiveness, and it does not replace institutional governance processes,
academic judgement, or professional review.

Capability mapping, reporting, and validation features are informational by
default and are intended to support reflection, assurance, and audit workflows,
not to enforce compliance or determine approval outcomes.

All outputs should be interpreted in context and alongside appropriate academic,
professional, and institutional judgement.


---

## Licensing & Scope

The CloudPedagogy Course Engine is open-source infrastructure released under the
MIT License.

CloudPedagogy frameworks, capability models, profiles, taxonomies, and training
materials are separate works and may be licensed differently.

This repository focuses on providing transparent, auditable tooling for course
production and review, without embedding or enforcing any specific framework.

---

## About CloudPedagogy

CloudPedagogy develops open, governance-credible resources for building confident, responsible AI capability across education, research, and public service.

- Website: https://www.cloudpedagogy.com/
- Framework: https://github.com/cloudpedagogy/cloudpedagogy-ai-capability-framework

