# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning.


## v1.8.0

### Fixed
- Corrected engine version reporting to derive from installed package metadata (eliminates version drift in CLI and explain JSON).

---

## v1.7.0 – Lesson Navigation & UX Polish

### Changed
- Lesson pages now use in-body table of contents (TOC) for long-form readability
- Removed redundant “Quick links” section from lessons index
- Standardised lesson navigation labels using `lesson_nav_title`
- Improved previous/next lesson navigation placement for clearer progression

### Notes
- This release focuses on UI/UX improvements only
- No changes to course schema or build logic

---

## v1.6.0

### Added
- Native support for **external lesson source files** via `lesson.source`
  - Lessons can now be authored as standalone Markdown (`.md`) or Quarto (`.qmd`) files
  - Source files are resolved relative to `course.yml`
  - Lesson titles are inferred automatically from the first Markdown H1 (`# Heading`) if omitted
- **Lesson source provenance tracking** in `manifest.json`
  - Records declared source path, resolved absolute path, and SHA-256 hash
  - Enables auditability, reproducibility, and change detection
- **Fail-fast guardrails** for common authoring errors
  - Clear errors for unsupported top-level keys (`content:`, top-level `modules:`)
  - Explicit validation when both `source` and `content_blocks` are defined
  - Explicit validation when neither `source` nor `content_blocks` is defined
- Manifest schema version bumped to **1.2.0**
  - Adds `lesson_sources` summary metadata

### Behaviour guarantees
- External lesson sourcing is **fully deterministic**
  - Lesson content is embedded at build time
  - Build output does not depend on runtime file availability
- Backwards compatible with inline `content_blocks`
- No change to validation, policy, or reporting behaviour unless lesson sources are used

### Notes
- This release eliminates the previous “silent empty lessons” failure mode
- External lesson files are treated as **inputs**, not build artefacts
- This lays the foundation for future framework packs and institutional portability (v1.7+)

---

## v1.5.0

### Added
- Explain-only policy resolution mode (`course-engine validate --explain`)
- Machine-readable JSON output for policy resolution (`--explain --json`)
- Policy provenance surfaced in explain output:
  - `policy_id`
  - `policy_name`
  - `owner`
  - `last_updated`
- Support for explain mode without requiring `manifest.json`
- Preset and file-based policy support in explain mode

### Behaviour guarantees
- Explain mode does not execute validation
- No build artefacts are required
- Backwards compatible with v1.4 validation behaviour

### Notes
- Enables safe integration with CI pipelines, dashboards, and external governance tooling
- Explain JSON output is considered a contract-stable interface

---

## v1.4.0

### Added
- Policy-based validation framework
- Support for preset and file-based policy definitions
- Profile inheritance and resolution logic

### Notes
- This release primarily introduced internal policy infrastructure
- User-facing explain and JSON interfaces were finalised in v1.5.0

---

## v1.3.1

### Changed
- Improved `course-engine validate` output wording for clarity (non-strict vs strict)

---

## v1.3.0

### Added
- Capability mapping defensibility validation (`course-engine validate`)
- Rule-based validation engine operating on `manifest.json`
- Non-strict (default) and strict validation modes
- Machine-readable exit codes for QA / CI workflows

### Notes
- Validation does not modify builds or enforce frameworks
- Builds remain non-blocking unless strict validation is explicitly enabled

---

## v1.2.0

### Added
- Capability coverage report command (`course-engine report`)
- Text, verbose, and JSON report outputs
- Optional `--fail-on-gaps` exit code for QA / CI use

### Notes
- Capability mapping remains informational (not enforced)

---

## v1.1.0

### Added
- Optional top-level `capability_mapping` metadata in `course.yml`
- Capability mapping recorded in `manifest.json` (informational, not enforced)
- `course-engine inspect` shows a capability mapping summary
- Tests covering parsing and manifest inclusion

### Changed
- Repository hygiene: ignore packaging/build artefacts (e.g. `*.egg-info/`)

---

## v1.0.0

- Initial stable release
- Deterministic build pipeline from `course.yml`
- Multi-format outputs:
  - Multi-page Quarto website
  - Single-page HTML handout
  - Print-ready PDF (Quarto + TinyTeX)
  - Markdown export package
- Non-destructive builds by default (`--overwrite` required)
- Build auditability via `manifest.json`
- CLI commands: `init`, `build`, `render`, `inspect`, `clean`, `check`
- End-user documentation and CI workflow added
