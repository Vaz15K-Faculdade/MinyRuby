grammar MiniRuby;

prog: (stmt NEWLINE*)* EOF;

stmt
    : simpleStmt NEWLINE*
    | ifStmt NEWLINE*
    | whileStmt NEWLINE*
    ;

simpleStmt
    : printStmt
    | assignStmt
    ;

printStmt: PUTS '('? exprList? ')'?;

assignStmt: ID '=' expr;

ifStmt: IF expr NEWLINE* stmt* elsePart? END;
elsePart: ELSE NEWLINE* stmt*;

whileStmt: WHILE expr DO? NEWLINE* stmt* END;

exprList: expr (',' expr)*;

expr: orExpr;

orExpr: andExpr (OR andExpr)*;
andExpr: eqExpr (AND eqExpr)*;
eqExpr: relExpr ((EQ | NEQ) relExpr)*;
relExpr: addExpr ((LT | LE | GT | GE) addExpr)*;
addExpr: mulExpr ((PLUS | MINUS) mulExpr)*;
mulExpr: unaryExpr ((MUL | DIV) mulExpr)*;

unaryExpr
    : NOT unaryExpr
    | factor
    ;

factor
    : NUMBER
    | STRING
    | GETS '('? ')'?
    | ID
    | '(' expr ')'
    ;

// Lexer Rules
PUTS: 'puts';
GETS: 'gets.chomp' | 'gets';
IF: 'if';
ELSE: 'else';
END: 'end';
WHILE: 'while';
DO: 'do';

OR: '||' | 'or';
AND: '&&' | 'and';
NOT: '!';
EQ: '==';
NEQ: '!=';
LT: '<';
LE: '<=';
GT: '>';
GE: '>=';
PLUS: '+';
MINUS: '-';
MUL: '*';
DIV: '/';

ID: [a-zA-Z_] [a-zA-Z_0-9]*;
NUMBER: [0-9]+ ('.' [0-9]+)?;
STRING: '"' (~["\r\n"])*? '"';
NEWLINE: '\r'? '\n';
WS: [ \t]+ -> skip;
LINE_COMMENT: '#' ~[\r\n]* -> skip;
