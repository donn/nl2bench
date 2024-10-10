import os
import pytest
import subprocess
from tempfile import NamedTemporaryFile
from nl2bench.nl2bench import verilog_netlist_to_bench
import gzip


@pytest.mark.parametrize(
    ("scl", "design"),
    [
        ("osu035", "s298"),
        ("osu035", "spm"),
        ("osu035", "aes128"),
    ],
)
def testy_basic(
    scl,
    design,
):
    netlist = os.path.join(pytest.test_root, "designs", design, scl, "nl.v.gz")
    lib = os.path.join(pytest.test_root, "tech", f"{scl}.lib")
    expected = os.path.join(pytest.test_root, "designs", design, scl, "nl.bench.gz")
    with NamedTemporaryFile("w", suffix=".bench") as f, NamedTemporaryFile(
        "wb", suffix=".expected.bench"
    ) as expected_x, gzip.open(expected, "rb") as expected_c:
        expected_x.write(expected_c.read())

        verilog_netlist_to_bench(netlist, [lib], f)
        f.flush()
        subprocess.check_call(["quaigh", "equiv", expected_x.name, f.name])
