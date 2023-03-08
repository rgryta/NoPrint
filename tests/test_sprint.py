"""
Module with tests for noprint.print_seeker
"""
from unittest import mock

import pytest

import noprint.logger as logging

from noprint.sprint import _get_subpackages, _get_prints, _parse_pyfile
from noprint.exceptions import ImportException


@pytest.mark.parametrize("origin", [None, "origin", "__init__.py"])
@pytest.mark.parametrize("name", [None, "name", "__pycache__"])
@mock.patch("noprint.sprint.os")
@mock.patch("noprint.sprint.find_spec")
def test__get_subpackages__correct(mock_spec, mock_os, origin, name):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    if origin is None and name is None:
        mod_mock = None
    else:
        mod_mock = mock.Mock()
        mod_mock.origin = origin
        mod_mock.name = name
        mod_mock.submodule_search_locations = ["loc"]

    mod_mock_e = mock.Mock()
    mod_mock_e.origin = "origin"
    mod_mock_e.name = "name"
    mod_mock_e.submodule_search_locations = ["loc"]

    mock_os.listdir.return_value = ["name"]

    mock_spec.side_effect = [
        spec
        for specs in [[mod_mock] * 2, [mod_mock] * 2, [mod_mock_e] * 2]
        for spec in specs
    ]
    for package in _get_subpackages("noprint", verbose=True):
        assert package is not None


@pytest.mark.parametrize("spec", [None, mock.Mock(), True])
@mock.patch("noprint.sprint.logging")
@mock.patch("noprint.sprint.find_spec")
def test__get_subpackages__missing_uninstalled_overshadowing(
    mock_spec, mock_logging, spec
):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    spec_system = mock.Mock()

    mock_logging.WARNING = logging.WARNING
    mock_logging.log = mock.MagicMock()

    if isinstance(spec, bool):
        spec = mock.Mock()
        mock_spec.side_effect = [spec, spec_system]

        for _ in _get_subpackages("noprint", verbose=True):
            pass
        args = mock_logging.log.mock_calls
        assert len(args) == 1
        assert args[0] == mock.call(
            "Module [noprint] is overshadowing installed module", 30
        )
        return
    if spec:
        mock_spec.side_effect = [spec, None]

        for _ in _get_subpackages("noprint", verbose=True):
            pass
        args = mock_logging.log.mock_calls
        assert len(args) == 1
        assert args[0] == mock.call("Module [noprint] is not installed", 30)
    else:
        mock_spec.side_effect = [spec, spec_system]
        assert (
            next(_get_subpackages("noprint")).args[0]
            == "Module [noprint] is not present in current environment, directory or PYTHONPATH"
        )


@mock.patch("noprint.sprint.find_spec")
def test__get_subpackages__import_exc(mock_spec):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    mock_spec.side_effect = [Exception("Dummy exception")]
    assert (
        next(_get_subpackages("noprint")).args[0]
        == "Module [noprint] raised Exception on import"
    )
    assert (
        next(_get_subpackages("noprint")).args[0]
        == "Module [noprint] raised StopIteration on import"
    )


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
    module.origin = "noprint"
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
