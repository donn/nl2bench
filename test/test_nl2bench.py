import os
import pytest
from nl2bench.__main__ import cli


@pytest.mark.parametrize(
    ("lib", "netlist"),
    [
        ("test.lib", "test.v"),
        ("test.lib", "test2.v"),
    ],
)
def testy_basic(lib, netlist):
    with pytest.raises(SystemExit, match="0"):
        cli(
            [
                "--lib-file",
                os.path.join(pytest.test_root, "designs", lib),
                os.path.join(pytest.test_root, "designs", netlist),
            ]
        )
