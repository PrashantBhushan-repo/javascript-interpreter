# ast_nodes.py

class Node:
    def to_dict(self) -> dict:
        raise NotImplementedError()

class Statement(Node):
    pass

class Expression(Node):
    pass

# --- Statements ---

class Program(Node):
    def __init__(self, statements: list):
        self.statements = statements

    def to_dict(self) -> dict:
        return {
            "type": "Program",
            "statements": [s.to_dict() for s in self.statements]
        }

    def __repr__(self) -> str:
        return f"Program({self.statements})"

class VariableDeclaration(Node):
    def __init__(self, name, value):
        self.name = name  # Identifier
        self.value = value  # Expression or None

    def to_dict(self) -> dict:
        return {
            "type": "VariableDeclaration",
            "name": self.name.value,
            "value": self.value.to_dict() if self.value else None
        }

    def __repr__(self) -> str:
        return f"Decl({self.name} = {self.value})"

class VariableStatement(Statement):
    def __init__(self, var_type: str, declarations: list):
        self.var_type = var_type  # "let", "const", or "var"
        self.declarations = declarations  # list of VariableDeclaration

    def to_dict(self) -> dict:
        return {
            "type": "VariableStatement",
            "var_type": self.var_type,
            "declarations": [d.to_dict() for d in self.declarations]
        }

    def __repr__(self) -> str:
        return f"VarStmt({self.var_type} {self.declarations})"

class ReturnStatement(Statement):
    def __init__(self, value):
        self.value = value  # Expression or None

    def to_dict(self) -> dict:
        return {
            "type": "ReturnStatement",
            "value": self.value.to_dict() if self.value else None
        }

    def __repr__(self) -> str:
        return f"Return({self.value})"

class ExpressionStatement(Statement):
    def __init__(self, expression):
        self.expression = expression  # Expression

    def to_dict(self) -> dict:
        return {
            "type": "ExpressionStatement",
            "expression": self.expression.to_dict()
        }

    def __repr__(self) -> str:
        return f"ExprStmt({self.expression})"

class BlockStatement(Statement):
    def __init__(self, statements: list):
        self.statements = statements

    def to_dict(self) -> dict:
        return {
            "type": "BlockStatement",
            "statements": [s.to_dict() for s in self.statements]
        }

    def __repr__(self) -> str:
        return f"Block({self.statements})"

class IfStatement(Statement):
    def __init__(self, condition, consequence, alternative):
        self.condition = condition  # Expression
        self.consequence = consequence  # BlockStatement
        self.alternative = alternative  # BlockStatement, IfStatement, or None

    def to_dict(self) -> dict:
        return {
            "type": "IfStatement",
            "condition": self.condition.to_dict(),
            "consequence": self.consequence.to_dict(),
            "alternative": self.alternative.to_dict() if self.alternative else None
        }

    def __repr__(self) -> str:
        return f"If({self.condition}, {self.consequence}, {self.alternative})"

class WhileStatement(Statement):
    def __init__(self, condition, body):
        self.condition = condition  # Expression
        self.body = body  # BlockStatement or Statement

    def to_dict(self) -> dict:
        return {
            "type": "WhileStatement",
            "condition": self.condition.to_dict(),
            "body": self.body.to_dict()
        }

    def __repr__(self) -> str:
        return f"While({self.condition}, {self.body})"

class DoWhileStatement(Statement):
    def __init__(self, body, condition):
        self.body = body  # BlockStatement or Statement
        self.condition = condition  # Expression

    def to_dict(self) -> dict:
        return {
            "type": "DoWhileStatement",
            "body": self.body.to_dict(),
            "condition": self.condition.to_dict()
        }

    def __repr__(self) -> str:
        return f"DoWhile({self.body}, {self.condition})"

class ForStatement(Statement):
    def __init__(self, initializer, condition, increment, body):
        self.initializer = initializer  # VariableStatement, ExpressionStatement, or None
        self.condition = condition  # Expression or None
        self.increment = increment  # Expression or None
        self.body = body  # BlockStatement or Statement

    def to_dict(self) -> dict:
        return {
            "type": "ForStatement",
            "initializer": self.initializer.to_dict() if self.initializer else None,
            "condition": self.condition.to_dict() if self.condition else None,
            "increment": self.increment.to_dict() if self.increment else None,
            "body": self.body.to_dict()
        }

    def __repr__(self) -> str:
        return f"For(init={self.initializer}, cond={self.condition}, inc={self.increment}, body={self.body})"

