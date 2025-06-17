from __future__ import annotations

import shutil
from pathlib import Path
from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("csharp")
class CSharpToolchain(BaseToolchain):
    """C#/.NET builds via `dotnet build`."""

    def _dotnet(self):
        if shutil.which("dotnet"):
            return "dotnet"
        raise MintError("dotnet CLI not found. Install .NET SDK.")

    def build(self):
        cmd = [self._dotnet(), "build", "-nologo", "-clp:NoSummary"]
        run(cmd, cwd=self.project_root)
        console.print("[green].NET project built successfully.[/]")
        return [] 