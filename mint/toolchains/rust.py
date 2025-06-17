from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("rust")
class RustToolchain(BaseToolchain):
    """Rust builds via Cargo."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.release: bool = self.config.get("release", False)

    def _cargo(self) -> str:
        cargo = shutil.which("cargo")
        if not cargo:
            raise MintError("Cargo not found in PATH. Install Rust toolchain.")
        return cargo

    def build(self) -> Path:
        cargo = self._cargo()
        args: List[str] = [cargo, "build"]
        if self.release or self.config.get("profile") == "release":
            args.append("--release")
        run(args, cwd=self.project_root)
        target_dir = self.project_root / "target" / ("release" if "--release" in args else "debug")
        # Not easy to know artifact name; just return folder
        console.print(f"[green]Rust build output:[/] {target_dir}")
        return target_dir 