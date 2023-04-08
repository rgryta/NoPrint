"""
Module with tests for noprint.module
"""
from pathlib import Path
from unittest import mock
from importlib.machinery import ModuleSpec

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


@pytest.mark.parametrize("search_loc", [["/root"], mock.Mock()])
def test__get_module_search_path(search_loc):
    """Testing _get_module_search_path"""
    mspec = mock.Mock()
    if isinstance(search_loc, mock.Mock):
        search_loc._path = ["/root"]  # pylint:disable=protected-access
    mspec.submodule_search_locations = search_loc
    assert _get_module_search_path(mspec) == "/root"


@pytest.mark.parametrize("has_loc", [False, True])
@pytest.mark.parametrize("file_name", ["file.py", "__init__.py", "file.nopy"])
def test__get_module_location(has_loc, file_name):
    """Testing _get_module_location"""
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
    """Testing _find_parent_dir"""
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
    """Testing _next_path"""
    with mock.patch("noprint.module.os.path.isdir", side_effect=isdir):
        submodules = "test.test.test"
        res = _next_path("test", submodules)
        if any(isdir):
            count = sum(not bls for bls in isdir)
            assert res == str(Path("test/" + submodules.rsplit(".", maxsplit=count)[0]))
        else:
            assert res is None


def test__package_to_dir():
    """Testing _package_to_dir"""
    with mock.patch("noprint.module.os.path.isdir", return_value=True):
        submodules = "test.test.test"
        assert str(Path(_package_to_dir("test", submodules))) == str(
            Path("test/test.test.test/")
        )
    with mock.patch("noprint.module.os.path.isdir", return_value=False):
        submodules = "test.test.test"
        assert _package_to_dir("test", submodules) is None


@pytest.mark.parametrize("found", [False, True])
def test_module___init__(found):
    """Testing Module.__init__"""
    with mock.patch(
        "noprint.module._find_parent_dir",
        side_effect=["/root" if found else Exception("exc")],
    ):
        if found:
            mod = Module(package="mod.module")
            assert mod.name == "mod.module"
            assert mod._parent_loc == "/root"  # pylint:disable=protected-access
        else:
            with pytest.raises(ParentModuleNotFoundException):
                Module(package="mod.module")


@pytest.mark.parametrize("isdir", [False, True])
@pytest.mark.parametrize("isfile", [False, True])
@mock.patch("noprint.module.os.path.isdir")
@mock.patch("noprint.module.os.path.isfile")
def test_module_origin(mock_isfile, mock_isdir, mock_module, isdir, isfile):
    """Testing Module.origin"""
    mock_isdir.return_value = isdir
    mock_isfile.return_value = isfile
    module = mock_module()
    if isfile is False:
        assert module.origin == []
    elif isdir is False:
        assert module.origin == [str(Path("/root/test/subpackage.py"))]
    else:
        assert "__init__.py" in [origin[-11:] for origin in module.origin]
        assert "__main__.py" in [origin[-11:] for origin in module.origin]


@pytest.mark.parametrize("isdir", [False, True])
@mock.patch("noprint.module.os.path.isdir")
def test_module_search_path(mock_isdir, mock_module, isdir):
    """Testing Module.search_path"""
    mock_isdir.return_value = isdir
    module = mock_module()
    with mock.patch("noprint.module._package_to_dir", return_value="/root"):
        assert [module.search_path] == ["/root" if isdir else None]


def test_module___eq__(mock_module):
    """Testing Module.__eq__"""
    module = mock_module()
    module_other = mock_module()
    assert module == module_other
    module_other._parent_loc = "/nonroot"  # pylint:disable=protected-access
    assert module != module_other
    assert module != 0
