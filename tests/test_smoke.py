from __future__ import annotations


def test_package_importable() -> None:
    import uptempo

    assert uptempo.__version__
