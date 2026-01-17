from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


Audience = Literal["learner", "instructor"]
ContentBlockType = Literal["markdown", "callout", "quiz", "reflection", "submission"]


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
    options: list[str] = field(default_factory=list)

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

    learning_objectives: list[str] = field(default_factory=list)
    content_blocks: list[ContentBlock] = field(default_factory=list)

    # v0.3 metadata
    duration: Optional[int] = None  # minutes
    tags: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)  # lesson ids
    readings: list[ReadingItem] = field(default_factory=list)  # reading list

    # v1.6: optional external source provenance (informational)
    source: Optional[str] = None  # as declared in course.yml (relative or absolute)
    source_sha256: Optional[str] = None  # hash of the source markdown content
    source_resolved_path: Optional[str] = None  # resolved absolute path used at build time


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    lessons: list[Lesson] = field(default_factory=list)


@dataclass(frozen=True)
class CapabilityDomainMapping:
    """Informational mapping for a single capability domain (v1.1)."""

    label: Optional[str] = None
    intent: Optional[str] = None
    coverage: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CapabilityMapping:
    """Top-level, non-enforced capability mapping metadata (v1.1)."""

    framework: Optional[str] = None
    version: Optional[str] = None
    domains: dict[str, CapabilityDomainMapping] = field(default_factory=dict)


@dataclass(frozen=True)
class FrameworkAlignment:
    """
    Declared framework alignment metadata (v1.6).

    This is declared intent (not lesson-level coverage evidence).
    Stored for auditability and manifest persistence.
    """
    framework_name: str
    domains: list[str] = field(default_factory=list)

    # Optional future extensions (safe defaults; can be populated later)
    mapping_mode: Optional[str] = None  # e.g., "informational"
    notes: Optional[str] = None


@dataclass(frozen=True)
class CourseSpec:
    id: str
    title: str
    subtitle: str | None
    version: str
    language: str

    # Existing flat fields (keep for backward compatibility)
    framework_name: str
    domains: list[str]

    # Non-default fields MUST come before any default fields (dataclasses rule)
    formats: list[str]
    theme: str | None
    toc: bool

    # NEW in v1.6: preserve the declared framework_alignment block as-is
    framework_alignment: FrameworkAlignment | None = None

    capability_mapping: CapabilityMapping | None = None
    modules: list[Module] = field(default_factory=list)
