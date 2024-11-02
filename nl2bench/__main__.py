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
from pathlib import Path
from typing import Iterable

import click

from .nl2bench import verilog_netlist_to_bench


@click.command()
@click.option(
    "-o", "--output", default=None, help="If not set, replacing .v with .bench"
)
@click.option(
    "-l",
    "--lib-file",
    "lib_files",
    multiple=True,
    type=click.Path(file_okay=True, exists=True),
)
@click.option(
    "-b",
    "--bypassing",
    "bypassed_ports",
    multiple=True,
    type=str,
)
@click.argument(
    "netlist_in",
    type=click.Path(file_okay=True, exists=True),
)
def cli(
    output: str,
    netlist_in: str,
    bypassed_ports: Iterable[str],
    lib_files: Iterable[str],
):
    if output is None:
        output = netlist_in
        if output.endswith(".v"):
            output = output[:-2]
        output = f"{output}.bench"
    with open(output, "w", encoding="utf8") as f:
        verilog_netlist_to_bench(
            Path(netlist_in), lib_files, f, bypass_ios=set(bypassed_ports)
        )
    print(f"Successfully saved to {output}.")


if __name__ == "__main__":
    cli()
