from __future__ import annotations

import shutil
from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("dart")
class DartToolchain(BaseToolchain):
    """Dart/Flutter builds."""

    def build(self):
        if shutil.which("flutter") and (self.project_root / "pubspec.yaml").exists():
            run(["flutter", "pub", "get"], cwd=self.project_root)
            run(["flutter", "build", "apk", "--debug"], cwd=self.project_root)
            console.print("[green]Flutter APK built.[/]")
        elif shutil.which("dart") and (self.project_root / "pubspec.yaml").exists():
            run(["dart", "pub", "get"], cwd=self.project_root)
            run(["dart", "compile", "exe", "bin/main.dart"], cwd=self.project_root)
            console.print("[green]Dart executable compiled.[/]")
        else:
            raise MintError("Dart or Flutter not found, or pubspec.yaml missing")
        return [] 