from __future__ import annotations

import abc
from pathlib import Path
from typing import List, Dict, Type
import atexit

from ..utils import load_cache, save_cache, fingerprint

class ToolchainError(RuntimeError):
    ...

_TOOLCHAINS: Dict[str, Type[BaseToolchain]] = {}

class BaseToolchain(abc.ABC):
    """Abstract base for any language/toolchain."""

    def __init__(self, project_root: Path, build_dir: Path, config: dict | None = None):
        self.project_root = project_root
        self.build_dir = build_dir
        self.config = config or {}
        self._fp_cache: dict = load_cache(build_dir)
        # register for atexit flush
        _ALL_TOOLCHAINS.append(self)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    @abc.abstractmethod
    def build(self) -> Path | List[Path]:  # returns artifact(s)
        """Perform build and return the produced artifact path(s)."""

    def clean(self) -> None:
        """Optional clean logic specific to toolchain."""
        pass

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _is_dirty(self, src: Path) -> bool:
        key = str(src)
        new_hash = fingerprint(src)
        cached = self._fp_cache.get(key)
        return cached != new_hash

    def _update_cache(self, src: Path):
        self._fp_cache[str(src)] = fingerprint(src)

    def _flush_cache(self):
        save_cache(self.build_dir, self._fp_cache)

    # ------------------------------------------------------------------
    # Ninja build generation
    # ------------------------------------------------------------------
    def ninja_rules(self) -> list[str]:
        """Optional: Return list of Ninja rule definitions for this toolchain."""
        return []

    def ninja_builds(self) -> list[str]:
        """Optional: Return list of Ninja build lines for this toolchain."""
        return []

# atexit flush of all toolchains
_ALL_TOOLCHAINS: list[BaseToolchain] = []

def _flush_all_caches():
    for tc in _ALL_TOOLCHAINS:
        try:
            tc._flush_cache()
        except Exception:
            pass

atexit.register(_flush_all_caches) 