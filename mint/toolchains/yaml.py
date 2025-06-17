from __future__ import annotations

import json
from pathlib import Path
from typing import List

import yaml
from rich.console import Console

from ..utils import MintError
from .base import BaseToolchain
from . import register

console = Console()


@register("yaml")
class YAMLToolchain(BaseToolchain):
    """YAML validation / conversion tool-chain.

    This tool-chain treats *.yaml / *.yml files as build artefacts that must at
    least parse correctly.  Optionally it can emit pretty-printed JSON copies
    of every validated file.

    Config keys (all optional):
      patterns : list[str] – glob patterns used to locate YAML sources          
      convert  : bool      – if *True* also emit JSON siblings                 
      out_dir  : str       – output directory relative to *build_dir*          
    """

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        super().__init__(project_root, build_dir, config)
        self.patterns: List[str] = self.config.get("patterns", ["*.yaml", "*.yml"])
        self.convert: bool = self.config.get("convert", False)
        self.out_dir: Path = (build_dir / self.config.get("out_dir", "generated")).resolve()
        # directory for Ninja stamp outputs
        self._check_dir: Path = build_dir / "yaml_checks"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _discover_sources(self) -> List[Path]:
        sources: List[Path] = []
        for p in self.patterns:
            sources.extend(list(self.project_root.rglob(p)))
        # De-duplicate & skip build directory artefacts
        unique = [p for p in set(sources) if "build" not in p.parts]
        if not unique:
            raise MintError("No YAML files found")
        return sorted(unique)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def build(self):
        yaml_files = self._discover_sources()
        validated: List[Path] = []
        for yf in yaml_files:
            # incremental check – only re-parse dirty files
            if not self._is_dirty(yf):
                validated.append(yf)
                continue
            try:
                yaml.safe_load(yf.read_text())
            except yaml.YAMLError as e:
                raise MintError(f"Invalid YAML in {yf}: {e}") from e
            self._update_cache(yf)
            validated.append(yf)

        console.print(f"[green]Validated {len(validated)} YAML file(s)[/]")

        outputs: List[Path] = []
        if self.convert:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            for yf in validated:
                json_path = self.out_dir / yf.with_suffix(".json").name
                data = yaml.safe_load(yf.read_text())
                json_path.write_text(json.dumps(data, indent=2))
                outputs.append(json_path)
            console.print(f"[green]Converted YAML → JSON in {self.out_dir}[/]")

        return outputs or validated

    # ------------------------------------------------------------------
    # Cleaning
    # ------------------------------------------------------------------
    def clean(self):
        import shutil
        # remove generated JSON directory
        if self.out_dir.exists():
            shutil.rmtree(self.out_dir, ignore_errors=True)
        # remove Ninja stamp dir
        if self._check_dir.exists():
            shutil.rmtree(self._check_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Ninja integration
    # ------------------------------------------------------------------
    def ninja_rules(self) -> list[str]:
        """Return a Ninja rule that validates YAML and emits an OK stamp."""
        rule = (
            "rule yaml_validate\n"
            "  command = python -c \"import sys,yaml,pathlib; p=pathlib.Path(sys.argv[2]); p.parent.mkdir(parents=True, exist_ok=True); yaml.safe_load(open(sys.argv[1])); p.touch()\" $in $out\n"
            "  description = YAML $in\n"
        )
        return [rule]

    def ninja_builds(self) -> list[str]:
        builds: list[str] = []
        try:
            sources = self._discover_sources()
        except MintError:
            return []
        for src in sources:
            rel = src.relative_to(self.project_root)
            out = self._check_dir / rel.with_suffix(".ok")
            # produce path strings relative to project root for Ninja
            builds.append(f"build {out}: yaml_validate {src}")
        return builds 