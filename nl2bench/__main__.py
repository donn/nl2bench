import os
import sys
import functools
from io import TextIOWrapper
from dataclasses import dataclass
from typing import Iterable, Dict, List

import click
from libparse import LibertyParser

from . import lib_fn_parser
from . import nl_parser


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
                            outputs[cell_element.args[0]] = lib_fn_parser.parse(
                                function
                            )
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


def n(identifier):
    if identifier.startswith("\\") and identifier.endswith(" "):
        identifier = identifier[1:-1]
    return identifier


def transform_function_rec(
    current_output: str,
    current_function,
    inst: nl_parser.Instance,
    f: TextIOWrapper,
    depth=0,
):
    counter = 0
    current_output = n(current_output)

    def handle_argument(arg):
        nonlocal counter
        if isinstance(arg, tuple):
            intermediate = f"{inst.name}.{depth}.{counter}"
            counter += 1
            transform_function_rec(intermediate, arg, inst, f, depth + 1)
            return intermediate
        else:
            assert arg in inst.io, "Unrecognized input port "
            return n(inst.io[arg])

    if current_function[0] == "!":
        print(f"{current_output} = NOT({handle_argument(current_function[1])})", file=f)
    elif current_function[0] == "&":
        print(
            f"{current_output} = AND({handle_argument(current_function[1])} , {handle_argument(current_function[2])})",
            file=f,
        )
    elif current_function[0] == "^":
        print(
            f"{current_output} = XOR({handle_argument(current_function[1])} , {handle_argument(current_function[2])})",
            file=f,
        )
    elif current_function[0] == "+":
        print(
            f"{current_output} = OR({handle_argument(current_function[1])} , {handle_argument(current_function[2])})",
            file=f,
        )
    else:
        raise ValueError(f"Unknown lib function {current_function[0]}.")


def to_bench_statements(inst: nl_parser.Instance, base: Cell, f: TextIOWrapper):
    for output, function in base.outputs.items():
        output_hooked_to = inst.io[output]
        transform_function_rec(output_hooked_to, function, inst, f)


@click.command()
@click.option(
    "-o",
    "--output",
    default="/dev/stdout" if os.name == "posix" else None,
    required=True,
)
@click.option(
    "-l",
    "--lib-file",
    "lib_files",
    multiple=True,
    type=click.Path(file_okay=True, exists=True),
)
@click.argument(
    "netlist_in",
    type=click.Path(file_okay=True, exists=True),
)
def cli(
    output: str,
    netlist_in: str,
    lib_files: Iterable[str],
):
    cells: Dict[str, Cell] = functools.reduce(
        lambda acc, path: acc.update(Cell.from_lib_file(path)) or acc,
        lib_files,
        {},
    )

    netlist = nl_parser.parse(open(netlist_in).read())
    with open(output, "w", encoding="utf8") as f:
        print("# Automatically generated. Do not modify.", file=f)
        for input in netlist.inputs:
            print(f"INPUT({n(input)})", file=f)
        for inst in netlist.instances:
            assert (
                inst.kind in cells
            ), f"Unknown cell {inst.kind}- are you sure the design is combinational?"
            base = cells[inst.kind]
            to_bench_statements(inst, base, f)
        for asst in netlist.assignments:
            print(f"{n(asst[0])} = BUFF({n(asst[1])})", file=f)
        for output in netlist.outputs:
            print(f"OUTPUT({n(output)})", file=f)


if __name__ == "__main__":
    cli()
