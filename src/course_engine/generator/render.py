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
