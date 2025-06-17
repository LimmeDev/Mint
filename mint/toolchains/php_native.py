from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()

@register("php_native")
class PhpNativeToolchain(BaseToolchain):
    """Package PHP project into a PHAR using `php -d phar.readonly=0`."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.entry = Path(self.config.get("entry", "index.php"))
        self.output = self.build_dir / "bin" / ((self.config.get("name") or project_root.name) + ".phar")

    def build(self):
        if not shutil.which("php"):
            raise MintError("php interpreter not found")
        if not self.entry.exists():
            raise MintError(f"PHP entry {self.entry} not found")
        if self.output.exists() and not self._is_dirty(self.entry):
            console.print("[grey]PHP up-to-date, skipping phar build[/]")
            return self.output
        self.output.parent.mkdir(parents=True, exist_ok=True)
        stub = f"<?php Phar::mapPhar('{self.output.name}'); require '{self.entry}'; __HALT_COMPILER(); ?>"
        stub_file = self.build_dir / "phar_stub.php"
        stub_file.write_text(stub)
        run(["php", "-d", "phar.readonly=0", "-r", f"$phar=new Phar('{self.output}'); $phar->buildFromDirectory('.'); $phar->setStub(file_get_contents('{stub_file}'));"], cwd=self.project_root)
        self._update_cache(self.entry)
        console.print(f"[green]PHP PHAR built:[/] {self.output.relative_to(self.project_root)}")
        return self.output 