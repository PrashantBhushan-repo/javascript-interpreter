# parser.py

import javascript_interpreter.tokens as tokens
from javascript_interpreter.tokens import Token
import javascript_interpreter.ast_nodes as ast_nodes

# Precedence levels
LOWEST = 1
ASSIGN = 2        # = += -= *= /=
OR = 3            # ||
AND = 4           # &&
EQUALITY = 5      # == === != !==
COMPARISON = 6    # < > <= >=
SUM = 7           # + -
PRODUCT = 8       # * / %
PREFIX = 9        # ! - +
CALL = 10         # f()
MEMBER = 11       # obj.prop, arr[idx]

PRECEDENCES = {
    tokens.ASSIGN: ASSIGN,
    tokens.ADD_ASSIGN: ASSIGN,
    tokens.SUB_ASSIGN: ASSIGN,
    tokens.MUL_ASSIGN: ASSIGN,
    tokens.DIV_ASSIGN: ASSIGN,
    tokens.OR: OR,
    tokens.AND: AND,
    tokens.EQ: EQUALITY,
    tokens.STRICT_EQ: EQUALITY,
    tokens.NOT_EQ: EQUALITY,
    tokens.STRICT_NOT_EQ: EQUALITY,
    tokens.LT: COMPARISON,
    tokens.GT: COMPARISON,
    tokens.LTE: COMPARISON,
    tokens.GTE: COMPARISON,
    tokens.PLUS: SUM,
    tokens.MINUS: SUM,
    tokens.ASTERISK: PRODUCT,
    tokens.SLASH: PRODUCT,
    tokens.MOD: PRODUCT,
    tokens.LPAREN: CALL,
    tokens.LBRACKET: MEMBER,
    tokens.DOT: MEMBER,
    tokens.INC: MEMBER,
    tokens.DEC: MEMBER,
}

