"""
Module with unit tests for noprint.cli
"""
from unittest import mock

import pytest

import noprint.cli

from noprint.exceptions import ImportException


@pytest.mark.parametrize(
    "detected",
    [
        ([("x", False), ("x", False)], []),
        ([("x", False), ("x", True)], []),
        ([("1", False)], []),
        ([("1", True)], []),
        ([("x", False), ("x", False)], [ImportException("X")]),
        ([("x", False), ("x", True)], [ImportException("X")]),
        ([("1", False)], [ImportException("X")]),
        ([("1", True)], [ImportException("X")]),
    ],
)
@pytest.mark.parametrize("as_error", [0, 1])
@pytest.mark.parametrize("verbosity", [0, 1, 2])
@mock.patch("noprint.cli.detect_prints")
@mock.patch("noprint.cli.logging")
def test_cli(
    mock_log, mock_detect, verbosity, as_error, detected
):  # pylint: disable=unused-argument
    """Function for testing cli method"""
    mock_detect.return_value = detected

    args = ["noprint", "noprint", "test"]
    if as_error:
        args.append("-e")
    for _ in range(verbosity):
        args.append("-v")

    with mock.patch("sys.argv", args), pytest.raises(SystemExit) as syse:
        noprint.cli.cli()
    assert syse.type == SystemExit
    if any(isinstance(errors, ImportException) for errors in detected[1]):
        assert syse.value.code == 2
    else:
        found_prints = any(found for _, found in detected[0])
        assert bool(syse.value.code) is bool(as_error and found_prints)
