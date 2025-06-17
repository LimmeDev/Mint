from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("kotlin_native")
class KotlinNativeToolchain(BaseToolchain):
    """Pure kotlinc JVM build emitting runnable JAR."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.sources = list(project_root.rglob("*.kt"))
        self.classes_dir = self.build_dir / "obj"
        self.jar_dir = self.build_dir / "bin"
        self.jar_name = (self.config.get("name") or project_root.name) + ".jar"
        self.main_class = self.config.get("main_class")

    def _kotlinc(self):
        k = shutil.which("kotlinc")
        if not k:
            raise MintError("kotlinc not found. Install Kotlin compiler")
        return k

    def build(self):
        if not self.sources:
            raise MintError("No Kotlin sources found")

        if (self.jar_dir / self.jar_name).exists() and not any(self._is_dirty(s) for s in self.sources):
            console.print("[grey]Kotlin up-to-date, skipping compile[/]")
            return self.jar_dir / self.jar_name

        self.classes_dir.mkdir(parents=True, exist_ok=True)
        self.jar_dir.mkdir(parents=True, exist_ok=True)
        compile_cmd = [self._kotlinc(), "-d", str(self.classes_dir)] + [str(p) for p in self.sources]
        run(compile_cmd, cwd=self.project_root)
        for s in self.sources:
            self._update_cache(s)
        jar_path = self.jar_dir / self.jar_name
        jar_cmd = ["jar", "cf", str(jar_path), "-C", str(self.classes_dir), "."]
        if not shutil.which("jar"):
            raise MintError("jar command not found (needs JDK)")
        run(jar_cmd, cwd=self.project_root)
        console.print(f"[green]Kotlin JAR built:[/] {jar_path.relative_to(self.project_root)}")
        return jar_path 