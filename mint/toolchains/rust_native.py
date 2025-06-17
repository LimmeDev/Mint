from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("rust_native")
class RustNativeToolchain(BaseToolchain):
    """Pure rustc build (no Cargo). Expects src/main.rs or specified entry."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.entry = Path(self.config.get("entry", "src/main.rs"))
        self.output = self.build_dir / "bin" / (self.config.get("name") or project_root.name)

    def _rustc(self):
        rustc = shutil.which("rustc")
        if not rustc:
            raise MintError("rustc not found. Install Rust toolchain.")
        return rustc

    def build(self):
        if not self.entry.exists():
            raise MintError(f"Entry Rust file {self.entry} not found")

        # incremental
        if self.output.exists() and not self._is_dirty(self.entry):
            console.print("[grey]Rust up-to-date, skipping compile[/]")
            return self.output

        self.output.parent.mkdir(parents=True, exist_ok=True)
        cmd = [self._rustc(), str(self.entry), "--edition=2021", "-O", "-o", str(self.output)]
        run(cmd, cwd=self.project_root)
        self._update_cache(self.entry)
        console.print(f"[green]Rust binary built:[/] {self.output.relative_to(self.project_root)}")
        return self.output 