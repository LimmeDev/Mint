from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("zig_native")
class ZigNativeToolchain(BaseToolchain):
    """Compile Zig source directly with `zig build-exe`."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.entry = Path(self.config.get("entry", "src/main.zig"))
        self.output = self.build_dir / "bin" / (self.config.get("name") or project_root.name)

    def build(self):
        if not shutil.which("zig"):
            raise MintError("zig compiler not found")
        if not self.entry.exists():
            raise MintError(f"Zig entry {self.entry} not found")

        if self.output.exists() and not self._is_dirty(self.entry):
            console.print("[grey]Zig up-to-date, skipping compile[/]")
            return self.output

        self.output.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["zig", "build-exe", str(self.entry), "-O", "ReleaseFast", "-femit-bin=" + str(self.output)]
        run(cmd, cwd=self.project_root)
        self._update_cache(self.entry)
        console.print(f"[green]Zig binary built:[/] {self.output.relative_to(self.project_root)}")
        return self.output 