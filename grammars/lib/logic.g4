// antlr4 -Dlanguage=Python3 -no-listener -visitor logic.g4 -o _antlr4_logic_parser
grammar logic;

function:
	LPAREN function RPAREN
	| NOT function
	| function function
	| function XOR function
	| function OR function
	| INPUT;

LPAREN: '(';
RPAREN: ')';
OR: '+';
XOR: '^';
NOT: '!';
INPUT: [A-Za-z0-9]+;
WHITESPACE: [ \n\t\r]+ -> skip;
