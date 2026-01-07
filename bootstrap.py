#!/usr/bin/env python3
"""
bootstrap.py — Course Engine v0.1 scaffold generator (Python-only)

What it does:
- Creates the full folder structure
- Creates all files AND writes full starter contents
- Safe by default: will NOT overwrite existing files unless you pass --force

Usage:
  python bootstrap.py
  python bootstrap.py --force

After running:
  python -m venv .venv
  source .venv/bin/activate
  pip install -e ".[dev]"
  pytest
  course-engine build examples/sample-course/course.yml --out dist

Notes:
- This script uses ONLY the Python standard library.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import dedent


def write_file(path: Path, content: str, force: bool) -> None:
    """
    Write a file safely (no overwrite unless --force).

    Generator hardening:
    - Normalize newlines
    - Ensure trailing newline
    - For .py files: dedent again, strip leading blank lines (keeps __future__ legal),
      and remove an accidental leading "\" line if present.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {path} (use --force)")

    # Normalize newlines (helps across OS/editor differences)
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # Harden Python sources against template indentation mistakes
    if path.suffix == ".py":
        content = dedent(content)
        content = content.lstrip("\n")

        # Remove a stray leading "\" line if present
        lines = content.splitlines()
        if lines and lines[0].strip() == "\\":
            content = "\n".join(lines[1:])

    # Ensure newline at EOF
    if content and not content.endswith("\n"):
        content += "\n"

    path.write_text(content, encoding="utf-8")


