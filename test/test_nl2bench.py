import os
import pytest
import subprocess
from tempfile import NamedTemporaryFile
from nl2bench.nl2bench import verilog_netlist_to_bench


@pytest.mark.parametrize(
    ("scl", "design"),
    [
        ("osu035", "s298"),
        ("osu035", "spm"),
    ],
)
def testy_basic(
    scl,
    design,
):
    netlist = os.path.join(pytest.test_root, "designs", design, scl, "nl.v")
    lib = os.path.join(pytest.test_root, "tech", f"{scl}.lib")
    expected = os.path.join(pytest.test_root, "designs", design, scl, "nl.bench")
    with NamedTemporaryFile("w", suffix=".bench") as f:
        verilog_netlist_to_bench(netlist, [lib], f)
        f.flush()
        subprocess.check_call(["quaigh", "equiv", expected, f.name])
