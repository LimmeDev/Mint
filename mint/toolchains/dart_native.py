from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("dart_native")
class DartNativeToolchain(BaseToolchain):
    """Compile Dart CLI app to native executable using dart compile exe."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.entry = Path(self.config.get("entry", "bin/main.dart"))
        self.output = self.build_dir / "bin" / (self.config.get("name") or project_root.name)

    def build(self):
        if not shutil.which("dart"):
            raise MintError("dart sdk not found")
        if not self.entry.exists():
            raise MintError(f"Dart entry {self.entry} not found")

        if self.output.exists() and not self._is_dirty(self.entry):
            console.print("[grey]Dart up-to-date, skipping compile[/]")
            return self.output

        self.output.parent.mkdir(parents=True, exist_ok=True)
        run(["dart", "pub", "get"], cwd=self.project_root)
        run(["dart", "compile", "exe", str(self.entry), "-o", str(self.output)], cwd=self.project_root)
        self._update_cache(self.entry)
        console.print(f"[green]Dart executable built:[/] {self.output.relative_to(self.project_root)}")
        return self.output 