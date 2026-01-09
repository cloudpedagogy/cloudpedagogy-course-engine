from __future__ import annotations

from pathlib import Path
from typing import Optional

import platform
import shutil
import sys

import typer
import yaml
from jinja2 import Template

from .generator.build import build_quarto_project
from .generator.html_single import build_html_single_project
from .generator.render import render_quarto
from .plugins import BuildContext, load_plugins
from .schema import validate_course_dict
from .utils.fileops import write_text
from .utils.manifest import load_manifest, update_manifest_after_render, write_manifest
from .utils.preflight import PrereqError, has_quarto, require_pdf_toolchain
from .utils.reporting import build_capability_report, report_to_json, report_to_text
from .utils.validation import (
    load_profile,
    validate_manifest,
    validation_to_json,
    validation_to_text,
)

app = typer.Typer(no_args_is_help=True)

DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def _emit_manifest(spec, out_dir: Path, output_format: str, source_course_yml: Path) -> None:
    mp = write_manifest(
        spec=spec,
        out_dir=out_dir,
        output_format=output_format,
        source_course_yml=source_course_yml,
        include_hashes=True,
    )
    typer.echo(f"Wrote manifest: {mp}")


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


@app.command()
def inspect(project_dir: str) -> None:
    """Inspect an output folder's manifest.json in a human-readable way."""
    out_dir = Path(project_dir)
    try:
        m = load_manifest(out_dir)
    except FileNotFoundError as e:
        raise typer.BadParameter(str(e)) from e

    course = m.get("course", {})
    output = m.get("output", {})
    builder = m.get("builder", {})
    files = m.get("files", []) or []
    render = m.get("render")

    typer.echo(f"Course: {course.get('title')} ({course.get('id')})")
    typer.echo(f"Course version: {course.get('version')}")
    typer.echo(f"Output: {output.get('format')}  |  Dir: {output.get('out_dir')}")
    typer.echo(f"Built at (UTC): {m.get('built_at_utc')}")
    if m.get("refreshed_at_utc"):
        typer.echo(f"Refreshed at (UTC): {m.get('refreshed_at_utc')}")
    typer.echo(f"Builder: {builder.get('name')} {builder.get('version')}  |  Python {builder.get('python')}")
    if m.get("input", {}).get("course_yml"):
        typer.echo(f"Source: {m['input']['course_yml']}")

    # v1.1: capability mapping summary (informational)
    if m.get("capability_mapping") is None:
        typer.echo("Capability mapping: none")
    else:
        cap = m["capability_mapping"] or {}
        typer.echo("Capability mapping:")
        typer.echo(f"  Framework: {cap.get('framework') or '—'}")
        typer.echo(f"  Version: {cap.get('version') or '—'}")
        typer.echo(f"  Domains declared: {cap.get('domains_declared') or 0}")
        domains = cap.get("domains") or {}
        if domains:
            typer.echo(f"  Domains: {', '.join(domains.keys())}")
        typer.echo(f"  Status: {cap.get('status') or 'informational'}")

    if render:
        typer.echo("\nRender:")
        typer.echo(f"  Rendered at (UTC): {render.get('rendered_at_utc')}")
        typer.echo(f"  To: {render.get('to')}")
        typer.echo(f"  Input file: {render.get('input_file')}")

    total_bytes = 0
    for f in files:
        b = f.get("bytes")
        if isinstance(b, int):
            total_bytes += b

    typer.echo("\nFiles:")
    typer.echo(f"  Count: {len(files)}")
    typer.echo(f"  Total bytes: {total_bytes}")

    sample = files[:12]
    if sample:
        typer.echo("  Sample:")
        for f in sample:
            typer.echo(f"   - {f.get('path')}")


