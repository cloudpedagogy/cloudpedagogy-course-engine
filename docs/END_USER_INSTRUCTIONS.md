# End User Instructions  
**course-engine v1.17.0**

---

## 1. What is `course-engine`?

`course-engine` is a command-line tool that turns a structured `course.yml` file into **consistent, reproducible, and auditable course outputs**.

It supports:

- Multi-page Quarto course sites (project build + `quarto render`)
- Single-page HTML handouts
- Print-ready PDF handouts
- Markdown export packages

It is designed for **educators, learning designers, and curriculum developers** who want:

- consistent outputs across formats  
- explicit structure and traceability  
- defensible design decisions  
- minimal manual document editing  

From v1.1 onwards, `course-engine` supports **optional capability mapping metadata** for governance, audit, and curriculum review contexts.

From **v1.6**, it supports **authoring lessons as separate source files**, with lesson provenance recorded in the build manifest.

From **v1.12**, it supports **explicit design intent metadata**, enabling authors to record rationale, AI positioning, and governance context without affecting build or validation behaviour.

From **v1.13**, the engine also supports **explicit structural AI scoping metadata**, allowing authors to record inspectable AI use boundaries separately from narrative design intent.

---

## 2. Who is this for?

You should use `course-engine` if you:

- design courses using structured specifications  
- need HTML and/or PDF outputs generated consistently  
- care about versioning, auditability, and defensibility  
- want artefacts suitable for teaching, QA, accreditation, or sharing  

You **do not** need to know Python beyond basic command-line usage.

---

## Quick start (recommended)

```bash
course-engine init my-course
cd my-course
course-engine build course.yml --out dist --overwrite
# build prints: ARTEFACT=dist/<course-id>
course-engine render dist/<course-id>
course-engine inspect dist/<course-id>
```

---

## 3. System Requirements

### 3.1 Python (mandatory)

- **Python 3.10 or newer**

Verify your version:

```bash
python --version
```

---

### 3.2 Quarto (required for Quarto-based builds)

Quarto is used to render multi-page sites and PDF/HTML outputs.

Install from: https://quarto.org/

Verify installation:

```bash
quarto --version
```

---

### 3.3 TinyTeX / LaTeX (required for PDF output only)

PDF output requires a LaTeX toolchain.

Recommended one-time installation:

```bash
quarto install tinytex
```

---

### 3.4 Preflight check (recommended)

Verify required external tools at any time:

```bash
course-engine check
```

---

## 4. Installation

### 4.1 Install locally (developer / repo checkout)

Clone or download the repository, then install in your virtual environment:

```bash
pip install -e .
```

Verify:

```bash
course-engine --help
```

---

## 5. One-time project setup

Create a starter course specification:

```bash
course-engine init my-course
```

This creates:

```text
my-course/
└── course.yml
```

Edit `course.yml` to define your course structure, lessons, and metadata.

---

## 6. Authoring lessons (v1.6)

Lessons may be authored either:

- inline using `content_blocks`, **or**
- as **separate Markdown or Quarto files** referenced using `source:`

### 6.1 Authoring lessons as source files

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

Rules:

- Paths are resolved **relative to `course.yml`**
- Titles are inferred from Markdown H1 if omitted
- Exactly one of `source` or `content_blocks` is required
- Provenance is recorded in `manifest.json`

---

## 7. Design intent metadata (v1.12)

Courses may optionally declare **design intent** in `course.yml`.

Design intent allows authors to record:

- rationale for design choices
- AI positioning and constraints
- relevant frameworks or policy context
- review cadence and evolution expectations

Example:

```yaml
design_intent:
  summary: >
    This course supports responsible AI-assisted curriculum foresight
    while preserving human judgement and decision accountability.
```

Design intent is:

- optional
- informational (not validated)
- recorded in `manifest.json`
- surfaced via `course-engine explain`

---

## 7.1 AI scoping metadata (v1.13)

From v1.13 onward, courses may optionally declare **structural AI scoping metadata** using an `ai_scoping` block in `course.yml`.

AI scoping is used to record **explicit, inspectable boundaries** around how AI tools may or may not be used within a course.

AI scoping is declarative metadata, not a policy or rule set, and is never enforced by the engine itself.

