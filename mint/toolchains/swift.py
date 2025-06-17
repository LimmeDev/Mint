from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("swift")
class SwiftToolchain(BaseToolchain):
    """Swift Package Manager build."""

    def _swift(self):
        if shutil.which("swift"):
            return "swift"
        raise MintError("swift CLI not found. Install Swift toolchain.")

    def build(self):
        cmd = [self._swift(), "build", "-c", "release"]
        run(cmd, cwd=self.project_root)
        console.print("[green]Swift package built (release).[/]")
        return [] 