# End User Instructions  
**course-engine v1.12**

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
course-engine render dist/my-course
course-engine inspect dist/my-course
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

## 8. Core commands

### Build

```bash
course-engine build course.yml --overwrite
```

### Render

```bash
course-engine render dist/my-course
```

### Inspect

```bash
course-engine inspect dist/my-course
```

### Explain (artefact-level)

```bash
course-engine explain dist/my-course --format text
course-engine explain dist/my-course --format json
```

Explain surfaces:

- course identity
- build provenance
- framework alignment
- capability mapping presence
- **design intent summary (v1.12)**

---

## 9. Capability mapping, reporting, and validation

All behaviour remains unchanged from earlier versions:

- Capability mapping is optional and informational
- Reporting summarises declared coverage
- Validation checks defensibility using explicit policies
- Design intent is **not** validated

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
