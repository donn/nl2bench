# Copyright 2024 Mohamed Gaber

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from libparse import LibertyParser, LibertyAst
import frozendict

from .lib_fn_parser import parse


def lib_group_as_dict(entry) -> dict:
    retval = {
        "args": tuple(entry.args),
    }
    for child in entry.children:
        value = child.value
        if isinstance(value, LibertyAst):
            value = lib_group_as_dict(value)
        retval[child.id] = child.value
    return retval


@dataclass(frozen=True)
class TestInfo:
    testing_ff: frozendict.frozendict
    sco: str
    sci: str
    sce: str


@dataclass
class Cell:
    inputs: List[str]
    outputs: Dict[str, Optional[tuple]]
    inouts: List[str]
    register_info: Optional[Tuple[str, frozendict.frozendict]]
    test_info: Optional[TestInfo]
    raw: frozendict.frozendict

    @staticmethod
    def _from_ast(cell_ast) -> "Cell":
        name = cell_ast.args[0]
        raw = lib_group_as_dict(cell_ast)

        inputs = []
        outputs = {}
        inouts = []
        register_info = None
        test_info = None
        for cell_element in cell_ast.children:
            if cell_element.id in ["ff", "latch"]:
                register_info = (
                    cell_element.id,
                    frozendict.deepfreeze(lib_group_as_dict(cell_element)),
                )
        for cell_element in cell_ast.children:
            if cell_element.id == "test_cell":
                test_info_dict = {}
                for test_element in cell_element.children:
                    if test_element.id == "ff":
                        test_info_dict["testing_ff"] = frozendict.deepfreeze(
                            lib_group_as_dict(test_element)
                        )
                    elif test_element.id == "pin":
                        pin_info = lib_group_as_dict(test_element)
                        pin_name = test_element.args[0]
                        if sigtype := pin_info.get("signal_type"):
                            if sigtype == "test_scan_out":
                                test_info_dict["sco"] = pin_name
                            elif sigtype == "test_scan_in":
                                test_info_dict["sci"] = pin_name
                            elif sigtype == "test_scan_enable":
                                test_info_dict["sce"] = pin_name
                test_info = TestInfo(**test_info_dict)
            if cell_element.id == "pin":
                function = None
                direction = None
                for pin_element in cell_element.children:
                    if pin_element.id == "direction":
                        direction = pin_element.value
                    if pin_element.id == "function":
                        function = pin_element.value

                if direction == "input":
                    inputs.append(cell_element.args[0])
                elif direction == "output":
                    if fn := function:
                        outputs[cell_element.args[0]] = parse(fn)
                    else:
                        outputs[cell_element.args[0]] = None
                else:
                    inouts.append(cell_element.args)

        return name, Cell(inputs, outputs, inouts, register_info, test_info, raw)

    @staticmethod
    def from_lib_file(path: str) -> Dict[str, "Cell"]:
        cells: Dict[str, Cell] = {}

        parser = LibertyParser(open(path))
        ast = parser.ast
        cells: Dict[str, Cell] = {}
        for entry in ast.children:
            if entry.id == "cell":
                name, cell = Cell._from_ast(entry)
                cells[name] = cell
        return cells
