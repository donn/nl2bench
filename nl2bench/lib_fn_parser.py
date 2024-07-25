from antlr4 import InputStream, CommonTokenStream

from nl2bench._antlr4_logic_parser.logicListener import logicListener
from nl2bench._antlr4_logic_parser.logicParser import logicParser
from nl2bench._antlr4_logic_parser.logicVisitor import logicVisitor
from nl2bench._antlr4_logic_parser.logicLexer import logicLexer


class _Listener(logicListener):
    def syntaxError(*args, **kwargs):
        raise Exception(f"{args} {kwargs}")


class _Visitor(logicVisitor):
    def visitFunction(self, ctx: logicParser.FunctionContext):
        children = [str(c) for c in ctx.children]
        if len(ctx.children) == 1:  # name
            return children[0]
        if children[0] == "(":
            return self.visit(ctx.children[1])
        if children[0] == "!":
            return ("!", self.visit(ctx.children[1]))
        if len(children) == 2:
            # guaranteed to be and at this point
            return ("&", self.visit(ctx.children[0]), self.visit(ctx.children[1]))
        # guaranteed to be xor or or
        return (children[1], self.visit(ctx.children[0]), self.visit(ctx.children[2]))


def parse(function: str):
    listener = _Listener()

    stream = InputStream(function)

    lexer = logicLexer(stream)
    lexer.addErrorListener(listener)
    token_stream = CommonTokenStream(lexer)
    token_stream.fill()
    parser = logicParser(token_stream)
    parser.addErrorListener(listener)

    tree = parser.function()

    return _Visitor().visit(tree)
