from __future__ import annotations

import shutil
from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("haskell")
class HaskellToolchain(BaseToolchain):
    """Haskell builds via stack or cabal."""

    def build(self):
        root = self.project_root
        if (root / "stack.yaml").exists():
            if not shutil.which("stack"):
                raise MintError("stack not found")
            run(["stack", "build"], cwd=root)
            console.print("[green]Haskell project built with stack.[/]")
        else:
            if not shutil.which("cabal"):
                raise MintError("cabal not found")
            run(["cabal", "build", "all"], cwd=root)
            console.print("[green]Haskell project built with cabal.[/]")
        return [] 