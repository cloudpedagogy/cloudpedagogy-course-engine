# Scenario Planning and Environmental Scanning (Example Course)

This example demonstrates the **recommended default workflow** for using the
**CloudPedagogy Course Engine v1.6** with explicitly declared lessons.

---

## What this example shows

- Pattern A (recommended): **explicit lessons declared in `course.yml`**
- Lesson content stored as separate Markdown files
- Deterministic navigation and auditable structure
- Clear separation between:
  - content (Markdown)
  - structure (YAML)
  - outputs (Quarto build artefacts)

---

## Folder structure

```
examples/
  course.scenario-planning.yml

content/
  lessons/
    _index.md
    lesson-1.md
    lesson-2.md
    lesson-3.md
    lesson-4.md
    lesson-5.md
```

---

## Build and render the course

From the repository root (with the virtual environment activated):

```bash
course-engine build examples/course.scenario-planning.yml --out dist --overwrite
course-engine render dist/scenario-planning-environmental-scanning
```

---

## View the output

Open the generated Quarto site:

```
dist/scenario-planning-environmental-scanning/_site/index.html
```

Lesson pages will appear under:

```
dist/scenario-planning-environmental-scanning/_site/lessons/
```

---

## Why lessons are declared in YAML

Course Engine does **not** infer course structure from Markdown headings.

From v1.6, lessons may be authored inline or as external source files — but **the navigable structure is always declared in** course.yml, and ambiguous mixed patterns are rejected.

All navigable pages must be declared explicitly in `course.yml` to ensure:

- predictable builds
- stable navigation
- auditability via `manifest.json`
- future policy validation

This design is intentional and required for governance‑ready course production.