class BreakStatement(Statement):
    def to_dict(self) -> dict:
        return {"type": "BreakStatement"}

    def __repr__(self) -> str:
        return "Break"

class ContinueStatement(Statement):
    def to_dict(self) -> dict:
        return {"type": "ContinueStatement"}

    def __repr__(self) -> str:
        return "Continue"

class CaseStatement(Statement):
    def __init__(self, test, consequent: list):
        self.test = test  # Expression or None (for default)
        self.consequent = consequent  # list of Statements

    def to_dict(self) -> dict:
        return {
            "type": "CaseStatement",
            "test": self.test.to_dict() if self.test else None,
            "consequent": [s.to_dict() for s in self.consequent]
        }

    def __repr__(self) -> str:
        return f"Case({self.test}, {self.consequent})"

class SwitchStatement(Statement):
    def __init__(self, discriminant, cases: list):
        self.discriminant = discriminant  # Expression
        self.cases = cases  # list of CaseStatement

    def to_dict(self) -> dict:
        return {
            "type": "SwitchStatement",
            "discriminant": self.discriminant.to_dict(),
            "cases": [c.to_dict() for c in self.cases]
        }

    def __repr__(self) -> str:
        return f"Switch({self.discriminant}, {self.cases})"

class FunctionDeclaration(Statement):
    def __init__(self, name, parameters: list, rest_parameter, body):
        self.name = name  # Identifier
        self.parameters = parameters  # list of Identifier
        self.rest_parameter = rest_parameter  # Identifier or None
        self.body = body  # BlockStatement

    def to_dict(self) -> dict:
        return {
            "type": "FunctionDeclaration",
            "name": self.name.value,
            "parameters": [p.value for p in self.parameters],
            "rest_parameter": self.rest_parameter.value if self.rest_parameter else None,
            "body": self.body.to_dict()
        }

    def __repr__(self) -> str:
        rest = f", ...{self.rest_parameter}" if self.rest_parameter else ""
        return f"FuncDecl({self.name}({','.join(repr(p) for p in self.parameters)}{rest}), {self.body})"

# --- Expressions ---

class Identifier(Expression):
    def __init__(self, value: str):
        self.value = value

    def to_dict(self) -> dict:
        return {
            "type": "Identifier",
            "value": self.value
        }

    def __repr__(self) -> str:
        return f"Ident({self.value})"

class Literal(Expression):
    def __init__(self, value, value_type: str):
        self.value = value  # Python representation (int, float, str, bool, or None)
        self.value_type = value_type  # "number", "string", "boolean", "null", "undefined"

    def to_dict(self) -> dict:
        return {
            "type": "Literal",
            "value_type": self.value_type,
            "value": self.value
        }

    def __repr__(self) -> str:
        return f"Literal({self.value_type}:{repr(self.value)})"

class ArrayLiteral(Expression):
    def __init__(self, elements: list):
        self.elements = elements  # list of Expressions, some could be SpreadExpression

    def to_dict(self) -> dict:
        return {
            "type": "ArrayLiteral",
            "elements": [e.to_dict() for e in self.elements]
        }

    def __repr__(self) -> str:
        return f"ArrayLiteral({self.elements})"

class ObjectLiteral(Expression):
    def __init__(self, properties: list):
        self.properties = properties  # list of (key_expr, value_expr)

    def to_dict(self) -> dict:
        return {
            "type": "ObjectLiteral",
            "properties": [(k.to_dict() if hasattr(k, "to_dict") else k, v.to_dict()) for k, v in self.properties]
        }

    def __repr__(self) -> str:
        return f"ObjectLiteral({self.properties})"

class PrefixExpression(Expression):
    def __init__(self, operator: str, right):
        self.operator = operator
        self.right = right  # Expression

    def to_dict(self) -> dict:
        return {
            "type": "PrefixExpression",
            "operator": self.operator,
            "right": self.right.to_dict()
        }

    def __repr__(self) -> str:
        return f"Prefix({self.operator}{self.right})"

class InfixExpression(Expression):
    def __init__(self, left, operator: str, right):
        self.left = left  # Expression
        self.operator = operator
        self.right = right  # Expression

    def to_dict(self) -> dict:
        return {
            "type": "InfixExpression",
            "left": self.left.to_dict(),
            "operator": self.operator,
            "right": self.right.to_dict()
        }

    def __repr__(self) -> str:
        return f"Infix({self.left} {self.operator} {self.right})"

