import os
import functools
from io import TextIOWrapper
from typing import Iterable, Dict

import click

from . import nl_parser
from .cell import Cell


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

    if isinstance(current_function, str):
        print(
            f"{current_output} = BUF({handle_argument(current_function)})",
            file=f,
        )
    elif current_function[0] == "!":
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
        raise ValueError(
            f"Unknown lib function {current_function} of type {type(current_function)} in {inst}."
        )


def to_bench_ios(port: nl_parser.Port, f: TextIOWrapper):
    if port.msb is None:
        print(f"{port.direction.upper()}({n(port.name)})", file=f)
    else:
        frm, to = min(port.msb, port.lsb), max(port.lsb, port.msb)
        i = frm
        while i <= to:
            print(f"{port.direction.upper()}({n(port.name)}[{i}])", file=f)
            i += 1


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
        for port in netlist.ports.values():
            to_bench_ios(port, f)
        for inst in netlist.instances:
            assert (
                inst.kind in cells
            ), f"Unknown cell {inst.kind}- are you sure the design is combinational?"
            base = cells[inst.kind]
            to_bench_statements(inst, base, f)
        for asst in netlist.assignments:
            print(f"{n(asst[0])} = BUF({n(asst[1])})", file=f)


if __name__ == "__main__":
    cli()