This is intentionally separated from `design_intent`:

- `design_intent` explains *why* AI is positioned a certain way
- `ai_scoping` records *what is permitted, restricted, or expected*

### What AI scoping captures

AI scoping may include:
- permitted uses of AI tools
- explicitly disallowed uses
- disclosure expectations
- data handling constraints
- decision-making boundaries

Example:

```yaml
ai_scoping:
  scope_summary: >
    AI tools may support learning activities and formative drafting,
    but must not be used to generate summative assessment submissions.
  permitted_uses:
    - Learning activities and exploratory analysis
    - Formative drafting and planning
  not_permitted:
    - Generating final summative assessment submissions
    - Entering sensitive or personal data into AI tools
```

### How AI scoping is used

AI scoping is:

- **optional**
- **structural (machine-readable)**
- **recorded in `manifest.json`**
- **used to suppress advisory governance signals** about missing AI boundaries
- **not enforced automatically**
- **interpreted only via policy if an institution chooses to do so**

This supports clearer QA, audit, and review conversations **without constraining pedagogy**.


---

## 8. Core commands

### Build

```bash
course-engine build course.yml --overwrite
```

On successful build, the resolved artefact path is printed as `ARTEFACT=...`
for easy reuse in scripts and CI pipelines (v1.17+).

### Render

```bash
course-engine render dist/my-course
```

### Inspect

```bash
course-engine inspect dist/my-course
```

> **Important note on artefact paths (v1.17+)**
>
> Most commands (`explain`, `validate`, `pack`) operate on the **artefact directory**
> that contains `manifest.json` (typically `dist/<course-id>/`).
>
> From v1.17 onward, `course-engine pack` will also accept a **parent output directory**
> *if* it contains exactly one artefact subdirectory with `manifest.json`.
>
> If multiple artefact candidates are found, the engine will fail with a
> clear, human-readable error listing the detected options.
>
> This behaviour matches common user workflows while preserving unambiguous
> governance output.

### Explain (artefact-level)

```bash
course-engine explain dist/my-course --format text
course-engine explain dist/my-course --format json
```

Explain surfaces (artefact-level, read-only):

- course identity
- build provenance
- framework alignment
- capability mapping presence
- **design intent summary (v1.12)**

Explain does **not** compute, emit, or evaluate governance signals.

Governance signals are:
- computed at build time,
- recorded in `manifest.json`,
- interpreted during validation (not explain-only runs).

---

## 9. Capability mapping, reporting, and validation

All behaviour remains unchanged from earlier versions:

- Capability mapping is optional and informational
- Reporting summarises declared coverage
- Validation checks defensibility using explicit policies
- Design intent is **not** validated

From v1.13 onward, governance signals and AI scoping improve validation clarity without changing capability mapping requirements or enforcement behaviour.

---

## 10. Design principles

- Fail fast  
- Non-destructive by default  
- Deterministic builds  
- Human-auditable artefacts  
- Clear separation between intent, structure, and enforcement  

---

## 11. Getting help

```bash
course-engine --help
```

Command-specific help:

```bash
course-engine build --help
course-engine explain --help
course-engine validate --help
```

---

## 12. Release verification (maintainers)

This section is intended for **maintainers and contributors**, not routine end users.

The script `scripts/verify-release.sh` is a **pre-release verification tool** designed to support
confidence, auditability, and institutional credibility.

### When to use this script

Run `verify-release.sh`:

- before merging a development branch into `master`
- before tagging a new release
- before sharing release artefacts with external institutions or QA reviewers

It is **not** intended for routine development or day-to-day editing.

### What the script verifies

The script performs a full release-level sanity check, including:

- CLI version and Python package version consistency
- linting, type checking, and test execution
- end-to-end demo course build and manifest generation
- inspect and explain output integrity
- policy explainability sanity checks

The script reports git status for transparency, but does not enforce a clean working tree
unless required by release policy.

### Relationship to smoke tests

- `scripts/smoke_test.sh` answers: *“Does the tool basically work?”*
- `scripts/verify-release.sh` answers: *“Is this release credible and defensible?”*

Maintainers should typically run **both scripts together** before major merges or releases.