@app.command()
def report(
    project_dir: str,
    json_out: bool = typer.Option(False, "--json", help="Print report as JSON."),
    verbose: bool = typer.Option(False, "--verbose", help="Include full coverage/evidence lists."),
    fail_on_gaps: bool = typer.Option(
        False,
        "--fail-on-gaps",
        help="Exit with code 2 if any domain has zero coverage and zero evidence (signal-only QA gate).",
    ),
) -> None:
    """
    Produce a capability coverage report from an output folder's manifest.json.

    Reads capability mapping metadata recorded in manifest.json (v1.1+) and prints a summary.
    This is informational and does not enforce mapping correctness unless --fail-on-gaps is used.
    """
    out_dir = Path(project_dir)

    try:
        m = load_manifest(out_dir)
    except FileNotFoundError as e:
        raise typer.BadParameter(str(e)) from e

    if "capability_mapping" not in m or not m.get("capability_mapping"):
        typer.echo("No capability_mapping found in manifest.json (nothing to report).")
        raise typer.Exit(code=1)

    rep = build_capability_report(m)

    if json_out:
        typer.echo(report_to_json(rep), nl=False)
    else:
        typer.echo(report_to_text(rep, verbose=verbose), nl=False)

    gaps = int((rep.get("summary") or {}).get("gaps") or 0)
    if fail_on_gaps and gaps > 0:
        raise typer.Exit(code=2)


@app.command()
def validate(
    project_dir: str,
    strict: bool = typer.Option(False, "--strict", help="Fail (non-zero exit) if rules are violated."),
    profile: Optional[str] = typer.Option(None, "--profile", help="Path to a YAML validation profile."),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON."),
):
    """
    Validate capability mapping defensibility against rules.

    Reads manifest.json from a built output directory. Framework-agnostic.
    """
    out_dir = Path(project_dir)

    try:
        manifest = load_manifest(out_dir)
    except FileNotFoundError as e:
        raise typer.BadParameter(str(e)) from e

    # Build the v1.2 report view (domain counts + gaps)
    rep = build_capability_report(manifest)

    # Load rules
    try:
        prof = load_profile(profile)
    except FileNotFoundError as e:
        raise typer.BadParameter(str(e)) from e

    result = validate_manifest(manifest=manifest, report=rep, profile=prof, strict=strict)

    if json_out:
        typer.echo(validation_to_json(result), nl=False)
    else:
        typer.echo(validation_to_text(result), nl=False)

    # Exit code: strict mode only
    if strict and not result.ok:
        raise typer.Exit(code=3)


def _is_dangerous_delete_target(p: Path) -> bool:
    """Conservative safety checks to avoid catastrophic deletes."""
    rp = p.resolve()

    if rp == Path("/"):
        return True

    home = Path.home().resolve()
    if rp == home:
        return True

    cwd = Path.cwd().resolve()
    if rp == cwd or rp == cwd.parent:
        return True

    # Intentionally conservative: avoid shallow paths like /Users, /Users/<name>, /Volumes, etc.
    if len(rp.parts) <= 3:
        return True

    return False


def _maybe_overwrite_dir(target: Path, *, overwrite: bool) -> None:
    """
    If target exists and overwrite=True, delete it safely. Otherwise error.
    """
    if not target.exists():
        return

    if not target.is_dir():
        raise typer.BadParameter(f"Output path exists but is not a directory: {target}")

    if not overwrite:
        raise typer.BadParameter(
            f"Target output folder already exists: {target}\n"
            "Delete it, choose a different --out directory, or pass --overwrite."
        )

    if _is_dangerous_delete_target(target):
        raise typer.BadParameter(
            f"Refusing to delete dangerous path: {target.resolve()}\n"
            "Choose a specific output folder (e.g., dist/<course-id>-pdf)."
        )

    shutil.rmtree(target.resolve())
    typer.echo(f"Overwrote existing output: {target.resolve()}")


