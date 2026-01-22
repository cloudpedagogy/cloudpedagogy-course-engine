# src/course_engine/cli.py

from __future__ import annotations

import json
import platform
import shutil
import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from jinja2 import Template

from . import __version__
from .explain import explain_course_yml
from .explain.artefact import explain_dist_dir
from .explain.text import explain_payload_to_text
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
    load_profile,  # v1.3 legacy profile file loader
    validate_manifest,
    validation_to_json,
    validation_to_text,
)

# v1.4+ policy support (profiles, presets, external policy files)
from .utils.policy import (
    load_policy_source,
    list_profiles as policy_list_profiles,
    resolve_profile as policy_resolve_profile,
)

app = typer.Typer(no_args_is_help=True)


@app.callback(invoke_without_command=True)
def _main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the installed course-engine version and exit.",
        is_eager=True,
    )
) -> None:
    """
    Global options.

    Typer versions vary in built-in version support, so implement --version
    via a callback (Click-compatible) to stay CI-safe.
    """
    if version:
        typer.echo(__version__)
        raise typer.Exit(code=0)


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

    fw = m.get("framework_alignment")
    if not fw:
        typer.echo("Framework alignment: none")
    else:
        typer.echo("Framework alignment:")
        typer.echo(f"  Framework: {fw.get('framework_name') or '—'}")
        domains = fw.get("domains") or []
        if domains:
            typer.echo(f"  Domains: {', '.join(domains)}")
        else:
            typer.echo("  Domains: —")
        if fw.get("mapping_mode"):
            typer.echo(f"  Mapping mode: {fw.get('mapping_mode')}")
        if fw.get("notes") not in (None, ""):
            typer.echo(f"  Notes: {fw.get('notes')}")

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

    ls = m.get("lesson_sources")
    if ls:
        typer.echo("Lesson sources:")
        typer.echo(f"  Count: {ls.get('count') or 0}")
        typer.echo(f"  Status: {ls.get('status') or 'informational (not enforced)'}")

    sigs = m.get("signals") or []
    if isinstance(sigs, list) and sigs:
        typer.echo("Signals:")
        typer.echo(f"  Count: {len(sigs)}")

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
def explain(
    path: str = typer.Argument(..., help="Path to course.yml OR dist/<course> folder to explain."),
    json_out: bool = typer.Option(
        True,
        "--json",
        help="Legacy/compatibility flag (default: true). Prefer --format json|text.",
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format",
        help="Output format: json | text (preferred; overrides --json).",
    ),
    out: Optional[str] = typer.Option(None, "--out", help="Write output to a file instead of stdout."),
) -> None:
    """
    Explain an input into a governance-friendly artefact (explain-only).

    Supported inputs:
      - course.yml (source explain)
      - dist/<course> directory containing manifest.json (artefact explain)

    This command does not build outputs and does not enforce policies.
    """
    if format is None:
        resolved_format = "json" if json_out else "text"
    else:
        resolved_format = format.strip().lower()

    allowed = {"json", "text"}
    if resolved_format not in allowed:
        raise typer.BadParameter("Unknown --format. Use: json | text")

    command_str = "course-engine " + " ".join(sys.argv[1:])

    p = Path(path)

    if p.exists() and p.is_dir():
        payload = explain_dist_dir(
            dist_dir=p,
            engine_version=__version__,
            command=command_str,
        )
    else:
        payload = explain_course_yml(
            course_yml_path=path,
            engine_version=__version__,
            command=command_str,
        )

    if resolved_format == "json":
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        text = explain_payload_to_text(payload) + "\n"

    if out:
        write_text(Path(out), text)
    else:
        typer.echo(text, nl=False)


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
    out_dir = Path(project_dir)

    try:
        m = load_manifest(out_dir)
    except FileNotFoundError as e:
        raise typer.BadParameter(str(e)) from e

    cap = m.get("capability_mapping")
    if cap:
        rep = build_capability_report(m)

        if json_out:
            typer.echo(report_to_json(rep), nl=False)
        else:
            typer.echo(report_to_text(rep, verbose=verbose), nl=False)

        gaps = int((rep.get("summary") or {}).get("gaps") or 0)
        if fail_on_gaps and gaps > 0:
            raise typer.Exit(code=2)
        return

    fw = m.get("framework_alignment")
    if fw:
        if json_out:
            payload = {
                "kind": "framework_alignment_only",
                "framework_alignment": fw,
                "note": "No capability_mapping present; coverage report not available.",
            }
            typer.echo(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", nl=False)
        else:
            typer.echo("Declared framework alignment (no capability mapping coverage data):")
            typer.echo(f"  Framework: {fw.get('framework_name') or '—'}")
            domains = fw.get("domains") or []
            if domains:
                typer.echo(f"  Domains: {', '.join(domains)}")
            else:
                typer.echo("  Domains: —")
            if fw.get("mapping_mode"):
                typer.echo(f"  Mapping mode: {fw.get('mapping_mode')}")
            if fw.get("notes") not in (None, ""):
                typer.echo(f"  Notes: {fw.get('notes')}")
        return

    typer.echo("No capability_mapping found in manifest.json (nothing to report).")
    raise typer.Exit(code=1)


def _looks_like_profile_path(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return False

    p = Path(v)
    if p.exists():
        return True

    return p.suffix.lower() in {".yml", ".yaml", ".json"}


@app.command()
def validate(
    project_dir: str,
    strict: bool = typer.Option(False, "--strict", help="Fail (non-zero exit) if rules are violated."),
    policy: Optional[str] = typer.Option(None, "--policy", help="Policy source: path or preset:<name>."),
    profile: Optional[str] = typer.Option(
        None,
        "--profile",
        help=(
            "Profile name within selected policy (v1.4+). "
            "If --policy is omitted and this looks like a file path, treated as v1.3 legacy profile path."
        ),
    ),
    list_profiles: bool = typer.Option(
        False,
        "--list-profiles",
        help="List available profiles for the selected policy and exit.",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Explain resolved policy/profile/rules/signals and exit (no validation).",
    ),
    json_out: bool = typer.Option(False, "--json", help="Output machine-readable JSON."),
):
    out_dir = Path(project_dir)

    if list_profiles or explain:
        try:
            pol = load_policy_source(policy)
        except ValueError as e:
            raise typer.BadParameter(str(e)) from e

        if list_profiles:
            names = policy_list_profiles(pol)
            for n in names:
                typer.echo(n)
            raise typer.Exit(code=0)

        try:
            resolved = policy_resolve_profile(pol, profile=profile)
        except ValueError as e:
            raise typer.BadParameter(str(e)) from e

        source_label = policy or "preset:baseline"

        if json_out:
            payload = {
                "policy": {
                    "source": source_label,
                    "policy_id": (pol or {}).get("policy_id"),
                    "policy_name": (pol or {}).get("policy_name"),
                    "owner": (pol or {}).get("owner"),
                    "last_updated": (pol or {}).get("last_updated"),
                    "policy_version": (pol or {}).get("policy_version"),
                },
                "profile": {
                    "name": resolved.get("profile"),
                    "description": resolved.get("description"),
                },
                "chain": resolved.get("chain") or [],
                "rules": resolved.get("rules") or {},
                "signals": resolved.get("signals") or {},
                "strict": bool(strict),
            }
            typer.echo(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", nl=False)
            raise typer.Exit(code=0)

        typer.echo(f"Policy: {source_label}")
        typer.echo(f"Profile: {resolved.get('profile')}")
        typer.echo(f"Strict: {'ON' if strict else 'OFF'}")
        chain = resolved.get("chain") or []
        typer.echo(f"Chain: {' -> '.join(chain) if chain else '—'}")
        typer.echo("Resolved rules:")
        typer.echo(str(resolved.get("rules") or {}))
        typer.echo("Resolved signals:")
        typer.echo(str(resolved.get("signals") or {}))
        raise typer.Exit(code=0)

    try:
        manifest = load_manifest(out_dir)
    except FileNotFoundError as e:
        raise typer.BadParameter(str(e)) from e

    rep = build_capability_report(manifest)

    if policy is not None:
        try:
            pol = load_policy_source(policy)
        except ValueError as e:
            raise typer.BadParameter(str(e)) from e

        try:
            resolved = policy_resolve_profile(pol, profile=profile)
        except ValueError as e:
            raise typer.BadParameter(str(e)) from e

        prof = {
            "name": resolved.get("profile"),
            "rules": resolved.get("rules") or {},
            "signals": resolved.get("signals") or {},
            "source": policy,
        }

    elif profile and _looks_like_profile_path(profile):
        try:
            prof = load_profile(profile)
        except FileNotFoundError as e:
            raise typer.BadParameter(str(e)) from e

        # Defensive: legacy profiles may not include signals
        if "signals" not in prof:
            prof["signals"] = {"default_action": "info", "overrides": {}, "ignore": []}

    else:
        prof = load_profile(None)

        # Defensive: engine defaults should always include signals too.
        # (Keeps validate_manifest() stable if defaults change.)
        if "signals" not in prof:
            prof["signals"] = {"default_action": "info", "overrides": {}, "ignore": []}

    result = validate_manifest(manifest=manifest, report=rep, profile=prof, strict=strict)

    if json_out:
        typer.echo(validation_to_json(result), nl=False)
    else:
        typer.echo(validation_to_text(result), nl=False)

    # Exit behaviour:
    # - If --strict is set and validation failed, exit 3 (existing convention).
    # - In non-strict mode, rule violations remain warnings, but signal action=error gates CI.
    if not result.ok:
        if strict:
            raise typer.Exit(code=3)
        if getattr(result, "signal_errors", []):
            raise typer.Exit(code=3)


def _is_dangerous_delete_target(p: Path) -> bool:
    rp = p.resolve()

    if rp == Path("/"):
        return True

    home = Path.home().resolve()
    if rp == home:
        return True

    cwd = Path.cwd().resolve()
    if rp == cwd or rp == cwd.parent:
        return True

    if len(rp.parts) <= 3:
        return True

    return False


def _maybe_overwrite_dir(target: Path, *, overwrite: bool) -> None:
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
    course_path = Path(course_yml)
    out_root = Path(out)
    templates_dir = Path(templates) if templates else DEFAULT_TEMPLATES_DIR

    data = yaml.safe_load(course_path.read_text(encoding="utf-8"))

    try:
        spec = validate_course_dict(data, source_course_yml=course_path)
    except ValueError as e:
        raise typer.BadParameter(f"Invalid course.yml: {e}") from e

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
    p = Path(project_dir)

    render_quarto(p, input_file=input, to=to)
    typer.echo("Render complete.")

    try:
        mp = update_manifest_after_render(p, to=to, input_file=input, include_hashes=True)
        typer.echo(f"Updated manifest: {mp}")
    except FileNotFoundError:
        pass
