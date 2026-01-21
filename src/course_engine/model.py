# src/course_engine/model.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


Audience = Literal["learner", "instructor"]
ContentBlockType = Literal["markdown", "callout", "quiz", "reflection", "submission"]

# v1.13: absence signalling
SignalSeverity = Literal["info", "warning"]


@dataclass(frozen=True)
class Signal:
    """
    v1.13: Absence signal (governance object)

    Signals are informational / advisory only:
    - non-blocking by default
    - no scoring, ranking, or compliance claims
    - designed for explain + manifest inspection surfaces
    """

    # Required (contract-stable)
    id: str
    severity: SignalSeverity
    summary: str
    detail: str
    evidence: List[str] = field(default_factory=list)

    # Optional (contract-stable)
    review_question: Optional[str] = None
    source: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """
        Stable, JSON-serialisable representation.

        Notes:
        - Always includes optional keys with explicit nulls / empty lists
          to keep downstream consumers stable.
        - Do not add computed/scoring fields here.
        """
        return {
            "id": self.id,
            "severity": self.severity,
            "summary": self.summary,
            "detail": self.detail,
            "evidence": list(self.evidence),
            "review_question": self.review_question,
            "source": self.source,
            "tags": list(self.tags),
        }


# -------------------------
# v1.12+ design intent (model layer)
# -------------------------

@dataclass(frozen=True)
class DesignIntentAIPosition:
    """
    Optional, descriptive AI positioning (informational only).
    Mirrors schema fields in a governance-readable structure.
    """
    assessments: Optional[str] = None
    learning_activities: Optional[str] = None


@dataclass(frozen=True)
class DesignIntentFrameworkReference:
    name: str
    version: Optional[str] = None
    alignment_type: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class DesignIntentPolicyContext:
    title: str
    scope: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None


@dataclass(frozen=True)
class DesignIntentReview:
    last_reviewed: Optional[str] = None
    review_cycle: Optional[str] = None
    reflection_prompt: Optional[str] = None


@dataclass(frozen=True)
class DesignIntent:
    """
    v1.12+: Design intent is a governance object:
    - optional
    - informational only
    - surfaced via explain and recorded in manifest
    """
    summary: Optional[str] = None
    ai_position: Optional[DesignIntentAIPosition] = None
    roles_and_responsibilities: Dict[str, str] = field(default_factory=dict)
    framework_references: List[DesignIntentFrameworkReference] = field(default_factory=list)
    policy_context: List[DesignIntentPolicyContext] = field(default_factory=list)
    review_and_evolution: Optional[DesignIntentReview] = None


# -------------------------
# course content structures
# -------------------------

@dataclass(frozen=True)
class ReadingItem:
    title: str
    url: Optional[str] = None
    required: bool = False


@dataclass(frozen=True)
class ContentBlock:
    type: ContentBlockType

    # markdown/callout
    body: Optional[str] = None
    title: Optional[str] = None
    style: Optional[str] = None  # note|warning|tip|important
    audience: Audience = "learner"

    # quiz/reflection/submission
    prompt: Optional[str] = None
    options: List[str] = field(default_factory=list)

    # quiz-only (render-only in v0.3)
    answer: Optional[int] = None  # 0-based index into options
    solution: Optional[str] = None  # optional explanation (render-only)


@dataclass(frozen=True)
class Lesson:
    id: str
    title: str

    # v1.7: optional display label (e.g., "5.3.6", "Key Takeaways", "Part A")
    # Used for navigation/UI only. Does NOT affect filenames, IDs, or slugs.
    display_label: Optional[str] = None

    learning_objectives: List[str] = field(default_factory=list)
    content_blocks: List[ContentBlock] = field(default_factory=list)

    # v0.3 metadata
    duration: Optional[int] = None  # minutes
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)  # lesson ids
    readings: List[ReadingItem] = field(default_factory=list)  # reading list

    # v1.6: optional external source provenance (informational)
    source: Optional[str] = None  # as declared in course.yml (relative or absolute)
    source_sha256: Optional[str] = None  # hash of the source markdown content
    source_resolved_path: Optional[str] = None  # resolved absolute path used at build time


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    lessons: List[Lesson] = field(default_factory=list)


# -------------------------
# capability + framework metadata
# -------------------------

@dataclass(frozen=True)
class CapabilityDomainMapping:
    """Informational mapping for a single capability domain (v1.1)."""
    label: Optional[str] = None
    intent: Optional[str] = None
    coverage: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CapabilityMapping:
    """Top-level, non-enforced capability mapping metadata (v1.1)."""
    framework: Optional[str] = None
    version: Optional[str] = None
    domains: Dict[str, CapabilityDomainMapping] = field(default_factory=dict)


@dataclass(frozen=True)
class FrameworkAlignment:
    """
    Declared framework alignment metadata (v1.6).

    This is declared intent (not lesson-level coverage evidence).
    Stored for auditability and manifest persistence.
    """
    framework_name: str
    domains: List[str] = field(default_factory=list)

    # Optional future extensions (safe defaults; can be populated later)
    mapping_mode: Optional[str] = None  # e.g., "informational"
    notes: Optional[str] = None


# -------------------------
# top-level course spec
# -------------------------

@dataclass(frozen=True)
class CourseSpec:
    id: str
    title: str
    subtitle: str | None
    version: str
    language: str

    # Existing flat fields (keep for backward compatibility)
    framework_name: str
    domains: List[str]

    # Non-default fields MUST come before any default fields (dataclasses rule)
    formats: List[str]
    theme: str | None
    toc: bool

    # Optional governance metadata (v1.12+)
    design_intent: DesignIntent | None = None

    # NEW in v1.6: preserve the declared framework_alignment block as-is
    framework_alignment: FrameworkAlignment | None = None

    capability_mapping: CapabilityMapping | None = None
    modules: List[Module] = field(default_factory=list)
