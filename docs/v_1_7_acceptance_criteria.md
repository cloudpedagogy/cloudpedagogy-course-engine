# CloudPedagogy Course Engine  
## v1.7 Acceptance Criteria

**Audience:** Maintainer (solo developer)  
**Purpose:** Internal release guardrails and design integrity check  
**User-facing:** No  
**Status:** Ready for v1.7.0 release

---

## How to Use This Document

This document is **not a development task list** and **not an end-user guide**.

It exists to:
- preserve design intent over time
- prevent scope creep during v1.7
- support confident release tagging

As a solo developer, this is a **reference artefact**, not a process burden.

---

## A. Global Release Integrity

v1.7 may be released **only if all statements below remain true**:

- [x] No breaking changes to v1.6 `course.yml` files
- [x] Existing demo courses build and render without modification
- [x] No new mandatory fields introduced
- [x] No enforcement logic added
- [x] No author intent inferred or auto-corrected
- [x] Engine remains framework-agnostic in enforcement

---

## B. Authoring Pipeline Documentation

- [x] Authoring pipeline is documented and understood
- [x] Pipeline explicitly described: Word → Pandoc → Markdown → Split → Build
- [x] Required Markdown heading semantics clearly stated
- [x] Canonical Pandoc command provided
- [x] Author vs tool responsibilities clearly separated
- [x] No implied validation or enforcement rules

---

## C. Authoring Utilities (`split_lessons.py`)

- [x] Script lives in `scripts/`
- [x] Header explicitly states that this is:
  - an authoring utility
  - pre-build only
  - not part of the runtime engine
- [x] Default behaviour uses deterministic splitting
- [x] Supports at least one legacy-compatible split mode
- [x] Does not infer lesson intent
- [x] Does not modify content beyond splitting

---

## D. Optional Lesson Display Labels

- [x] `display_label` supported as optional lesson metadata
- [x] Absence of `display_label` causes no warnings or errors
- [x] Display labels do not affect ordering or validation
- [x] Display labels are informational only
- [x] Lesson Markdown remains numbering-free

---

## E. Inspection & UI Behaviour

- [x] Existing `inspect` behaviour unchanged by default
- [x] Lesson navigation and ordering are stable and reproducible
- [x] Lesson index UI renders correctly across screen sizes
- [x] Sidebar navigation collapses responsively
- [x] Previous / Next navigation works consistently
- [x] Search index builds and functions on a static web server
- [x] No UI behaviour requires server-side logic

> Note: Additional inspection output (expanded JSON detail, richer explain-only views)
> is intentionally deferred to v1.8+.

---

## F. Explain-Only & Read-Only Guarantees

- [x] No explain-only or inspection features enforce validation
- [x] All inspection and navigation features are read-only
- [x] No scoring, ranking, or compliance logic introduced
- [x] Human judgement remains final authority

---

## G. Backward Compatibility

- [x] All v1.6 demo courses build under v1.7
- [x] No changes required to existing `course.yml`
- [x] Legacy lesson-numbered Markdown remains supported via authoring utilities
- [x] Manifest schema remains compatible

---

## H. Governance & Trust Guarantees

- [x] All new behaviour is explainable via documentation or inspection
- [x] No hidden heuristics introduced
- [x] No implicit decisions made on behalf of authors
- [x] UI changes are presentational only
- [x] Author intent is preserved end-to-end

---

## I. Release Gate (Final Checks)

v1.7 may be tagged (`v1.7.0`) only when:

- [x] This document has been reviewed end-to-end
- [x] `docs/v1.7-design.md` matches implemented behaviour
- [x] Demo course reflects intended authoring and UI patterns
- [x] No v1.8+ features have leaked into the release

---

*This document exists to support clarity, not compliance.*

*End of v1.7 acceptance criteria*
