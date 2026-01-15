from __future__ import annotations

from pathlib import Path
from typing import Optional

from ..generator.build import build_course_nav  # reuse the canonical nav model
from ..model import ContentBlock, CourseSpec, Lesson, ReadingItem
from ..utils.fileops import ensure_empty_dir, write_text


def _md_link(text: str, url: Optional[str]) -> str:
    if url:
        return f"[{text}]({url})"
    return text


def _render_readings(readings: list[ReadingItem]) -> str:
    if not readings:
        return ""
    lines = ["## Readings", ""]
    for reading in readings:
        prefix = "(Required)" if reading.required else "(Optional)"
        lines.append(f"- {prefix} {_md_link(reading.title, reading.url)}")
    lines.append("")
    return "\n".join(lines)


def _render_lesson_metadata(lesson: Lesson) -> str:
    parts: list[str] = []
    if lesson.duration is not None:
        parts.append(f"- **Estimated time:** {lesson.duration} minutes")
    if lesson.tags:
        parts.append(f"- **Tags:** {', '.join(lesson.tags)}")
    if lesson.prerequisites:
        parts.append(f"- **Prerequisites:** {', '.join(lesson.prerequisites)}")

    if not parts:
        return ""

    return "## Lesson details\n\n" + "\n".join(parts) + "\n"


def _render_learning_objectives(lesson: Lesson) -> str:
    lines = ["## Learning objectives", ""]
    if lesson.learning_objectives:
        for lo in lesson.learning_objectives:
            lines.append(f"- {lo}")
    else:
        lines.append("- (Add learning objectives)")
    lines.append("")
    return "\n".join(lines)


def _render_block(block: ContentBlock) -> str:
    """
    v0.4 rule: portable markdown, no Quarto directives.
    - markdown: render body
    - callout: render as bold label + blockquote
    - quiz: render question + options (NO answers by default)
    - reflection: render prompt
    - submission: render prompt (minimal)
    - instructor-only blocks: render under an 'Instructor notes' heading style
    """
    audience = getattr(block, "audience", "learner") or "learner"

    # Instructor-only wrapper (keep it obvious but still portable)
    instructor_prefix = ""
    if audience == "instructor":
        instructor_prefix = "**Instructor note:**\n\n"

    if block.type == "markdown":
        body = (block.body or "").strip()
        return (instructor_prefix + body + "\n") if body else ""

    if block.type == "callout":
        style = (block.style or "note").upper()
        title = (block.title or style).strip()
        body = (block.body or "").strip()
        if not body:
            return ""
        # simple portable callout
        lines = [f"{instructor_prefix}**{title} ({style})**", ""]
        for line in body.splitlines():
            lines.append(f"> {line}".rstrip())
        lines.append("")
        return "\n".join(lines)

    if block.type == "quiz":
        prompt = (block.prompt or "").strip()
        options = block.options or []
        if not prompt or not options:
            return ""
        lines: list[str] = []
        if instructor_prefix:
            lines.append(instructor_prefix.rstrip())
        lines.append("## Knowledge check")
        lines.append("")
        lines.append(f"**{prompt}**")
        lines.append("")
        for opt in options:
            lines.append(f"- {opt}")
        lines.append("")
        # v0.4: do NOT show answers/solutions by default
        return "\n".join(lines)

    if block.type == "reflection":
        prompt = (block.prompt or "").strip()
        if not prompt:
            return ""
        lines: list[str] = []
        if instructor_prefix:
            lines.append(instructor_prefix.rstrip())
        lines.append("## Reflection")
        lines.append("")
        lines.append(prompt)
        lines.append("")
        return "\n".join(lines)

    if block.type == "submission":
        prompt = (block.prompt or "").strip()
        if not prompt:
            return ""
        lines: list[str] = []
        if instructor_prefix:
            lines.append(instructor_prefix.rstrip())
        lines.append("## Submission")
        lines.append("")
        lines.append(prompt)
        lines.append("")
        return "\n".join(lines)

    return ""


