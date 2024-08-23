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
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker, ParserRuleContext

from _nl2bench_antlr4_verilog.VerilogParserListener import VerilogParserListener
from _nl2bench_antlr4_verilog.VerilogParser import VerilogParser
from _nl2bench_antlr4_verilog.VerilogLexer import VerilogLexer


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


class _Listener(VerilogParserListener):
    def syntaxError(*args, **kwargs):
        raise Exception(f"{args} {kwargs}")

    def getText(self, of: ParserRuleContext):
        try:
            token_source = of.start.getTokenSource()
            input_stream = token_source.inputStream
            start, stop = of.start.start, of.stop.stop
            return input_stream.getText(start, stop)
        except AttributeError:
            return ""

    def enterModule_declaration(self, ctx: VerilogParser.Module_declarationContext):
        self.netlist = Netlist()
        self.netlist.module = self.getText(ctx.children[1])
        return super().enterModule_declaration(ctx)

    def enterList_of_port_declarations(
        self, ctx: VerilogParser.List_of_port_declarationsContext
    ):
        for port in ctx.port():
            name = self.getText(port)
            self.netlist.ports[name] = Port(name=name)
        return super().enterList_of_port_declarations(ctx)

    def ranged_declaration(self, dir, ctx):
        frm, to = None, None
        if range := ctx.range_():
            frm = int(self.getText(range.msb_constant_expression()))
            to = int(self.getText(range.lsb_constant_expression()))

        for child in ctx.list_of_port_identifiers().children:
            name = self.getText(child)
            self.netlist.ports[name] = self.netlist.ports[name] or Port(name=name)
            self.netlist.ports[name].direction = dir
            self.netlist.ports[name].msb = frm
            self.netlist.ports[name].lsb = to

    def enterInput_declaration(self, ctx: VerilogParser.Input_declarationContext):
        self.ranged_declaration("input", ctx)
        return super().enterInput_declaration(ctx)

    def enterOutput_declaration(self, ctx: VerilogParser.Output_declarationContext):
        self.ranged_declaration("output", ctx)
        return super().enterOutput_declaration(ctx)

    def enterModule_instantiation(self, ctx: VerilogParser.Module_instantiationContext):
        for instance in ctx.module_instance():
            obj = Instance(
                name=self.getText(instance.name_of_module_instance()),
                kind=self.getText(ctx.module_identifier()),
            )

            for hook in instance.list_of_port_connections().named_port_connection():
                port = self.getText(hook.port_identifier())
                expression = self.getText(hook.expression())
                obj.io[port] = expression

            self.netlist.instances.append(obj)
        return super().enterModule_instantiation(ctx)

    def enterNet_assignment(self, ctx: VerilogParser.Net_assignmentContext):
        lvalue = self.getText(ctx.net_lvalue())
        expr = self.getText(ctx.expression())
        self.netlist.assignments.append((lvalue, expr))
        return super().enterNet_assignment(ctx)


def parse(verilog_netlist: str):
    listener = _Listener()

    stream = InputStream(verilog_netlist)

    lexer = VerilogLexer(stream)
    lexer.addErrorListener(listener)
    token_stream = CommonTokenStream(lexer)
    token_stream.fill()
    parser = VerilogParser(token_stream)
    parser.addErrorListener(listener)

    tree = parser.module_declaration()

    ParseTreeWalker.DEFAULT.walk(listener, tree)

    return listener.netlist
