"""
Module with unit tests for noprint.cli
"""
from unittest import mock

import pytest

import noprint.cli


@pytest.mark.parametrize("detected", [0, 1, 2])
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
    if detected == 2:
        assert syse.value.code == 2
    else:
        assert bool(syse.value.code) is bool(as_error and detected)
