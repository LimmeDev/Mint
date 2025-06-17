from __future__ import annotations

from pathlib import Path
from typing import Optional
import yaml
import os
import sys
import shutil
import subprocess

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
    explain: bool = typer.Option(False, "--explain", help="Print full compile/link lines and include/lib paths on failure"),
    cache: str = typer.Option("none", "--cache", help="Build cache backend: none | sccache | auto"),
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
        if explain:
            os.environ['MINT_EXPLAIN'] = '1'

        use_sccache = False
        if cache.lower() in {"sccache", "auto"}:
            if shutil.which("sccache"):
                use_sccache = True
            elif cache.lower() == "sccache":
                console.print("[yellow]sccache requested but not found in PATH – continuing without cache.[/]")

        cfg = BuildConfig.load(config)

        root = Path.cwd()

        detected_lang = lang if lang != "auto" else _detect_lang(root)

        if detected_lang == "cpp":
            builder = Builder(root, build_dir=target_build_dir, release=release, config=cfg, use_sccache=use_sccache)
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
def clean(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt and delete immediately"),
):
    """Delete build artifacts (./build by default).

    Adds a safety prompt unless the --yes/-y flag is provided or running in non-interactive mode (stdin not a TTY).
    """

    build_dir = Builder(Path.cwd()).build_dir

    if not yes and typer.get_app().info.param_defaults:  # heuristic for interactive TTY
        confirm = typer.confirm(f"Delete {build_dir}?", default=False)
        if not confirm:
            console.print("[yellow]Clean aborted[/]")
            raise typer.Exit()

    try:
        builder = Builder(Path.cwd())
        builder.clean()
    except MintError as e:
        console.print(f"[red bold]⨯ {e}")
        raise typer.Exit(code=1)


@app.command()
def configure(
    generator: str = typer.Option("ninja", "-G", help="Build system generator (ninja)"),
    ide: str = typer.Option(None, "--ide", help="Generate IDE project files: vs | xcode | eclipse"),
):
    """Generate native build scripts (Ninja) and/or IDE project files."""

    if ide:
        ide = ide.lower()
        if ide not in {"vs", "xcode", "eclipse"}:
            console.print("[red]Unsupported IDE. Choose vs, xcode, or eclipse.[/]")
            raise typer.Exit(1)

    if ide == "vs":
        _generate_vs_project()
        # Continue with ninja generator if requested additionally

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


