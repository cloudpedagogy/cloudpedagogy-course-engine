# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning.


## v1.2.0

### Added
- Capability coverage report command (`course-engine report`)
- Text, verbose, and JSON report outputs
- Optional `--fail-on-gaps` exit code for QA / CI use

### Notes
- Capability mapping remains informational (not enforced)



## v1.1.0

- Added optional top-level `capability_mapping` metadata in `course.yml`
- Capability mapping is recorded in `manifest.json` (informational, not enforced)
- `course-engine inspect` shows a capability mapping summary
- Added tests covering parsing and manifest inclusion
- Repo hygiene: ignore packaging/build artefacts (e.g., `*.egg-info/`)


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
- CLI commands: init, build, render, inspect, clean, check
- End-user documentation and CI workflow added