class Parser:
    def __init__(self, lexer):
        self.tokens_list = []
        while True:
            tok = lexer.next_token()
            self.tokens_list.append(tok)
            if tok.type == tokens.EOF:
                break
        
        self.pos = 0
        self.cur_token = None
        self.peek_token = None
        self.errors = []
        self._advance()
        self._advance()

        # Prefix parsers mapping
        self.prefix_parsers = {
            tokens.IDENTIFIER: self.parse_identifier,
            tokens.NUMBER: self.parse_number,
            tokens.STRING: self.parse_string,
            tokens.TRUE: self.parse_boolean,
            tokens.FALSE: self.parse_boolean,
            tokens.NULL: self.parse_null,
            tokens.UNDEFINED: self.parse_undefined,
            tokens.PLUS: self.parse_prefix_expression,
            tokens.MINUS: self.parse_prefix_expression,
            tokens.BANG: self.parse_prefix_expression,
            tokens.LPAREN: self.parse_grouped_or_arrow_function,
            tokens.LBRACKET: self.parse_array_literal,
            tokens.LBRACE: self.parse_object_literal,
            tokens.NEW: self.parse_new_expression,
            tokens.FUNCTION: self.parse_function_expression,
            tokens.INC: self.parse_prefix_update_expression,
            tokens.DEC: self.parse_prefix_update_expression,
        }

        # Infix parsers mapping
        self.infix_parsers = {
            tokens.PLUS: self.parse_infix_expression,
            tokens.MINUS: self.parse_infix_expression,
            tokens.ASTERISK: self.parse_infix_expression,
            tokens.SLASH: self.parse_infix_expression,
            tokens.MOD: self.parse_infix_expression,
            tokens.EQ: self.parse_infix_expression,
            tokens.STRICT_EQ: self.parse_infix_expression,
            tokens.NOT_EQ: self.parse_infix_expression,
            tokens.STRICT_NOT_EQ: self.parse_infix_expression,
            tokens.LT: self.parse_infix_expression,
            tokens.GT: self.parse_infix_expression,
            tokens.LTE: self.parse_infix_expression,
            tokens.GTE: self.parse_infix_expression,
            tokens.AND: self.parse_infix_expression,
            tokens.OR: self.parse_infix_expression,
            tokens.ASSIGN: self.parse_infix_expression,
            tokens.ADD_ASSIGN: self.parse_infix_expression,
            tokens.SUB_ASSIGN: self.parse_infix_expression,
            tokens.MUL_ASSIGN: self.parse_infix_expression,
            tokens.DIV_ASSIGN: self.parse_infix_expression,
            tokens.LPAREN: self.parse_call_expression,
            tokens.LBRACKET: self.parse_index_expression,
            tokens.DOT: self.parse_member_expression,
            tokens.INC: self.parse_postfix_update_expression,
            tokens.DEC: self.parse_postfix_update_expression,
        }

    def _advance(self):
        self.cur_token = self.peek_token
        if self.pos < len(self.tokens_list):
            self.peek_token = self.tokens_list[self.pos]
            self.pos += 1
        else:
            self.peek_token = Token(tokens.EOF, "", self.cur_token.line, self.cur_token.column)

    def cur_token_is(self, t: str) -> bool:
        return self.cur_token.type == t

    def peek_token_is(self, t: str) -> bool:
        return self.peek_token.type == t

    def expect_peek(self, t: str) -> bool:
        if self.peek_token_is(t):
            self._advance()
            return True
        else:
            self.errors.append(f"Line {self.peek_token.line}: expected next token to be {t}, got {self.peek_token.type} instead")
            return False

    def peek_precedence(self) -> int:
        return PRECEDENCES.get(self.peek_token.type, LOWEST)

    def cur_precedence(self) -> int:
        return PRECEDENCES.get(self.cur_token.type, LOWEST)

    # --- Statement Parsers ---

    def parse_program(self) -> ast_nodes.Program:
        statements = []
        while not self.cur_token_is(tokens.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self._advance()
        return ast_nodes.Program(statements)

    def parse_statement(self):
        if self.cur_token_is(tokens.LET) or self.cur_token_is(tokens.CONST) or self.cur_token_is(tokens.VAR):
            return self.parse_variable_statement()
        elif self.cur_token_is(tokens.RETURN):
            return self.parse_return_statement()
        elif self.cur_token_is(tokens.IF):
            return self.parse_if_statement()
        elif self.cur_token_is(tokens.WHILE):
            return self.parse_while_statement()
        elif self.cur_token_is(tokens.DO):
            return self.parse_do_while_statement()
        elif self.cur_token_is(tokens.FOR):
            return self.parse_for_statement()
        elif self.cur_token_is(tokens.BREAK):
            return self.parse_break_statement()
        elif self.cur_token_is(tokens.CONTINUE):
            return self.parse_continue_statement()
        elif self.cur_token_is(tokens.SWITCH):
            return self.parse_switch_statement()
        elif self.cur_token_is(tokens.LBRACE):
            return self.parse_block_statement()
        elif self.cur_token_is(tokens.FUNCTION) and self.peek_token_is(tokens.IDENTIFIER):
            return self.parse_function_declaration()
        else:
            return self.parse_expression_statement()

    def parse_variable_statement(self) -> ast_nodes.VariableStatement:
        var_type = self.cur_token.literal  # "let", "const", "var"
        declarations = []
        
        while True:
            self._advance() # Consume let/const/var or comma
            if not self.cur_token_is(tokens.IDENTIFIER):
                self.errors.append(f"Line {self.cur_token.line}: expected identifier after variable binding keyword")
                return None
            
            name = ast_nodes.Identifier(self.cur_token.literal)
            value = None

            if self.peek_token_is(tokens.ASSIGN):
                self._advance() # Move to =
                self._advance() # Move to start of expression
                value = self.parse_expression(LOWEST)

            declarations.append(ast_nodes.VariableDeclaration(name, value))

            if self.peek_token_is(tokens.COMMA):
                self._advance() # Move to comma
            else:
                break

        if self.peek_token_is(tokens.SEMICOLON):
            self._advance()

        return ast_nodes.VariableStatement(var_type, declarations)

    def parse_return_statement(self) -> ast_nodes.ReturnStatement:
        self._advance() # Consume return
        value = None
        if not self.cur_token_is(tokens.SEMICOLON) and not self.cur_token_is(tokens.EOF):
            value = self.parse_expression(LOWEST)
        if self.peek_token_is(tokens.SEMICOLON):
            self._advance()
        return ast_nodes.ReturnStatement(value)

    def parse_if_statement(self) -> ast_nodes.IfStatement:
        if not self.expect_peek(tokens.LPAREN):
            return None
        self._advance() # Move to condition start
        condition = self.parse_expression(LOWEST)
        if not self.expect_peek(tokens.RPAREN):
            return None
        
        self._advance() # Move to consequence
        consequence = self.parse_statement()
        # Wrap single statement consequence into BlockStatement if not already
        if not isinstance(consequence, ast_nodes.BlockStatement):
            consequence = ast_nodes.BlockStatement([consequence])

        alternative = None
        if self.peek_token_is(tokens.ELSE):
            self._advance() # Move to else
            self._advance() # Move to start of alternative statement
            alternative = self.parse_statement()
            # Wrap single statement alternative into BlockStatement if not already,
            # except if it is another IfStatement (else if)
            if not isinstance(alternative, (ast_nodes.BlockStatement, ast_nodes.IfStatement)):
                alternative = ast_nodes.BlockStatement([alternative])

        return ast_nodes.IfStatement(condition, consequence, alternative)

    def parse_while_statement(self) -> ast_nodes.WhileStatement:
        if not self.expect_peek(tokens.LPAREN):
            return None
        self._advance()
        condition = self.parse_expression(LOWEST)
        if not self.expect_peek(tokens.RPAREN):
            return None
        self._advance()
        body = self.parse_statement()
        if not isinstance(body, ast_nodes.BlockStatement):
            body = ast_nodes.BlockStatement([body])
        return ast_nodes.WhileStatement(condition, body)

    def parse_do_while_statement(self) -> ast_nodes.DoWhileStatement:
        self._advance() # Consume do
        body = self.parse_statement()
        if not isinstance(body, ast_nodes.BlockStatement):
            body = ast_nodes.BlockStatement([body])
        if not self.expect_peek(tokens.WHILE):
            return None
        if not self.expect_peek(tokens.LPAREN):
            return None
        self._advance()
        condition = self.parse_expression(LOWEST)
        if not self.expect_peek(tokens.RPAREN):
            return None
        if self.peek_token_is(tokens.SEMICOLON):
            self._advance()
        return ast_nodes.DoWhileStatement(body, condition)

    def parse_for_statement(self) -> ast_nodes.ForStatement:
        if not self.expect_peek(tokens.LPAREN):
            return None
        
        self._advance() # Move past LPAREN to initializer start
        
        # 1. Initializer
        initializer = None
        if not self.cur_token_is(tokens.SEMICOLON):
            initializer = self.parse_statement() # leaves cur_token as ;
        if self.cur_token_is(tokens.SEMICOLON):
            self._advance()
        else:
            self.errors.append(f"Line {self.cur_token.line}: expected ; after for initializer")
            return None

        # 2. Condition
        condition = None
        if not self.cur_token_is(tokens.SEMICOLON):
            condition = self.parse_expression(LOWEST)
            if self.cur_token_is(tokens.SEMICOLON):
                pass
            else:
                if not self.expect_peek(tokens.SEMICOLON):
                    return None
        self._advance() # Move past ;

        # 3. Increment
        increment = None
        if not self.cur_token_is(tokens.RPAREN):
            increment = self.parse_expression(LOWEST)
            if self.cur_token_is(tokens.RPAREN):
                pass
            else:
                if not self.expect_peek(tokens.RPAREN):
                    return None
        
        self._advance() # Move past RPAREN
        body = self.parse_statement()
        if not isinstance(body, ast_nodes.BlockStatement):
            body = ast_nodes.BlockStatement([body])

        return ast_nodes.ForStatement(initializer, condition, increment, body)

    def parse_break_statement(self) -> ast_nodes.BreakStatement:
        if self.peek_token_is(tokens.SEMICOLON):
            self._advance()
        return ast_nodes.BreakStatement()

    def parse_continue_statement(self) -> ast_nodes.ContinueStatement:
        if self.peek_token_is(tokens.SEMICOLON):
            self._advance()
        return ast_nodes.ContinueStatement()

    def parse_switch_statement(self) -> ast_nodes.SwitchStatement:
        if not self.expect_peek(tokens.LPAREN):
            return None
        self._advance()
        discriminant = self.parse_expression(LOWEST)
        if not self.expect_peek(tokens.RPAREN):
            return None
        if not self.expect_peek(tokens.LBRACE):
            return None
        
        self._advance() # Move inside switch block
        cases = []
        while not self.cur_token_is(tokens.RBRACE) and not self.cur_token_is(tokens.EOF):
            if self.cur_token_is(tokens.CASE):
                self._advance()
                test = self.parse_expression(LOWEST)
                self.expect_peek(tokens.COLON)
                self._advance()
                consequent = []
                while not self.cur_token_is(tokens.CASE) and not self.cur_token_is(tokens.DEFAULT) and not self.cur_token_is(tokens.RBRACE) and not self.cur_token_is(tokens.EOF):
                    stmt = self.parse_statement()
                    if stmt:
                        consequent.append(stmt)
                    self._advance()
                cases.append(ast_nodes.CaseStatement(test, consequent))
            elif self.cur_token_is(tokens.DEFAULT):
                if not self.expect_peek(tokens.COLON):
                    return None
                self._advance()
                consequent = []
                while not self.cur_token_is(tokens.CASE) and not self.cur_token_is(tokens.DEFAULT) and not self.cur_token_is(tokens.RBRACE) and not self.cur_token_is(tokens.EOF):
                    stmt = self.parse_statement()
                    if stmt:
                        consequent.append(stmt)
                    self._advance()
                cases.append(ast_nodes.CaseStatement(None, consequent))
            else:
                # Skip illegal/unrecognized items directly inside switch
                self._advance()

        return ast_nodes.SwitchStatement(discriminant, cases)

    def parse_block_statement(self) -> ast_nodes.BlockStatement:
        # We start at LBRACE
        statements = []
        self._advance()
        while not self.cur_token_is(tokens.RBRACE) and not self.cur_token_is(tokens.EOF):
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self._advance()
        return ast_nodes.BlockStatement(statements)

    def parse_function_declaration(self) -> ast_nodes.FunctionDeclaration:
        # cur is FUNCTION, peek is IDENTIFIER
        self._advance() # Move to IDENTIFIER
        name = ast_nodes.Identifier(self.cur_token.literal)
        
        if not self.expect_peek(tokens.LPAREN):
            return None
            
        parameters, rest_parameter = self.parse_function_parameters()
        
        if not self.expect_peek(tokens.LBRACE):
            return None
            
        body = self.parse_block_statement()
        return ast_nodes.FunctionDeclaration(name, parameters, rest_parameter, body)

    def parse_expression_statement(self) -> ast_nodes.ExpressionStatement:
        expr = self.parse_expression(LOWEST)
        if self.peek_token_is(tokens.SEMICOLON):
            self._advance()
        return ast_nodes.ExpressionStatement(expr)

    # --- Expression Parsers ---

    def parse_expression(self, precedence: int):
        prefix = self.prefix_parsers.get(self.cur_token.type)
        if not prefix:
            # If current token doesn't map to prefix, e.g. a trailing comma/etc., log error
            self.errors.append(f"Line {self.cur_token.line}: no prefix parse function for {self.cur_token.type} found")
            return None
        
        left_exp = prefix()

        # Single-identifier arrow function check: x => ...
        if isinstance(left_exp, ast_nodes.Identifier) and self.peek_token_is(tokens.ARROW):
            self._advance() # Move to ARROW =>
            left_exp = self.parse_arrow_function_literal([left_exp], None)

        while not self.peek_token_is(tokens.SEMICOLON) and precedence < self.peek_precedence():
            infix = self.infix_parsers.get(self.peek_token.type)
            if not infix:
                return left_exp
            self._advance()
            left_exp = infix(left_exp)

        return left_exp

    def parse_identifier(self) -> ast_nodes.Identifier:
        return ast_nodes.Identifier(self.cur_token.literal)

    def parse_number(self) -> ast_nodes.Literal:
        val = self.cur_token.literal
        # parse as int or float
        if "." in val:
            return ast_nodes.Literal(float(val), "number")
        else:
            return ast_nodes.Literal(int(val), "number")

    def parse_string(self) -> ast_nodes.Literal:
        return ast_nodes.Literal(self.cur_token.literal, "string")

    def parse_boolean(self) -> ast_nodes.Literal:
        return ast_nodes.Literal(self.cur_token_is(tokens.TRUE), "boolean")

    def parse_null(self) -> ast_nodes.Literal:
        return ast_nodes.Literal(None, "null")

    def parse_undefined(self) -> ast_nodes.Literal:
        return ast_nodes.Literal(None, "undefined")

    def parse_prefix_expression(self) -> ast_nodes.PrefixExpression:
        op = self.cur_token.literal
        self._advance()
        right = self.parse_expression(PREFIX)
        return ast_nodes.PrefixExpression(op, right)

    def is_arrow_function(self) -> bool:
        # Check if parenthesized list is followed by Arrow =>
        depth = 0
        i = self.pos - 2 # self.pos is currently pointing past peek_token, so current is pos-2
        while i < len(self.tokens_list):
            t = self.tokens_list[i]
            if t.type == tokens.LPAREN:
                depth += 1
            elif t.type == tokens.RPAREN:
                depth -= 1
                if depth == 0:
                    if i + 1 < len(self.tokens_list) and self.tokens_list[i + 1].type == tokens.ARROW:
                        return True
                    break
            i += 1
        return False

    def parse_grouped_or_arrow_function(self):
        # We are at LPAREN. Is it an arrow function?
        if self.is_arrow_function():
            # Parse arrow function
            parameters, rest_parameter = self.parse_function_parameters()
            self._advance() # Move to ARROW =>
            return self.parse_arrow_function_literal(parameters, rest_parameter)
        else:
            # Standard grouped expression
            self._advance() # Consume LPAREN
            expr = self.parse_expression(LOWEST)
            if not self.expect_peek(tokens.RPAREN):
                return None
            return expr

    def parse_arrow_function_literal(self, parameters: list, rest_parameter):
        # We are at ARROW =>
        self._advance() # Consume ARROW =>
        
        if self.cur_token_is(tokens.LBRACE):
            # Block body
            body = self.parse_block_statement()
            return ast_nodes.ArrowFunctionLiteral(parameters, rest_parameter, body, is_expression_body=False)
        else:
            # Expression body
            body = self.parse_expression(LOWEST)
            return ast_nodes.ArrowFunctionLiteral(parameters, rest_parameter, body, is_expression_body=True)

    def parse_array_literal(self) -> ast_nodes.ArrayLiteral:
        elements = []
        if self.peek_token_is(tokens.RBRACKET):
            self._advance()
            return ast_nodes.ArrayLiteral(elements)
        
        self._advance() # Move past LBRACKET
        while True:
            if self.cur_token_is(tokens.SPREAD):
                self._advance() # Consume ...
                expr = self.parse_expression(LOWEST)
                elements.append(ast_nodes.SpreadExpression(expr))
            else:
                expr = self.parse_expression(LOWEST)
                elements.append(expr)

            if self.peek_token_is(tokens.COMMA):
                self._advance() # Move to comma
                self._advance() # Move to next element start
            else:
                break
        
        self.expect_peek(tokens.RBRACKET)
        return ast_nodes.ArrayLiteral(elements)

    def parse_object_literal(self) -> ast_nodes.ObjectLiteral:
        properties = []
        if self.peek_token_is(tokens.RBRACE):
            self._advance()
            return ast_nodes.ObjectLiteral(properties)

        self._advance() # Move past LBRACE
        while True:
            # Key can be Identifier, String, or Number
            if not (self.cur_token_is(tokens.IDENTIFIER) or self.cur_token_is(tokens.STRING) or self.cur_token_is(tokens.NUMBER)):
                self.errors.append(f"Line {self.cur_token.line}: expected identifier, string, or number as property key")
                return None
            
            key = self.cur_token.literal
            
            self.expect_peek(tokens.COLON)
            self._advance() # Move past COLON
            value = self.parse_expression(LOWEST)
            properties.append((key, value))

            if self.peek_token_is(tokens.COMMA):
                self._advance() # Move to comma
                self._advance() # Move to next key start
            else:
                break
        
        self.expect_peek(tokens.RBRACE)
        return ast_nodes.ObjectLiteral(properties)

    def parse_new_expression(self) -> ast_nodes.NewExpression:
        self._advance() # Consume new
        constructor = self.parse_expression(CALL) # usually a MemberExpression or Identifier
        
        arguments = []
        if self.peek_token_is(tokens.LPAREN):
            self._advance() # Move to LPAREN
            if not self.peek_token_is(tokens.RPAREN):
                self._advance()
                while True:
                    expr = self.parse_expression(LOWEST)
                    arguments.append(expr)
                    if self.peek_token_is(tokens.COMMA):
                        self._advance()
                        self._advance()
                    else:
                        break
            self.expect_peek(tokens.RPAREN)
            
        return ast_nodes.NewExpression(constructor, arguments)

    def parse_function_expression(self) -> ast_nodes.FunctionExpression:
        # cur is FUNCTION
        if self.peek_token_is(tokens.IDENTIFIER):
            self._advance()
            # named function expression (optional, let's keep identifier name in a dictionary if needed, but we can treat it as anonymous function mostly)
            # name = self.cur_token.literal
        
        if not self.expect_peek(tokens.LPAREN):
            return None
            
        parameters, rest_parameter = self.parse_function_parameters()
        
        if not self.expect_peek(tokens.LBRACE):
            return None
            
        body = self.parse_block_statement()
        return ast_nodes.FunctionExpression(parameters, rest_parameter, body)

    def parse_function_parameters(self):
        # We start at LPAREN
        params = []
        rest_param = None
        
        if self.peek_token_is(tokens.RPAREN):
            self._advance()
            return params, rest_param
            
        self._advance() # move to first param or ...
        
        while True:
            if self.cur_token_is(tokens.SPREAD):
                self._advance() # consume ...
                if not self.cur_token_is(tokens.IDENTIFIER):
                    self.errors.append(f"Line {self.cur_token.line}: expected identifier after spread in parameters")
                    return params, rest_param
                rest_param = ast_nodes.Identifier(self.cur_token.literal)
                break # rest parameter must be last
            else:
                if not self.cur_token_is(tokens.IDENTIFIER):
                    self.errors.append(f"Line {self.cur_token.line}: expected identifier in parameters")
                    return params, rest_param
                params.append(ast_nodes.Identifier(self.cur_token.literal))
                
            if self.peek_token_is(tokens.COMMA):
                self._advance()
                self._advance()
            else:
                break
                
        self.expect_peek(tokens.RPAREN)
        return params, rest_param

    def parse_infix_expression(self, left) -> ast_nodes.InfixExpression:
        op = self.cur_token.literal
        precedence = self.cur_precedence()
        
        if op in ["=", "+=", "-=", "*=", "/="]:
            # Right-associative assignment: parse right with one lower precedence
            self._advance()
            right = self.parse_expression(precedence - 1)
        else:
            self._advance()
            right = self.parse_expression(precedence)
            
        return ast_nodes.InfixExpression(left, op, right)

    def parse_call_expression(self, function) -> ast_nodes.CallExpression:
        arguments = []
        if self.peek_token_is(tokens.RPAREN):
            self._advance()
            return ast_nodes.CallExpression(function, arguments)
            
        self._advance() # Move past LPAREN
        while True:
            if self.cur_token_is(tokens.SPREAD):
                self._advance() # Consume ...
                expr = self.parse_expression(LOWEST)
                arguments.append(ast_nodes.SpreadExpression(expr))
            else:
                expr = self.parse_expression(LOWEST)
                arguments.append(expr)
                
            if self.peek_token_is(tokens.COMMA):
                self._advance()
                self._advance()
            else:
                break
                
        self.expect_peek(tokens.RPAREN)
        return ast_nodes.CallExpression(function, arguments)

    def parse_index_expression(self, left) -> ast_nodes.IndexExpression:
        self._advance() # Move past LBRACKET [
        index = self.parse_expression(LOWEST)
        self.expect_peek(tokens.RBRACKET)
        return ast_nodes.IndexExpression(left, index)

    def parse_member_expression(self, left) -> ast_nodes.MemberExpression:
        self._advance() # Move past DOT .
        if not self.cur_token_is(tokens.IDENTIFIER):
            self.errors.append(f"Line {self.cur_token.line}: expected identifier after dot member accessor")
            return None
        member = ast_nodes.Identifier(self.cur_token.literal)
        return ast_nodes.MemberExpression(left, member)

    def parse_prefix_update_expression(self) -> ast_nodes.UpdateExpression:
        op = self.cur_token.literal
        self._advance()
        right = self.parse_expression(PREFIX)
        return ast_nodes.UpdateExpression(op, right, is_prefix=True)

    def parse_postfix_update_expression(self, left) -> ast_nodes.UpdateExpression:
        op = self.cur_token.literal
        self._advance()
        return ast_nodes.UpdateExpression(op, left, is_prefix=False)
