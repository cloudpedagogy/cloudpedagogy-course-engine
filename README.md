# CloudPedagogy Course Engine (v1.7)

A Python-first, Quarto-backed **course compiler** that generates consistent, auditable learning artefacts from a single `course.yml` source of truth.

This tool is designed for **reproducible course production** in educator, learning design, QA, and governance contexts.

---

## What it does

- Treats `course.yml` as the **single source of truth**
- Validates course structure and metadata
- Compiles publishable artefacts via templates
- Produces **auditable, reproducible outputs** with a machine-readable `manifest.json`
- Defaults to **non-destructive builds** (explicit `--overwrite` required)
- Supports optional **capability mapping metadata** for governance and audit (v1.1)
- Supports **external lesson source files with provenance tracking** (v1.6)

---

## What’s new in v1.6

v1.6 introduces **first-class support for authoring lessons as external source files**, while preserving deterministic, auditable builds.

New in v1.6:

- Lessons may be authored as standalone `.md` or `.qmd` files using `source:`
- Strict guardrails prevent ambiguous lesson definitions
- Lesson source provenance (paths and SHA-256 hashes) is recorded in `manifest.json`
- Invalid course layouts fail fast with explicit, actionable errors

No new build modes or CLI flags were added.

---

## What’s new in v1.7

v1.7 is a **stability and clarity release**. It does not introduce new build modes, enforcement logic, or automation.

The focus of this release is to make existing, real-world authoring workflows **explicit, predictable, and governance-safe**, based on lessons learned from v1.6.

New in v1.7:

- Formalised expectations for the authoring pipeline (documentation-only)
- Explicit recognition of lesson-splitting as a supported authoring utility
- Optional lesson display labels for academic referencing (informational only)
- Consolidated lesson-level navigation and in-page TOC behaviour
- Improved inspection clarity for QA and review contexts

There are **no schema changes** and **no breaking changes** in this release.

---

## Outputs

- Multi-page Quarto website (project build + `quarto render`)
- Single-page HTML handout
- Print-ready PDF handout (via Quarto + TinyTeX/LaTeX)
- Markdown export package

---

## Install (dev)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

---

## Quickstart

Preflight checks (recommended):

```bash
course-engine check
```

Build a website (example):

```bash
course-engine build examples/sample-course/course.yml --out dist --overwrite
course-engine render dist/sample-course
```

Build a PDF handout (example):

```bash
course-engine build examples/sample-course/course.yml --format pdf --out dist --overwrite
course-engine render dist/sample-course-pdf
```

Inspect build metadata:

```bash
course-engine inspect dist/sample-course-pdf
```

---

## CLI commands

- **`init`** – Scaffold a new course project
- **`build`** – Compile `course.yml` into an output package
- **`render`** – Run Quarto to render the built package
- **`inspect`** – Show build metadata (manifest summary)
- **`report`** – Generate a capability coverage report from build outputs (v1.2)
- **`validate`** – Validate or explain capability policy resolution (v1.3 / v1.5)
- **`clean`** – Remove generated artefacts safely
- **`check`** – Run dependency preflight checks (Quarto / TinyTeX where relevant)

---

## Capability mapping (v1.1)

Course Engine supports optional, **informational capability mapping metadata**.

This allows a course to declare how its content aligns to capability domains
(e.g. an AI capability framework) without enforcing compliance at build time.

In v1.1, capability mapping is:

- optional
- non-enforced (informational only)
- intended for governance, QA, and audit contexts

---

## Capability coverage reporting (v1.2)

In v1.2, Course Engine adds **capability coverage reporting**.

This moves capability mapping from *declared metadata* to a **defensible, auditable view of coverage and gaps**.

The reporting system:

- reads capability mapping data from `manifest.json`
- summarises coverage and evidence per domain
- flags domains with no declared coverage or evidence
- produces **human-readable**, **verbose**, or **JSON** output

Reporting examples (CLI):

```bash
course-engine report dist/sample-course
course-engine report dist/sample-course --verbose
course-engine report dist/sample-course --json
```

Capability mapping example (`course.yml`):

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

---

## Capability validation (v1.3)

In v1.3, Course Engine introduces **capability mapping defensibility validation**.

This allows declared capability mappings to be checked against explicit rules, supporting assurance, audit, and governance workflows.

Validation operates on the generated `manifest.json` and does **not modify builds**.

Validation rules focus on presence, traceability, and consistency — not pedagogical quality or effectiveness.

