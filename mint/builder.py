from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List

import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .utils import MintError, detect_compiler, default_build_dir, run

console = Console()


class BuildConfig:
    """Represents user configuration loaded from mint.yaml (if any)."""

    def __init__(self, data: Dict | None = None):
        self.name: str | None = None
        self.cxxflags: List[str] = []
        self.ldflags: List[str] = []
        self.targets: List[Dict] = []
        if data:
            self.__dict__.update(data)

    @staticmethod
    def load(path: Path) -> "BuildConfig":
        if path.exists():
            data = yaml.safe_load(path.read_text()) or {}
            return BuildConfig(data)
        return BuildConfig()


class Builder:
    def __init__(self, project_root: Path, build_dir: Path | None = None, *, release: bool = False, config: BuildConfig | None = None):
        self.project_root = project_root
        self.build_dir = build_dir or default_build_dir(project_root)
        self.obj_dir = self.build_dir / "obj"
        self.bin_dir = self.build_dir / "bin"
        self.release = release
        self.config = config or BuildConfig()
        self.compiler = detect_compiler()
        self.cxxflags = ["-std=c++20"] + (self.config.cxxflags or [])
        if release:
            self.cxxflags += ["-O3"]
        else:
            self.cxxflags += ["-O0", "-g"]
        self.ldflags = self.config.ldflags or []
        self.compile_commands: List[Dict] = []

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def build(self) -> None:
        console.rule("[bold cyan]Mint Build Start")
        self._prepare_dirs()
        sources = self._discover_sources()
        objects = self._compile_sources(sources)
        exe = self._link(objects)
        self._write_compile_commands()
        console.print(f"\n[bold green]✓ Build succeeded[/] -> {exe.relative_to(self.project_root)}")

    def clean(self) -> None:
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            console.print(f"[yellow]Cleaned {self.build_dir}")
        else:
            console.print("Nothing to clean")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_dirs(self):
        self.obj_dir.mkdir(parents=True, exist_ok=True)
        self.bin_dir.mkdir(parents=True, exist_ok=True)

    def _discover_sources(self) -> List[Path]:
        exts = {".cpp", ".c", ".cc", ".cxx"}
        sources: List[Path] = [p for p in self.project_root.rglob("*") if p.suffix in exts and "build" not in p.parts]
        if not sources:
            raise MintError("No source files found")
        return sorted(sources)

    def _object_path(self, src: Path) -> Path:
        rel = src.relative_to(self.project_root)
        obj_name = rel.with_suffix(".o")
        return self.obj_dir / obj_name

    def _needs_rebuild(self, src: Path, obj: Path) -> bool:
        if not obj.exists():
            return True
        return src.stat().st_mtime > obj.stat().st_mtime

    def _compile_sources(self, sources: List[Path]) -> List[Path]:
        objects: List[Path] = []
        compile_tasks = {}
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True) as progress:
            task_id = progress.add_task("Compiling", total=len(sources))
            with ThreadPoolExecutor(max_workers=os.cpu_count()) as pool:
                for src in sources:
                    obj = self._object_path(src)
                    obj.parent.mkdir(parents=True, exist_ok=True)
                    if not self._needs_rebuild(src, obj):
                        progress.advance(task_id)
                        objects.append(obj)
                        continue
                    fut = pool.submit(self._compile_single, src, obj)
                    compile_tasks[fut] = (src, obj)
                for fut in as_completed(compile_tasks):
                    src, obj = compile_tasks[fut]
                    try:
                        fut.result()
                        objects.append(obj)
                    except Exception as e:
                        console.print(f"[red]Error compiling {src}: {e}")
                        raise
                    finally:
                        progress.advance(task_id)
        return objects

    def _compile_single(self, src: Path, obj: Path):
        cmd = [self.compiler, "-c", *self.cxxflags, "-I", str(self.project_root), "-o", str(obj), str(src)]
        run(cmd)
        self.compile_commands.append({
            "directory": str(self.project_root),
            "file": str(src),
            "command": " ".join(cmd),
        })

    def _link(self, objects: List[Path]) -> Path:
        output = self.bin_dir / (self.config.name or self.project_root.name)
        cmd = [self.compiler, "-o", str(output), *map(str, objects), *self.ldflags]
        run(cmd)
        return output

    def _write_compile_commands(self):
        cc_json = self.build_dir / "compile_commands.json"
        cc_json.write_text(json.dumps(self.compile_commands, indent=2)) 