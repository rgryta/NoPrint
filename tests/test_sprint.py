"""
Module with tests for noprint.sprint
"""
from unittest import mock

import pytest

import noprint

from noprint.sprint import (
    PackageFinder,
    _parse_pyfile,
    _get_module,
    _get_subpackages,
    _parse_module,
)
from noprint.exceptions import ImportException, ParentModuleNotFoundException


@pytest.mark.parametrize("origin", [None, "origin", "__init__.py"])
@pytest.mark.parametrize("name", ["name", "__pycache__"])
@mock.patch("noprint.sprint.os")
def test_get_subpackages(mock_os, origin, name):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    mod_mock = mock.MagicMock()
    mod_mock.origin = [origin] if origin is not None else []
    mod_mock.name = name
    mod_mock.search_path = "loc"
    mod_mock.submodule_search_locations = ["loc"]

    mod_mock_e = mock.MagicMock()
    mod_mock_e.origin = ["origin"]
    mod_mock_e.name = "name"
    mod_mock_e.search_path = "loc"
    mod_mock_e.submodule_search_locations = ["loc"]

    mock_os.listdir.return_value = ["name"]

    for package in _get_subpackages("noprint", verbose=True, module=mod_mock):
        assert package is not None


@pytest.mark.parametrize("sub_pkgs", [[], [mock.Mock()], [mock.Mock(), mock.Mock()]])
@pytest.mark.parametrize("origin", [None, "origin"])
def test_parse_module(origin, sub_pkgs):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    module = mock.Mock()
    module.origin = origin
    with mock.patch("noprint.sprint._get_module", return_value=module), mock.patch(
        "noprint.sprint._get_subpackages", return_value=sub_pkgs
    ):
        result = _parse_module(package="noprint")
        if module.origin:
            assert result[0] == module
        else:
            assert result[0] is None
        assert len(result[1]) == len(sub_pkgs)


def _parse_mock(package, verbose):
    return (package, [])


def test_pf_packages_iter():
    pf = PackageFinder(1)

    noprint.sprint._parse_module = _parse_mock

    packages = ("source", "test")
    assert set([x for x in pf.packages_iter(packages=packages)]) == set(packages)


@pytest.mark.parametrize(
    "ret",
    [
        [mock.MagicMock(), mock.MagicMock()],
        [mock.MagicMock(), None],
        [mock.MagicMock()] * 2,
    ],
)
def test__get_module__mod(ret):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""

    with mock.patch("noprint.sprint.Module") as mock_mod:
        if isinstance(ret[1], mock.MagicMock):
            ret[1].origin.__len__.return_value = 1
        mock_mod.side_effect = ret
        _get_module("noprint", verbose=True)


@pytest.mark.parametrize(
    "ret", [None, ParentModuleNotFoundException("Dummy exception")]
)
def test__get_module__import_exc(ret):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""

    with mock.patch("noprint.sprint.Module") as mock_mod, pytest.raises(
        ImportException
    ) as exc:
        if ret is None:
            mock_mod.return_value = ret
        else:
            mock_mod.side_effect = ret
        _get_module("noprint", verbose=True)


@pytest.mark.parametrize("code", ["print('')", "", "i=1"])
@pytest.mark.parametrize("first", [True, False])
@pytest.mark.parametrize("mod", [None, ImportException("X")])
@mock.patch("builtins.open")
def test__parse_pyfile(mock_open, mod, first, code):
    """Test method for _parse_python - finding print statements"""
    fin = mock.Mock()
    fin.return_value.readline.return_value = "# -*- coding: utf-8-sig -*-"
    fin.return_value.read.return_value = code
    mock_open.return_value.__enter__ = fin

    module = mock.Mock()
    module.origin = ["noprint"]
    module.name = "noprint"

    if mod is None:
        mod = module

    res = _parse_pyfile(mod, first)

    if isinstance(mod, ImportException):
        assert not res[0]
        assert isinstance(res[1], ImportException)
        assert res[1].args[0] == mod.args[0]
    elif "print" in code:
        assert res == ([("[noprint] Line: 1", True)], None)
    else:
        assert res == ([("[CLEAR]:[noprint]", False)], None)


@pytest.mark.parametrize("first", [True, False])
@pytest.mark.parametrize(
    "mod",
    [
        (
            [("X", False)],
            None,
        ),
        (
            [("X", True)],
            None,
        ),
        (
            [],
            ImportException("X"),
        ),
    ],
)
@mock.patch(
    "noprint.sprint._parse_pyfile", side_effect=lambda module, first_only: module
)
def test_pf_run(mock_parse, mod, first):
    """Testing function for _get_prints - verifying if code contains print statements"""

    def _subpackages(package, _):  # pylint: disable=unused-argument
        i = 0
        yield mod
        i = i + 1
        if i == 10:
            return

    with mock.patch(
        "noprint.sprint.PackageFinder.packages_iter", side_effect=_subpackages
    ):
        prints = PackageFinder(1).run(
            packages=["noprint"], first_only=first, verbose=True
        )
        expected = (mod[0], [mod[1]] if mod[1] else [])
        assert prints == expected
