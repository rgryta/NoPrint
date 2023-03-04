"""
Module with unit tests for noprint.cli
"""
from unittest import mock

from click.testing import CliRunner
import pytest

from noprint.cli import _log, cli


@pytest.mark.parametrize("err", [True, False])
@mock.patch("noprint.cli.click.secho")
@mock.patch("noprint.cli.click.decorators.get_current_context")
def test__log(mock_click_ctx, mock_secho, err):
    """Function for testing _log method"""
    ctx = mock.Mock()
    ctx.params = {"as_error": err}
    mock_click_ctx.return_value = ctx

    msg = "test"
    colour = "red" if err else "yellow"
    _log(msg)
    mock_secho.assert_called_with(msg, fg=colour)


@pytest.mark.parametrize("detected", [[], [1, 2, 3]])
@pytest.mark.parametrize("as_error", [0, 1])
@mock.patch("noprint.cli.detect_prints")
@mock.patch("noprint.cli._log")
def test_cli(
    mock_log, mock_detect, as_error, detected
):  # pylint: disable=unused-argument
    """Function for testing cli method"""
    mock_detect.return_value = detected

    runner = CliRunner()
    params = ["noprint", "test"]
    if as_error:
        params.append("-e")
    result = runner.invoke(cli, params)
    assert bool(result.exit_code) is bool(as_error and detected)
