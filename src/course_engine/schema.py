from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator

from .model import (
    CapabilityDomainMapping,
    CapabilityMapping,
    ContentBlock,
    CourseSpec,
    FrameworkAlignment,
    Lesson,
    Module,
    ReadingItem,
)

Audience = Literal["learner", "instructor"]
BlockType = Literal["markdown", "callout", "quiz", "reflection", "submission"]


# -------------------------
# v1.6 lesson source helpers
# -------------------------
def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _infer_title_from_md(md: str) -> Optional[str]:
    # First Markdown H1 only: "# Title"
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            return title if title else None
    return None


def _read_lesson_source(base_dir: Path, source: str) -> tuple[str, str, str]:
    """
    Returns (markdown_body, sha256, resolved_path_str).
    Resolves relative paths against base_dir.
    """
    src = Path(source)
    resolved = src if src.is_absolute() else (base_dir / src)

    try:
        md = resolved.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise ValueError(f"Lesson source file not found: {resolved}") from e
    except Exception as e:
        raise ValueError(f"Failed to read lesson source file: {resolved} ({e})") from e

    return md, _sha256_text(md), str(resolved)


# -------------------------
# Pydantic models
# -------------------------
class ReadingItemModel(BaseModel):
    title: str = Field(min_length=1)
    url: Optional[str] = None
    required: bool = False


class ContentBlockModel(BaseModel):
    type: BlockType

    # shared
    audience: Audience = "learner"

    # markdown/callout
    body: Optional[str] = None
    title: Optional[str] = None
    style: Optional[str] = None  # note|warning|tip|important

    # quiz/reflection/submission
    prompt: Optional[str] = None
    options: list[str] = Field(default_factory=list)

    # quiz-only (render-only in v0.3)
    answer: Optional[int] = None  # 0-based index into options
    solution: Optional[str] = None

    def validate_semantics(self) -> None:
        if self.type in ("markdown", "callout"):
            if not self.body or not self.body.strip():
                raise ValueError(f"{self.type} block requires non-empty 'body'")

        elif self.type == "quiz":
            if not self.prompt or not self.prompt.strip():
                raise ValueError("quiz block requires non-empty 'prompt'")
            if len(self.options) < 2:
                raise ValueError("quiz block requires 'options' with at least 2 items")
            if self.answer is not None:
                if self.answer < 0 or self.answer >= len(self.options):
                    raise ValueError("quiz 'answer' is out of range for provided options")

        elif self.type in ("reflection", "submission"):
            if not self.prompt or not self.prompt.strip():
                raise ValueError(f"{self.type} block requires non-empty 'prompt'")


class LessonModel(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9\-]*$")

    # v1.6: title can be omitted if source is provided (we can infer from Markdown H1)
    title: Optional[str] = None

    # v1.7: optional display label for UI/nav ("5.3.6", "A", "Key Takeaways", etc.)
    # This does not affect IDs or filenames.
    display_label: Optional[str] = None

    learning_objectives: list[str] = Field(default_factory=list)

    # v1.6: either inline blocks OR external source
    content_blocks: list[ContentBlockModel] = Field(default_factory=list)
    source: Optional[str] = None

    # metadata
    duration: Optional[int] = Field(default=None, ge=1)
    tags: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    readings: list[ReadingItemModel] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_source_or_blocks(self) -> "LessonModel":
        """
        v1.6 rule set:
          - source XOR content_blocks (cannot have both)
          - preferred: require one of them
          - compatibility: allow "minimal lesson" with neither, as long as title exists
            (we will inject a placeholder markdown block at build time)

        v1.7:
          - display_label is optional and independent (may be present in any case)
        """
        has_source = bool(self.source)
        has_blocks = bool(self.content_blocks)

        if has_source and has_blocks:
            raise ValueError("Lesson cannot have both 'source' and 'content_blocks'")

        # If neither source nor blocks provided, allow minimal lesson ONLY if title exists
        if not has_source and not has_blocks:
            if not self.title or not self.title.strip():
                raise ValueError(
                    "Lesson must define either 'source' or 'content_blocks' (or at minimum a non-empty 'title')"
                )
            return self

        # If no source, title is required
        if not has_source:
            if not self.title or not self.title.strip():
                raise ValueError("Lesson 'title' is required when 'source' is not provided")

        return self


class ModuleModel(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9\-]*$")
    title: str = Field(min_length=1)
    lessons: list[LessonModel] = Field(default_factory=list)


class OutputsModel(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ["html"])
    theme: Optional[str] = "cosmo"
    toc: bool = True


