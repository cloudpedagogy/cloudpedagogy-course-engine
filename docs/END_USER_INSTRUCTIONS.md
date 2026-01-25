# End User Instructions  
**course-engine v1.20.0**

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

## 3.4 Preflight check (recommended)

`course-engine` includes a built-in **preflight check** to verify that required
external tools are installed and working correctly.

This is recommended:
- before your first build,
- when setting up a new machine,
- in CI or automation workflows,
- or when troubleshooting PDF or rendering issues.

### Run the preflight check

```bash
course-engine check
```

This performs a non-destructive environment check and reports:

- Python version and platform
- Quarto availability and version
- Pandoc availability (as reported by Quarto, if exposed)
- PDF toolchain readiness (TinyTeX / LaTeX)
- Clear remediation guidance if something is missing

### Explicit output formats 

From v1.19 onward, preflight output format can be selected explicitly.

For **machine-readable output** (CI, scripts, support tooling):

```bash
course-engine check --format json
```

For **human-readable diagnostic output**:

```bash
course-engine check --format text
```

Notes:

- `--format` is the **preferred** output selector.
- `--json` remains supported as a **legacy / compatibility flag**.
- If both are supplied, `--format` takes precedence.


### Requirement modes and exit behaviour (v1.20+)

From v1.20 onward, `course-engine check` cleanly separates:

- environment inspection (facts),
- workflow requirements (intent),
- exit semantics (decision).

By default, `course-engine check` runs in **informational mode**
and will always exit `0`, even if optional tools are missing.

This is suitable for:
- local setup,
- onboarding,
- diagnostics,
- support workflows.


# CI-Grade Preflight Usage (course-engine v1.20+)

This document describes how to use `course-engine check` in
**CI, automation, and scripted workflows** where deterministic
exit behaviour is required.

It supplements the End User Instructions and focuses specifically
on **preflight gating semantics**.

---

## CI-grade usage

To enable deterministic gating in CI and automation workflows,
invoke `course-engine check` with explicit requirements.

```bash
course-engine check --strict
course-engine check --require pdf --format json
```

### Modes explained

- `--strict`
  - Requires **Quarto** and **PDF toolchain readiness**
  - Intended for CI pipelines and release gating

- `--require pdf`
  - Explicitly enforces PDF readiness
  - Useful when HTML builds are optional but PDFs are mandatory
  - Does not implicitly enable other strict checks unless required

By default (no flags), `course-engine check` runs in
**informational mode** and always exits `0`.

---

## Exit codes

When requirements are enabled, `course-engine check` returns
**deterministic exit codes** suitable for CI and automation:

- `0` — OK
- `2` — required tooling missing (e.g. Quarto)
- `3` — PDF toolchain not ready when required
- `4` — filesystem / temp-write diagnostic failed
- `1` — unexpected or internal error

Exit codes are stable and versioned as part of the v1.20
preflight contract.

---

## JSON contract note

When `--format json` is used, the output always includes a
`requirements` block describing **which capabilities were required**
for the current invocation.

This allows CI systems, dashboards, and support tooling to
distinguish:

- what the environment provides, from
- what the workflow explicitly requires.

The JSON payload is **additive, facts-only, and contract-stable**.


### Requirement modes and exit behaviour (v1.20+)

From v1.20 onward, `course-engine check` cleanly separates:

- environment inspection (facts),
- workflow requirements (intent),
- exit semantics (decision).

By default, `course-engine check` runs in **informational mode**
and will always exit `0`, even if optional tools are missing.

This is suitable for:
- local setup,
- onboarding,
- diagnostics,
- support workflows.


### Behaviour guarantees

The preflight check:

- does **not** modify your system or project,
- does **not** build or render content,
- does **not** enforce policies or validation rules,
- is safe to run repeatedly.

It is intended purely as a **diagnostic and onboarding aid**.

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

## 6. Authoring lessons

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

## 7.1 AI scoping metadata 

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

> **Important note on artefact paths**
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

### 8.1 Governance packs

`course-engine pack` generates a **facts-only governance pack** from an existing build artefact.

Governance packs are designed for:
- QA and review workflows
- audit and accreditation evidence
- institutional handover and assurance
- CI and documentation pipelines

They do **not**:
- rebuild content,
- render outputs,
- enforce policies,
- or evaluate pedagogical quality.

#### Pack profiles

From v1.18 onward, pack composition is controlled by an explicit `--profile`:

- `audit` – full factual governance context (default)
- `qa` – factual governance content suitable for internal QA and review workflows, where full audit traceability is not required
- `minimal` – lightweight summary-only pack

Profiles determine **which artefacts are included**.  
Invalid profile values are rejected at the CLI layer.

Example:

```bash
# Full governance / audit pack (default)
course-engine pack dist/my-course \
  --out packs/my-course-audit \
  --profile audit \
  --overwrite

# QA review pack (reduced scope, same factual basis)
course-engine pack dist/my-course \
  --out packs/my-course-qa \
  --profile qa \
  --overwrite

# Lightweight handover or archive pack
course-engine pack dist/my-course \
  --out packs/my-course-minimal \
  --profile minimal \
  --overwrite
```

#### Pack contents

Depending on profile, a governance pack may include:

- `README.txt` – generated description of pack scope and intent
- summary text
- explain text and JSON
- `manifest.json`
- capability report (text and/or JSON)

All contents are:
- deterministic,
- facts-only,
- derived from `manifest.json`,
- safe for governance and audit use.

The generated `README.txt` explains:
- what the pack is for,
- what it is *not* for,
- which profile was used,
- and how the contents should be interpreted.


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

