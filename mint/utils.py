from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import hashlib
import json
from pathlib import Path
from typing import List
import time
import shlex
import concurrent.futures

from rich.console import Console

console = Console()

# Verbosity and dry-run flags toggled by CLI.
_VERBOSE = False
_DRY_RUN = False

# Keep raw logs on failure
_KEEP_LOGS = False

# timing
_TIMINGS: list[tuple[str, float]] = []


def set_verbose(v: bool):
    global _VERBOSE
    _VERBOSE = v


def set_dry_run(v: bool):
    """Toggle dry-run mode: print commands without executing."""
    global _DRY_RUN
    _DRY_RUN = v


def set_keep_logs(v: bool):
    """Toggle raw log capture for failed commands."""
    global _KEEP_LOGS
    _KEEP_LOGS = v


class MintError(RuntimeError):
    """Custom error wrapper so the CLI can present clean messages."""


def run(cmd: List[str], *, cwd: Path | None = None) -> None:
    """Run a shell command with rich feedback.

    Streams live output when verbose mode is on. On error, shows captured
    stdout/stderr so the caller gets actionable diagnostics.
    """

    start = time.perf_counter()

    # Dry-run support
    if _DRY_RUN:
        console.print(f"[magenta][dry-run]$ {' '.join(cmd)}[/]")
        return

    if _VERBOSE:
        console.print(f"[cyan]$ {' '.join(cmd)}[/]")
        result = subprocess.run(cmd, cwd=cwd)
        rc = result.returncode
    else:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        rc = result.returncode

    if rc != 0:
        if not _VERBOSE:
            console.rule(f":boom: Command Failed ({rc})")
            if result.stdout:
                console.print("[yellow]stdout:[/]")
                console.print(result.stdout.rstrip())
            if result.stderr:
                console.print("[red]stderr:[/]")
                console.print(result.stderr.rstrip())
        # Keep raw logs to file
        if _KEEP_LOGS and cwd is not None:
            logs_dir = Path(cwd) / 'build' / 'logs'
            logs_dir.mkdir(parents=True, exist_ok=True)
            import time
            ts = int(time.time())
            log_file = logs_dir / f"mint-fail-{ts}.log"
            log_file.write_text(result.stdout + '\n' + result.stderr)
            console.print(f"[blue]Raw logs written to {log_file}[/]")
        raise MintError(f"Command failed (exit {rc}): {' '.join(cmd)}")

    # record timing
    duration = time.perf_counter() - start
    _TIMINGS.append((shlex.join(cmd[:2]) if len(cmd)>2 else ' '.join(cmd), duration))


def get_timings() -> list[tuple[str, float]]:
    return _TIMINGS


_DEFAULT_COMPILERS = [
    os.getenv("CXX"),
    "clang++",
    "g++",
]


def detect_compiler() -> str:
    """Return a working C++ compiler executable or raise MintError."""

    for cxx in _DEFAULT_COMPILERS:
        if not cxx:
            continue
        if shutil.which(cxx):
            return cxx
    raise MintError(
        "No C++ compiler found. Install clang++ or g++, or set the CXX env var."
    )


def default_build_dir(root: Path) -> Path:
    return root / "build"


# ---------------------------------------------------------------------------
# Simple fingerprint cache utilities (per build directory)
# ---------------------------------------------------------------------------


def _cache_path(build_dir: Path) -> Path:
    return build_dir / "cache.json"


def load_cache(build_dir: Path) -> dict:
    p = _cache_path(build_dir)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def save_cache(build_dir: Path, data: dict):
    p = _cache_path(build_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data))


def fingerprint(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest() 