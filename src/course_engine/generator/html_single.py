from __future__ import annotations

from pathlib import Path

from ..model import CourseSpec
from ..utils.fileops import ensure_empty_dir, write_text
from .build import build_course_nav  # reuse your canonical nav model
from .templates import get_env


def build_html_single_project(spec: CourseSpec, out_root: Path, templates_dir: Path) -> Path:
    """
    v0.5: Build a single-page Quarto project (handout mode).
    Output: dist/<course-id>-handout/ with _quarto.yml + index.qmd
    """
    out_dir = out_root / f"{spec.id}-handout"
    ensure_empty_dir(out_dir)

    env = get_env(templates_dir)
    nav = build_course_nav(spec)

    write_text(out_dir / "_quarto.yml", env.get_template("_handout_quarto.yml.j2").render(spec=spec, nav=nav))
    write_text(out_dir / "index.qmd", env.get_template("handout_index.qmd.j2").render(spec=spec, nav=nav))

    return out_dir
