from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .builder import BuildConfig, Builder
from .utils import MintError, set_verbose, get_timings, run, set_dry_run, set_keep_logs
from .toolchains import get as get_toolchain, available as available_toolchains

app = typer.Typer(add_completion=False, help="mint – minimal yet ultra-stable C/C++ build tool")
console = Console()


@app.command()
def build(
    config: Optional[Path] = typer.Option("mint.yaml", "--config", "-c", help="Path to config YAML"),
    lang: str = typer.Option("auto", "--lang", help="Language/toolchain key (cpp, rust, go, etc., or auto-detect)"),
    release: bool = typer.Option(False, "--release", "-r", help="Build with optimizations (toolchain-dependent)"),
    clean_first: bool = typer.Option(False, "--clean", help="Clean before building"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show commands and full output"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print commands without executing"),
    keep_logs: bool = typer.Option(False, "--keep-logs", help="Save raw logs on failures"),
    log: Path | None = typer.Option(None, "--log", help="Write timing JSON log to this file"),
    build_dir: Path | None = typer.Option(None, "--build-dir", help="Custom build directory (default: ./build)"),
):
    """Compile & link the current project."""

    # Auto-delegate to Ninja if a build.ninja exists
    target_build_dir: Path = build_dir or (Path.cwd() / "build")
    ninja_file = target_build_dir / "build.ninja"
    if ninja_file.exists():
        console.print("[blue]build.ninja detected, invoking Ninja…[/]")
        run(["ninja", "-C", str(target_build_dir)])
        return
    try:
        # Setup flags
        set_verbose(verbose)
        set_dry_run(dry_run)
        set_keep_logs(keep_logs)

        cfg = BuildConfig.load(config)

        root = Path.cwd()

        detected_lang = lang if lang != "auto" else _detect_lang(root)

        if detected_lang == "cpp":
            builder = Builder(root, build_dir=target_build_dir, release=release, config=cfg)
            if clean_first:
                builder.clean()
            builder.build()
        else:
            try:
                TC = get_toolchain(detected_lang)
            except KeyError:
                console.print(f"[red]Unsupported toolchain '{detected_lang}'. Available: {', '.join(available_toolchains().keys())}")
                raise typer.Exit(code=1)

            tc = TC(root, target_build_dir, config=cfg.__dict__)  # pass raw dict
            if clean_first:
                tc.clean()
            tc.build()
            try:
                # flush cache for toolchain
                tc._flush_cache()
            except Exception:
                pass

        # after build success show timings
        times = get_timings()
        if times:
            console.rule("Timing Summary")
            for cmd, sec in times:
                console.print(f"[blue]{cmd}[/] -> {sec:.2f}s")
            if log:
                import json
                log.parent.mkdir(parents=True, exist_ok=True)
                log.write_text(json.dumps([{"cmd": c, "sec": s} for c, s in times], indent=2))
    except MintError as e:
        console.print(f"[red bold]⨯ {e}")
        raise typer.Exit(code=1)


@app.command()
def clean():
    """Delete build artifacts."""

    try:
        builder = Builder(Path.cwd())
        builder.clean()
    except MintError as e:
        console.print(f"[red bold]⨯ {e}")
        raise typer.Exit(code=1)


@app.command()
def configure(
    generator: str = typer.Option("ninja", "-G", help="Build system generator (ninja)"),
):
    """Generate native build scripts (Ninja). Currently supports C++ projects."""

    if generator.lower() != "ninja":
        console.print("[red]Only Ninja generator supported right now[/]")
        raise typer.Exit(1)

    root = Path.cwd()
    # collect toolchains that support ninja
    mode = 'ninja'
    from .toolchains import available
    from .utils import detect_compiler
    from .ninja_writer import NinjaWriter
    from .builder import Builder

    # load config for toolchain-specific options
    cfg = BuildConfig.load(Path("mint.yaml"))

    # instantiate builders for each available toolchain
    tcs = []
    for lang in available().keys():
        try:
            TC = get_toolchain(lang)
            tc = TC(root, root / 'build', config=cfg.__dict__)
            # skip those without ninja_rules
            if hasattr(tc, 'ninja_rules') and hasattr(tc, 'ninja_builds'):
                # skip default if no rules
                if tc.ninja_rules() or tc.ninja_builds():
                    tcs.append(tc)
        except Exception:
            continue

    if not tcs:
        console.print(f"[red]No toolchains with Ninja support found[/]")
        raise typer.Exit(1)

    # prepare ninja writer
    # pick flags from C++ as defaults
    b = Builder(root)
    nw = NinjaWriter(root, b.build_dir, b.compiler, ' '.join(b.cxxflags), ' '.join(b.ldflags))
    nw.header()
    # collect all rules
    for tc in tcs:
        for rule in tc.ninja_rules():
            nw.external_rules.append(rule)
    # base C++ rules
    nw.rules()
    # collect all builds
    for tc in tcs:
        for build_line in tc.ninja_builds():
            nw.external_builds.append(build_line)
    # write file
    ninja_file = nw.write()
    console.print(f"[green]Generated {ninja_file} for languages: {', '.join([tc.__class__.__name__ for tc in tcs])}[/]")
    console.print("Run: ninja -C build")


@app.command("version")
def version():
    """Show mint build tool version."""
    from mint import __version__
    console.print(f"mint version {__version__}")


if __name__ == "__main__":
    app()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_lang(root: Path) -> str:
    """Heuristic language detection based on well-known config files."""

    # Rust
    if (root / "Cargo.toml").exists():
        return "rust"
    # Go
    if (root / "go.mod").exists() or list(root.glob("*.go")):
        return "go"
    # Node
    if (root / "package.json").exists():
        return "node"
    # Python
    if (root / "pyproject.toml").exists() or (root / "setup.py").exists():
        return "python"
    # PHP
    if (root / "composer.json").exists() or (root / "index.php").exists():
        return "php_native"
    # Ruby
    if any(root.rglob("*.rb")):
        return "ruby_native"
    # Lua
    if any(root.rglob("*.lua")):
        return "lua_native"
    # YAML projects (pure configs)
    if any(root.rglob("*.yaml")) or any(root.rglob("*.yml")):
        return "yaml"
    # default
    return "cpp" 