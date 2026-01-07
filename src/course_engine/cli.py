from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from .schema import validate_course_dict
from .generator.build import build_quarto_project
from .generator.render import render_quarto
from .generator.html_single import build_html_single_project
from .plugins import BuildContext, load_plugins
from .utils.fileops import write_text

app = typer.Typer(no_args_is_help=True)

DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


@app.command()
def init(path: str):
    """Create a starter course.yml."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)

    starter = """\
course:
  id: ai-capability-foundations
  title: "AI Capability Foundations"
  subtitle: "Practical, responsible, framework-aligned e-learning"
  version: "0.1.0"
  language: "en-GB"

framework_alignment:
  framework_name: "CloudPedagogy AI Capability Framework (2026 Edition)"
  domains:
    - Awareness
    - Co-Agency
    - Applied Practice & Innovation
    - Ethics, Equity & Impact
    - Decision-Making & Governance
    - Reflection, Learning & Renewal

outputs:
  formats: ["html"]
  theme: "cosmo"
  toc: true

structure:
  modules:
    - id: m1
      title: "Orientation"
      lessons:
        - id: l1
          title: "Welcome and how this course works"
          duration: 15
          tags: ["orientation", "foundations"]
          prerequisites: []
          readings:
            - title: "CloudPedagogy AI Capability Framework (2026 Edition)"
              url: "https://www.cloudpedagogy.com/pages/ai-capability-framework"
              required: true
          learning_objectives:
            - "Explain what AI capability means in this course context."
            - "Identify how the six domains will be used."
          content_blocks:
            - type: "markdown"
              body: |
                This is a sample lesson body.

            - type: "callout"
              style: "note"
              title: "Tip"
              body: "Keep this course practical and defensible."

            - type: "quiz"
              prompt: "Which domain focuses most directly on governance?"
              options:
                - "Awareness"
                - "Decision-Making & Governance"
                - "Reflection, Learning & Renewal"
              answer: 1
              solution: "Governance sits most directly in Decision-Making & Governance, even though other domains contribute."

            - type: "reflection"
              prompt: "Where in your current work would a capability lens reduce risk or improve clarity?"

            - type: "markdown"
              audience: "instructor"
              body: |
                Emphasise that governance is not a 'policy afterthought' — it shapes design choices from the start.
"""
    write_text(p / "course.yml", starter)
    typer.echo(f"Created {p / 'course.yml'}")


@app.command()
def build(
    course_yml: str,
    out: str = "dist",
    templates: Optional[str] = None,
    format: str = typer.Option("quarto", "--format", "-f", help="quarto | markdown | html-single"),
):
    """Build outputs from course.yml."""
    course_path = Path(course_yml)
    out_root = Path(out)
    templates_dir = Path(templates) if templates else DEFAULT_TEMPLATES_DIR

    data = yaml.safe_load(course_path.read_text(encoding="utf-8"))
    spec = validate_course_dict(data)

    if format == "quarto":
        ctx = BuildContext()
        plugins = load_plugins()
        for plg in plugins:
            plg.pre_build(spec, ctx)

        out_dir = build_quarto_project(spec, out_root=out_root, templates_dir=templates_dir)

        for plg in plugins:
            plg.post_build(spec, ctx, out_dir)

        typer.echo(f"Built Quarto project: {out_dir}")
        return

    if format == "markdown":
        # Lazy import so the CLI doesn't break if the module name changes.
        # If your markdown builder is in a different file, update the import below.
        try:
            from .generator.markdown import build_markdown_package  # type: ignore
        except ModuleNotFoundError:
            # Fallback: try common alternative names (no harm if they don't exist)
            try:
                from .generator.md import build_markdown_package  # type: ignore
            except ModuleNotFoundError:
                try:
                    from .generator.export_markdown import build_markdown_package  # type: ignore
                except ModuleNotFoundError as e:
                    raise typer.BadParameter(
                        "Markdown output is not wired: could not import build_markdown_package. "
                        "Find which file contains it and update cli.py accordingly."
                    ) from e

        out_dir = build_markdown_package(spec, out_root=out_root)
        typer.echo(f"Built Markdown package: {out_dir}")
        return

    if format == "html-single":
        out_dir = build_html_single_project(spec, out_root=out_root, templates_dir=templates_dir)
        typer.echo(f"Built single-page HTML Quarto project: {out_dir}")
        typer.echo("Next: course-engine render " + str(out_dir))
        return

    raise typer.BadParameter("Unknown --format. Use: quarto | markdown | html-single")


@app.command()
def render(project_dir: str):
    """Render an existing Quarto project directory (calls `quarto render`)."""
    p = Path(project_dir)
    render_quarto(p)
    typer.echo("Render complete.")
