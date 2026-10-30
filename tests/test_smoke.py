"""Smoke test: confirms the package layout imports and pytest is wired up."""

import importlib

import pytest


@pytest.mark.parametrize("module", ["src.ingestion", "src.analysis", "src.modeling", "src.viz"])
def test_subpackages_import(module: str) -> None:
    assert importlib.import_module(module) is not None