class FrameworkAlignmentModel(BaseModel):
    framework_name: str = Field(min_length=1)
    domains: list[str] = Field(min_length=1)
    mapping_mode: Optional[str] = None
    notes: Optional[str] = None


class DesignIntentAIPositionModel(BaseModel):
    assessments: Optional[str] = None
    learning_activities: Optional[str] = None


class DesignIntentFrameworkReferenceModel(BaseModel):
    name: str
    version: Optional[str] = None
    alignment_type: Optional[str] = None
    notes: Optional[str] = None


class DesignIntentPolicyContextModel(BaseModel):
    title: str
    scope: Optional[str] = None
    url: Optional[str] = None
    notes: Optional[str] = None


class DesignIntentReviewModel(BaseModel):
    last_reviewed: Optional[str] = None
    review_cycle: Optional[str] = None
    reflection_prompt: Optional[str] = None


class DesignIntentModel(BaseModel):
    summary: Optional[str] = None
    ai_position: Optional[DesignIntentAIPositionModel] = None
    roles_and_responsibilities: Dict[str, str] = Field(default_factory=dict)
    framework_references: List[DesignIntentFrameworkReferenceModel] = Field(default_factory=list)
    policy_context: List[DesignIntentPolicyContextModel] = Field(default_factory=list)
    review_and_evolution: Optional[DesignIntentReviewModel] = None


class CapabilityDomainMappingModel(BaseModel):
    label: Optional[str] = None
    intent: Optional[str] = None
    coverage: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class CapabilityMappingModel(BaseModel):
    framework: Optional[str] = None
    version: Optional[str] = None
    domains: dict[str, CapabilityDomainMappingModel] = Field(default_factory=dict)


class CourseMetaModel(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9\-]*$")
    title: str = Field(min_length=1)
    subtitle: Optional[str] = None
    version: str = Field(min_length=1)
    language: str = Field(default="en-GB")


class RootModel(BaseModel):
    course: CourseMetaModel
    design_intent: Optional[DesignIntentModel] = None
    framework_alignment: FrameworkAlignmentModel
    capability_mapping: Optional[CapabilityMappingModel] = None
    outputs: OutputsModel = Field(default_factory=OutputsModel)
    structure: dict = Field(default_factory=dict)

    def to_spec(self, *, base_dir: Optional[Path] = None) -> CourseSpec:
        base_dir = base_dir or Path.cwd()

        modules_raw = self.structure.get("modules", [])
        modules: list[Module] = []

        for m in modules_raw:
            mm = ModuleModel.model_validate(m)

            lessons: list[Lesson] = []
            for lm in mm.lessons:
                lesson_title = (lm.title.strip() if lm.title and lm.title.strip() else None)
                source_sha256: Optional[str] = None
                source_resolved: Optional[str] = None
                source_path: Optional[str] = lm.source

                # ---- Case 1: lesson.source (v1.6) ----
                if lm.source:
                    md, h, resolved = _read_lesson_source(base_dir, lm.source)
                    source_sha256 = h
                    source_resolved = resolved

                    if not lesson_title:
                        inferred = _infer_title_from_md(md)
                        if inferred:
                            lesson_title = inferred

                    if not lesson_title:
                        raise ValueError(
                            f"Lesson '{lm.id}' has 'source' but no title could be inferred. "
                            f"Add 'title' in course.yml or include a '# Heading' in the source file."
                        )

                    # One markdown block from source file
                    ContentBlockModel(type="markdown", body=md).validate_semantics()
                    blocks = [
                        ContentBlock(
                            type="markdown",
                            audience="learner",
                            body=md,
                            title=None,
                            style=None,
                            prompt=None,
                            options=[],
                            answer=None,
                            solution=None,
                        )
                    ]

                # ---- Case 2: inline content_blocks ----
                elif lm.content_blocks:
                    for b in lm.content_blocks:
                        b.validate_semantics()

                    blocks = [
                        ContentBlock(
                            type=b.type,
                            audience=b.audience,
                            body=b.body,
                            title=b.title,
                            style=b.style,
                            prompt=b.prompt,
                            options=list(b.options),
                            answer=b.answer,
                            solution=b.solution,
                        )
                        for b in lm.content_blocks
                    ]

                    lesson_title = lesson_title or lm.title  # type: ignore[assignment]

                # ---- Case 3: minimal lesson (compatibility) ----
                else:
                    # Inject a placeholder markdown body so downstream generators always have content.
                    placeholder = "Content pending."
                    ContentBlockModel(type="markdown", body=placeholder).validate_semantics()
                    blocks = [
                        ContentBlock(
                            type="markdown",
                            audience="learner",
                            body=placeholder,
                            title=None,
                            style=None,
                            prompt=None,
                            options=[],
                            answer=None,
                            solution=None,
                        )
                    ]
                    lesson_title = lesson_title or lm.title  # type: ignore[assignment]

                readings = [ReadingItem(title=r.title, url=r.url, required=r.required) for r in lm.readings]

                lessons.append(
                    Lesson(
                        id=lm.id,
                        title=lesson_title,  # type: ignore[arg-type]
                        display_label=(lm.display_label.strip() if lm.display_label and lm.display_label.strip() else None),
                        learning_objectives=list(lm.learning_objectives),
                        content_blocks=blocks,
                        duration=lm.duration,
                        tags=list(lm.tags),
                        prerequisites=list(lm.prerequisites),
                        readings=readings,
                        source=source_path,
                        source_sha256=source_sha256,
                        source_resolved_path=source_resolved,
                    )
                )

            modules.append(Module(id=mm.id, title=mm.title, lessons=lessons))

        capability_mapping = None
        if self.capability_mapping is not None:
            capability_mapping = CapabilityMapping(
                framework=self.capability_mapping.framework,
                version=self.capability_mapping.version,
                domains={
                    k: CapabilityDomainMapping(
                        label=v.label,
                        intent=v.intent,
                        coverage=list(v.coverage),
                        evidence=list(v.evidence),
                    )
                    for k, v in self.capability_mapping.domains.items()
                },
            )

        # Persist declared framework_alignment in both flattened + structured form
        fw = FrameworkAlignment(
            framework_name=self.framework_alignment.framework_name,
            domains=list(self.framework_alignment.domains),
            mapping_mode=self.framework_alignment.mapping_mode or "informational",
            notes=self.framework_alignment.notes,
        )

        return CourseSpec(
            id=self.course.id,
            title=self.course.title,
            subtitle=self.course.subtitle,
            version=self.course.version,
            language=self.course.language,
            # existing flat fields (keep)
            framework_name=self.framework_alignment.framework_name,
            domains=list(self.framework_alignment.domains),
            # new structured field (v1.6)
            framework_alignment=fw,
            formats=self.outputs.formats,
            theme=self.outputs.theme,
            toc=self.outputs.toc,
            capability_mapping=capability_mapping,
            modules=modules,
        )


