"""
Module with tests for noprint.sprint
"""
from unittest import mock

import pytest

import noprint.logger as logging

from noprint.sprint import _get_subpackages, _get_prints, _parse_pyfile
from noprint.exceptions import ImportException, ParentModuleNotFoundException


@pytest.mark.parametrize("origin", [None, "origin", "__init__.py"])
@pytest.mark.parametrize("name", [None, "name", "__pycache__"])
@mock.patch("noprint.sprint.os")
def test__get_subpackages__correct(mock_os, origin, name):
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
def test__get_subpackages__missing_uninstalled_overshadowing(mock_logging, spec):
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


def test__get_subpackages__import_exc():
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""

    with mock.patch("noprint.sprint.Module") as mock_mod:
        mock_mod.side_effect = [ParentModuleNotFoundException("Dummy exception")]
        fun = iter(_get_subpackages("noprint"))
        res = next(fun).args[0]
        assert type(res) == ParentModuleNotFoundException
        assert str(res) == "Dummy exception"
        with pytest.raises(StopIteration):
            next(fun)


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
@mock.patch("noprint.sprint.Pool")
def test__get_prints(mock_pool, mod, first):
    """Testing function for _get_prints - verifying if code contains print statements"""

    def _subpackages(package, _):  # pylint: disable=unused-argument
        i = 0
        yield mod
        i = i + 1
        if i == 10:
            return

    mock_pool.return_value.__enter__.return_value.imap.side_effect = _subpackages

    prints = _get_prints(packages=["noprint"], first_only=first, verbose=True)
    expected = (mod[0], [mod[1]] if mod[1] else [])
    assert prints == expected
