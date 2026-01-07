from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Optional
import shutil
import tempfile

# Cache PDF preflight result per process to avoid re-checking repeatedly.
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

    We avoid parsing `quarto check` output (can vary across versions) and instead
    perform a minimal Quarto->PDF smoke test in a temporary directory.
    """
    global _PDF_PREFLIGHT_OK

    if _PDF_PREFLIGHT_OK is True:
        return

    _require_quarto()

    with tempfile.TemporaryDirectory(prefix="course-engine-pdf-check-") as td:
        tdir = Path(td)

        # Minimal QMD
        (tdir / "index.qmd").write_text(
            "# PDF preflight\n\nIf you can read this, PDF rendering works.\n",
            encoding="utf-8",
        )

        # Minimal Quarto config forcing PDF format
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

        # Attempt render
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

            # Provide a short tail of diagnostic output (helpful, not overwhelming)
            if details:
                tail = "\n".join(details.splitlines()[-25:])
                msg += "\n---\nQuarto/LaTeX details (tail):\n" + tail + "\n"

            raise RuntimeError(msg)

    _PDF_PREFLIGHT_OK = True


def render_quarto(
    project_dir: Path,
    *,
    input_file: Optional[str] = None,
    to: Optional[str] = None,
) -> None:
    """
    Render a Quarto project directory.

    Args:
        project_dir: Path to the Quarto project folder (contains _quarto.yml).
        input_file: Optional input file to render (e.g., "index.qmd"). If omitted,
                    Quarto will render the project default.
        to: Optional output format override (e.g., "pdf", "html"). If omitted,
            Quarto uses the format(s) defined in _quarto.yml.

    Raises:
        RuntimeError: If Quarto is not installed, PDF prerequisites are missing,
                      or rendering fails.
    """
    project_dir = Path(project_dir)

    # Fail-fast prerequisites
    if to == "pdf":
        _require_pdf_toolchain()
    else:
        _require_quarto()

    cmd = ["quarto", "render"]

    if input_file:
        cmd.append(str(project_dir / input_file))
    else:
        cmd.append(str(project_dir))

    if to:
        cmd.extend(["--to", to])

    try:
        completed = subprocess.run(
            cmd,
            check=True,
            text=True,
            capture_output=True,
        )
        # Quarto often prints useful info to stderr even on success; keep it quiet by default.
        _ = completed.stdout
        _ = completed.stderr

    except FileNotFoundError as e:
        # Defensive fallback (should be prevented by _require_quarto)
        raise RuntimeError(
            "Quarto not found. Install Quarto and ensure `quarto` is on PATH."
        ) from e

    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        stdout = (e.stdout or "").strip()

        # Prefer stderr (it usually contains the real LaTeX/PDF error)
        details = stderr if stderr else stdout
        if details:
            raise RuntimeError(
                f"Quarto render failed with exit code {e.returncode}.\n\n{details}"
            ) from e

        raise RuntimeError(f"Quarto render failed with exit code {e.returncode}.") from e
