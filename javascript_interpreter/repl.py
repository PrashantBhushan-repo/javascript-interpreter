# repl.py

import sys
from . import tokens
from .lexer import Lexer
from .parser import Parser
from .evaluator import Evaluator
from . import ast_nodes
from . import values

# ANSI Color Codes
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

BANNER = f"""{BOLD}{CYAN}
   ___       _   _                    _ _           
  / _ \\_ __ | |_(_) __ _ _ __ __ ___ (_) |_ _   _   
 / /_\\/ '_ \\| __| |/ _` | '__/ _` \\ \\ / / __| | | |  
/ /_\\\\| |_) | |_| | (_| | | | (_| |\\ V /| |_| |_| |  
\\____/| .__/ \\__|_|\\__, |_|  \\__,_| \\_/  \\__|\\__, |  
      |_|          |___/                     |___/   
{RESET}{GREEN}
  JavaScript Interpreter (Python implementation)
  Type code to evaluate. Commands:
    {BOLD}.exit{RESET}{GREEN} / {BOLD}.quit{RESET}{GREEN} : Exit the shell
    {BOLD}.tokens{RESET}{GREEN}     : Toggle token stream visualization
    {BOLD}.ast{RESET}{GREEN}        : Toggle AST tree visualization
    {BOLD}.env{RESET}{GREEN}        : Print active global scope bindings
{RESET}"""

def print_value(val: values.JSValue):
    if isinstance(val, values.JSNumber):
        print(f"{CYAN}{val.to_string()}{RESET}")
    elif isinstance(val, values.JSString):
        print(f"{YELLOW}'{val.to_string()}'{RESET}")
    elif isinstance(val, values.JSBoolean):
        print(f"{BLUE}{val.to_string()}{RESET}")
    elif isinstance(val, values.JSNull):
        print(f"{MAGENTA}null{RESET}")
    elif isinstance(val, values.JSUndefined):
        print(f"{GRAY}undefined{RESET}")
    elif isinstance(val, values.JSArray):
        print(f"{RESET}[ {', '.join(repr_colored(e) for e in val.elements)} ]")
    elif isinstance(val, values.JSFunction):
        print(f"{MAGENTA}[Function]{RESET}")
    elif isinstance(val, values.JSBuiltinFunction):
        print(f"{MAGENTA}[BuiltinFunction: {val.name}]{RESET}")
    else:
        print(f"{RESET}{repr(val)}")

def repr_colored(val: values.JSValue) -> str:
    if isinstance(val, values.JSNumber):
        return f"{CYAN}{val.to_string()}{RESET}"
    elif isinstance(val, values.JSString):
        return f"{YELLOW}'{val.to_string()}'{RESET}"
    elif isinstance(val, values.JSBoolean):
        return f"{BLUE}{val.to_string()}{RESET}"
    elif isinstance(val, values.JSNull):
        return f"{MAGENTA}null{RESET}"
    elif isinstance(val, values.JSUndefined):
        return f"{GRAY}undefined{RESET}"
    return repr(val)

def print_tokens(lexer: Lexer):
    print(f"\n{BOLD}{MAGENTA}--- Token Stream ---{RESET}")
    temp_lexer = Lexer(lexer.input_str)
    while True:
        tok = temp_lexer.next_token()
        print(f"  {GRAY}Line {tok.line}, Col {tok.column:<2}:{RESET} {GREEN}{tok.type:<15}{RESET} -> {YELLOW}{repr(tok.literal)}{RESET}")
        if tok.type == tokens.EOF:
            break
    print(f"{BOLD}{MAGENTA}--------------------{RESET}\n")

