from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("go")
class GoToolchain(BaseToolchain):
    """Go builds via `go build`."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.output = self.config.get("output")  # optional custom output path

    def _go(self) -> str:
        go = shutil.which("go")
        if not go:
            raise MintError("Go executable not found in PATH. Install Go.")
        return go

    def build(self):
        go = self._go()
        args: List[str] = [go, "build"]
        if self.output:
            args += ["-o", str(self.output)]
        run(args, cwd=self.project_root)
        out = Path(self.output) if self.output else self.project_root / self.project_root.name
        console.print(f"[green]Go build complete:[/] {out.relative_to(self.project_root)}")
        return out 