@app.command()
def init(
    output: Path = typer.Option("mint.yaml", "--output", "-o", help="Path to write generated YAML"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Overwrite existing file without confirmation"),
):
    """Interactively create a starter *mint.yaml* by inspecting the current repository.

    The command attempts to:
    1. Detect the primary language/tool-chain.
    2. Discover source files (currently C/C++ only).
    3. Prompt the user for missing metadata (target name, shared vs executable).
    4. Emit a minimal yet valid *mint.yaml* that the user can build straight away.
    """

    root = Path.cwd()

    # ------------------------------------------------------------------
    # Safeguards
    # ------------------------------------------------------------------
    if output.exists() and not yes:
        overwrite = typer.confirm(f"{output} already exists – overwrite?", default=False)
        if not overwrite:
            console.print("[yellow]Aborted – existing file left untouched.[/]")
            raise typer.Exit()

    # ------------------------------------------------------------------
    # Language detection
    # ------------------------------------------------------------------
    detected_lang = _detect_lang(root)

    if detected_lang not in {"cpp", "c", "cpp_native"}:  # currently we only scaffold C/C++
        console.print(
            f"[red]mint init currently supports C/C++ projects only (detected: {detected_lang}). "
            "Feel free to create mint.yaml manually for other languages."
        )
        raise typer.Exit(1)

    # ------------------------------------------------------------------
    # Interactive prompts
    # ------------------------------------------------------------------
    default_name = root.name
    target_name: str = typer.prompt("Target name", default=default_name)

    shared_choice = typer.prompt("Build type [exe/shared]", default="exe")
    target_type = "shared" if shared_choice.lower().startswith("s") else "executable"

    # ------------------------------------------------------------------
    # Source discovery – limit to C/C++ files for now
    # ------------------------------------------------------------------
    c_exts = {".c", ".cc", ".cpp", ".cxx"}
    discovered_sources = [str(p.relative_to(root)) for p in root.rglob("*") if p.suffix in c_exts and "build" not in p.parts]

    if not discovered_sources:
        # Fallback to typical layout placeholder
        discovered_sources = ["src/*.cpp"]

    # ------------------------------------------------------------------
    # YAML structure
    # ------------------------------------------------------------------
    config = {
        "name": target_name,
        "cxxflags": [],
        "ldflags": [],
        "targets": [
            {
                "type": target_type,
                "name": target_name,
                "sources": sorted(discovered_sources),
            }
        ],
    }

    # ------------------------------------------------------------------
    # Write file
    # ------------------------------------------------------------------
    output.write_text(yaml.safe_dump(config, sort_keys=False, indent=2))
    console.print(f"[green]Created {output.relative_to(root)} – happy hacking!")


@app.command()
def doctor():
    """Print environment diagnostics to help debug common issues."""

    import platform
    import shutil
    import subprocess

    console.rule("[bold cyan]mint doctor")

    # Basic system info
    console.print(f"[blue]OS:[/] {platform.system()} {platform.release()} ({platform.machine()})")
    console.print(f"[blue]Python:[/] {platform.python_version()} ({sys.executable})")

    # Compiler detection
    from .utils import detect_compiler

    try:
        cxx = detect_compiler()
        result = subprocess.run([cxx, "--version"], capture_output=True, text=True)
        version_line = result.stdout.splitlines()[0]
        console.print(f"[blue]C++ compiler:[/] {version_line}")
    except MintError as e:
        console.print(f"[red]C++ compiler:[/] {e}")

    # Path order summary (first 5 entries)
    path_entries = os.getenv("PATH", "").split(":")[:5]
    console.print("[blue]PATH (first 5):[/] " + ", ".join(path_entries))

    # Check for Ninja presence
    ninja = shutil.which("ninja")
    console.print(f"[blue]Ninja:[/] {'found at ' + ninja if ninja else 'not found'}")

    # Check for sccache
    sccache = shutil.which("sccache")
    console.print(f"[blue]sccache:[/] {'found' if sccache else 'not found'}")

    console.rule()


@app.command()
def upgrade(
    pre: bool = typer.Option(False, "--pre", help="Install canary/pre-release version"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Self-upgrade mint via pip.

    Example: `mint upgrade --pre` for latest canary build.
    """

    if not yes:
        proceed = typer.confirm("Upgrade mint to the latest version available on PyPI?", default=True)
        if not proceed:
            console.print("[yellow]Upgrade cancelled[/]")
            raise typer.Exit()

    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"]
    if pre:
        cmd.append("--pre")
    cmd.append("mint-build")

    console.print("[cyan]$ " + " ".join(cmd))
    try:
        subprocess.check_call(cmd)
        console.print("[green]mint upgraded successfully – restart your shell to pick up the new version if needed.")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Upgrade failed (exit {e.returncode}). Check the output above for details.")
        raise typer.Exit(code=e.returncode)


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


# ---------------------------------------------------------------------------
# IDE project generation helpers
# ---------------------------------------------------------------------------


def _generate_vs_project():
    """Emit a minimal Visual Studio Makefile (.vcxproj) that delegates to mint build."""

    import uuid

    root = Path.cwd()
    proj_name = root.name
    guid = str(uuid.uuid4()).upper()

    vcxproj = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
<Project DefaultTargets=\"Build\" ToolsVersion=\"17.0\" xmlns=\"http://schemas.microsoft.com/developer/msbuild/2003\">
  <ItemGroup Label=\"ProjectConfigurations\">
    <ProjectConfiguration Include=\"Debug|x64\">
      <Configuration>Debug</Configuration>
      <Platform>x64</Platform>
    </ProjectConfiguration>
  </ItemGroup>
  <PropertyGroup Label=\"Globals\">
    <ProjectGuid>{{{guid}}}</ProjectGuid>
    <Keyword>MakeFileProj</Keyword>
    <ProjectName>{proj_name}</ProjectName>
  </PropertyGroup>
  <Import Project=\"$(VCTargetsPath)\\Microsoft.Cpp.Default.props\" />
  <PropertyGroup Condition=\"'$(Configuration)|$(Platform)'=='Debug|x64'\" Label=\"Configuration\">
    <ConfigurationType>Makefile</ConfigurationType>
    <UseDebugLibraries>true</UseDebugLibraries>
  </PropertyGroup>
  <Import Project=\"$(VCTargetsPath)\\Microsoft.Cpp.props\" />
  <PropertyGroup Label=\"UserMacros\" />
  <PropertyGroup>
    <NMakeBuildCommandLine>mint build</NMakeBuildCommandLine>
    <NMakeCleanCommandLine>mint clean --yes</NMakeCleanCommandLine>
    <NMakeReBuildCommandLine>mint clean --yes &amp;&amp; mint build</NMakeReBuildCommandLine>
    <NMakeOutput>build\\bin\\{proj_name}</NMakeOutput>
  </PropertyGroup>
  <ItemGroup />
  <Import Project=\"$(VCTargetsPath)\\Microsoft.Cpp.targets\" />
  <ImportGroup Label=\"ExtensionTargets\" />
</Project>"""

    proj_path = root / f"{proj_name}.vcxproj"
    proj_path.write_text(vcxproj)

    console.print(f"[green]Generated {proj_path} – open it in Visual Studio and hit Build.[/]")

    # Optional .sln wrapper: VS can open .vcxproj directly, so we skip for brevity. 