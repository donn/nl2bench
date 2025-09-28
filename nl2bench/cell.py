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
from immutabledict import immutabledict

from .lib_fn_parser import parse


def lib_group_as_dict(entry: LibertyAst) -> immutabledict:
    retval = {}
    if len(entry.args):
        retval["args"] = tuple(arg.strip('"') for arg in entry.args)
    for child in entry.children:
        if len(child.value):
            retval[child.id] = child.value.strip('"')
            continue
        if len(child.children):
            retval.setdefault(child.id, tuple())
            retval[child.id] = (*retval[child.id], lib_group_as_dict(child))
    return immutabledict(retval)


@dataclass(frozen=True)
class TestInfo:
    testing_ff: immutabledict
    sco: str
    sci: str
    sce: str


@dataclass(frozen=True)
class Cell:
    inputs: List[str]
    outputs: Dict[str, Optional[tuple]]
    inouts: List[str]
    register_info: Optional[Tuple[str, immutabledict]]
    test_info: Optional[TestInfo]
    raw: immutabledict

    @staticmethod
    def _from_ast(cell_ast) -> "Cell":
        raw = lib_group_as_dict(cell_ast)
        cell_args = raw["args"]
        name = cell_args[0]

        inputs = []
        outputs = {}
        inouts = []
        register_info = None
        test_info = None
        for id, info in raw.items():
            if id in ["ff", "latch"]:
                register_info = (id, info)
        if test_cell_info := raw.get("test_cell"):
            test_info_dict = {}

            assert len(test_cell_info) == 1
            test_cell_info = test_cell_info[0]

            ff_info = test_cell_info.get("ff")
            assert len(ff_info) == 1
            ff_info = ff_info[0]
            test_info_dict["testing_ff"] = ff_info

            for pin in test_cell_info["pin"]:
                pin_name = pin["args"][0]
                if sigtype := pin.get("signal_type"):
                    if sigtype == "test_scan_out":
                        test_info_dict["sco"] = pin_name
                    elif sigtype == "test_scan_in":
                        test_info_dict["sci"] = pin_name
                    elif sigtype == "test_scan_enable":
                        test_info_dict["sce"] = pin_name
            test_info = TestInfo(**test_info_dict)
        if pin_info := raw.get("pin"):
            for pin in pin_info:
                pin_args = pin["args"]
                pin_name = pin_args[0]
                function = None
                direction = None
                for pin_element_id, pin_element in pin.items():
                    if pin_element_id == "direction":
                        direction = pin_element
                    if pin_element_id == "function":
                        function = pin_element

                if direction == "input":
                    inputs.append(pin_name)
                elif direction == "output":
                    if fn := function:
                        outputs[pin_name] = parse(fn)
                    else:
                        outputs[pin_name] = None
                else:
                    inouts.append(pin_name)

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
