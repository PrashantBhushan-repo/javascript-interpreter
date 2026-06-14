# tokens.py

# Token Types
EOF = "EOF"
ILLEGAL = "ILLEGAL"

# Identifiers + Literals
IDENTIFIER = "IDENTIFIER"
NUMBER = "NUMBER"
STRING = "STRING"

# Operators
ASSIGN = "="
ADD_ASSIGN = "+="
SUB_ASSIGN = "-="
MUL_ASSIGN = "*="
DIV_ASSIGN = "/="

PLUS = "+"
MINUS = "-"
ASTERISK = "*"
SLASH = "/"
MOD = "%"

EQ = "=="
STRICT_EQ = "==="
NOT_EQ = "!="
STRICT_NOT_EQ = "!=="

LT = "<"
GT = ">"
LTE = "<="
GTE = ">="

AND = "&&"
OR = "||"
BANG = "!"

ARROW = "=>"
DOT = "."
SPREAD = "..."
INC = "++"
DEC = "--"

# Delimiters
LPAREN = "("
RPAREN = ")"
LBRACE = "{"
RBRACE = "}"
LBRACKET = "["
RBRACKET = "]"
COMMA = ","
SEMICOLON = ";"
COLON = ":"
QUESTION = "?"

# Keywords
LET = "let"
CONST = "const"
VAR = "var"
FUNCTION = "function"
RETURN = "return"
IF = "if"
ELSE = "else"
FOR = "for"
WHILE = "while"
DO = "do"
BREAK = "break"
CONTINUE = "continue"
SWITCH = "switch"
CASE = "case"
DEFAULT = "default"
NEW = "new"
TRUE = "true"
FALSE = "false"
NULL = "null"
UNDEFINED = "undefined"

KEYWORDS = {
    "let": LET,
    "const": CONST,
    "var": VAR,
    "function": FUNCTION,
    "return": RETURN,
    "if": IF,
    "else": ELSE,
    "for": FOR,
    "while": WHILE,
    "do": DO,
    "break": BREAK,
    "continue": CONTINUE,
    "switch": SWITCH,
    "case": CASE,
    "default": DEFAULT,
    "new": NEW,
    "true": TRUE,
    "false": FALSE,
    "null": NULL,
    "undefined": UNDEFINED,
}

class Token:
    def __init__(self, type_: str, literal: str, line: int, column: int):
        self.type = type_
        self.literal = literal
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"Token({self.type}, {repr(self.literal)}, line={self.line}, col={self.column})"

def lookup_identifier(ident: str) -> str:
    return KEYWORDS.get(ident, IDENTIFIER)
