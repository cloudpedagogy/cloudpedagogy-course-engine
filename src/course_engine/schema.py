from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError

from .model import CourseSpec, Module, Lesson, ContentBlock, ReadingItem


Audience = Literal["learner", "instructor"]
BlockType = Literal["markdown", "callout", "quiz", "reflection", "submission"]


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
        # Keep v0.3 light: basic checks so authors don’t create broken blocks.
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
    title: str = Field(min_length=1)
    learning_objectives: list[str] = Field(default_factory=list)
    content_blocks: list[ContentBlockModel] = Field(default_factory=list)

    # v0.3 metadata
    duration: Optional[int] = Field(default=None, ge=1)
    tags: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    readings: list[ReadingItemModel] = Field(default_factory=list)


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


class CourseMetaModel(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9\-]*$")
    title: str = Field(min_length=1)
    subtitle: Optional[str] = None
    version: str = Field(min_length=1)
    language: str = Field(default="en-GB")


class RootModel(BaseModel):
    course: CourseMetaModel
    framework_alignment: FrameworkAlignmentModel
    outputs: OutputsModel = Field(default_factory=OutputsModel)
    structure: dict = Field(default_factory=dict)

    def to_spec(self) -> CourseSpec:
        modules_raw = self.structure.get("modules", [])
        modules: list[Module] = []

        for m in modules_raw:
            mm = ModuleModel.model_validate(m)

            lessons: list[Lesson] = []
            for lm in mm.lessons:
                # semantic checks
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

                readings = [
                    ReadingItem(title=r.title, url=r.url, required=r.required) for r in lm.readings
                ]

                lessons.append(
                    Lesson(
                        id=lm.id,
                        title=lm.title,
                        learning_objectives=list(lm.learning_objectives),
                        content_blocks=blocks,
                        duration=lm.duration,
                        tags=list(lm.tags),
                        prerequisites=list(lm.prerequisites),
                        readings=readings,
                    )
                )

            modules.append(Module(id=mm.id, title=mm.title, lessons=lessons))

        return CourseSpec(
            id=self.course.id,
            title=self.course.title,
            subtitle=self.course.subtitle,
            version=self.course.version,
            language=self.course.language,
            framework_name=self.framework_alignment.framework_name,
            domains=self.framework_alignment.domains,
            formats=self.outputs.formats,
            theme=self.outputs.theme,
            toc=self.outputs.toc,
            modules=modules,
        )


def validate_course_dict(data: dict) -> CourseSpec:
    try:
        root = RootModel.model_validate(data)
        return root.to_spec()
    except ValidationError as e:
        raise ValueError(str(e)) from e
    except ValueError as e:
        # semantic validation errors from validate_semantics()
        raise ValueError(str(e)) from e