# -------------------------
# User-friendly guardrails
# -------------------------
def _preflight_course_dict(data: dict) -> None:
    """
    v1.6: Fail fast with clear messages for common authoring mistakes.

    Note:
      - structure.modules MAY be an empty list (allowed for tests / minimal specs)
      - generators may still choose to enforce "at least one module" elsewhere if desired
    """
    if not isinstance(data, dict):
        raise ValueError("course.yml must parse to a YAML mapping (top-level object).")

    # Common legacy/alternate layouts
    if "modules" in data and "structure" not in data:
        raise ValueError(
            "Invalid course.yml structure: found top-level 'modules'.\n"
            "Course Engine expects modules under:\n"
            "  structure:\n"
            "    modules:\n"
            "Move 'modules:' under 'structure:' and try again."
        )

    if "content" in data:
        raise ValueError(
            "Unsupported key in course.yml: found top-level 'content:'.\n"
            "Course Engine v1.6 expects lesson content to be provided via:\n"
            "  structure.modules[].lessons[].content_blocks\n"
            "or\n"
            "  structure.modules[].lessons[].source\n"
            "Remove 'content:' and reference files directly in lesson.source."
        )

    struct = data.get("structure")
    if struct is None or not isinstance(struct, dict):
        raise ValueError(
            "Missing required key: 'structure'.\n"
            "Expected:\n"
            "  structure:\n"
            "    modules:\n"
            "      - id: ...\n"
            "        title: ...\n"
            "        lessons: ..."
        )

    mods = struct.get("modules")
    if mods is None or not isinstance(mods, list):
        raise ValueError("structure.modules must be a list (it may be empty).")


def validate_course_dict(data: dict, *, source_course_yml: Optional[Path] = None) -> CourseSpec:
    """
    source_course_yml (optional) lets the validator resolve lesson.source paths
    relative to the course.yml location. If omitted, Path.cwd() is used.
    """
    try:
        _preflight_course_dict(data)
        root = RootModel.model_validate(data)
        base_dir = source_course_yml.parent if source_course_yml is not None else None
        return root.to_spec(base_dir=base_dir)
    except ValidationError as e:
        raise ValueError(str(e)) from e
    except ValueError as e:
        raise ValueError(str(e)) from e