class CallExpression(Expression):
    def __init__(self, function, arguments: list):
        self.function = function  # Expression
        self.arguments = arguments  # list of Expressions (can contain SpreadExpression)

    def to_dict(self) -> dict:
        return {
            "type": "CallExpression",
            "function": self.function.to_dict(),
            "arguments": [a.to_dict() for a in self.arguments]
        }

    def __repr__(self) -> str:
        return f"Call({self.function}, args={self.arguments})"

class IndexExpression(Expression):
    def __init__(self, left, index):
        self.left = left  # Expression
        self.index = index  # Expression

    def to_dict(self) -> dict:
        return {
            "type": "IndexExpression",
            "left": self.left.to_dict(),
            "index": self.index.to_dict()
        }

    def __repr__(self) -> str:
        return f"Index({self.left}[{self.index}])"

class MemberExpression(Expression):
    def __init__(self, left, member):
        self.left = left  # Expression
        self.member = member  # Identifier

    def to_dict(self) -> dict:
        return {
            "type": "MemberExpression",
            "left": self.left.to_dict(),
            "member": self.member.to_dict()
        }

    def __repr__(self) -> str:
        return f"Member({self.left}.{self.member})"

class NewExpression(Expression):
    def __init__(self, constructor, arguments: list):
        self.constructor = constructor  # Expression
        self.arguments = arguments  # list of Expressions

    def to_dict(self) -> dict:
        return {
            "type": "NewExpression",
            "constructor": self.constructor.to_dict(),
            "arguments": [a.to_dict() for a in self.arguments]
        }

    def __repr__(self) -> str:
        return f"New({self.constructor}, args={self.arguments})"

class FunctionExpression(Expression):
    def __init__(self, parameters: list, rest_parameter, body):
        self.parameters = parameters  # list of Identifier
        self.rest_parameter = rest_parameter  # Identifier or None
        self.body = body  # BlockStatement

    def to_dict(self) -> dict:
        return {
            "type": "FunctionExpression",
            "parameters": [p.value for p in self.parameters],
            "rest_parameter": self.rest_parameter.value if self.rest_parameter else None,
            "body": self.body.to_dict()
        }

    def __repr__(self) -> str:
        rest = f", ...{self.rest_parameter}" if self.rest_parameter else ""
        return f"FuncExpr(({','.join(repr(p) for p in self.parameters)}{rest}), {self.body})"

class ArrowFunctionLiteral(Expression):
    def __init__(self, parameters: list, rest_parameter, body, is_expression_body: bool):
        self.parameters = parameters  # list of Identifier
        self.rest_parameter = rest_parameter  # Identifier or None
        self.body = body  # BlockStatement or Expression
        self.is_expression_body = is_expression_body

    def to_dict(self) -> dict:
        return {
            "type": "ArrowFunctionLiteral",
            "parameters": [p.value for p in self.parameters],
            "rest_parameter": self.rest_parameter.value if self.rest_parameter else None,
            "body": self.body.to_dict(),
            "is_expression_body": self.is_expression_body
        }

    def __repr__(self) -> str:
        rest = f", ...{self.rest_parameter}" if self.rest_parameter else ""
        return f"Arrow(({','.join(repr(p) for p in self.parameters)}{rest}) => {self.body})"

class SpreadExpression(Expression):
    def __init__(self, expression):
        self.expression = expression  # Expression

    def to_dict(self) -> dict:
        return {
            "type": "SpreadExpression",
            "expression": self.expression.to_dict()
        }

    def __repr__(self) -> str:
        return f"Spread(...{self.expression})"

class UpdateExpression(Expression):
    def __init__(self, operator: str, argument, is_prefix: bool):
        self.operator = operator # "++" or "--"
        self.argument = argument # Identifier, MemberExpression, or IndexExpression
        self.is_prefix = is_prefix

    def to_dict(self) -> dict:
        return {
            "type": "UpdateExpression",
            "operator": self.operator,
            "argument": self.argument.to_dict(),
            "is_prefix": self.is_prefix
        }

    def __repr__(self) -> str:
        if self.is_prefix:
            return f"Update({self.operator}{self.argument})"
        return f"Update({self.argument}{self.operator})"
