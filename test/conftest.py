import os

import pytest


def pytest_configure():
    pytest.test_root = os.path.abspath(os.path.dirname(__file__))