def render_lesson_md(spec: CourseSpec, lesson: Lesson) -> str:
    parts: list[str] = []
    parts.append(f"# {lesson.title}\n")

    meta = _render_lesson_metadata(lesson)
    if meta:
        parts.append(meta + "\n")

    parts.append(_render_learning_objectives(lesson))

    parts.append("## Content\n")
    if lesson.content_blocks:
        for block in lesson.content_blocks:
            chunk = _render_block(block)
            if chunk:
                parts.append(chunk)
    parts.append("")

    readings = _render_readings(lesson.readings or [])
    if readings:
        parts.append(readings)

    # Framework footer
    parts.append("---\n")
    parts.append(f"**Framework:** {spec.framework_name}\n")
    parts.append(f"**Domains:** {', '.join(spec.domains)}\n")

    return "\n".join(parts).strip() + "\n"


def render_course_overview_md(spec: CourseSpec) -> str:
    lines: list[str] = []
    lines.append(f"# {spec.title}")
    if spec.subtitle:
        lines.append(f"\n{spec.subtitle}\n")
    else:
        lines.append("\n")

    lines.append("## Course information\n")
    lines.append(f"- **Course ID:** `{spec.id}`")
    lines.append(f"- **Version:** `{spec.version}`")
    lines.append(f"- **Framework:** {spec.framework_name}")
    lines.append("")

    lines.append("## Capability domains\n")
    for domain in spec.domains:
        lines.append(f"- {domain}")
    lines.append("")

    lines.append("## Modules\n")
    for module in spec.modules:
        lines.append(f"### {module.title}")
        for lesson in module.lessons:
            lines.append(f"- {lesson.title}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_markdown_package(spec: CourseSpec, out_root: Path) -> Path:
    """
    v0.4: Create a portable Markdown package.

    Output structure:
      dist/<course-id>-markdown/
        README.md
        course.md
        modules/<module-id>-<slug>.md
        lessons/<module-id>-<lesson-id>-<slug>.md
    """
    out_dir = out_root / f"{spec.id}-markdown"
    ensure_empty_dir(out_dir)

    nav = build_course_nav(spec)

    # Top-level entrypoints
    write_text(out_dir / "README.md", f"# {spec.title}\n\nSee `course.md`.\n")
    write_text(out_dir / "course.md", render_course_overview_md(spec))

    # Modules (minimal: one file per module listing lessons)
    modules_dir = out_dir / "modules"
    lessons_dir = out_dir / "lessons"
    modules_dir.mkdir(parents=True, exist_ok=True)
    lessons_dir.mkdir(parents=True, exist_ok=True)

    for module in spec.modules:
        mod_lines = [f"# {module.title}\n", "## Lessons\n"]
        for item in nav.flat_lessons:
            if item.module_id == module.id:
                # link to lesson md file (same filename, but .md)
                lesson_filename = item.href.split("/")[-1].replace(".qmd", ".md")
                mod_lines.append(f"- [{item.lesson_title}](../lessons/{lesson_filename})")
        mod_lines.append("")

        module_slug = module.title.lower().replace(" ", "-")
        module_filename = f"{module.id}-{module_slug}.md"
        write_text(modules_dir / module_filename, "\n".join(mod_lines))

    # Lessons
    for item in nav.flat_lessons:
        module_obj = next((m for m in spec.modules if m.id == item.module_id), None)
        if not module_obj:
            continue

        lesson_obj = next(
            (lesson for lesson in module_obj.lessons if lesson.id == item.lesson_id),
            None,
        )
        if not lesson_obj:
            continue

        lesson_md_name = item.href.split("/")[-1].replace(".qmd", ".md")
        write_text(lessons_dir / lesson_md_name, render_lesson_md(spec, lesson_obj))

    return out_dir
