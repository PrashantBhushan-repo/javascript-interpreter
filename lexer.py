# lexer.py

from tokens import Token, lookup_identifier
import tokens

class Lexer:
    def __init__(self, input_str: str):
        self.input_str = input_str
        self.position = 0
        self.read_position = 0
        self.ch = ""
        self.line = 1
        self.column = 0
        self.read_char()

    def read_char(self):
        if self.read_position >= len(self.input_str):
            self.ch = ""
        else:
            self.ch = self.input_str[self.read_position]
        self.position = self.read_position
        self.read_position += 1
        self.column += 1

    def peek_char(self) -> str:
        if self.read_position >= len(self.input_str):
            return ""
        return self.input_str[self.read_position]

    def peek_char_n(self, n: int) -> str:
        pos = self.position + n
        if pos >= len(self.input_str):
            return ""
        return self.input_str[pos]

    def skip_whitespace_and_comments(self):
        while True:
            # Skip whitespace
            if self.ch in [" ", "\t", "\r", "\n"]:
                if self.ch == "\n":
                    self.line += 1
                    self.column = 0
                self.read_char()
                continue
            
            # Skip comments
            if self.ch == "/":
                next_ch = self.peek_char()
                if next_ch == "/":
                    # Single-line comment
                    while self.ch != "\n" and self.ch != "":
                        self.read_char()
                    continue
                elif next_ch == "*":
                    # Multi-line comment
                    self.read_char() # Consume '/'
                    self.read_char() # Consume '*'
                    while not (self.ch == "*" and self.peek_char() == "/") and self.ch != "":
                        if self.ch == "\n":
                            self.line += 1
                            self.column = 0
                        self.read_char()
                    if self.ch != "":
                        self.read_char() # Consume '*'
                        self.read_char() # Consume '/'
                    continue
            
            break

    def read_identifier(self) -> str:
        start_pos = self.position
        while self.is_letter_or_digit(self.ch):
            self.read_char()
        return self.input_str[start_pos:self.position]

    def is_letter_or_digit(self, ch: str) -> bool:
        # JS identifiers can start with a letter, _, $, and contain numbers
        return ch.isalnum() or ch == "_" or ch == "$"

    def is_digit(self, ch: str) -> bool:
        return ch.isdigit()

    def read_number(self) -> str:
        start_pos = self.position
        has_dot = False
        while self.is_digit(self.ch) or (self.ch == "." and not has_dot and self.peek_char().isdigit()):
            if self.ch == ".":
                has_dot = True
            self.read_char()
        return self.input_str[start_pos:self.position]

    def read_string(self, quote: str) -> str:
        # quote is either "'" or '"'
        self.read_char() # Skip opening quote
        chars = []
        while self.ch != quote and self.ch != "":
            if self.ch == "\\":
                self.read_char() # Skip '\\'
                if self.ch == "n":
                    chars.append("\n")
                elif self.ch == "t":
                    chars.append("\t")
                elif self.ch == "r":
                    chars.append("\r")
                elif self.ch == "b":
                    chars.append("\b")
                elif self.ch == "f":
                    chars.append("\f")
                elif self.ch in ["'", '"', "\\"]:
                    chars.append(self.ch)
                else:
                    chars.append(self.ch) # Keep it literally
            else:
                if self.ch == "\n":
                    self.line += 1
                    self.column = 0
                chars.append(self.ch)
            self.read_char()
        
        if self.ch == quote:
            self.read_char() # Skip closing quote
        return "".join(chars)

    def next_token(self) -> Token:
        self.skip_whitespace_and_comments()

        tok_line = self.line
        tok_col = self.column

        if self.ch == "":
            tok = Token(tokens.EOF, "", tok_line, tok_col)
            self.read_char()
            return tok

        # Match operators and punctuation
        if self.ch == "=":
            if self.peek_char() == ">":
                self.read_char()
                tok = Token(tokens.ARROW, "=>", tok_line, tok_col)
            elif self.peek_char() == "=":
                self.read_char()
                if self.peek_char() == "=":
                    self.read_char()
                    tok = Token(tokens.STRICT_EQ, "===", tok_line, tok_col)
                else:
                    tok = Token(tokens.EQ, "==", tok_line, tok_col)
            else:
                tok = Token(tokens.ASSIGN, "=", tok_line, tok_col)
        elif self.ch == "+":
            if self.peek_char() == "+":
                self.read_char()
                tok = Token(tokens.INC, "++", tok_line, tok_col)
            elif self.peek_char() == "=":
                self.read_char()
                tok = Token(tokens.ADD_ASSIGN, "+=", tok_line, tok_col)
            else:
                tok = Token(tokens.PLUS, "+", tok_line, tok_col)
        elif self.ch == "-":
            if self.peek_char() == "-":
                self.read_char()
                tok = Token(tokens.DEC, "--", tok_line, tok_col)
            elif self.peek_char() == "=":
                self.read_char()
                tok = Token(tokens.SUB_ASSIGN, "-=", tok_line, tok_col)
            else:
                tok = Token(tokens.MINUS, "-", tok_line, tok_col)
        elif self.ch == "*":
            if self.peek_char() == "=":
                self.read_char()
                tok = Token(tokens.MUL_ASSIGN, "*=", tok_line, tok_col)
            else:
                tok = Token(tokens.ASTERISK, "*", tok_line, tok_col)
        elif self.ch == "/":
            # Division or Div-Assign (comments already skipped)
            if self.peek_char() == "=":
                self.read_char()
                tok = Token(tokens.DIV_ASSIGN, "/=", tok_line, tok_col)
            else:
                tok = Token(tokens.SLASH, "/", tok_line, tok_col)
        elif self.ch == "%":
            tok = Token(tokens.MOD, "%", tok_line, tok_col)
        elif self.ch == "!":
            if self.peek_char() == "=":
                self.read_char()
                if self.peek_char() == "=":
                    self.read_char()
                    tok = Token(tokens.STRICT_NOT_EQ, "!==", tok_line, tok_col)
                else:
                    tok = Token(tokens.NOT_EQ, "!=", tok_line, tok_col)
            else:
                tok = Token(tokens.BANG, "!", tok_line, tok_col)
        elif self.ch == "<":
            if self.peek_char() == "=":
                self.read_char()
                tok = Token(tokens.LTE, "<=", tok_line, tok_col)
            else:
                tok = Token(tokens.LT, "<", tok_line, tok_col)
        elif self.ch == ">":
            if self.peek_char() == "=":
                self.read_char()
                tok = Token(tokens.GTE, ">=", tok_line, tok_col)
            else:
                tok = Token(tokens.GT, ">", tok_line, tok_col)
        elif self.ch == "&":
            if self.peek_char() == "&":
                self.read_char()
                tok = Token(tokens.AND, "&&", tok_line, tok_col)
            else:
                tok = Token(tokens.ILLEGAL, "&", tok_line, tok_col)
        elif self.ch == "|":
            if self.peek_char() == "|":
                self.read_char()
                tok = Token(tokens.OR, "||", tok_line, tok_col)
            else:
                tok = Token(tokens.ILLEGAL, "|", tok_line, tok_col)
        elif self.ch == ".":
            if self.peek_char() == "." and self.peek_char_n(2) == ".":
                self.read_char()
                self.read_char()
                tok = Token(tokens.SPREAD, "...", tok_line, tok_col)
            else:
                tok = Token(tokens.DOT, ".", tok_line, tok_col)
        elif self.ch == "(":
            tok = Token(tokens.LPAREN, "(", tok_line, tok_col)
        elif self.ch == ")":
            tok = Token(tokens.RPAREN, ")", tok_line, tok_col)
        elif self.ch == "{":
            tok = Token(tokens.LBRACE, "{", tok_line, tok_col)
        elif self.ch == "}":
            tok = Token(tokens.RBRACE, "}", tok_line, tok_col)
        elif self.ch == "[":
            tok = Token(tokens.LBRACKET, "[", tok_line, tok_col)
        elif self.ch == "]":
            tok = Token(tokens.RBRACKET, "]", tok_line, tok_col)
        elif self.ch == ",":
            tok = Token(tokens.COMMA, ",", tok_line, tok_col)
        elif self.ch == ";":
            tok = Token(tokens.SEMICOLON, ";", tok_line, tok_col)
        elif self.ch == ":":
            tok = Token(tokens.COLON, ":", tok_line, tok_col)
        elif self.ch == "?":
            tok = Token(tokens.QUESTION, "?", tok_line, tok_col)
        elif self.ch in ["'", '"']:
            literal = self.read_string(self.ch)
            return Token(tokens.STRING, literal, tok_line, tok_col)
        else:
            # Identifier or Number or Illegal
            if self.ch.isalpha() or self.ch == "_" or self.ch == "$":
                literal = self.read_identifier()
                tok_type = lookup_identifier(literal)
                return Token(tok_type, literal, tok_line, tok_col)
            elif self.ch.isdigit():
                literal = self.read_number()
                return Token(tokens.NUMBER, literal, tok_line, tok_col)
            else:
                tok = Token(tokens.ILLEGAL, self.ch, tok_line, tok_col)

        self.read_char()
        return tok
