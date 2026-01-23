# CloudPedagogy Course Engine (v1.14.0)

A Python-first, Quarto-backed **course compiler** that generates consistent, auditable learning artefacts from a single `course.yml` source of truth.

The Course Engine is designed for **reproducible course production** in educator, learning design, quality assurance (QA), and academic governance contexts.

It prioritises **determinism, transparency, and explainability** over automation or enforcement.


---

## What it does

- Treats `course.yml` as the **single source of truth**
- Validates course structure and metadata
- Compiles publishable artefacts via templates
- Produces **auditable, reproducible outputs** with a machine-readable `manifest.json`
- Records declared **design intent** (rationale, AI positioning, governance context) and surfaces it in `manifest.json` and `course-engine explain` (v1.12)
- Defaults to **non-destructive builds** (explicit `--overwrite` required)
- Supports optional **capability mapping metadata** for governance and audit (v1.1)
- Supports **external lesson source files with provenance tracking** (v1.6)
- Supports **explain-only policy resolution** (read-only) for CI, dashboards, and QA workflows via `validate --explain --json` (v1.10+)

---

## Why this matters

Universities increasingly need to demonstrate **how** and **why** courses are designed — particularly where AI, capability frameworks, or external expectations are involved — without turning curriculum design into a compliance exercise.  

The **CloudPedagogy Course Engine** provides a practical middle ground: it makes **design intent**, **structural decisions**, and **declared alignments** explicit, inspectable, and reproducible, while deliberately avoiding automated judgement or enforcement.  

This supports **quality assurance, audit, and review conversations** with clearer evidence, reduced ambiguity, and lower operational risk — **without constraining academic autonomy or pedagogical practice**.

---

## What’s new in v1.14

v1.14 is a **stability and governance-credibility release**.

It introduces **no new schema, validation rules, or enforcement behaviour**.
Instead, it focuses on ensuring that versioning, release verification, and
governance artefacts are **consistent, reproducible, and defensible**.

### Highlights

- **Version alignment hardened**
  - CLI version, Python package version, and build metadata are now fully aligned
    and verifiable prior to release.

- **Release verification workflow clarified**
  - A dedicated maintainer script (`scripts/verify-release.sh`) provides
    end-to-end release assurance covering tests, demo builds, manifests,
    explain output, and policy resolution.
  - This supports institutional QA, audit, and external review workflows.

- **Repository hygiene improved**
  - Ignore rules clarified to prevent accidental masking of tracked content.
  - Build artefacts and local caches are cleanly separated from source control.

This release is intended to **increase trust and confidence** in the Course Engine
without changing its behaviour or governance posture.


---

## What’s new in v1.13

v1.13 refines Course Engine’s governance model by introducing **explicit absence signalling**
and **structural AI scoping**, completing the separation between:

- *declared intent*,
- *inspectable structure*, and
- *policy interpretation*.

This release focuses on **reducing governance ambiguity and validation noise**
without increasing enforcement or automation.

### Highlights

- **Absence signals introduced (manifest v1.4.0)**
  - The engine now records *absence conditions* (e.g. missing design intent, missing mapping)
    as **explicit, inspectable signals**.
  - Signals are:
    - informational by default,
    - deterministic,
    - non-scoring and non-comparative.
  - Signals are recorded in `manifest.json` and interpreted by policies — never enforced by the engine itself.

- **Structured AI scoping metadata (`ai_scoping`)**
  - Courses may now declare **explicit AI use boundaries** separately from narrative design intent.
  - This resolves ambiguity where AI positioning existed but no inspectable scope was declared.
  - When present, AI scoping suppresses the advisory signal for missing AI boundaries.

- **Policy-controlled signal interpretation**
  - Policies now define how signals are treated (`ignore`, `info`, `warn`, `error`),
    enabling:
    - quiet authoring defaults,
    - stricter CI gates,
    - transparent QA review.
  - Signal interpretation is explainable and inspectable via
    `course-engine validate --explain --json`.

- **Validation noise reduction**
  - Well-scoped courses now validate cleanly under strict profiles.
  - Governance issues are surfaced only when structurally meaningful.

These changes complete the **governance contract**:
the engine computes facts, policies interpret them, and institutions decide how to act.

---

## What’s new in v1.12

v1.12 introduces **explicit design intent capture** as a first-class governance signal.

Courses may now declare *why* design choices were made — including AI positioning,
framework references, and review context — without affecting build behaviour.

### Highlights

- **Design intent block added to `course.yml`**
  - Optional, informational metadata capturing rationale, AI use boundaries, and governance context.

- **Manifest upgraded (v1.3.0)**
  - Design intent is recorded with a stable hash and summary for auditability.

- **Explain output enhanced**
  - `course-engine explain` surfaces design intent in both JSON and human-readable reports.

This change strengthens transparency and audit readiness without introducing
validation or enforcement.

---

## What’s new in v1.11

v1.11 was a **governance adoption and documentation hardening** release.

It focused on making policy validation and explainability **easy to operationalise** in QA, CI, and audit workflows without changing build behaviour.

### Highlights

- **Demo course includes defensible capability mapping**
  - The scenario-planning demo declares both `framework_alignment` (intent) and `capability_mapping` (coverage and evidence), enabling end-to-end QA demonstrations.

- **Policy validation guidance clarified**
  - `docs/POLICY_FILES.md` documents:
    - what policy validation evaluates (structure only),
    - the requirement for `capability_mapping`,
    - and how profiles and thresholds are resolved.

- **Explainability JSON contract documented**
  - A stable, machine-readable contract for policy resolution output:
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
course-engine validate dist/course   --policy policies/my-policy.yml   --profile strict-ci   --explain   --json
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

## Design intent (v1.12)

Course Engine supports an optional `design_intent` block in `course.yml`.

Design intent allows authors to declare:

- the rationale behind course design choices,
- how (and where) AI is positioned or constrained,
- relevant frameworks or policy contexts,
- review cadence and evolution expectations.

Design intent is:

- optional
- informational (not enforced)
- recorded in `manifest.json`
- surfaced via `course-engine explain`

It is intended to support **audit, QA, and governance conversations**
without inspecting lesson content or evaluating pedagogical quality.

From v1.13 onward, structural AI scoping is recorded separately from design intent,
allowing narrative rationale and inspectable boundaries to evolve independently.

---

## Versioning and evolution

The Course Engine evolves conservatively through minor releases, prioritising:

- backward compatibility
- non-destructive defaults
- governance safety

Detailed history is maintained in `CHANGELOG.md`.

---

## Documentation

- **Course Engine Handbook:** `docs/course-engine-handbook.md` (includes design intent and governance metadata)
- **Design & Rationale:** `docs/course-engine-design-rationale.md`
- **Policy files guide:** `docs/POLICY_FILES.md`
- **Explainability JSON contract:** `docs/explainability-json-contract.md`
- **Release notes:** `docs/releases/`
- **AI scoping & governance notes:** `docs/releases/v1.13.1-ai-scoping.md`
- **Maintainer release verification:** see `scripts/verify-release.sh` and
  Section 12 of `END_USER_INSTRUCTIONS.md`


Derived Word and PDF artefacts (where available) are in:

- `docs/handbook/`

---

## Disclaimer

The CloudPedagogy Course Engine is a technical tool for compiling, inspecting,
and explaining course artefacts.

It records declared intent and structure for transparency, but does **not**
evaluate pedagogical quality or replace institutional governance processes.

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
