from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("ruby")
class RubyToolchain(BaseToolchain):
    """Ruby builds using Rake or Gem build."""

    def build(self):
        root = self.project_root
        if (root / "Rakefile").exists():
            if not shutil.which("rake"):
                raise MintError("rake not found")
            run(["rake", "build"], cwd=root)
            console.print("[green]Rake build completed.[/]")
        else:
            # Try gem build *.gemspec
            gemspecs = list(root.glob("*.gemspec"))
            if not gemspecs:
                raise MintError("No Rakefile or gemspec to build Ruby project")
            if not shutil.which("gem"):
                raise MintError("gem command not found")
            run(["gem", "build", gemspecs[0].name], cwd=root)
            console.print("[green]Ruby gem built.[/]")
        return [] 