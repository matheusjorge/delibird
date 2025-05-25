from pathlib import Path

import pytest

from delibird.core.package import _ensure_path


def test_ensure_path():
    assert _ensure_path(".") == Path(".")
    assert _ensure_path("test") == Path("test")
    assert _ensure_path(Path("test")) == Path("test")


def test_ensure_path_raises_value_error():
    with pytest.raises(TypeError):
        _ensure_path(1)
