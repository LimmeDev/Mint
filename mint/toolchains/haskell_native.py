from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("haskell_native")
class HaskellNativeToolchain(BaseToolchain):
    """Compile Haskell sources directly with ghc."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.main = Path(self.config.get("entry", "Main.hs"))
        self.output = self.build_dir / "bin" / (self.config.get("name") or project_root.name)

    def _ghc(self):
        g = shutil.which("ghc")
        if not g:
            raise MintError("ghc compiler not found. Install GHC.")
        return g

    def build(self):
        if not self.main.exists():
            raise MintError(f"Haskell entry {self.main} not found")

        if self.output.exists() and not self._is_dirty(self.main):
            console.print("[grey]Haskell up-to-date, skipping compile[/]")
            return self.output

        self.output.parent.mkdir(parents=True, exist_ok=True)
        cmd = [self._ghc(), "-O2", "-outputdir", str(self.build_dir / "obj"), "-o", str(self.output), str(self.main)]
        run(cmd, cwd=self.project_root)
        self._update_cache(self.main)
        console.print(f"[green]Haskell binary built:[/] {self.output.relative_to(self.project_root)}")
        return self.output 