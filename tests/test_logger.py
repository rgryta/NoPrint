"""
Module with tests for noprint.logger
"""
import logging

from unittest import mock

import pytest

import noprint.logger


@pytest.mark.parametrize(
    "lvl", [logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
)
@mock.patch("noprint.logger.logger.info")
@mock.patch("noprint.logger.logger.warning")
@mock.patch("noprint.logger.logger.error")
@mock.patch("noprint.logger.logger.critical")
def test_log(mock_c, mock_e, mock_w, mock_i, lvl):
    """Function for testing _log method"""
    noprint.logger.log("testmsg", lvl)
    if lvl == logging.CRITICAL:
        mock_c.assert_called_once()
    elif lvl == logging.ERROR:
        mock_e.assert_called_once()
    elif lvl == logging.WARNING:
        mock_w.assert_called_once()
    elif lvl == logging.INFO:
        mock_i.assert_called_once()
