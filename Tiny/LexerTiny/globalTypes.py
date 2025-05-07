from enum import Enum

# TokenType


class TokenType(Enum):
    ENDFILE = 300
    ERROR = 301
    # reserved words
    IF = 'if'
    THEN = 'then'
    ELSE = 'else'
    END = 'end'
    REPEAT = 'repeat'
    UNTIL = 'until'
    READ = 'read'
    WRITE = 'write'
    # multicharacter tokens
    ID = 310
    NUM = 311
    # special symbols
    ASSIGN = ':='
    EQ = '='
    LT = '<'
    PLUS = '+'
    MINUS = '-'
    TIMES = '*'
    OVER = '/'
    LPAREN = '('
    RPAREN = ')'
    SEMI = ';'


# StateType
class StateType(Enum):
    START = 0
    INASSIGN = 1
    INCOMMENT = 2
    INNUM = 3
    INID = 4
    DONE = 5

# ReservedWords


class ReservedWords(Enum):
    IF = 'if'
    THEN = 'then'
    ELSE = 'else'
    END = 'end'
    REPEAT = 'repeat'
    UNTIL = 'until'
    READ = 'read'
    WRITE = 'write'

# ***********   Syntax tree for parsing ************
