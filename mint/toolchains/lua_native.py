from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()

@register("lua_native")
class LuaNativeToolchain(BaseToolchain):
    """Compile Lua sources to bytecode via luac."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.sources = list(project_root.rglob("*.lua"))
        self.output = self.build_dir / "bin" / ((self.config.get("name") or project_root.name) + ".luac")

    def build(self):
        if not shutil.which("luac"):
            raise MintError("luac compiler not found")
        if not self.sources:
            raise MintError("No Lua sources found")
        main = self.config.get("entry") or self.sources[0]
        if self.output.exists() and not self._is_dirty(Path(main)):
            console.print("[grey]Lua up-to-date, skipping compile[/]")
            return self.output
        self.output.parent.mkdir(parents=True, exist_ok=True)
        run(["luac", "-o", str(self.output), str(main)])
        self._update_cache(Path(main))
        console.print(f"[green]Lua bytecode built:[/] {self.output.relative_to(self.project_root)}")
        return self.output 