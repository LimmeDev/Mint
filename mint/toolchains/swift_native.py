from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("swift_native")
class SwiftNativeToolchain(BaseToolchain):
    """Swift build via swiftc directly (no swift package manager)."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.sources = list((project_root / "Sources").rglob("*.swift")) or list(project_root.rglob("*.swift"))
        self.output = self.build_dir / "bin" / (self.config.get("name") or project_root.name)

    def _swiftc(self):
        s = shutil.which("swiftc")
        if not s:
            raise MintError("swiftc not found")
        return s

    def build(self):
        if not self.sources:
            raise MintError("No Swift sources found")

        latest = max(self.sources, key=lambda p: p.stat().st_mtime)
        if self.output.exists() and not any(self._is_dirty(s) for s in self.sources):
            console.print("[grey]Swift up-to-date, skipping compile[/]")
            return self.output

        self.output.parent.mkdir(parents=True, exist_ok=True)
        cmd = [self._swiftc(), "-o", str(self.output), "-O"] + [str(p) for p in self.sources]
        run(cmd, cwd=self.project_root)
        console.print(f"[green]Swift binary built:[/] {self.output.relative_to(self.project_root)}")
        for s in self.sources:
            self._update_cache(s)
        return self.output 