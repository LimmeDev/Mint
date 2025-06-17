from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from ..utils import run, MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("php")
class PhpToolchain(BaseToolchain):
    """PHP projects using Composer scripts."""

    def build(self):
        root = self.project_root
        if not (root / "composer.json").exists():
            raise MintError("composer.json not found – not a PHP Composer project")
        composer = "composer"
        if (root / "composer.phar").exists():
            composer = "php composer.phar"
        run(composer.split() + ["install", "--no-dev", "--optimize-autoloader"], cwd=root)
        console.print("[green]Composer install complete (prod).[/]")
        return [] 