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
    learning_objectives: list[str] = field(default_factory=list)
    content_blocks: list[ContentBlock] = field(default_factory=list)

    # v0.3 metadata
    duration: Optional[int] = None  # minutes
    tags: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)  # lesson ids
    readings: list[ReadingItem] = field(default_factory=list)  # reading list


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    lessons: list[Lesson] = field(default_factory=list)


@dataclass(frozen=True)
class CourseSpec:
    id: str
    title: str
    subtitle: str | None
    version: str
    language: str
    framework_name: str
    domains: list[str]
    formats: list[str]
    theme: str | None
    toc: bool
    modules: list[Module] = field(default_factory=list)
