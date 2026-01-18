# End User Instructions  
**course-engine v1.6**

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

From **v1.6**, it also supports **authoring lessons as separate source files**, with lesson provenance recorded in the build manifest.

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

This makes the `course-engine` command available.

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

From **v1.6**, lessons can be authored either:

- inline using `content_blocks`, **or**
- as **separate Markdown or Quarto files** referenced using `source:`

### 6.1 Authoring lessons as source files

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

How this works:

- `source:` paths are resolved **relative to the `course.yml` location**
- Lesson title is resolved in this order:
  1. explicit `title:` in `course.yml`
  2. first Markdown H1 (`# Heading`) in the source file
- Source files are injected as a single internal Markdown content block at build time
- Provenance is recorded in `manifest.json` under `lesson_sources` (informational)

### Constraints (enforced)

- A lesson must define **exactly one of**:
  - `source`, or
  - `content_blocks`
- Defining both will cause a build error
- Defining neither will cause a build error
- If no title can be inferred, the build fails with a clear message

---

## 7. Core commands

### 7.1 Build outputs

Build a multi-page Quarto project (default):

```bash
course-engine build course.yml
```

Build a single-page HTML handout:

```bash
course-engine build course.yml --format html-single
```

Build a PDF handout project:

```bash
course-engine build course.yml --format pdf
```

If the output directory already exists, rebuild safely with:

```bash
course-engine build course.yml --overwrite
```

Or (example):

```bash
course-engine build course.yml --format pdf --overwrite
```

Notes:

- `build` generates the project files + writes `manifest.json`
- For Quarto/PDF formats, you typically follow with `course-engine render`

---

### 7.2 Render outputs (Quarto render)

Render an existing Quarto project directory:

```bash
course-engine render dist/my-course
```

Common results:

- **Multi-page Quarto site:** typically appears under `dist/my-course/_site/`
- **PDF project:** by default appears as `index.pdf` in the project directory (and is listed in the manifest)

---

### 7.3 Inspect outputs (recommended)

Each build produces a `manifest.json`.

Inspect it with:

```bash
course-engine inspect dist/my-course
```

This shows:

- course metadata  
- build and render timestamps  
- output format  
- declared framework alignment and mapping mode (if present)  
- capability mapping summary (if declared)  
- file inventory with counts/sizes  
- **lesson source provenance summary (v1.6)**  

---

### 7.4 Clean outputs

Safely delete generated output directories:

```bash
course-engine clean dist/my-course
```

Skip confirmation:

```bash
course-engine clean dist/my-course -y
```

---

### 7.5 Capability coverage reporting (v1.2+)

If a course declares capability mapping metadata, `course-engine` can generate a **capability coverage report** from a built output directory.

Generate a report:

```bash
course-engine report dist/my-course
```

Verbose output:

```bash
course-engine report dist/my-course --verbose
```

Machine-readable JSON:

```bash
course-engine report dist/my-course --json
```

v1.6 behaviour:

- If `capability_mapping` is missing but `framework_alignment` is present, `report` prints a **declared alignment summary** (informational).

---

### 7.6 Capability validation (v1.3+)

From v1.3, `course-engine` can validate the **defensibility** of declared capability mappings using explicit rules.

Validation:

- reads `manifest.json`
- does not modify outputs
- supports governance, QA, and audit workflows

Run validation:

```bash
course-engine validate dist/my-course
```

Strict mode (non-zero exit on failure):

```bash
course-engine validate dist/my-course --strict
```

If no `capability_mapping` is present, validation exits non-zero with a clear message (because there is nothing defensible to validate).

---

### 7.7 Policy explanation & inspection (v1.5+)

From v1.5, `course-engine validate` supports **explain-only policy inspection**.

This allows inspection of:

- policy source and provenance
- selected profile
- inheritance chain
- resolved rules
- strict mode state

Example (explain-only, JSON):

```bash
course-engine validate /tmp --policy preset:baseline --profile baseline --explain --json
```

This mode:

- does not require `manifest.json`
- does not execute validation
- is safe for CI pipelines and dashboards

---

## 8. Output structure (examples)

Typical Quarto site build + render:

```text
dist/my-course/
├── _quarto.yml
├── index.qmd
├── lessons/
│   └── ...
├── _site/
│   └── ... rendered HTML site ...
└── manifest.json
```

Typical PDF build + render:

```text
dist/my-course-pdf/
├── _quarto.yml
├── index.qmd
├── index.pdf
└── manifest.json
```

---

## 9. Common errors & fixes

### “PDF output requires a LaTeX toolchain”

Run:

```bash
quarto install tinytex
```

Then try `course-engine render` again.

---

### “Target output folder already exists”

Rebuild safely with:

```bash
course-engine build course.yml --overwrite
```

---

### “Lesson cannot have both `source` and `content_blocks`”

Remove one of the two fields. Exactly one is required.

---

### “Lesson must define either `source` or `content_blocks`”

Add one of the two fields to the lesson.

---

### “Lesson has `source` but no title could be inferred”

Add a `title:` to the lesson **or** include a Markdown H1 in the source file.

---

### “Invalid course.yml structure: found top-level `modules`”

Modules must be nested under:

```yaml
structure:
  modules:
```

---

### “Unsupported key: found top-level `content`”

Remove unsupported legacy keys. Lesson content must be provided via:

- `structure.modules[].lessons[].content_blocks`, or
- `structure.modules[].lessons[].source`

---

## 10. Design principles

- Fail fast: errors are explicit and early  
- Non-destructive by default: outputs are never overwritten silently  
- Traceable: every build produces a manifest  
- Format-agnostic: one spec → multiple outputs  
- Human-auditable: outputs and metadata are readable without special tooling  

---

## 11. Versioning notes

- v1.0–v1.1: stability, reproducibility, clarity  
- v1.1: optional capability mapping metadata  
- v1.2: capability coverage reporting  
- v1.3: rule-based capability validation  
- v1.4: policy/profile selection (with inheritance)  
- v1.5: explain-only policy inspection (`--explain --json`)  
- **v1.6: external lesson source files + provenance + schema guardrails**  

---

## 12. Getting help

General help:

```bash
course-engine --help
```

Command help:

```bash
course-engine build --help
course-engine render --help
course-engine inspect --help
course-engine report --help
course-engine validate --help
```
