from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import MintError
from ..utils.java import (
    compile_java_sources,
    create_jar,
    find_java_sources,
    parse_imports,
)
from .base import BaseToolchain
from . import register

console = Console()


@register("java_native")
class JavaNativeToolchain(BaseToolchain):
    """Pure javac + jar build (no Gradle/Maven)."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.classes_dir = self.build_dir / "obj"
        self.jar_dir = self.build_dir / "bin"
        self.main_class = self.config.get("main_class")

    def build(self) -> Path:
        self.classes_dir.mkdir(parents=True, exist_ok=True)
        self.jar_dir.mkdir(parents=True, exist_ok=True)
        sources = find_java_sources(self.project_root / "src") or find_java_sources(self.project_root)
        if not sources:
            raise MintError("No Java sources found")
        dirty = [s for s in sources if self._is_dirty(s)]
        if dirty:
            compile_java_sources(dirty, out_dir=self.classes_dir)
            for s in dirty:
                self._update_cache(s)
        jar_path = self.jar_dir / (self.config.get("name") or (self.project_root.name + ".jar"))
        create_jar(jar_path, manifest_main=self.main_class, classes_dir=self.classes_dir)
        console.print(f"[green]Java JAR built:[/] {jar_path.relative_to(self.project_root)}")
        return jar_path 