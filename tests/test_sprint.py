"""
Module with tests for noprint.print_seeker
"""
from unittest import mock

import pytest

from noprint.sprint import _get_subpackages, _get_prints
from noprint.exceptions import ImportException


@pytest.mark.parametrize("origin", [None, "origin", "__init__.py"])
@pytest.mark.parametrize("name", [None, "name", "__pycache__"])
@mock.patch("noprint.sprint.os")
@mock.patch("noprint.sprint.find_spec")
def test__get_subpackages(mock_spec, mock_os, origin, name):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    mod_mock = mock.Mock()
    mod_mock.origin = origin
    mod_mock.name = name
    mod_mock.submodule_search_locations = ["loc"]

    mod_mock_e = mock.Mock()
    mod_mock_e.origin = "origin"
    mod_mock_e.name = "name"
    mod_mock_e.submodule_search_locations = ["loc"]

    mock_os.listdir.return_value = ["name"]

    mock_spec.side_effect = [mod_mock, mod_mock, mod_mock_e]
    for package in _get_subpackages("noprint"):
        assert package is not None


@mock.patch("noprint.sprint.find_spec")
def test__get_subpackages__import_exc(mock_spec):
    """Testing function for _get_subpackages - mock several different module specs and finish with a proper one"""
    mock_spec.side_effect = [Exception("Dummy exception")]
    with pytest.raises(ImportException):
        for _ in _get_subpackages("noprint"):
            pass


@pytest.mark.parametrize("code", ["print('')", "", "i=1"])
@pytest.mark.parametrize("first", [True, False])
@mock.patch("builtins.open")
@mock.patch("noprint.sprint._get_subpackages")
def test__get_prints(mock_subpackages, mock_open, first, code):
    """Testing function for _get_prints - verifying if code contains print statements"""

    def _subpackages(package):  # pylint: disable=unused-argument
        i = 0
        module = mock.Mock()
        module.origin = "origin"
        yield module
        i = i + 1
        if i == 10:
            return

    mock_subpackages.side_effect = _subpackages

    fin = mock.Mock()
    fin.return_value.readline.return_value = "# -*- coding: utf-8-sig -*-"
    fin.return_value.read.return_value = code
    mock_open.return_value.__enter__ = fin

    prints = _get_prints("noprint", first)
    if code.startswith("print"):
        assert "Line:" in prints[0]
    else:
        assert len(prints) == 0
    mock_open.assert_called_with("origin", "r", encoding="utf-8-sig")
