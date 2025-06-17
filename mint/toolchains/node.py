from __future__ import annotations

import json
import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("node")
class NodeToolchain(BaseToolchain):
    """Node/TypeScript builds using npm/yarn/pnpm scripts."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.script = self.config.get("script", "build")

    def _package_json(self) -> Path:
        pkg = self.project_root / "package.json"
        if not pkg.exists():
            raise MintError("package.json not found – not a Node project")
        return pkg

    def _detect_package_manager(self) -> str:
        if (self.project_root / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (self.project_root / "yarn.lock").exists():
            return "yarn"
        return "npm"

    def build(self):
        self._package_json()
        pm = self._detect_package_manager()
        run([pm, "run", self.script], cwd=self.project_root)
        console.print(f"[green]Node script '{self.script}' completed using {pm}.[/]")
        return [] 