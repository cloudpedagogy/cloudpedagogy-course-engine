# End User Instructions  
**course-engine v1.2**

---

## 1. What is `course-engine`?

`course-engine` is a command-line tool for turning a structured `course.yml` file into high-quality, defensible course outputs, including:

- Multi-page Quarto projects
- Single-page HTML handouts
- Print-ready PDF handouts
- Markdown export packages

It is designed for **educators, learning designers, and curriculum developers** who want reproducible, auditable course outputs without manually editing documents.

From v1.1 onwards, course-engine also supports optional capability mapping metadata for governance, audit, and curriculum review contexts.

---

## 2. Who is this for?

You should use `course-engine` if you:

- Design courses using structured specifications
- Need **PDF or HTML outputs** generated consistently
- Care about **traceability, versioning, and defensibility**
- Want outputs suitable for teaching, QA, or sharing

You **do not** need to know Python beyond basic command-line usage.

---

## 3. System Requirements (Mandatory)

### 3.1 Python
- **Python 3.10 or newer**
- Verify:
  ```bash
  python --version
```

---

## 3.2 Quarto (Required for all builds)

Quarto is the document engine used for rendering outputs.

Install from: https://quarto.org/

Verify:
  ```bash

quarto --version
 ```
---

## 3.3 TinyTeX / LaTeX (Required for PDF output only)

PDF output requires a LaTeX toolchain.

Recommended installation (one-time):

 ```bash
quarto install tinytex
 ```

You can verify your setup at any time:
 ```bash
course-engine check
 ```
---

## 4. Installation

Clone or download the repository, then install locally:

 ```bash
pip install -e .
 ```

This makes the course-engine command available in your environment.

---

## 5. One-Time Project Setup

Create a starter course specification:

 ```bash
course-engine init my-course
 ```

This creates:
 ```
my-course/
└── course.yml
 ```
Edit course.yml to define your course structure, content, and metadata.

---

## 6. Core Commands
### 6.1 Build Outputs

Build a Quarto project
 ```bash
course-engine build course.yml
 ```

Build a single-page HTML handout
 ```bash
course-engine build course.yml --format html-single
 ```

Build a PDF handout
 ```bash
course-engine build course.yml --format pdf
 ```

If the output directory already exists, you must either delete it or pass:
 ```bash
--overwrite
 ```

Example:
 ```bash

course-engine build course.yml --format pdf --overwrite
 ```
### 6.2 Render Outputs

After building, render with Quarto:
 ```bash
course-engine render dist/my-course-pdf
 ```

For PDFs, the result will be:
 ```bash
dist/my-course-pdf/index.pdf
 ```
### 6.3 Inspect Outputs (Recommended)

Each build produces a manifest.json.

Inspect it with:
 ```bash
course-engine inspect dist/my-course-pdf
 ```

This shows:

- Course metadata
- Build time
- Render time
- Output format
- Capability mapping summary (if declared)
- File inventory and sizes

### 6.4 Clean Outputs

Safely delete generated output directories:
 ```bash
course-engine clean dist/my-course-pdf
 ```

With confirmation disabled:
 ```bash
course-engine clean dist/my-course-pdf -y
 ```

### 6.5 Capability Coverage Reporting (v1.2)

If a course declares capability mapping metadata, course-engine can generate
a **capability coverage report** from an existing build.

This report summarises:

- Which capability domains are declared
- What coverage has been claimed per domain
- What evidence has been provided
- Whether any domains have gaps (no coverage or evidence)

Generate a report from a built output directory:
```bash
course-engine report dist/my-course
```

Verbose mode (shows declared coverage and evidence):
```bash
course-engine report dist/my-course --verbose
```

Machine-readable JSON output (for QA, audit, or pipelines):
```bash
course-engine report dist/my-course --json
```


---

## 7. Output Structure

Typical PDF output:
 
 ```
dist/my-course-pdf/
├── _quarto.yml
├── index.qmd
├── index.pdf
└── manifest.json
 ```
The PDF file is always index.pdf.

---

## 8. Common Errors & Fixes
“PDF output requires a LaTeX toolchain”

Run:
 ```bash
quarto install tinytex
```

Then retry your command.

“Target output folder already exists”

Either:

Delete the folder, or

Rebuild with:
 ```bash
--overwrite
```
“Quarto not found”

Install Quarto from https://quarto.org/
 and ensure it is on your PATH.

---

## 9. Design Principles (Why it works this way)

Fail fast: missing dependencies are detected early

Non-destructive by default: outputs are never overwritten silently

Traceable: every output has a manifest

Format-agnostic: same course spec → multiple outputs

Human-auditable: outputs and metadata are inspectable without tools

---

## 10. Versioning Notes

v1.0–v1.1 focus on stability, reproducibility, and clarity

From v1.1, optional capability mapping metadata can be declared in course.yml.
This metadata is informational and not enforced.

Capability-Driven Development (CDD) concepts provide design context but are not mandatory.

Future versions may add:

capability intent files

governance constraints

lineage assertions

---

## 11. Getting Help

Run:
 ```bash
course-engine --help
```

or inspect individual commands:
 ```bash
course-engine build --help
```
