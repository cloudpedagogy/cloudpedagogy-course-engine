# CloudPedagogy Course Engine (v1.10.0)

A Python-first, Quarto-backed **course compiler** that generates consistent, auditable learning artefacts from a single `course.yml` source of truth.

The Course Engine is designed for **reproducible course production** in educator, learning design, quality assurance (QA), and academic governance contexts.

It prioritises **determinism, transparency, and explainability** over automation or enforcement.

---

## What it does

- Treats `course.yml` as the **single source of truth**
- Validates course structure and metadata
- Compiles publishable artefacts via templates
- Produces **auditable, reproducible outputs** with a machine-readable `manifest.json`
- Defaults to **non-destructive builds** (explicit `--overwrite` required)
- Supports optional **capability mapping metadata** for governance and audit (v1.1)
- Supports **external lesson source files with provenance tracking** (v1.6)
- Supports **explain-only inspection workflows** without building (v1.8+)

---

## What’s new in v1.10

v1.10 is a **polish, clarity, and interface-hardening release**.

It introduces no new build modes, schemas, or enforcement behaviour.
Instead, it finalises the **explainability and governance interfaces** introduced in earlier versions.

### Highlights

- **Clear, unambiguous explain output selection**
  - `--format json|text` is now the preferred interface
  - `--json` is retained as a **legacy / compatibility flag**
- **Explain determinism confirmed**
  - Only runtime timestamps vary
  - All structural and provenance data is stable and diff-friendly
- **Improved CLI semantics and help text**
  - Explicit signalling of defaults and overrides
  - Reduced ambiguity for CI, QA, and automation contexts
- **Type safety and static analysis hardened**
  - Clean `ruff`, `mypy`, and `pytest` runs across the codebase
- **Documentation alignment**
  - README, CLI behaviour, and explain output now tell a single, coherent story

v1.10 marks the point at which **explainability is no longer experimental**, but a stable, governance-ready capability.

---

## Outputs

- Multi-page Quarto websites
- Single-page HTML handouts
- Print-ready PDF handouts (via Quarto + TinyTeX/LaTeX)
- Portable Markdown export packages

---

## Quickstart

Preflight checks (recommended):

```bash
course-engine check
```

Build a website:

```bash
course-engine build examples/sample-course/course.yml --out dist --overwrite
course-engine render dist/sample-course
```

Explain a course (no build required; read-only):

```bash
course-engine explain course.yml --format json
```

---

## CLI commands

- **init** – Scaffold a new course project
- **build** – Compile `course.yml` into an output package
- **render** – Render outputs with Quarto
- **inspect** – Summarise build metadata
- **explain** – Explain course structure and provenance
- **report** – Generate capability coverage reports
- **validate** – Validate or explain policy resolution
- **clean** – Remove generated artefacts safely
- **check** – Run dependency preflight checks

---

## Capability mapping (v1.1)

Course Engine supports optional, **informational capability mapping metadata**.

This allows a course to declare how its content aligns to capability domains
(e.g. an AI capability framework) without enforcing compliance at build time.

Capability mapping is:

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

Reporting examples:

```bash
course-engine report dist/sample-course
course-engine report dist/sample-course --verbose
course-engine report dist/sample-course --json
```

---

## Capability validation (v1.3)

In v1.3, Course Engine introduces **capability mapping defensibility validation**.

This allows declared capability mappings to be checked against explicit rules, supporting assurance, audit, and governance workflows.

Validation operates on the generated `manifest.json` and does **not modify builds**.

---

## Policy explain mode (v1.5)

In v1.5, Course Engine introduces an **explain-only policy resolution mode**.

This allows policies and profiles to be resolved, inspected, and consumed by external tools **without requiring a built course or `manifest.json`**.

Explain mode is:

- explain-only (no validation executed)
- safe for CI, dashboards, and automation
- machine-readable via JSON output

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

---

## Explainability (v1.8)

v1.8 introduces **first-class explainability** for `course.yml`, enabling
governance, review, and audit workflows **without executing builds**.

Explain output is designed to be:

- stable
- diff-friendly
- machine-consumable

---

## Versioning and evolution

The Course Engine evolves conservatively through minor releases, prioritising:

- backward compatibility
- non-destructive defaults
- governance safety

Detailed history is maintained in `CHANGELOG.md`.

---

## Course Engine Handbook

A detailed, governance-aware guide is available in:

- `docs/course-engine-handbook.md`

Derived Word and PDF versions are available in:

- `docs/handbook/`

---

## Course Engine Design & Rationale

Design principles and architectural decisions are documented in:

- `docs/course-engine-design-rationale.md`
- `docs/v1.6-design.md`

---

## Disclaimer

The CloudPedagogy Course Engine is a technical tool for compiling, inspecting,
and explaining course artefacts.

It does **not** evaluate pedagogical quality or replace institutional governance processes.

---

## Licensing

- Course Engine code: **MIT License**
- CloudPedagogy frameworks and models: licensed separately

---

## Attribution & Citation (Optional)

If you use the **CloudPedagogy Course Engine** in **academic, institutional, or published work**, you are encouraged (but not required) to acknowledge its use or cite the repository.

This software is released under the MIT Licence, which **does not require public attribution** beyond retaining the licence text in redistributions. However, acknowledgement helps support the ongoing development of open, governance-aware educational tooling.

**Suggested acknowledgement wording (optional):**

> “This work was produced using the CloudPedagogy Course Engine.”

or

> “Course materials were compiled using the CloudPedagogy Course Engine (MIT Licence).”

Where appropriate, you may also cite or link to the project repository.


---

## About CloudPedagogy

CloudPedagogy develops governance-credible resources for building confident,
responsible AI capability across education, research, and public service.

- Website: https://www.cloudpedagogy.com/
- Framework repo: https://github.com/cloudpedagogy/cloudpedagogy-ai-capability-framework
