"""
Module with tests for noprint.print_seeker
"""
from unittest import mock

import pytest

from noprint.logger import log


@pytest.mark.parametrize("err", [True, False])
@mock.patch("noprint.logger.logger.error")
@mock.patch("noprint.logger.logger.warning")
def test_log(mock_warning, mock_error, err):
    """Function for testing _log method"""
    log("testmsg", err)
    if err:
        mock_error.assert_called_once()
    else:
        mock_warning.assert_called_once()