def print_ast(node, indent="", is_last=True):
    # Tree branch graphics
    marker = "└── " if is_last else "├── "
    next_indent = indent + ("    " if is_last else "│   ")
    
    node_name = type(node).__name__
    
    if isinstance(node, ast_nodes.Program):
        print(f"{BOLD}{BLUE}Program{RESET}")
        for i, stmt in enumerate(node.statements):
            print_ast(stmt, indent, i == len(node.statements) - 1)
            
    elif isinstance(node, ast_nodes.VariableStatement):
        print(f"{indent}{marker}{BOLD}{GREEN}VariableStatement{RESET} ({node.var_type})")
        for i, decl in enumerate(node.declarations):
            print_ast(decl, next_indent, i == len(node.declarations) - 1)
            
    elif isinstance(node, ast_nodes.VariableDeclaration):
        print(f"{indent}{marker}{BOLD}{CYAN}Decl{RESET} ({node.name.value})")
        if node.value:
            print_ast(node.value, next_indent, True)
            
    elif isinstance(node, ast_nodes.ExpressionStatement):
        print(f"{indent}{marker}{BOLD}{GREEN}ExprStmt{RESET}")
        print_ast(node.expression, next_indent, True)
        
    elif isinstance(node, ast_nodes.Literal):
        print(f"{indent}{marker}{YELLOW}Literal{RESET} ({node.value_type}: {node.value})")
        
    elif isinstance(node, ast_nodes.Identifier):
        print(f"{indent}{marker}{CYAN}Identifier{RESET} ({node.value})")
        
    elif isinstance(node, ast_nodes.InfixExpression):
        print(f"{indent}{marker}{BOLD}{BLUE}Infix{RESET} ({node.operator})")
        print_ast(node.left, next_indent, False)
        print_ast(node.right, next_indent, True)
        
    elif isinstance(node, ast_nodes.PrefixExpression):
        print(f"{indent}{marker}{BOLD}{BLUE}Prefix{RESET} ({node.operator})")
        print_ast(node.right, next_indent, True)
        
    elif isinstance(node, ast_nodes.BlockStatement):
        print(f"{indent}{marker}{BOLD}{GREEN}Block{RESET}")
        for i, stmt in enumerate(node.statements):
            print_ast(stmt, next_indent, i == len(node.statements) - 1)
            
    elif isinstance(node, ast_nodes.IfStatement):
        print(f"{indent}{marker}{BOLD}{GREEN}If{RESET}")
        print_ast(node.condition, next_indent, False)
        print_ast(node.consequence, next_indent, node.alternative is None)
        if node.alternative:
            print_ast(node.alternative, next_indent, True)
            
    elif isinstance(node, (ast_nodes.WhileStatement, ast_nodes.DoWhileStatement)):
        print(f"{indent}{marker}{BOLD}{GREEN}{node_name}{RESET}")
        print_ast(node.condition, next_indent, False)
        print_ast(node.body, next_indent, True)
        
    elif isinstance(node, ast_nodes.ForStatement):
        print(f"{indent}{marker}{BOLD}{GREEN}For{RESET}")
        if node.initializer: print_ast(node.initializer, next_indent, False)
        if node.condition: print_ast(node.condition, next_indent, False)
        if node.increment: print_ast(node.increment, next_indent, False)
        print_ast(node.body, next_indent, True)
        
    elif isinstance(node, ast_nodes.CallExpression):
        print(f"{indent}{marker}{BOLD}{BLUE}Call{RESET}")
        print_ast(node.function, next_indent, not node.arguments)
        for i, arg in enumerate(node.arguments):
            print_ast(arg, next_indent, i == len(node.arguments) - 1)
            
    elif isinstance(node, ast_nodes.FunctionDeclaration):
        params_str = f"({', '.join(p.value for p in node.parameters)})"
        print(f"{indent}{marker}{BOLD}{GREEN}FuncDecl{RESET} ({node.name.value} {params_str})")
        print_ast(node.body, next_indent, True)
        
    elif isinstance(node, ast_nodes.ArrowFunctionLiteral):
        params_str = f"({', '.join(p.value for p in node.parameters)})"
        print(f"{indent}{marker}{BOLD}{GREEN}ArrowFunction{RESET} ({params_str})")
        print_ast(node.body, next_indent, True)

    else:
        print(f"{indent}{marker}{GRAY}{node_name}{RESET}")

def start_repl():
    print(BANNER)
    
    evaluator = Evaluator()
    show_tokens = False
    show_ast = False

    while True:
        try:
            line = input(f"{BOLD}{GREEN}js> {RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        cleaned = line.strip()
        if not cleaned:
            continue

        # Commands
        if cleaned == ".exit" or cleaned == ".quit":
            print("Goodbye!")
            break
        elif cleaned == ".tokens":
            show_tokens = not show_tokens
            print(f"Token stream visualization: {BOLD}{'ENABLED' if show_tokens else 'DISABLED'}{RESET}")
            continue
        elif cleaned == ".ast":
            show_ast = not show_ast
            print(f"AST visualization: {BOLD}{'ENABLED' if show_ast else 'DISABLED'}{RESET}")
            continue
        elif cleaned == ".env":
            print(f"\n{BOLD}{CYAN}--- Active Scope Bindings ---{RESET}")
            for k, v in evaluator.global_env.store.items():
                print(f"  {BOLD}{k}{RESET} : {repr_colored(v)}")
            print(f"{BOLD}{CYAN}-----------------------------{RESET}\n")
            continue

        # Handle multi-line block entry
        if cleaned.endswith("{") or cleaned.endswith("("):
            lines = [line]
            open_braces = cleaned.count("{") - cleaned.count("}")
            open_parens = cleaned.count("(") - cleaned.count(")")
            while open_braces > 0 or open_parens > 0:
                try:
                    next_line = input(f"{GRAY}... {RESET}")
                    lines.append(next_line)
                    open_braces += next_line.count("{") - next_line.count("}")
                    open_parens += next_line.count("(") - next_line.count(")")
                except (KeyboardInterrupt, EOFError):
                    print("\nOperation cancelled.")
                    lines = []
                    break
            if not lines:
                continue
            line = "\n".join(lines)

        lexer = Lexer(line)
        
        if show_tokens:
            print_tokens(lexer)

        parser = Parser(lexer)
        program = parser.parse_program()

        if parser.errors:
            for err in parser.errors:
                print(f"{RED}{BOLD}SyntaxError: {err}{RESET}")
            continue

        if show_ast:
            print(f"\n{BOLD}{BLUE}--- Abstract Syntax Tree ---{RESET}")
            print_ast(program)
            print(f"{BOLD}{BLUE}----------------------------{RESET}\n")

        try:
            val = evaluator.evaluate(program, evaluator.global_env)
            print_value(val)
        except Exception as e:
            print(f"{RED}{BOLD}RuntimeError: {e}{RESET}")
