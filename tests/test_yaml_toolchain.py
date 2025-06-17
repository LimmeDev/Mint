import tempfile
from pathlib import Path

import pytest

from mint.toolchains.yaml import YAMLToolchain
from mint.utils import MintError


def _make_project(tmp_path: Path, content: str, filename: str = "config.yaml") -> Path:
    yf = tmp_path / filename
    yf.write_text(content)
    return yf


def test_yaml_toolchain_valid(tmp_path: Path):
    _make_project(tmp_path, """
    key: value
    list:
      - 1
      - 2
    """)

    build_dir = tmp_path / "build"
    tc = YAMLToolchain(tmp_path, build_dir, config={"convert": True})
    outputs = tc.build()

    # Expect JSON conversion file present
    assert outputs, "Outputs should not be empty"
    for out in outputs:
        assert out.exists()
        assert out.suffix == ".json"


def test_yaml_toolchain_invalid(tmp_path: Path):
    # Missing colon induces error
    _make_project(tmp_path, "invalid_yaml: [1, 2,", filename="bad.yaml")

    build_dir = tmp_path / "build"
    tc = YAMLToolchain(tmp_path, build_dir)
    with pytest.raises(MintError):
        tc.build() 