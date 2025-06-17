from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, List, Set
import os

from rich.console import Console

from ..utils import MintError, run

console = Console()


IMPORT_RE = re.compile(r"^\s*import\s+([a-zA-Z0-9_\.]+);")


def find_java_sources(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.java") if "build" not in p.parts]


def parse_imports(java_file: Path) -> Set[str]:
    imports: Set[str] = set()
    for line in java_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = IMPORT_RE.match(line)
        if m:
            imports.add(m.group(1).split(".")[0])
    return imports


def ensure_javac() -> str:
    javac = shutil.which("javac")
    if not javac:
        raise MintError("javac not found in PATH. Install JDK.")
    return javac


def ensure_jar() -> str:
    jar = shutil.which("jar")
    if not jar:
        raise MintError("jar command not found. Install JDK.")
    return jar


def compile_java_sources(sources: List[Path], *, out_dir: Path, classpath: List[str] | None = None):
    if not sources:
        return
    javac = ensure_javac()
    classpath_str = os.pathsep.join(classpath) if classpath else ""
    cmd = [javac, "-d", str(out_dir)]
    if classpath_str:
        cmd += ["-classpath", classpath_str]
    # Split compile into batches to avoid arg list overflow
    batch_size = 100
    for i in range(0, len(sources), batch_size):
        batch = [str(p) for p in sources[i : i + batch_size]]
        run(cmd + batch)


def create_jar(target: Path, *, manifest_main: str | None, classes_dir: Path):
    jar = ensure_jar()
    manifest_arg = []
    if manifest_main:
        mf_path = classes_dir / "MANIFEST.MF"
        mf_path.write_text(f"Main-Class: {manifest_main}\n")
        manifest_arg = ["cfm", str(target), str(mf_path)]
    else:
        manifest_arg = ["cf", str(target)]
    run([jar, *manifest_arg, "-C", str(classes_dir), "."]) 