@app.command()
def clean(
    path: str,
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt."),
) -> None:
    """
    Delete a generated output directory safely.

    Example:
      course-engine clean dist/ai-capability-foundations-pdf
    """
    p = Path(path)

    if not p.exists():
        typer.echo(f"Nothing to clean: {p} (does not exist)")
        raise typer.Exit(code=1)

    if not p.is_dir():
        raise typer.BadParameter(f"Refusing to clean: {p} (not a directory)")

    if _is_dangerous_delete_target(p):
        raise typer.BadParameter(
            f"Refusing to delete dangerous path: {p.resolve()}\n"
            "Pick a specific output folder (e.g., dist/<course-id>-pdf)."
        )

    resolved = p.resolve()

    if not yes:
        typer.echo(f"About to delete: {resolved}")
        ok = typer.confirm("Proceed?", default=False)
        if not ok:
            typer.echo("Cancelled.")
            raise typer.Exit(code=0)

    shutil.rmtree(resolved)
    typer.echo(f"Deleted: {resolved}")


def _write_handout_pdf_quarto_config(out_dir: Path, templates_dir: Path) -> None:
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
    format: str = typer.Option("quarto", "--format", "-f", help="quarto | markdown | html-single | pdf"),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="If the output directory exists, delete it first and rebuild (safe, opt-in).",
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
        out_dir = out_root / spec.id
        _maybe_overwrite_dir(out_dir, overwrite=overwrite)

        ctx = BuildContext()
        plugins = load_plugins()
        for plg in plugins:
            plg.pre_build(spec, ctx)

        out_dir = build_quarto_project(spec, out_root=out_root, templates_dir=templates_dir)

        for plg in plugins:
            plg.post_build(spec, ctx, out_dir)

        typer.echo(f"Built Quarto project: {out_dir}")
        _emit_manifest(spec, out_dir, "quarto", course_path)
        return

    if format == "markdown":
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
        _emit_manifest(spec, out_dir, "markdown", course_path)
        return

    if format == "html-single":
        out_dir = build_html_single_project(spec, out_root=out_root, templates_dir=templates_dir)
        typer.echo(f"Built single-page HTML Quarto project: {out_dir}")
        _emit_manifest(spec, out_dir, "html-single", course_path)
        typer.echo("Next: course-engine render " + str(out_dir))
        return

    if format == "pdf":
        try:
            require_pdf_toolchain()
        except PrereqError as e:
            raise typer.BadParameter(str(e)) from e

        out_dir = out_root / f"{spec.id}-pdf"
        _maybe_overwrite_dir(out_dir, overwrite=overwrite)

        tmp_dir = build_html_single_project(spec, out_root=out_root, templates_dir=templates_dir)

        if tmp_dir != out_dir:
            if out_dir.exists():
                # If tmp_dir already exists, it may be the one we are renaming from.
                # But if out_dir exists here, it's an actual conflict.
                raise typer.BadParameter(
                    f"Target output folder already exists: {out_dir}\n"
                    "Delete it, choose a different --out directory, or pass --overwrite."
                )
            tmp_dir.rename(out_dir)

        _write_handout_pdf_quarto_config(out_dir, templates_dir)

        typer.echo(f"Built single-page PDF Quarto project: {out_dir}")
        _emit_manifest(spec, out_dir, "pdf", course_path)
        typer.echo("Next: course-engine render " + str(out_dir))
        return


@app.command()
def render(
    project_dir: str,
    to: Optional[str] = typer.Option(None, "--to", help="Optional Quarto output format override (e.g., pdf, html)."),
    input: Optional[str] = typer.Option(None, "--input", help='Optional input file to render (e.g., "index.qmd").'),
):
    """Render an existing Quarto project directory (calls `quarto render`)."""
    p = Path(project_dir)

    render_quarto(p, input_file=input, to=to)
    typer.echo("Render complete.")

    # v0.9: if a manifest exists, update it to capture rendered outputs
    try:
        mp = update_manifest_after_render(p, to=to, input_file=input, include_hashes=True)
        typer.echo(f"Updated manifest: {mp}")
    except FileNotFoundError:
        # Not fatal: render can be used on arbitrary Quarto projects
        pass
