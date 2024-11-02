# Copyright 2024 Mohamed Gaber, Efabless Corporation

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Code partially adapted from Verilog Backend of:
#
# yosys -- Yosys Open SYnthesis Suite
#
# Copyright (C) 2012  Claire Xenia Wolf <claire@yosyshq.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from pathlib import Path
import shlex
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


from pyosys import libyosys as ys


@dataclass
class Instance:
    name: str
    kind: str
    io: Dict[str, str] = field(default_factory=lambda: {})


@dataclass
class Port:
    name: str
    direction: str = "Unknown"
    msb: Optional[int] = None
    lsb: Optional[int] = None


@dataclass
class Netlist:
    module: str = ""
    ports: Dict[str, Port] = field(default_factory=lambda: {})
    instances: List[Instance] = field(default_factory=lambda: [])
    assignments: List[Tuple[str, str]] = field(default_factory=lambda: [])


def _clean_str(id: ys.IdString):
    string_id = id.str()
    if string_id.startswith("\\"):
        string_id = string_id[1:]
    return string_id


def _dump_sigchunk(chunk: ys.SigChunk):
    assert chunk.wire, "constants not supported"
    assert chunk.width == 1, "splitnets did not split this mf net"
    wire_name = _clean_str(chunk.wire.name)
    if chunk.width == chunk.wire.width:
        return wire_name
    else:
        if chunk.wire.upto:
            return f"{wire_name}[{chunk.wire.width - (chunk.offset - 1) + chunk.wire.start_offset}]"
        else:
            return f"{wire_name}[{chunk.offset + chunk.wire.start_offset}]"


def _dump_sigbit(bit: ys.SigBit):
    if bit.is_wire():
        if bit.wire.width == 1:
            return _clean_str(bit.wire.name)
        else:
            return f"{_clean_str(bit.wire.name)}[{bit.offset}]"
    else:
        if bit.data == ys.State.S1:
            return 1
        elif bit.data == ys.State.S0:
            return 0
        else:
            assert "unknown constants not supported"


def parse(verilog_netlist: Path):
    d = ys.Design()
    ys.run_pass(f"read_verilog {shlex.quote(str(verilog_netlist))}", d)
    ys.run_pass("hierarchy -auto-top")
    ys.run_pass("flatten")
    ys.run_pass("splitnets")

    ys_module = d.top_module()

    ports: Dict[str, Port] = {
        # just to keep declaration order
        _clean_str(port): Port(name=_clean_str(port))
        for port in ys_module.ports
    }

    for wire_idstr in ys_module.wires_:
        wire = ys_module.wire(wire_idstr)
        if wire.port_id == 0:
            continue
        port_name = _clean_str(wire.name)

        msb = None
        lsb = None
        upto = wire.upto == 1
        offset = wire.start_offset
        width = wire.width
        if width > 1:
            msb = offset + width - 1
            lsb = offset
            if upto:
                msb, lsb = lsb, msb
        ports[port_name] = Port(
            port_name,
            "input" if wire.port_input else "output",
            msb,
            lsb,
        )

    assignments: List[Tuple[str, str]] = []
    for conn_from, conn_to in ys_module.connections():
        for bit_from, bit_to in zip(conn_from.bits(), conn_to.bits()):
            assignments.append((_dump_sigbit(bit_from), _dump_sigbit(bit_to)))

    instances: List[Instance] = []
    for cell_idstr in ys_module.cells_:
        cell = ys_module.cell(cell_idstr)
        instance_io = {}
        for port_idstr, spec in cell.connections().items():
            instance_io[_clean_str(port_idstr)] = _dump_sigchunk(spec.as_chunk())
        cell_name = _clean_str(cell.name)
        cell_type = _clean_str(cell.type)
        instances.append(Instance(cell_name, cell_type, instance_io))

    return Netlist(_clean_str(ys_module.name), ports, instances, assignments)
