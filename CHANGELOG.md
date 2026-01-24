# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning.


## v1.19.0 – 2026-01-24

### Added
- `course-engine check --format json|text` output selector for explicit, script-safe preflight output.
- Human-readable preflight output mode (`--format text`) including:
  - Python version + platform
  - Quarto + Pandoc presence/version
  - PDF toolchain readiness
  - actionable remediation guidance

### Changed
- `course-engine check --json` is now explicitly documented as a **legacy/compatibility flag** (prefer `--format json`).
- Preflight JSON output is treated as a stable, machine-readable diagnostic payload suitable for CI/support workflows.

### Behaviour guarantees
- No schema changes
- No validation or enforcement behaviour introduced
- Fully backward compatible with existing `check --json` workflows

---

## v1.18.0 – Governance Pack Profiles & Composition Guarantees

### Added
- **Profile-based governance pack composition**
  - `course-engine pack` now enforces explicit profiles:
    - `audit`
    - `qa`
    - `minimal`
  - Profiles determine which factual artefacts are included in a pack.
  - Profile selection is validated at the CLI layer.

- **Facts-only pack README generation**
  - Each governance pack now includes a generated `README.txt` describing:
    - pack purpose and non-purpose,
    - profile used,
    - included artefacts,
    - generation context.
  - README content is non-evaluative and governance-safe by design.

### Changed
- **Strict CLI validation for pack profiles**
  - Invalid `--profile` values are rejected immediately with clear error messages.
  - Prevents ambiguous or partial governance outputs.

### Behaviour guarantees
- No schema changes
- No validation or enforcement behaviour introduced
- No impact on build or render outputs
- Fully backward compatible with v1.17.0

### Notes
- This release completes the governance packaging workflow.
- Pack generation remains:
  - deterministic,
  - facts-only,
  - policy-agnostic.

### Fixed
- Restored and stabilised `python -m course_engine` entrypoint
- Clarified Typer callback vs entrypoint structure
- No functional changes to governance pack outputs

----

## v1.17.0

### Workflow ergonomics (CI- and institution-friendly)

- **build:** prints a copy/paste-ready resolved artefact path (`ARTEFACT=...`) on success.
- **pack:** accepts either an artefact directory *or* a parent OUT directory containing exactly one artefact subdirectory (auto-detected via `manifest.json`).
- **pack:** improved failure messages for ambiguous or unrecognised directories, including candidate listings.
- **tests:** added coverage for parent-OUT auto-detection and multi-candidate failure behaviour.
- **cli:** supports `python -m course_engine.cli ...` module execution.

----

## v1.16.0 – Release hygiene & artefact path correctness

### Changed
- Hardened release and smoke-test workflows to **consistently operate on the correct artefact directory**
  (i.e. the directory that actually contains `manifest.json`, not its parent).
- Ensured published version is **fully aligned and verifiable** across:
  - CLI (`course-engine --version`)
  - Python package metadata
  - Build artefact manifests
- Clarified maintainer expectations around build output paths in verification and packing workflows.

### Fixed
- Eliminated a common maintainer error where `explain`, `validate`, or `pack` were run
  against a parent output directory rather than the generated artefact subdirectory.
- Smoke tests now reliably detect and resolve the correct artefact path before running
  explain, validate, and pack steps.

### Behaviour guarantees
- No schema changes
- No validation or enforcement changes
- No impact on build or render outputs
- Fully backward compatible with v1.15.0

### Notes
- This is a **release hygiene and workflow correctness** update.
- It improves maintainer confidence, CI reliability, and governance reproducibility
  without changing user-facing behaviour.

----

## v1.15.0

### Fixed
- `explain` now correctly distinguishes between:
  - course project directories (source `course.yml`)
  - built artefact directories (`manifest.json`)
- Summary output no longer mislabels explain time as a “build”.

### Improved
- Summary wording clarified to avoid interpretive claims:
  - “Generated at (UTC)” replaces “Built at (UTC)” in summaries
  - Capability mapping status now reported as `present: yes|no`
- `explain --summary` output is now safe to paste into emails and reports.

---

## v1.14.0 – Stability & governance credibility

### Changed
- Aligned CLI, package, and build metadata versioning
- Hardened pre-release verification workflow (`verify-release.sh`)
- Clarified maintainer release checks vs smoke tests
- Improved repository hygiene and ignore rules

### Notes
- No changes to course schema, validation behaviour, or governance logic
- This release focuses on reproducibility, auditability, and release confidence

---

## v1.13.1 – AI Scoping & Signal Stabilisation

### Added
- **Structured AI scoping metadata** (`ai_scoping`) as a first-class, inspectable block in `course.yml`
  - Separates narrative AI positioning from structural AI boundaries
  - Designed for governance clarity, auditability, and policy interpretation
- **AI scoping recorded in `manifest.json`**
  - Stored with:
    - presence flag,
    - stable SHA-256 hash,
    - inspectable structure
  - Enables deterministic detection of AI scope changes without inspecting content

### Changed
- **SIG-AI-001 behaviour refined**
  - Advisory signal is now **suppressed** when valid `ai_scoping` metadata is present
  - Reduces false-positive governance noise in well-specified courses
- **Manifest schema version bumped to 1.4.0**
  - Adds first-class `signals` array
  - Fully backward compatible for downstream consumers

