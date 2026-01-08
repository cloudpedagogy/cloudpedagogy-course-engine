# Changelog

All notable changes to this project are documented in this file.

This project follows semantic versioning.

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
