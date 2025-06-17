# Mint Build Tool

A minimal yet robust build system for C and C++ projects with optional language‐specific extensions (Rust, Go, etc.).  Mint focuses on speed, cross-platform compatibility, and zero-configuration defaults—you can compile a simple project with one command:

```bash
mint build
```

## Features

* **Zero-config**: run in any directory containing `*.cpp` files—no JSON or XML manifests required.
* **Cross-platform**: Windows, macOS, and Linux supported out of the box (uses `clang++` or `g++`).
* **Incremental**: only recompiles files whose timestamps changed.
* **Parallel**: compiles sources concurrently using all CPU cores.
* **Multiple toolchains**: choose `--lang rust`, `--lang go`, etc., to delegate to language-specific builders.
* **Ninja generator**: `mint configure` writes a `build.ninja` for IDE integration.
* **YAML toolchain**: includes `yaml` for configuration validation.

## Installation (pip)

```bash
python -m pip install mint-build
```

Or from source:

```bash
git clone https://github.com/LimmeDev/Mint.git
cd Mint
python -m pip install -e .
```

## Quick Start

```bash
# in your C/C++ project directory
mint build          # Debug build (default)
mint build -r       # Release build (-O3)

mint clean          # Remove build artifacts
```

## Command-line Reference

```bash
mint build  [options]   Compile & link project
mint clean              Delete build directory
mint configure          Generate build.ninja
mint version            Show Mint version
```

Common `build` options:

| Option | Description |
|--------|-------------|
| `--release, -r` | Optimised build (equivalent to `-O3`) |
| `--clean`       | Clean before building |
| `--lang <key>`  | Force toolchain (`cpp`, `rust`, `go`, …) |
| `--verbose, -v` | Show every compiler command |
| `--dry-run`     | Print commands without executing |

## Design Goals

1. **Simplicity**—one small dependency-free YAML config (optional).
2. **Speed**—uses a thread-pool and minimal I/O.
3. **Portability**—no POSIX‐only tricks; works with MSVC, MinGW, Clang, GCC.

## Contributing

Issues and PRs are welcome!  See `CONTRIBUTING.md` for guidelines.

## License

MIT 