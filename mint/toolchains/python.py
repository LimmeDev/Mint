from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("python")
class PythonToolchain(BaseToolchain):
    """Python build packaging via `python -m build` or `pyinstaller`."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.method = self.config.get("method", "wheel")  # wheel|installer

    def build(self):
        if self.method == "wheel":
            self._build_wheel()
            dist = self.project_root / "dist"
            console.print(f"[green]Python wheel built:[/] {dist}")
            return dist
        elif self.method == "installer":
            self._build_installer()
            build_dir = self.project_root / "dist"
            console.print(f"[green]PyInstaller dist:[/] {build_dir}")
            return build_dir
        else:
            raise MintError(f"Unknown python build method '{self.method}'")

    def _build_wheel(self):
        # Require build package
        if not shutil.which("python"):
            raise MintError("Python interpreter not found")
        run(["python", "-m", "pip", "install", "--upgrade", "build"], cwd=self.project_root)
        run(["python", "-m", "build"], cwd=self.project_root)

    def _build_installer(self):
        if not shutil.which("pyinstaller"):
            raise MintError("pyinstaller not found – install with 'pip install pyinstaller'")
        entry = self.config.get("entry")
        if not entry:
            raise MintError("PyInstaller mode requires 'entry' in config")
        run(["pyinstaller", "--onefile", entry], cwd=self.project_root) 