def make_dirs(base: Path) -> None:
    # Core dirs
    (base / "src" / "course_engine" / "generator").mkdir(parents=True, exist_ok=True)
    (base / "src" / "course_engine" / "plugins").mkdir(parents=True, exist_ok=True)
    (base / "src" / "course_engine" / "utils").mkdir(parents=True, exist_ok=True)

    # Project dirs
    (base / "templates").mkdir(parents=True, exist_ok=True)
    (base / "examples" / "sample-course").mkdir(parents=True, exist_ok=True)
    (base / "tests").mkdir(parents=True, exist_ok=True)
    (base / ".github" / "workflows").mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap the course-engine repo scaffold.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite files if they already exist.",
    )
    args = parser.parse_args()
    force = args.force

    base = Path.cwd()

    make_dirs(base)

    files: dict[str, str] = {}

    files[".gitignore"] = dedent(
        """\
        .venv/
        __pycache__/
        dist/
        *.pyc
        .DS_Store
        """
    )

    files["LICENSE"] = dedent(
        """\
        MIT License

        Copyright (c) 2026 CloudPedagogy

        Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.

        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.
        """
    )

    files["pyproject.toml"] = dedent(
        """\
        [build-system]
        requires = ["setuptools>=68", "wheel"]
        build-backend = "setuptools.build_meta"

        [project]
        name = "course-engine"
        version = "0.1.0"
        description = "A Python-first, Quarto-backed course production engine aligned to CloudPedagogy AI Capability Framework and Capability-Driven Development."
        readme = "README.md"
        requires-python = ">=3.10"
        license = {text = "MIT"}
        authors = [{name = "CloudPedagogy"}]
        dependencies = [
          "typer>=0.12.0",
          "pydantic>=2.7.0",
          "pyyaml>=6.0.1",
          "jinja2>=3.1.3",
        ]

        [project.optional-dependencies]
        dev = [
          "pytest>=8.0.0",
          "pytest-cov>=5.0.0",
          "ruff>=0.5.0",
        ]

        [project.scripts]
        course-engine = "course_engine.cli:app"

        [tool.pytest.ini_options]
        testpaths = ["tests"]
        addopts = "-q"

        [tool.ruff]
        line-length = 100
        """
    )

    files["README.md"] = dedent(
        """\
        # Course Engine (v0.1)

        A Python-first, Quarto-backed course production engine designed to generate consistent, reproducible e-learning course artefacts from a structured `course.yml`.

        ## Why this exists
        - **Consistency:** one course spec → deterministic outputs
        - **Maintainability:** update once, regenerate cleanly
        - **Extensibility:** plugin hooks for validation, lineage, adaptation (and later agentic workflows)

        ## Install (dev)
        ```bash
        python -m venv .venv && source .venv/bin/activate
        pip install -e ".[dev]"
        pytest
        ```

        ## Quickstart
        ```bash
        course-engine build examples/sample-course/course.yml --out dist
        # optional (requires Quarto installed):
        course-engine render dist/ai-capability-foundations
        ```

        ## Alignment
        This project is intended to be:
        - **AI Capability Framework-aligned** (capability outcomes and governance lenses)
        - **Capability-Driven Development-aligned** (intent-first specs, validation, modularity, extensibility)
        """
    )

    # src package
    files["src/course_engine/__init__.py"] = dedent(
        """\
        __all__ = ["__version__"]
        __version__ = "0.1.0"
        """
    )

    files["src/course_engine/generator/__init__.py"] = ""
    files["src/course_engine/utils/__init__.py"] = ""

    files["src/course_engine/model.py"] = dedent(
        """\
        from __future__ import annotations
        from dataclasses import dataclass
        from typing import Literal, Optional

        ContentBlockType = Literal["markdown", "callout"]

        @dataclass(frozen=True)
        class ContentBlock:
            type: ContentBlockType
            body: str
            title: Optional[str] = None
            style: Optional[str] = None  # note|warning|tip|important

        @dataclass(frozen=True)
        class Lesson:
            id: str
            title: str
            learning_objectives: list[str]
            content_blocks: list[ContentBlock]

        @dataclass(frozen=True)
        class Module:
            id: str
            title: str
            lessons: list[Lesson]

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
            modules: list[Module]
        """
    )

    files["src/course_engine/schema.py"] = dedent(
        """\
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError

from .model import CourseSpec, Module, Lesson, ContentBlock


class ContentBlockModel(BaseModel):
    type: Literal["markdown", "callout"]
    body: str = Field(min_length=1)
    title: Optional[str] = None
    style: Optional[str] = None


class LessonModel(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9\\-]*$")
    title: str = Field(min_length=1)
    learning_objectives: list[str] = Field(default_factory=list)
    content_blocks: list[ContentBlockModel] = Field(default_factory=list)


class ModuleModel(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9\\-]*$")
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
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9\\-]*$")
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
            lessons: list[Lesson] = []
            for l in m.get("lessons", []):
                blocks = [
                    ContentBlock(
                        type=b["type"],
                        body=b["body"],
                        title=b.get("title"),
                        style=b.get("style"),
                    )
                    for b in l.get("content_blocks", [])
                ]
                lessons.append(
                    Lesson(
                        id=l["id"],
                        title=l["title"],
                        learning_objectives=l.get("learning_objectives", []),
                        content_blocks=blocks,
                    )
                )
            modules.append(Module(id=m["id"], title=m["title"], lessons=lessons))

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
"""
    )

    files["src/course_engine/utils/fileops.py"] = dedent(
        """\
        from __future__ import annotations
        from pathlib import Path
        import shutil

        def ensure_empty_dir(path: Path) -> None:
            if path.exists():
                shutil.rmtree(path)
            path.mkdir(parents=True, exist_ok=True)

        def write_text(path: Path, content: str) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        """
    )

    files["src/course_engine/generator/templates.py"] = dedent(
        """\
        from __future__ import annotations
        from pathlib import Path
        from jinja2 import Environment, FileSystemLoader, select_autoescape

        def get_env(templates_dir: Path) -> Environment:
            return Environment(
                loader=FileSystemLoader(str(templates_dir)),
                autoescape=select_autoescape(enabled_extensions=()),
                keep_trailing_newline=True,
            )
        """
    )

    files["src/course_engine/generator/build.py"] = dedent(
        """\
        from __future__ import annotations

        from pathlib import Path
        import re

        from ..model import CourseSpec
        from ..utils.fileops import ensure_empty_dir, write_text
        from .templates import get_env

        def slugify(text: str) -> str:
            s = text.lower().strip()
            s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
            return s or "item"

        def build_quarto_project(spec: CourseSpec, out_root: Path, templates_dir: Path) -> Path:
            out_dir = out_root / spec.id
            ensure_empty_dir(out_dir)

            env = get_env(templates_dir)

            write_text(out_dir / "_quarto.yml", env.get_template("_quarto.yml.j2").render(spec=spec))
            write_text(out_dir / "index.qmd", env.get_template("index.qmd.j2").render(spec=spec))

            lesson_template = env.get_template("lesson.qmd.j2")
            for module in spec.modules:
                for lesson in module.lessons:
                    filename = f"{module.id}-{lesson.id}-{slugify(lesson.title)}.qmd"
                    write_text(
                        out_dir / "lessons" / filename,
                        lesson_template.render(spec=spec, module=module, lesson=lesson),
                    )

            return out_dir
        """
    )

    files["src/course_engine/generator/render.py"] = dedent(
        """\
        from __future__ import annotations
        from pathlib import Path
        import subprocess

        def render_quarto(project_dir: Path) -> None:
            cmd = ["quarto", "render", str(project_dir)]
            try:
                subprocess.run(cmd, check=True)
            except FileNotFoundError as e:
                raise RuntimeError("Quarto not found. Install Quarto and ensure `quarto` is on PATH.") from e
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Quarto render failed with exit code {e.returncode}.") from e
        """
    )

    files["src/course_engine/plugins/base.py"] = dedent(
        """\
        from __future__ import annotations
        from dataclasses import dataclass
        from pathlib import Path
        from typing import Protocol

        from ..model import CourseSpec

        @dataclass
        class BuildContext:
            run_id: str = "local"

        class Plugin(Protocol):
            name: str
            def pre_build(self, spec: CourseSpec, ctx: BuildContext) -> None: ...
            def post_build(self, spec: CourseSpec, ctx: BuildContext, out_dir: Path) -> None: ...
        """
    )

    files["src/course_engine/plugins/loader.py"] = dedent(
        """\
        from __future__ import annotations
        import os
        from importlib import import_module
        from typing import List

        from .base import Plugin

        def load_plugins() -> List[Plugin]:
            raw = os.getenv("COURSE_ENGINE_PLUGINS", "").strip()
            if not raw:
                return []

            plugins: List[Plugin] = []
            for mod_path in [p.strip() for p in raw.split(",") if p.strip()]:
                mod = import_module(mod_path)
                plugin = getattr(mod, "plugin", None)
                if plugin is None:
                    raise RuntimeError(f"Plugin module {mod_path} has no `plugin` object.")
                plugins.append(plugin)
            return plugins
        """
    )

    files["src/course_engine/plugins/__init__.py"] = dedent(
        """\
        from .base import BuildContext, Plugin
        from .loader import load_plugins

        __all__ = ["BuildContext", "Plugin", "load_plugins"]
        """
    )

    files["src/course_engine/cli.py"] = dedent(
        """\
        from __future__ import annotations

        from pathlib import Path
        import yaml
        import typer

        from .schema import validate_course_dict
        from .generator.build import build_quarto_project
        from .generator.render import render_quarto
        from .plugins import BuildContext, load_plugins
        from .utils.fileops import write_text

        app = typer.Typer(no_args_is_help=True)

        DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"

        @app.command()
        def init(path: str):
            \"\"\"Create a starter course.yml.\"\"\"
            p = Path(path)
            p.mkdir(parents=True, exist_ok=True)
            starter = \"\"\"\
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
                  learning_objectives:
                    - "Explain what AI capability means in this course context."
                  content_blocks:
                    - type: "markdown"
                      body: |
                        Write your intro content here.
                    - type: "callout"
                      style: "note"
                      title: "Tip"
                      body: "Keep this course practical and defensible."
        \"\"\"
            write_text(p / "course.yml", starter)
            typer.echo(f"Created {p / 'course.yml'}")

        @app.command()
        def build(course_yml: str, out: str = "dist", templates: str | None = None):
            \"\"\"Build a Quarto project from course.yml into dist/<course-id>/.\"\"\"
            course_path = Path(course_yml)
            out_root = Path(out)
            templates_dir = Path(templates) if templates else DEFAULT_TEMPLATES_DIR

            data = yaml.safe_load(course_path.read_text(encoding="utf-8"))
            spec = validate_course_dict(data)

            ctx = BuildContext()
            plugins = load_plugins()
            for plg in plugins:
                plg.pre_build(spec, ctx)

            out_dir = build_quarto_project(spec, out_root=out_root, templates_dir=templates_dir)

            for plg in plugins:
                plg.post_build(spec, ctx, out_dir)

            typer.echo(f"Built Quarto project: {out_dir}")

        @app.command()
        def render(project_dir: str):
            \"\"\"Render an existing Quarto project directory (calls `quarto render`).\"\"\"
            p = Path(project_dir)
            render_quarto(p)
            typer.echo("Render complete.")
        """
    )

    # Quarto templates
    files["templates/_quarto.yml.j2"] = dedent(
        """\
        project:
          type: website

        website:
          title: "{{ spec.title }}"
          navbar:
            left:
              - href: index.qmd
                text: Home
              - href: lessons/
                text: Lessons

        format:
          html:
            theme: {{ spec.theme or "cosmo" }}
            toc: {{ "true" if spec.toc else "false" }}

        language: {{ spec.language }}
        """
    )

    files["templates/index.qmd.j2"] = dedent(
        """\
        ---
        title: "{{ spec.title }}"
        ---

        {% if spec.subtitle %}
        {{ spec.subtitle }}
        {% endif %}

        ## Course information

        - **Course ID:** `{{ spec.id }}`
        - **Version:** `{{ spec.version }}`
        - **Framework:** {{ spec.framework_name }}

        ## Capability domains

        {% for d in spec.domains %}
        - {{ d }}
        {% endfor %}

        ## Modules

        {% for m in spec.modules %}
        ### {{ m.title }}

        {% for l in m.lessons %}
        - {{ l.title }}
        {% endfor %}
        {% endfor %}
        """
    )

    files["templates/lesson.qmd.j2"] = dedent(
        """\
        ---
        title: "{{ lesson.title }}"
        ---

        ## Learning objectives
        {% if lesson.learning_objectives %}
        {% for lo in lesson.learning_objectives %}
        - {{ lo }}
        {% endfor %}
        {% else %}
        - (Add learning objectives)
        {% endif %}

        ## Content

        {% for b in lesson.content_blocks %}
        {% if b.type == "markdown" %}
        {{ b.body }}

        {% elif b.type == "callout" %}
        ::: {.callout-{{ b.style or "note" }}}
        {% if b.title %}## {{ b.title }}{% endif %}
        {{ b.body }}
        :::

        {% endif %}
        {% endfor %}

        ---

        ### Framework alignment
        This lesson sits within: **{{ spec.framework_name }}**  
        Domains: {% for d in spec.domains %}{{ d }}{% if not loop.last %}, {% endif %}{% endfor %}
        """
    )

    # Example course spec
    files["examples/sample-course/course.yml"] = dedent(
        """\
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
        """
    )

    # Tests
    files["tests/test_schema.py"] = dedent(
        """\
        import pytest
        from course_engine.schema import validate_course_dict

        def test_validate_minimal_course():
            data = {
                "course": {"id": "test-course", "title": "Test", "version": "0.1.0", "language": "en-GB"},
                "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
                "outputs": {"formats": ["html"], "theme": "cosmo", "toc": True},
                "structure": {"modules": [{"id": "m1", "title": "Module 1", "lessons": [{"id": "l1", "title": "Lesson 1"}]}]},
            }
            spec = validate_course_dict(data)
            assert spec.id == "test-course"
            assert spec.modules[0].lessons[0].title == "Lesson 1"

        def test_invalid_course_id_raises():
            data = {
                "course": {"id": "BAD ID", "title": "Test", "version": "0.1.0", "language": "en-GB"},
                "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
                "structure": {"modules": []},
            }
            with pytest.raises(ValueError):
                validate_course_dict(data)
        """
    )

    files["tests/test_build.py"] = dedent(
        """\
        from pathlib import Path

        from course_engine.schema import validate_course_dict
        from course_engine.generator.build import build_quarto_project

        def test_build_creates_expected_files(tmp_path: Path):
            data = {
                "course": {"id": "test-course", "title": "Test", "version": "0.1.0", "language": "en-GB"},
                "framework_alignment": {"framework_name": "Framework", "domains": ["Awareness"]},
                "outputs": {"formats": ["html"], "theme": "cosmo", "toc": True},
                "structure": {
                    "modules": [
                        {"id": "m1", "title": "Module 1", "lessons": [
                            {"id": "l1", "title": "Lesson 1", "content_blocks": [{"type": "markdown", "body": "Hello"}]}
                        ]}
                    ]
                },
            }
            spec = validate_course_dict(data)
            repo_templates = Path(__file__).resolve().parents[1] / "templates"
            out_dir = build_quarto_project(spec, out_root=tmp_path, templates_dir=repo_templates)

            assert (out_dir / "_quarto.yml").exists()
            assert (out_dir / "index.qmd").exists()
            lessons = list((out_dir / "lessons").glob("*.qmd"))
            assert len(lessons) == 1
            assert "Lesson 1" in lessons[0].read_text(encoding="utf-8")
        """
    )

    # GitHub Actions (optional now, useful later)
    files[".github/workflows/ci.yml"] = dedent(
        """\
        name: CI
        on:
          push:
          pull_request:

        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: "3.11"
              - run: pip install -e ".[dev]"
              - run: pytest
        """
    )

    # Write all files
    created = 0
    for rel_path, content in files.items():
        path = base / rel_path
        write_file(path, content, force=force)
        created += 1

    print(f"Bootstrap complete: wrote {created} files.")
    print("Next:")
    print("  python -m venv .venv")
    print("  source .venv/bin/activate")
    print('  pip install -e ".[dev]"')
    print("  pytest")
    print("Then:")
    print("  course-engine build examples/sample-course/course.yml --out dist")
    print("Optional (requires Quarto installed):")
    print("  course-engine render dist/ai-capability-foundations")


if __name__ == "__main__":
    main()
