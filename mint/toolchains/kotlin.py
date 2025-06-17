from __future__ import annotations

import shutil
from pathlib import Path
from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("kotlin")
class KotlinToolchain(BaseToolchain):
    """Kotlin JVM/Multiplatform builds via Gradle."""

    def _gradle_cmd(self):
        root = self.project_root
        if (root / "gradlew").exists():
            return ["./gradlew", "build", "--console=plain"]
        if shutil.which("gradle"):
            return ["gradle", "build", "--console=plain"]
        raise MintError("Gradle not found for Kotlin build")

    def build(self):
        cmd = self._gradle_cmd()
        run(cmd, cwd=self.project_root)
        console.print("[green]Kotlin project built.[/]")
        return [] 