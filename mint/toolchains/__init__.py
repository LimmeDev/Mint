from __future__ import annotations

from typing import Dict, Type

from .base import BaseToolchain

_TOOLCHAINS: Dict[str, Type[BaseToolchain]] = {}


def register(name: str):
    """Class decorator to register a toolchain by language key."""

    def decorator(cls):
        if not issubclass(cls, BaseToolchain):
            raise TypeError("Toolchain must inherit from BaseToolchain")
        _TOOLCHAINS[name] = cls
        return cls

    return decorator


def get(name: str) -> Type[BaseToolchain]:
    try:
        return _TOOLCHAINS[name]
    except KeyError as e:
        raise KeyError(f"No toolchain registered for language '{name}'") from e


def available() -> Dict[str, Type[BaseToolchain]]:
    return dict(_TOOLCHAINS)


# ---------------------------------------------------------------------------
# Auto-import built-in toolchains so they self-register via the decorator.
# Keeping the imports optional avoids forcing the user to install every
# build-time dependency.  If a language's runtime is missing (e.g. `cargo`),
# the corresponding module can still be imported because we only shell out
# at build() time.
# ---------------------------------------------------------------------------

from importlib import import_module

_builtin = (
    "cpp",
    "rust",
    "go",
    "node",
    "python",
    "command",
    "java",
    "kotlin",
    "csharp",
    "swift",
    "ruby",
    "php",
    "dart",
    "scala",
    "haskell",
    "zig",
    "java_native",
    "rust_native",
    "swift_native",
    "csharp_native",
    "kotlin_native",
    "scala_native",
    "haskell_native",
    "zig_native",
    "dart_native",
    "php_native",
    "ruby_native",
    "lua_native",
)

for _name in _builtin:
    try:
        import_module(f"mint.toolchains.{_name}")
    except ModuleNotFoundError:
        # The optional toolchain may rely on deps that are not installed.
        # It can still be registered later if the user installs them.
        pass 