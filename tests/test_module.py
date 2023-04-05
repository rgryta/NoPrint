"""
Module with tests for noprint.module
"""
import os

from pathlib import Path
from unittest import mock
from importlib.machinery import ModuleSpec, PathFinder

import pytest

from noprint.exceptions import ParentModuleNotFoundException
from noprint.module import (
    Module,
    _get_module_search_path,
    _get_module_location,
    _find_parent_dir,
    _next_path,
    _package_to_dir,
)


@pytest.fixture
def mock_module():
    """Mock a module for testing"""

    class MockModule(Module):
        def __init__(self):
            self._package = "test.package"
            self._parent_loc = "/root"

    return MockModule


@pytest.mark.parametrize("search_loc", [["/root"], mock.Mock()])
def test__get_module_search_path(search_loc):
    mspec = mock.Mock()
    if isinstance(search_loc, mock.Mock):
        search_loc._path = ["/root"]
    mspec.submodule_search_locations = search_loc
    assert _get_module_search_path(mspec) == "/root"


@pytest.mark.parametrize("has_loc", [False, True])
@pytest.mark.parametrize("file_name", ["file.py", "__init__.py", "file.nopy"])
def test__get_module_location(has_loc, file_name):
    mspec = mock.Mock()
    mspec.has_location = has_loc
    mspec.origin = f"/root/test/{file_name}"
    with mock.patch(
        "noprint.module._get_module_search_path", side_effect=["/root/test"]
    ):
        if not has_loc or file_name == "__init__.py":
            assert _get_module_location(mspec) == str(Path("/root"))
        else:
            assert _get_module_location(mspec) == str(Path("/root/test"))


@pytest.mark.parametrize("in_cwd", [False, True])
@pytest.mark.parametrize("found", [False, True])
def test__find_parent_dir(in_cwd, found):
    with mock.patch("noprint.module.PathFinder.find_spec") as mod_findspec:
        mock_mod = mock.Mock(spec=ModuleSpec)
        mock_mod.origin = "origin"
        mod_findspec.side_effect = [mock_mod if found else None]
        if not found:
            with pytest.raises(ParentModuleNotFoundException):
                _find_parent_dir("test", in_cwd)
        else:
            res = _find_parent_dir("test", in_cwd)
            assert res == "."


@pytest.mark.parametrize(
    "isdir", [[True], [False, True], [False, False, True], [False, False, False]]
)
def test__next_path(isdir):
    with mock.patch("noprint.module.os.path.isdir", side_effect=isdir):
        submodules = "test.test.test"
        res = _next_path("test", submodules)
        if any(isdir):
            count = sum([not bls for bls in isdir])
            assert res == str(Path("test/" + submodules.rsplit(".", maxsplit=count)[0]))
        else:
            assert res is None


def test__package_to_dir():
    with mock.patch("noprint.module.os.path.isdir", return_value=True):
        submodules = "test.test.test"
        assert str(Path(_package_to_dir("test", submodules))) == str(
            Path("test/test.test.test/")
        )
    with mock.patch("noprint.module.os.path.isdir", return_value=False):
        submodules = "test.test.test"
        assert _package_to_dir("test", submodules) is None
