from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("java")
class JavaToolchain(BaseToolchain):
    """Java/Kotlin JVM builds using Gradle or Maven automatically."""

    def _detect_build_tool(self) -> List[str]:
        root = self.project_root
        if (root / "gradlew").exists():
            return ["./gradlew", "build", "--console=plain"]
        if (root / "mvnw").exists():
            return ["./mvnw", "package", "-q"]
        if shutil.which("gradle"):
            return ["gradle", "build", "--console=plain"]
        if shutil.which("mvn"):
            return ["mvn", "package", "-q"]
        raise MintError("No Gradle or Maven found for Java build")

    def build(self):
        cmd = self._detect_build_tool()
        run(cmd, cwd=self.project_root)
        console.print(f"[green]Java project built using {' '.join(cmd[:1])}[/]")
        return [] 