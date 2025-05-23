import os
import pytest
from nl2bench.cell import Cell


@pytest.mark.parametrize(
    "scl",
    [
        "osu035",
        "sky130_fd_sc_hd" "ihp-sg13g2",
    ],
)
def test_cell_parse(scl):
    lib = os.path.join(pytest.test_root, "tech", f"{scl}.lib")
    cells = Cell.from_lib_file(lib)
    assert len(list(cells.keys())) != 0, "Failed to parse scl lib file"
