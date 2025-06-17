from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import MintError, detect_compiler, run
from .base import BaseToolchain
from . import register

console = Console()


@register("cpp")
class CppToolchain(BaseToolchain):
    """C/C++ compilation using host clang++/g++."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.obj_dir = self.build_dir / "obj"
        self.bin_dir = self.build_dir / "bin"
        self.compiler = detect_compiler()
        self.cxxflags = config.get("cxxflags", ["-std=c++20", "-O2"])
        self.ldflags = config.get("ldflags", [])
        self.name = config.get("name") or project_root.name

    def _discover_sources(self) -> List[Path]:
        exts = {".cpp", ".c", ".cc", ".cxx"}
        return [p for p in self.project_root.rglob("*") if p.suffix in exts and "build" not in p.parts]

    def _object_path(self, src: Path) -> Path:
        rel = src.relative_to(self.project_root)
        return self.obj_dir / rel.with_suffix(".o")

    def _needs_rebuild(self, src: Path, obj: Path) -> bool:
        return not obj.exists() or src.stat().st_mtime > obj.stat().st_mtime

    def build(self) -> Path:
        self.obj_dir.mkdir(parents=True, exist_ok=True)
        self.bin_dir.mkdir(parents=True, exist_ok=True)
        sources = self._discover_sources()
        if not sources:
            raise MintError("No C/C++ sources found")
        objects: List[Path] = []
        for src in sources:
            obj = self._object_path(src)
            obj.parent.mkdir(parents=True, exist_ok=True)
            if self._needs_rebuild(src, obj):
                cmd = [self.compiler, "-c", *self.cxxflags, "-I", str(self.project_root), "-o", str(obj), str(src)]
                run(cmd)
            objects.append(obj)
        out = self.bin_dir / self.name
        cmd = [self.compiler, "-o", str(out), *map(str, objects), *self.ldflags]
        run(cmd)
        console.print(f"[green]C++ build complete:[/] {out.relative_to(self.project_root)}")
        return out

    def clean(self):
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir) 