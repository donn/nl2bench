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
from antlr4 import InputStream, CommonTokenStream

from _nl2bench_antlr4_liblogic.logicListener import logicListener
from _nl2bench_antlr4_liblogic.logicParser import logicParser
from _nl2bench_antlr4_liblogic.logicVisitor import logicVisitor
from _nl2bench_antlr4_liblogic.logicLexer import logicLexer


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
        operator = children[1]
        if operator == "|":
            operator = "+"
        return (operator, self.visit(ctx.children[0]), self.visit(ctx.children[2]))


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
