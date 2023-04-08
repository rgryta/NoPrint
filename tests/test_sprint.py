"""
Module with tests for noprint.sprint
"""
from unittest import mock

import pytest

import noprint.logger as logging

from noprint.sprint import PackageFinder, _parse_pyfile, _get_module
from noprint.exceptions import ImportException, ParentModuleNotFoundException


@pytest.mark.parametrize("origin", [None, "origin", "__init__.py"])
@pytest.mark.parametrize("name", [None, "name", "__pycache__"])
@mock.patch("noprint.sprint.os")
def _get_subpackages__correct(mock_os, origin, name):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    if origin is None and name is None:
        mod_mock = None
    else:
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

    with mock.patch("noprint.sprint.Module") as mock_mod:
        mock_mod.side_effect = [
            spec
            for specs in [[mod_mock] * 2, [mod_mock] * 2, [mod_mock_e] * 2]
            for spec in specs
        ]
        for package in _get_subpackages("noprint", verbose=True):
            assert package is not None


@pytest.mark.parametrize("spec", [None, mock.MagicMock(), True])
@mock.patch("noprint.sprint.logging")
def _get_subpackages__missing_uninstalled_overshadowing(mock_logging, spec):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    spec_system = mock.MagicMock()

    mock_logging.WARNING = logging.WARNING
    mock_logging.log = mock.MagicMock()

    with mock.patch("noprint.sprint.Module") as mock_mod:
        if isinstance(spec, bool):
            spec = mock.MagicMock()
            mock_mod.side_effect = [spec, spec_system]

            for _ in _get_subpackages("noprint", verbose=True):
                pass
            args = mock_logging.log.mock_calls
            assert len(args) == 1
            assert args[0] == mock.call(
                "Module [noprint] is overshadowing installed module", 30
            )
            return
        if spec:
            mock_mod.side_effect = [spec, None]

            for _ in _get_subpackages("noprint", verbose=True):
                pass
            args = mock_logging.log.mock_calls
            assert len(args) == 1
            assert args[0] == mock.call("Module [noprint] is not installed", 30)
        else:
            mock_mod.side_effect = [spec, spec_system]
            assert (
                next(_get_subpackages("noprint")).args[0]
                == "Module [noprint] is not present in current environment, directory or PYTHONPATH"
            )


@pytest.mark.parametrize("ret", [[mock.MagicMock(), mock.MagicMock()], [mock.MagicMock(), None], [mock.MagicMock()]*2])
def test__get_module__mod(ret):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""

    with mock.patch("noprint.sprint.Module") as mock_mod:
        if isinstance(ret[1], mock.MagicMock):
            ret[1].origin.__len__.return_value = 1
        mock_mod.side_effect = ret
        _get_module("noprint", verbose=True)


@pytest.mark.parametrize("ret", [None, ParentModuleNotFoundException("Dummy exception")])
def test__get_module__import_exc(ret):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""

    with mock.patch("noprint.sprint.Module") as mock_mod, \
            pytest.raises(ImportException) as exc:
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
@mock.patch("noprint.sprint._parse_pyfile", side_effect=lambda module, first_only: module)
@mock.patch("noprint.sprint.Pool")
def test_pf_run(mock_pool, mock_parse, mod, first):
    """Testing function for _get_prints - verifying if code contains print statements"""

    def _subpackages(package, _):  # pylint: disable=unused-argument
        i = 0
        yield mod
        i = i + 1
        if i == 10:
            return

    with mock.patch("noprint.sprint.PackageFinder.packages_iter", side_effect=_subpackages):
        prints = PackageFinder(1).run(
            packages=["noprint"], first_only=first, verbose=True
        )
        expected = (mod[0], [mod[1]] if mod[1] else [])
        assert prints == expected
