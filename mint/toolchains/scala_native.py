from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("scala_native")
class ScalaNativeToolchain(BaseToolchain):
    """Compile Scala code with scalac and package into JAR (no sbt)."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.sources = list(project_root.rglob("*.scala"))
        self.classes_dir = self.build_dir / "obj"
        self.jar_dir = self.build_dir / "bin"
        self.jar_name = (self.config.get("name") or project_root.name) + ".jar"
        self.main_class = self.config.get("main_class")

    def _scalac(self):
        sc = shutil.which("scalac")
        if not sc:
            raise MintError("scalac not found. Install Scala SDK")
        return sc

    def build(self):
        if not self.sources:
            raise MintError("No Scala sources found")
        self.classes_dir.mkdir(parents=True, exist_ok=True)
        self.jar_dir.mkdir(parents=True, exist_ok=True)

        jar_path = self.jar_dir / self.jar_name
        if jar_path.exists() and not any(self._is_dirty(s) for s in self.sources):
            console.print("[grey]Scala up-to-date, skipping compile[/]")
            return jar_path

        dirty = [s for s in self.sources if self._is_dirty(s)]
        if dirty:
            compile_cmd = [self._scalac(), "-d", str(self.classes_dir)] + [str(p) for p in dirty]
            run(compile_cmd, cwd=self.project_root)
            for s in dirty:
                self._update_cache(s)

        if not shutil.which("jar"):
            raise MintError("jar command not found (needs JDK)")
        jar_cmd = ["jar", "cf", str(jar_path), "-C", str(self.classes_dir), "."]
        run(jar_cmd)
        console.print(f"[green]Scala JAR built:[/] {jar_path.relative_to(self.project_root)}")
        return jar_path 