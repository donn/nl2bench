// antlr4 -Dlanguage=Python3 -no-listener -visitor logic.g4 -o _antlr4_logic_parser
grammar logic;

function:
	LPAREN function RPAREN
	| NOT function
	| function function
	| function AND function
	| function AND2 function
	| function XOR function
	| function OR function
	| function OR2 function
	| INPUT;

LPAREN: '(';
RPAREN: ')';
OR: '+';
OR2: '|';
XOR: '^';
NOT: '!';
AND: '&';
AND2: '*';
INPUT: [A-Za-z0-9_]+;
WHITESPACE: [ \n\t\r]+ -> skip;
