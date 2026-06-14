# main.py

import sys
import os
from lexer import Lexer
from parser import Parser
from evaluator import Evaluator
from repl import start_repl

def run_file(filepath: str):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
        
    lexer = Lexer(source)
    parser = Parser(lexer)
    program = parser.parse_program()
    
    if parser.errors:
        for err in parser.errors:
            print(f"SyntaxError: {err}", file=sys.stderr)
        sys.exit(1)
        
    evaluator = Evaluator()
    try:
        evaluator.evaluate(program, evaluator.global_env)
    except Exception as e:
        print(f"RuntimeError: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) > 1:
        run_file(sys.argv[1])
    else:
        start_repl()

if __name__ == "__main__":
    main()
