import os
import pytest
from nl2bench import cli


@pytest.mark.parametrize(
    ("lib", "netlist"),
    [
        ("osu035_stdcells.lib", "osu035_nl1.v"),
        ("osu035_stdcells.lib", "osu035_nl2.v"),
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