### Fixed
- Schema alignment between `design_intent.ai_position` and `ai_scoping`
- Signal computation determinism under strict CI profiles
- Validation noise under strict governance profiles for well-scoped courses

### Behaviour guarantees
- No new enforcement introduced
- No changes to build or render outputs
- Signals remain informational by default
- Fully backward compatible with v1.13.0 (except improved signal precision)

### Notes
- This is a **stabilisation and governance-hardening patch**
- Intended to make v1.13 safe for institutional rollout and CI use

---

## v1.13.0 – Absence Signals & Governance Contract Completion

### Added
- **Absence signalling framework**
  - The engine now computes explicit, deterministic signals for missing or thin declarations, including:
    - missing design intent,
    - declared alignment without inspectable mapping,
    - thin or empty capability mappings,
    - AI positioning without structural scoping
  - Signals are:
    - non-blocking by default,
    - recorded in `manifest.json`,
    - interpreted only by policies (never enforced by the engine)

- **Signals recorded in `manifest.json`**
  - Provides a machine-readable governance surface
  - Enables transparent downstream interpretation by QA tools, CI pipelines, and dashboards

### Changed
- **Clear separation of responsibilities**
  - Engine computes facts
  - Policies interpret signals
  - Institutions decide enforcement thresholds
- Validation behaviour clarified to reduce ambiguity and over-warning

### Behaviour guarantees
- Signals are informational unless elevated by policy
- No automatic enforcement or scoring introduced
- No pedagogical judgement performed
- Fully backward compatible with v1.12.0

### Notes
- This release completes the **governance contract** introduced in earlier versions
- Establishes a stable foundation for institutional adoption

---

## v1.12.0 – Design Intent & Governance Signal Formalisation

### Added
- **Design intent metadata block** (`design_intent`) in `course.yml`
  - Optional, informational author-declared rationale
  - Intended to capture:
    - design context and reasoning,
    - AI positioning and boundaries,
    - relevant frameworks or governance considerations
  - Does not affect build, render, validation, or enforcement behaviour

- **Design intent recorded in `manifest.json`**
  - Stored with:
    - presence flag,
    - stable SHA-256 hash,
    - human-readable summary
  - Enables auditability and change detection without inspecting lesson content

- **Explain output enhanced**
  - `course-engine explain` now surfaces design intent in:
    - machine-readable JSON output
    - human-readable text reports
  - Available in artefact (manifest-backed) explain mode

### Changed
- Manifest schema version bumped to **1.3.0**
  - Adds `design_intent` metadata
  - Fully backward compatible with earlier manifests

### Behaviour guarantees
- No changes to build outputs or rendering behaviour
- No new validation or enforcement logic introduced
- Design intent is **purely informational**
- Fully backward compatible with v1.11.0

### Notes
- This release strengthens governance transparency and audit readiness
- Design intent complements (but does not replace) `framework_alignment` and `capability_mapping`


---

## v1.11.0 – Governance Adoption & Documentation Consolidation

### Added
- Demonstration course updated to include **defensible capability mapping**
  - Declares both `framework_alignment` (intent) and `capability_mapping` (coverage and evidence)
  - Enables end-to-end QA, validation, and reporting demonstrations
- Documented **explainability JSON contract** for policy resolution
  - Formalises the structure and guarantees of `validate --explain --json`
  - Intended for CI pipelines, dashboards, and governance tooling

### Changed
- Policy documentation clarified to emphasise:
  - structural (not qualitative) validation
  - requirement for `capability_mapping` to enable validation
  - separation between declaration, reporting, and enforcement
- Documentation aligned with current CLI semantics and governance positioning

### Behaviour guarantees
- No changes to build outputs, schemas, or validation logic
- No new enforcement behaviour introduced
- Fully backward compatible with v1.10.0

### Notes
- This is a **documentation and adoption release**
- Intended to make existing governance features easier to understand and operationalise

---

## v1.10.0 – Explain Interface Stabilisation & Governance Hardening

### Changed
- Introduced `--format json|text` as the **preferred output selector** for `course-engine explain`
- Retained `--json` as a **legacy / backward-compatibility flag**
- Clarified output precedence:
  - `--format` always overrides `--json`
  - JSON remains the default when no flags are supplied
- Improved CLI help text to explicitly document defaults and overrides

### Fixed
- Eliminated ambiguity in explain output selection for CI, QA, and automation workflows
- Hardened type safety across explain, policy, and exporter subsystems
- Achieved clean static analysis (`ruff`, `mypy`) and test (`pytest`) runs across the codebase

### Behaviour guarantees
- No changes to build outputs, schemas, or enforcement behaviour
- Explain output remains deterministic except for runtime timestamps
- Fully backward compatible with existing scripts using `--json`

### Notes
- This is a **polish and interface-hardening release**
- Explainability is now considered **stable and governance-ready**


---

## v1.9.0 – Internal Refactor & Preparation Release

### Notes
- Internal refactoring and groundwork for explain interface stabilisation
- No user-facing feature additions
- No schema, build, or behaviour changes
- Released as a stepping stone toward v1.10.0


---

## v1.8.1

### Fixed
- Explain now resolves lesson-level `source:` files and reports full provenance under `sources.files` and `sources.resolution`.
- File existence, byte size, and SHA-256 hashes are surfaced for governance and audit workflows.

### Notes
- This is an explain-only change.
- No impact on build, render, or UI output.
- Includes a demo regression fixture to validate provenance resolution.

---

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
