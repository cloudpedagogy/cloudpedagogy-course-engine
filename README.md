# CloudPedagogy Course Engine (v1.11.0)

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
- Supports **explain-only policy resolution** (read-only) for CI, dashboards, and QA workflows via `validate --explain --json` (v1.10+)

---

## What’s new in v1.11

v1.11 is a **governance adoption and documentation hardening** release.

It focuses on making policy validation and explainability **easy to operationalise** in QA, CI, and audit workflows without changing build behaviour.

### Highlights

- **Demo course includes defensible capability mapping**
  - The scenario-planning demo now declares both `framework_alignment` (intent) and `capability_mapping` (coverage and evidence), enabling end-to-end QA demonstrations.

- **Policy validation guidance clarified**
  - `docs/POLICY_FILES.md` explicitly documents:
    - what policy validation evaluates (structure only),
    - the requirement for `capability_mapping`,
    - and how profiles and thresholds are resolved.

- **Explainability JSON contract documented**
  - A stable, machine-readable contract for policy resolution output is now documented:
    - `docs/explainability-json-contract.md`
  - Intended for CI pipelines, dashboards, and governance tooling.

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

Explain resolved validation rules (no validation executed; read-only):

```bash
course-engine validate dist/<course> --policy preset:strict-ci --explain --json
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

Capability coverage reporting provides a **defensible view of coverage and gaps**
based on declared capability mapping.

The reporting system:

- reads capability mapping data from `manifest.json`
- summarises coverage and evidence per domain
- flags domains with no declared coverage or evidence
- produces **human-readable**, **verbose**, or **JSON** output

Examples:

```bash
course-engine report dist/sample-course
course-engine report dist/sample-course --verbose
course-engine report dist/sample-course --json
```

---

## Capability validation (v1.3+)

Capability validation checks declared capability mappings against **explicit, user-defined rules**.

Validation:

- operates on `manifest.json`
- never modifies builds
- evaluates declared structure only (not pedagogical quality)

Policies and profiles are documented in:

- `docs/POLICY_FILES.md`

---

## Explain-only policy resolution (v1.5+)

Explain mode resolves policies and profiles **without executing validation**.

This mode is:

- read-only
- safe for CI and automation
- available as stable JSON output

```bash
course-engine validate dist/course \
  --policy policies/my-policy.yml \
  --profile strict-ci \
  --explain \
  --json
```

The JSON contract is documented in:

- `docs/explainability-json-contract.md`

---

## External lesson authoring (v1.6+)

Lessons may be authored **inline** or as **external source files**.

Each lesson must define **exactly one of**:

- `content_blocks` (inline YAML authoring), or
- `source` (external Markdown or Quarto file)

Example:

```yaml
lessons:
  - id: lesson-01
    title: "Optional explicit title"
    source: content/lessons/lesson-01.md
```

---

## Versioning and evolution

The Course Engine evolves conservatively through minor releases, prioritising:

- backward compatibility
- non-destructive defaults
- governance safety

Detailed history is maintained in `CHANGELOG.md`.

---

## Documentation

- **Course Engine Handbook:** `docs/course-engine-handbook.md`
- **Design & Rationale:** `docs/course-engine-design-rationale.md`
- **Policy files guide:** `docs/POLICY_FILES.md`
- **Explainability JSON contract:** `docs/explainability-json-contract.md`
- **Release notes:** `docs/releases/`

Derived Word and PDF artefacts (where available) are in:

- `docs/handbook/`

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

## Attribution & citation (optional)

If you use the **CloudPedagogy Course Engine** in academic, institutional, or published work, you are encouraged (but not required) to acknowledge its use.

**Suggested wording (optional):**

> “This work was produced using the CloudPedagogy Course Engine.”

---

## About CloudPedagogy

CloudPedagogy develops governance-credible resources for building confident,
responsible AI capability across education, research, and public service.

- Website: https://www.cloudpedagogy.com/
- Framework repository: https://github.com/cloudpedagogy/cloudpedagogy-ai-capability-framework
