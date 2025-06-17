from __future__ import annotations

import shutil
from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("zig")
class ZigToolchain(BaseToolchain):
    """Zig builds via `zig build`."""

    def build(self):
        if not shutil.which("zig"):
            raise MintError("zig executable not found")
        run(["zig", "build"], cwd=self.project_root)
        console.print("[green]Zig project built.[/]")
        return [] 