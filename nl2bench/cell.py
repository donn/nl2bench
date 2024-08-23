import sys
from dataclasses import dataclass
from typing import Dict, List

from libparse import LibertyParser

from .lib_fn_parser import parse


@dataclass
class Cell:
    inputs: List[str]
    outputs: Dict[str, tuple]

    @staticmethod
    def from_lib_file(path: str) -> Dict[str, "Cell"]:
        cells: Dict[str, Cell] = {}

        parser = LibertyParser(open(path))
        ast = parser.ast
        cells: Dict[str, Cell] = {}
        for entry in ast.children:
            if entry.id == "cell":
                inputs = []
                outputs = {}
                withhold = None
                for cell_element in entry.children:
                    if cell_element.id in ["ff", "latch"]:
                        withhold = cell_element.id
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
                            if function is None:
                                withhold = "no function"
                            else:
                                outputs[cell_element.args[0]] = parse(function)
                        else:
                            withhold = "tri-state"
                if withhold is not None:
                    print(
                        f"⚠️ Skipping {withhold} cell {entry.args[0]}.",
                        file=sys.stderr,
                    )
                else:
                    cells[entry.args[0]] = Cell(inputs, outputs)
        return cells
