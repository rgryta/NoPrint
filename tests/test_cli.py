"""
Module with unit tests for noprint.cli
"""
from unittest import mock

import pytest

import noprint.cli

from noprint.exceptions import ImportException


@pytest.mark.parametrize("detected", [[[], []], [[1], [2]], [[1], ImportException()]])
@pytest.mark.parametrize("as_error", [0, 1])
@mock.patch("noprint.cli.detect_prints")
@mock.patch("noprint.cli.logging")
def test_cli(
    mock_log, mock_detect, as_error, detected
):  # pylint: disable=unused-argument
    """Function for testing cli method"""
    mock_detect.side_effect = detected

    args = ["noprint", "noprint", "test"]
    if as_error:
        args.append("-e")

    with mock.patch("sys.argv", args), pytest.raises(SystemExit) as syse:
        noprint.cli.cli()
    assert syse.type == SystemExit
    if any(isinstance(prints, ImportException) for prints in detected):
        assert syse.value.code == 2
    else:
        found_prints = len([y for x in detected for y in x])
        assert bool(syse.value.code) is bool(as_error and found_prints)
