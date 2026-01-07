from __future__ import annotations

from pathlib import Path
from typing import Optional

import sys
import platform
import typer
import yaml
from jinja2 import Template

from .schema import validate_course_dict
from .generator.build import build_quarto_project
from .generator.render import render_quarto
from .generator.html_single import build_html_single_project
from .plugins import BuildContext, load_plugins
from .utils.fileops import write_text
from .utils.preflight import PrereqError, has_quarto, require_pdf_toolchain

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
def check() -> None:
    """
    Check whether required external tools are installed.

    Exit codes:
      0 = ready (Quarto + PDF available)
      1 = Quarto missing
      2 = PDF toolchain missing (TinyTeX not installed / not working)
    """
    typer.echo(f"Python: {sys.version.split()[0]} ({platform.system()})")

    if has_quarto():
        typer.echo("✔ Quarto found")
    else:
        typer.echo("✖ Quarto not found")
        typer.echo("Fix: Install Quarto from https://quarto.org/")
        raise typer.Exit(code=1)

    try:
        require_pdf_toolchain()
        typer.echo("✔ PDF rendering available (LaTeX OK)")
    except PrereqError:
        typer.echo("✖ PDF rendering unavailable")
        typer.echo("Fix: quarto install tinytex")
        raise typer.Exit(code=2)

    typer.echo("\nSystem ready.")


def _write_handout_pdf_quarto_config(out_dir: Path, templates_dir: Path) -> None:
    """
    Replace the generated _quarto.yml in a handout project with a PDF-specific config.

    Expects a template file:
      templates/_handout_pdf_quarto.yml.j2

    For v0.6/v0.7 we intentionally keep this template static (no variables required).
    """
    tpl_path = templates_dir / "_handout_pdf_quarto.yml.j2"
    if not tpl_path.exists():
        raise typer.BadParameter(
            f"Missing PDF Quarto config template: {tpl_path}\n"
            "Create templates/_handout_pdf_quarto.yml.j2 to enable --format pdf."
        )

    raw = tpl_path.read_text(encoding="utf-8")
    rendered = Template(raw).render()
    write_text(out_dir / "_quarto.yml", rendered)


@app.command()
def build(
    course_yml: str,
    out: str = "dist",
    templates: Optional[str] = None,
    format: str = typer.Option(
        "quarto",
        "--format",
        "-f",
        help="quarto | markdown | html-single | pdf",
    ),
):
    """Build outputs from course.yml."""
    course_path = Path(course_yml)
    out_root = Path(out)
    templates_dir = Path(templates) if templates else DEFAULT_TEMPLATES_DIR

    data = yaml.safe_load(course_path.read_text(encoding="utf-8"))
    spec = validate_course_dict(data)

    allowed = {"quarto", "markdown", "html-single", "pdf"}
    if format not in allowed:
        raise typer.BadParameter("Unknown --format. Use: quarto | markdown | html-single | pdf")

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
        try:
            from .generator.markdown import build_markdown_package  # type: ignore
        except ModuleNotFoundError:
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

    if format == "pdf":
        # v0.7: fail fast with a friendly message if PDF prerequisites are missing
        try:
            require_pdf_toolchain()
        except PrereqError as e:
            raise typer.BadParameter(str(e)) from e

        # v0.7: build to a clearer folder name
        out_dir = out_root / f"{spec.id}-pdf"
        # Build using the existing handout generator, but target our chosen folder.
        # Easiest approach: generate into the default handout folder then copy/rename is avoided here;
        # instead we call build_html_single_project then rename after.
        tmp_dir = build_html_single_project(spec, out_root=out_root, templates_dir=templates_dir)

        # If the handout generator already uses a consistent name (e.g. <id>-handout),
        # we rename it to <id>-pdf for clarity.
        if tmp_dir != out_dir:
            if out_dir.exists():
                # ensure_empty_dir is not imported here; keep it simple
                # and avoid destructive deletes unexpectedly.
                raise typer.BadParameter(
                    f"Target output folder already exists: {out_dir}\n"
                    "Delete it or choose a different --out directory."
                )
            tmp_dir.rename(out_dir)

        # Swap in a PDF-specific _quarto.yml config.
        _write_handout_pdf_quarto_config(out_dir, templates_dir)

        typer.echo(f"Built single-page PDF Quarto project: {out_dir}")
        typer.echo("Next: course-engine render " + str(out_dir))
        return


@app.command()
def render(
    project_dir: str,
    to: Optional[str] = typer.Option(
        None, "--to", help="Optional Quarto output format override (e.g., pdf, html)."
    ),
    input: Optional[str] = typer.Option(
        None, "--input", help='Optional input file to render (e.g., "index.qmd").'
    ),
):
    """Render an existing Quarto project directory (calls `quarto render`)."""
    p = Path(project_dir)
    render_quarto(p, input_file=input, to=to)
    typer.echo("Render complete.")