---

## Policy explain mode (v1.5)

In v1.5, Course Engine introduces an **explain-only policy resolution mode**.

This allows policies and profiles to be resolved, inspected, and consumed by external tools **without requiring a built course or `manifest.json`**.

Explain mode is:

- explain-only (no validation executed)
- safe for CI, dashboards, and automation
- machine-readable via JSON output
- compatible with preset and file-based policies

Explain examples (CLI):

```bash
course-engine validate /tmp   --policy preset:baseline   --profile baseline   --explain   --json
```

Validation modes:

- **Non-strict (default)**  
  Reports warnings and informational issues without failing. Suitable for review, QA, and iterative design.

- **Strict mode**  
  Treats unmet rules as errors and exits with a non-zero status. Suitable for automated QA or CI gating.

Validation examples (CLI):

```bash
course-engine validate dist/sample-course
course-engine validate dist/sample-course --strict
```

For guidance on configuring thresholds using policy files and profiles, see:

- `docs/POLICY_FILES.md`

---

## External lesson authoring (v1.6)

From v1.6, lessons may be authored **either inline** or as **external source files**.

Lessons must define **exactly one of**:

- `content_blocks` (inline YAML authoring), or
- `source` (external Markdown or Quarto file)

Example:

```yaml
structure:
  modules:
    - id: module-1
      title: Foundations
      lessons:
        - id: lesson-01
          title: "Optional explicit title"
          source: content/lessons/lesson-01.md
```

Behaviour:

- `source:` paths are resolved relative to the `course.yml` location
- Lesson titles are resolved from:
  1. an explicit `title:` in `course.yml` (if provided), or
  2. the first Markdown H1 (`# Heading`) in the source file
- Source files are injected internally as a single Markdown content block
- Invalid combinations fail fast with clear, actionable errors
- Lesson source provenance is recorded in `manifest.json` under `lesson_sources` (informational)

See **End User Instructions (v1.6)** for full authoring rules and examples:

- `docs/END_USER_INSTRUCTIONS.md`

---

## Alignment

This project is intended to be:

- **Framework-aligned** — courses can declare framework and capability-domain alignment
- **Capability-Driven Development (CDD)-aligned** — intent-first specifications, auditability, and non-destructive builds

Reports and validation are informational by default and do not block builds unless strict validation is explicitly enabled.

---

## Versioning and evolution

The Course Engine evolves incrementally through minor and patch releases.

New capabilities are added conservatively, with an emphasis on:

- backward compatibility
- non-destructive defaults
- preserving human judgement and governance boundaries

Detailed change history is maintained in `CHANGELOG.md`.

---

## Course Builder Handbook

A detailed, governance-aware guide to the intent, design principles, capabilities, boundaries, and responsible use of the Course Engine is available in:

- `docs/course-builder-handbook.md`

This Markdown file is the **canonical source** of the handbook.

Derived versions for distribution and reference are also available in:

- `docs/handbook/`

These include Word and PDF formats generated from the Markdown source.

---

## Course Builder Design & Rationale

A separate design record documenting the principles, architectural decisions, and deliberate trade-offs behind the Course Engine is available in:

- `docs/course-builder-design-rationale.md`

Design decisions specific to v1.6 are documented in:

- `docs/v1.6-design.md`

---

## Disclaimer

The CloudPedagogy Course Engine is a technical tool for compiling, inspecting, and reviewing course artefacts in a transparent and reproducible manner.

It does not evaluate pedagogical quality, academic merit, or educational effectiveness, and it does not replace institutional governance processes, academic judgement, or professional review.

Capability mapping, reporting, and validation features are informational by default and are intended to support reflection, assurance, and audit workflows — not to enforce compliance or determine approval outcomes.

All outputs should be interpreted in context and alongside appropriate academic, professional, and institutional judgement.

---

## Licensing & scope

The CloudPedagogy Course Engine is open-source infrastructure released under the MIT License.

CloudPedagogy frameworks, capability models, profiles, taxonomies, and training materials are separate works and may be licensed differently.

This repository focuses on providing transparent, auditable tooling for course production and review, without embedding or enforcing any specific framework.

---

## About CloudPedagogy

CloudPedagogy develops open, governance-credible resources for building confident, responsible AI capability across education, research, and public service.

- Website: https://www.cloudpedagogy.com/
- Framework repo: https://github.com/cloudpedagogy/cloudpedagogy-ai-capability-framework
