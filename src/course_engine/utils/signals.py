# src/course_engine/utils/signals.py
"""
v1.13 — Absence signalling (governance-grade, non-blocking by default)

This module defines the computation seam for absence signals.
Implementation MUST adhere to:
- docs/design/v1.13.0-absence-signals.md
- docs/acceptance/v1.13.0-acceptance_criteria.md

Notes:
- Signals are informational/advisory only (never fail by default).
- Output must be deterministic for identical inputs.
"""

from __future__ import annotations


from ..model import CourseSpec, Signal


def _is_thin_mapping(mapping: object) -> bool:
    """
    Conservative heuristic for 'thin' mapping.

    v1.13 intention: detect clearly empty mappings without judging quality.
    """
    if mapping is None:
        return True

    # CapabilityMapping in model.py has `domains: dict[...]`
    if hasattr(mapping, "domains"):
        try:
            return not bool(getattr(mapping, "domains"))
        except Exception:
            return False

    # Fallback for dict-like inputs (defensive)
    if isinstance(mapping, dict):
        return not bool(mapping)

    return False


def compute_signals(course: CourseSpec) -> list[Signal]:
    """
    Compute v1.13 absence signals for a validated CourseSpec.

    Determinism rules:
    - Always return signals sorted by signal id.
    - Evidence paths are stable strings.

    Signals (v1.13 minimal set):
    - SIG-INTENT-001: design intent missing
    - SIG-MAP-001: alignment declared without capability mapping
    - SIG-MAP-002: capability mapping present but thin
    - SIG-AI-001: AI positioning declared without separate structural scoping metadata (limited in v1.13)
    """
    signals: list[Signal] = []

    # Design intent is now a first-class field on CourseSpec (v1.12+ wiring).
    design_intent = course.design_intent

    # --- SIG-INTENT-001: Design intent missing (info)
    if design_intent is None:
        signals.append(
            Signal(
                id="SIG-INTENT-001",
                severity="info",
                summary="Design intent not declared",
                detail=(
                    "The course does not declare a design_intent section. "
                    "Design intent is optional, but its absence may reduce traceability in review contexts."
                ),
                evidence=["course.yml:design_intent"],
                review_question=(
                    "Is design intent documented elsewhere, and should it be recorded here for auditability?"
                ),
                source="course.yml",
                tags=["intent"],
            )
        )

    # --- SIG-MAP-001: Alignment declared without capability mapping (warning)
    # framework_alignment is required by schema; capability_mapping is optional.
    if course.capability_mapping is None:
        signals.append(
            Signal(
                id="SIG-MAP-001",
                severity="warning",
                summary="Framework alignment declared without capability mapping",
                detail=(
                    "The course declares framework alignment but provides no inspectable capability_mapping. "
                    "This increases review friction because the alignment claim cannot be traced to evidence."
                ),
                evidence=["course.yml:framework_alignment", "course.yml:capability_mapping"],
                review_question="Is the alignment claim sufficiently evidenced for internal or external review?",
                source="course.yml",
                tags=["mapping", "claims"],
            )
        )
    else:
        # --- SIG-MAP-002: Capability mapping present but thin (warning)
        if _is_thin_mapping(course.capability_mapping):
            signals.append(
                Signal(
                    id="SIG-MAP-002",
                    severity="warning",
                    summary="Capability mapping present but appears thin",
                    detail=(
                        "The course includes a capability_mapping object, but it appears empty or minimally populated. "
                        "Thin mapping can create the appearance of evidence without sufficient inspectable detail."
                    ),
                    evidence=["course.yml:capability_mapping"],
                    review_question=(
                        "Does the mapping contain enough inspectable detail to support the stated alignment claim?"
                    ),
                    source="course.yml",
                    tags=["mapping"],
                )
            )

    # --- SIG-AI-001: AI positioning declared without structural scoping metadata (info)
    # v1.13 minimal implementation: the schema provides design_intent.ai_position, but no separate
    # structured AI scoping fields exist. We treat this as a review prompt, not a failure.
    if design_intent is not None and design_intent.ai_position is not None:
        signals.append(
            Signal(
                id="SIG-AI-001",
                severity="info",
                summary="AI positioning declared without structural scoping metadata",
                detail=(
                    "Design intent includes AI positioning (design_intent.ai_position), but there is no separate, "
                    "structured AI scoping metadata in the course specification. This may be acceptable, but "
                    "reviewers may want explicit boundaries for traceability."
                ),
                evidence=["course.yml:design_intent.ai_position"],
                review_question="Are the scope and boundaries of AI use clearly recorded for review and assurance?",
                source="course.yml",
                tags=["ai", "intent"],
            )
        )

    # Deterministic ordering
    return sorted(signals, key=lambda s: s.id)
