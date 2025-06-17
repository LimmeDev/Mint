from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()

@register("ruby_native")
class RubyNativeToolchain(BaseToolchain):
    """Checks syntax and packages sources into tar.gz gem-like archive."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.sources = list(project_root.rglob("*.rb"))
        self.output = self.build_dir / "bin" / ((self.config.get("name") or project_root.name) + ".tar.gz")

    def build(self):
        if not shutil.which("ruby"):
            raise MintError("ruby interpreter not found")
        if not self.sources:
            raise MintError("No Ruby sources found")
        if self.output.exists() and not any(self._is_dirty(s) for s in self.sources):
            console.print("[grey]Ruby up-to-date, skipping package[/]")
            return self.output
        # syntax check
        for src in self.sources:
            run(["ruby", "-c", str(src)])
            self._update_cache(src)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        run(["tar", "czf", str(self.output)] + [str(s.relative_to(self.project_root)) for s in self.sources], cwd=self.project_root)
        console.print(f"[green]Ruby sources packaged:[/] {self.output.relative_to(self.project_root)}")
        return self.output 