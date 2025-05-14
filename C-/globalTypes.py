''' Gabriel Rodriguez De Los Reyes - A01027384 '''

from enum import Enum


class TokenType(Enum):
    PROGRAM = 99
    ENDFILE = 0
    ENTERO = 4
    REAL = 5
    SUMA = 6
    RESTA = 7
    ERROR = 8
    ID = 10
    MULT = 11
    DIV = 12
    MAYOR = 13
    MENOR = 14
    MAYORI = 15
    MENORI = 16
    IGUAL = 17
    NIGUAL = 18
    ASIGNAR = 19
    SEMICOLON = 20
    COMA = 21
    POPEN = 22
    PCLOSE = 23
    BOPEN = 24
    BCLOSE = 25
    LLOPEN = 26
    LLCLOSE = 27
    INT = 28
    ELSE = 29
    IF = 30
    VOID = 31
    RETURN = 32
    WHILE = 33
    FUNCTION = 34
    VARIABLE = 35
    PARAMS = 36
    POSITION = 37


class CharMap(Enum):
    DIGITS = '0123456789'
    PLUS = '+'
    MINUS = '-'
    MULT = '*'
    DIV = '/'
    GREATER = '>'
    LESS = '<'
    EQUAL = '='
    EXCLAMATION = '!'
    SEMICOLON = ';'
    COMA = ','
    LPAREN = '('
    RPAREN = ')'
    LBRACE = '{'
    RBRACE = '}'
    LBRACKET = '['
    RBRACKET = ']'
    DOT = '.'
    # letters and underscore
    LETTERS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_'
    WHITESPACE = ' \t\n$'
    OTHER = ''


resreved_words = {
    "int": TokenType.INT,
    "else": TokenType.ELSE,
    "if": TokenType.IF,
    "void": TokenType.VOID,
    "return": TokenType.RETURN,
    "while": TokenType.WHILE
}

char_map = {
    0: CharMap.DIGITS.value,
    1: CharMap.PLUS.value,
    2: CharMap.MINUS.value,
    3: CharMap.MULT.value,
    4: CharMap.DIV.value,
    5: CharMap.GREATER.value,
    6: CharMap.LESS.value,
    7: CharMap.EQUAL.value,
    8: CharMap.EXCLAMATION.value,
    9: CharMap.SEMICOLON.value,
    10: CharMap.COMA.value,
    11: CharMap.LPAREN.value,
    12: CharMap.RPAREN.value,
    13: CharMap.LBRACE.value,
    14: CharMap.RBRACE.value,
    15: CharMap.LBRACKET.value,
    16: CharMap.RBRACKET.value,
    17: CharMap.DOT.value,
    18: CharMap.LETTERS.value,
    19: CharMap.WHITESPACE.value,
    20: CharMap.OTHER.value
}

# Estaos que se regresan
rewind_states = {4, 5, 10, 19}

final_states = {
    4:  TokenType.ENTERO,       # Digitos
    5:  TokenType.REAL,         # Digitos.Digitos
    6:  TokenType.SUMA,         # +
    7:  TokenType.RESTA,        # -
    8:  TokenType.ERROR,        # ERROR
    10: TokenType.ID,          # ID (Palabras reservadas)
    11: TokenType.MULT,        # *
    12: TokenType.DIV,         # /
    13: TokenType.MAYOR,       # >
    14: TokenType.MENOR,       # <
    15: TokenType.MAYORI,      # >=
    16: TokenType.MENORI,      # <=
    17: TokenType.IGUAL,       # ==
    18: TokenType.NIGUAL,      # !=
    19: TokenType.ASIGNAR,     # =
    20: TokenType.SEMICOLON,   # ;
    21: TokenType.COMA,        # ,
    22: TokenType.POPEN,       # (
    23: TokenType.PCLOSE,      # )
    24: TokenType.LLOPEN,       # {
    25: TokenType.LLCLOSE,      # }
    26: TokenType.BOPEN,      # [
    27: TokenType.BCLOSE,     # ]
}

comparison_operators = [
    TokenType.MAYOR,    # >
    TokenType.MENOR,    #
    TokenType.MAYORI,   # >=
    TokenType.MENORI,   # <=
    TokenType.IGUAL,    # ==
    TokenType.NIGUAL    # !=
]

operation_operators = [
    TokenType.SUMA,     # +
    TokenType.RESTA,    # -
    TokenType.MULT,     # *
    TokenType.DIV,      # /
    TokenType.ASIGNAR   # =
]

# -------- Parser -------------


class NodeKind(Enum):
    StmtK = 0
    ExpK = 1


class StmtKind(Enum):
    IfK = 0
    RepeatK = 1
    AssignK = 2
    ReadK = 3
    WriteK = 4


class ExpKind(Enum):
    OpK = 0
    ConstK = 1
    IdK = 2

# ExpType is used for type checking


class ExpType(Enum):
    void = 0
    int = 1
    arr = 2
    error = 3


class VarType():
    def __init__(self, name, size=None, param=False):
        self.type = name
        self.size = size
        self.params = param


class TreeNode:
    def __init__(self, type=None, token=TokenType, lexema=None, child=None, line=None, column=None):
        # Use None as default and create a new list in the method body
        self.child = [] if child is None else child  # Each instance gets its own list
        self.type = type
        self.token = token
        self.lexema = lexema   # tipo NodeKind, en globalTypes
        self.line = line
        self.column = column
        self.parent = None


class ErrorNode:
    def __init__(self, lexema, line=None, column=None, errorMessage=None):
        self.lexema = lexema
        self.line = line
        self.column = column
        self.token = TokenType.ERROR
        self.errorMessage = errorMessage
