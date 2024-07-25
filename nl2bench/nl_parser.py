from typing import List, Dict, Tuple
from dataclasses import dataclass, field

from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker, ParserRuleContext

from nl2bench._antlr4_verilog_parser.VerilogParserListener import VerilogParserListener
from nl2bench._antlr4_verilog_parser.VerilogParser import VerilogParser
from nl2bench._antlr4_verilog_parser.VerilogLexer import VerilogLexer


@dataclass
class Instance:
    name: str
    kind: str
    io: Dict[str, str] = field(default_factory=lambda: {})


@dataclass
class Netlist:
    module: str = ""
    inputs: List[str] = field(default_factory=lambda: [])
    outputs: List[str] = field(default_factory=lambda: [])
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

    def ranged_declaration(self, ref, ctx):
        frm, to = None, None
        if range := ctx.range_():
            frm = int(self.getText(range.msb_constant_expression()))
            to = int(self.getText(range.lsb_constant_expression()))
            frm, to = min(frm, to), max(frm, to)

        for child in ctx.list_of_port_identifiers().children:
            name = self.getText(child)
            if frm is not None:
                i = frm
                while i <= to:
                    ref.append(f"{name}[{i}]")
                    i += 1
            else:
                ref.append(name)

    def enterInput_declaration(self, ctx: VerilogParser.Input_declarationContext):
        self.ranged_declaration(self.netlist.inputs, ctx)
        return super().enterInput_declaration(ctx)

    def enterOutput_declaration(self, ctx: VerilogParser.Output_declarationContext):
        self.ranged_declaration(self.netlist.outputs, ctx)
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
