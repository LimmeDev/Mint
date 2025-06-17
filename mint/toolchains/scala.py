from __future__ import annotations

import shutil
from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("scala")
class ScalaToolchain(BaseToolchain):
    """Scala builds via sbt."""

    def build(self):
        if shutil.which("sbt"):
            run(["sbt", "compile"], cwd=self.project_root)
            console.print("[green]Scala project compiled with sbt.[/]")
        else:
            raise MintError("sbt not found. Install Scala sbt.")
        return [] 