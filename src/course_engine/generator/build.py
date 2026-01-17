from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Optional

from ..model import CourseSpec, Module, Lesson
from ..utils.fileops import ensure_empty_dir, write_text
from .templates import get_env


# Cache PDF preflight per process
_PDF_PREFLIGHT_OK: Optional[bool] = None


def _require_quarto() -> None:
    """Fail fast if Quarto is not installed."""
    if shutil.which("quarto") is None:
        raise RuntimeError(
            "Quarto not found.\n\n"
            "Install Quarto and ensure `quarto` is on PATH.\n"
            "Quarto: https://quarto.org/"
        )


def _require_pdf_toolchain() -> None:
    """
    Fail fast if PDF rendering is not available.

    Uses a minimal Quarto->PDF smoke test rather than parsing `quarto check`
    output (which can vary).
    """
    global _PDF_PREFLIGHT_OK

    if _PDF_PREFLIGHT_OK is True:
        return

    _require_quarto()

    with tempfile.TemporaryDirectory(prefix="course-engine-pdf-check-") as td:
        tdir = Path(td)

        (tdir / "index.qmd").write_text(
            "# PDF preflight\n\nIf you can read this, PDF rendering works.\n",
            encoding="utf-8",
        )

        (tdir / "_quarto.yml").write_text(
            "project:\n"
            "  type: default\n"
            "\n"
            "format:\n"
            "  pdf:\n"
            "    toc: false\n"
            "execute:\n"
            "  echo: false\n",
            encoding="utf-8",
        )

        cmd = ["quarto", "render", str(tdir)]
        completed = subprocess.run(cmd, capture_output=True, text=True)

        if completed.returncode != 0:
            _PDF_PREFLIGHT_OK = False

            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            details = stderr if stderr else stdout

            msg = (
                "PDF output requires a LaTeX toolchain.\n\n"
                "Recommended fix (one-time):\n"
                "  quarto install tinytex\n\n"
                "Then retry your command.\n"
            )

            # Add short diagnostic tail for debugging
            if details:
                tail = "\n".join(details.splitlines()[-25:])
                msg += "\n---\nQuarto/LaTeX details (tail):\n" + tail + "\n"

            raise RuntimeError(msg)

    _PDF_PREFLIGHT_OK = True


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "item"


@dataclass(frozen=True)
class LessonNavItem:
    module_id: str
    module_title: str
    lesson_id: str

    # Canonical lesson title (what the author wrote / what we inferred)
    lesson_title: str

    # v1.7: optional UI label (e.g., "5.3.6", "A", "5.3.A")
    lesson_display_label: Optional[str]

    # Convenience: what to show in nav lists by default (label + title)
    lesson_nav_title: str

    href: str  # path relative to project root, e.g. lessons/m1-l1-title.qmd


@dataclass(frozen=True)
class CourseNav:
    """
    Canonical navigation model (v0.2).

    This is the single source of truth for:
    - sidebar/navbar generation
    - lessons index generation
    - next/previous links
    - future exports/manifests/plugin checks
    """

    modules: list[Module]
    flat_lessons: list[LessonNavItem]
    href_to_module_lesson: dict[str, tuple[Module, Lesson]]


def build_course_nav(spec: CourseSpec) -> CourseNav:
    flat: list[LessonNavItem] = []
    href_map: dict[str, tuple[Module, Lesson]] = {}

    for module in spec.modules:
        for lesson in module.lessons:
            filename = f"{module.id}-{lesson.id}-{slugify(lesson.title)}.qmd"
            href = f"lessons/{filename}"

            # v1.7: optional display label (safe even if older Lesson instances exist)
            label = getattr(lesson, "display_label", None)
            label = label.strip() if isinstance(label, str) and label.strip() else None

            nav_title = f"{label} {lesson.title}" if label else lesson.title

            item = LessonNavItem(
                module_id=module.id,
                module_title=module.title,
                lesson_id=lesson.id,
                lesson_title=lesson.title,
                lesson_display_label=label,
                lesson_nav_title=nav_title,
                href=href,
            )
            flat.append(item)
            href_map[href] = (module, lesson)

    return CourseNav(modules=spec.modules, flat_lessons=flat, href_to_module_lesson=href_map)


def build_quarto_project(
    spec: CourseSpec,
    out_root: Path,
    templates_dir: Path,
    *,
    preflight_pdf: bool = False,
) -> Path:
    """
    Build a multi-page Quarto website project for a course.

    Args:
        spec: Validated course spec.
        out_root: Root output directory.
        templates_dir: Directory containing Jinja templates.
        preflight_pdf: If True, run a PDF toolchain preflight check and fail fast
                       with a friendly TinyTeX instruction if PDF is unavailable.

    Returns:
        Path to the built Quarto project directory.
    """
    if preflight_pdf:
        _require_pdf_toolchain()
    else:
        _require_quarto()

    out_dir = out_root / spec.id
    ensure_empty_dir(out_dir)

    env = get_env(templates_dir)
    nav = build_course_nav(spec)

    # Core project files
    write_text(out_dir / "_quarto.yml", env.get_template("_quarto.yml.j2").render(spec=spec, nav=nav))
    write_text(out_dir / "index.qmd", env.get_template("index.qmd.j2").render(spec=spec, nav=nav))

    # Lessons index page (so "Lessons" is a real destination)
    # This template should create links to each lesson using item.href (already includes "lessons/...")
    write_text(
        out_dir / "lessons" / "index.qmd",
        env.get_template("lessons_index.qmd.j2").render(spec=spec, nav=nav),
    )

    # Lesson pages + prev/next links
    lesson_template = env.get_template("lesson.qmd.j2")

    # Map href -> index so we can compute prev/next reliably
    href_to_idx = {item.href: i for i, item in enumerate(nav.flat_lessons)}

    for item in nav.flat_lessons:
        i = href_to_idx[item.href]
        prev_item = nav.flat_lessons[i - 1] if i > 0 else None
        next_item = nav.flat_lessons[i + 1] if i < (len(nav.flat_lessons) - 1) else None

        module, lesson = nav.href_to_module_lesson[item.href]

        # IMPORTANT:
        # - `current` now includes lesson_display_label + lesson_nav_title
        # - We still pass `module` and `lesson` to avoid breaking existing templates.
        write_text(
            out_dir / item.href,
            lesson_template.render(
                spec=spec,
                nav=nav,
                module=module,
                lesson=lesson,
                current=item,
                prev_item=prev_item,
                next_item=next_item,
            ),
        )

    return out_dir
