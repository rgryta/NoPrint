"""Pytest fixtures"""
from unittest import mock

import pytest

from noprint.module import Module


@pytest.fixture
def mock_module():
    """Mock a module for testing"""

    class MockModule(Module):
        """Module mock class for testing"""

        def __init__(self):
            with mock.patch("noprint.module._find_parent_dir", return_value="/root"):
                super().__init__("test.subpackage")

    return MockModule
