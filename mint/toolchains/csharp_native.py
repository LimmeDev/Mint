from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()

@register("csharp_native")
class CSharpNativeToolchain(BaseToolchain):
    """Compile C# sources using Roslyn csc (no MSBuild)."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.sources = list(project_root.rglob("*.cs"))
        self.output = self.build_dir / "bin" / (self.config.get("name") or project_root.name + ".exe")
        self.framework = self.config.get("framework")  # net8.0 etc.

    def _csc(self):
        # dotnet provides csc under sdk; but we can call "dotnet" "csc.dll"
        if shutil.which("csc"):
            return "csc"
        elif shutil.which("dotnet"):
            # path to csc.dll not portable; use dotnet exec
            return "dotnet"
        raise MintError("C# compiler not found (csc or dotnet)")

    def build(self):
        if not self.sources:
            raise MintError("No C# sources found")
        if self.output.exists() and not any(self._is_dirty(s) for s in self.sources):
            console.print("[grey]C# up-to-date, skipping compile[/]")
            return self.output

        self.output.parent.mkdir(parents=True, exist_ok=True)
        compiler = self._csc()
        if compiler == "csc":
            cmd = ["csc", "/nologo", "/optimize", f"/out:{self.output}"] + [str(p) for p in self.sources]
        else:
            # dotnet exec path/to/Roslyn - use dotnet build as fallback minimal
            cmd = ["dotnet", "build", "-c", "Release", "-o", str(self.output.parent), "--nologo"]
        run(cmd, cwd=self.project_root)
        for s in self.sources:
            self._update_cache(s)
        console.print(f"[green]C# executable built:[/] {self.output.relative_to(self.project_root)}")
        return self.output 