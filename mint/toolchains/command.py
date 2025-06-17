from __future__ import annotations

from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import run
from .base import BaseToolchain
from . import register

console = Console()


@register("cmd")
class CommandToolchain(BaseToolchain):
    """Generic toolchain that just runs a shell command provided in config.

    Example mint.yaml:
        lang: cmd
        cmd: ["make"]
    """

    def build(self):
        cmd: List[str] = self.config.get("cmd")
        if not cmd:
            raise ValueError("CommandToolchain requires 'cmd' list in config")
        run(cmd, cwd=self.project_root)
        console.print(f"[green]Command executed successfully:[/] {' '.join(cmd)}")
        return [] 