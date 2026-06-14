# evaluator.py

import javascript_interpreter.ast_nodes as ast_nodes
import javascript_interpreter.values as values
from javascript_interpreter.environment import Environment
import math
import random
from datetime import datetime

# --- Custom Exceptions for Control Flow ---

class ReturnException(Exception):
    def __init__(self, value: values.JSValue):
        self.value = value

class BreakException(Exception):
    pass

class ContinueException(Exception):
    pass


class Evaluator:
    def __init__(self):
        self.stdout_buffer = []
        self.global_env = Environment(outer=None, is_function_boundary=True)
        self.init_global_env()

    def init_global_env(self):
        # Bind 'this' in global scope to global object
        global_this = values.JSObject()
        self.global_env.declare_let("this", global_this)
        
        # console object
        console = values.JSObject()
        console.set_member("log", values.JSBuiltinFunction("log", self.builtin_console_log))
        self.global_env.declare_let("console", console)

        # Math object
        math_obj = values.JSObject()
        math_obj.set_member("PI", values.JSNumber(math.pi))
        math_obj.set_member("E", values.JSNumber(math.e))
        math_obj.set_member("floor", values.JSBuiltinFunction("floor", self.builtin_math_floor))
        math_obj.set_member("random", values.JSBuiltinFunction("random", self.builtin_math_random))
        math_obj.set_member("max", values.JSBuiltinFunction("max", self.builtin_math_max))
        math_obj.set_member("min", values.JSBuiltinFunction("min", self.builtin_math_min))
        math_obj.set_member("abs", values.JSBuiltinFunction("abs", self.builtin_math_abs))
        math_obj.set_member("pow", values.JSBuiltinFunction("pow", self.builtin_math_pow))
        math_obj.set_member("sqrt", values.JSBuiltinFunction("sqrt", self.builtin_math_sqrt))
        self.global_env.declare_let("Math", math_obj)

        # Date constructor function
        date_ctor = values.JSBuiltinFunction("Date", values.date_constructor)
        self.global_env.declare_let("Date", date_ctor)

    # --- Built-in Implementations ---

    def builtin_console_log(self, evaluator, this_val, args):
        msg = " ".join(arg.to_string() for arg in args)
        print(msg)
        self.stdout_buffer.append(msg)
        return values.UNDEFINED

    def builtin_math_floor(self, evaluator, this_val, args):
        val = args[0].to_number() if args else float('nan')
        if math.isnan(val): return values.JSNumber(float('nan'))
        return values.JSNumber(math.floor(val))

    def builtin_math_random(self, evaluator, this_val, args):
        return values.JSNumber(random.random())

    def builtin_math_max(self, evaluator, this_val, args):
        if not args: return values.JSNumber(float('-inf'))
        # convert args to float
        nums = []
        for arg in args:
            num = arg.to_number()
            if math.isnan(num): return values.JSNumber(float('nan'))
            nums.append(num)
        return values.JSNumber(max(nums))

    def builtin_math_min(self, evaluator, this_val, args):
        if not args: return values.JSNumber(float('inf'))
        nums = []
        for arg in args:
            num = arg.to_number()
            if math.isnan(num): return values.JSNumber(float('nan'))
            nums.append(num)
        return values.JSNumber(min(nums))

    def builtin_math_abs(self, evaluator, this_val, args):
        val = args[0].to_number() if args else float('nan')
        if math.isnan(val): return values.JSNumber(float('nan'))
        return values.JSNumber(abs(val))

    def builtin_math_pow(self, evaluator, this_val, args):
        base = args[0].to_number() if len(args) > 0 else float('nan')
        exp = args[1].to_number() if len(args) > 1 else float('nan')
        if math.isnan(base) or math.isnan(exp):
            return values.JSNumber(float('nan'))
        try:
            return values.JSNumber(math.pow(base, exp))
        except (ValueError, OverflowError):
            return values.JSNumber(float('nan'))

    def builtin_math_sqrt(self, evaluator, this_val, args):
        val = args[0].to_number() if args else float('nan')
        if val < 0 or math.isnan(val): return values.JSNumber(float('nan'))
        return values.JSNumber(math.sqrt(val))

    # --- Hoisting Scans ---

    def hoist_vars(self, node, env):
        if isinstance(node, ast_nodes.Program) or isinstance(node, ast_nodes.BlockStatement):
            for stmt in node.statements:
                self.hoist_vars(stmt, env)
        elif isinstance(node, ast_nodes.VariableStatement):
            if node.var_type == "var":
                for decl in node.declarations:
                    env.declare_var(decl.name.value, values.UNDEFINED)
        elif isinstance(node, ast_nodes.IfStatement):
            self.hoist_vars(node.consequence, env)
            if node.alternative:
                self.hoist_vars(node.alternative, env)
        elif isinstance(node, ast_nodes.WhileStatement) or isinstance(node, ast_nodes.DoWhileStatement):
            self.hoist_vars(node.body, env)
        elif isinstance(node, ast_nodes.ForStatement):
            if node.initializer:
                self.hoist_vars(node.initializer, env)
            self.hoist_vars(node.body, env)
        elif isinstance(node, ast_nodes.SwitchStatement):
            for case in node.cases:
                for stmt in case.consequent:
                    self.hoist_vars(stmt, env)

    def hoist_functions(self, node, env):
        if isinstance(node, ast_nodes.Program) or isinstance(node, ast_nodes.BlockStatement):
            for stmt in node.statements:
                self.hoist_functions(stmt, env)
        elif isinstance(node, ast_nodes.FunctionDeclaration):
            func_val = values.JSFunction(
                parameters=node.parameters,
                rest_parameter=node.rest_parameter,
                body=node.body,
                env=env,
                is_arrow=False
            )
            env.declare_var(node.name.value, func_val)
        elif isinstance(node, ast_nodes.IfStatement):
            self.hoist_functions(node.consequence, env)
            if node.alternative:
                self.hoist_functions(node.alternative, env)
        elif isinstance(node, ast_nodes.WhileStatement) or isinstance(node, ast_nodes.DoWhileStatement):
            self.hoist_functions(node.body, env)
        elif isinstance(node, ast_nodes.ForStatement):
            if node.initializer:
                self.hoist_functions(node.initializer, env)
            self.hoist_functions(node.body, env)
        elif isinstance(node, ast_nodes.SwitchStatement):
            for case in node.cases:
                for stmt in case.consequent:
                    self.hoist_functions(stmt, env)

    # --- Core Evaluator ---

    def evaluate(self, node, env) -> values.JSValue:
        if node is None:
            return values.UNDEFINED

        # --- Statements ---

        if isinstance(node, ast_nodes.Program):
            self.hoist_vars(node, env)
            self.hoist_functions(node, env)
            
            result = values.UNDEFINED
            for stmt in node.statements:
                # Do not re-evaluate FunctionDeclarations as expressions since they are hoisted
                if isinstance(stmt, ast_nodes.FunctionDeclaration):
                    continue
                result = self.evaluate(stmt, env)
            return result

        elif isinstance(node, ast_nodes.BlockStatement):
            child_env = Environment(outer=env, is_function_boundary=False)
            result = values.UNDEFINED
            for stmt in node.statements:
                result = self.evaluate(stmt, child_env)
            return result

        elif isinstance(node, ast_nodes.VariableStatement):
            for decl in node.declarations:
                val = self.evaluate(decl.value, env) if decl.value else values.UNDEFINED
                if node.var_type == "let":
                    env.declare_let(decl.name.value, val)
                elif node.var_type == "const":
                    env.declare_const(decl.name.value, val)
                elif node.var_type == "var":
                    env.declare_var(decl.name.value, val)
            return values.UNDEFINED

        elif isinstance(node, ast_nodes.ReturnStatement):
            val = self.evaluate(node.value, env) if node.value else values.UNDEFINED
            raise ReturnException(val)

        elif isinstance(node, ast_nodes.ExpressionStatement):
            return self.evaluate(node.expression, env)

        elif isinstance(node, ast_nodes.IfStatement):
            cond_val = self.evaluate(node.condition, env)
            if cond_val.is_truthy():
                return self.evaluate(node.consequence, env)
            elif node.alternative:
                return self.evaluate(node.alternative, env)
            return values.UNDEFINED

        elif isinstance(node, ast_nodes.WhileStatement):
            result = values.UNDEFINED
            while True:
                cond_val = self.evaluate(node.condition, env)
                if not cond_val.is_truthy():
                    break
                try:
                    result = self.evaluate(node.body, env)
                except BreakException:
                    break
                except ContinueException:
                    continue
            return result

        elif isinstance(node, ast_nodes.DoWhileStatement):
            result = values.UNDEFINED
            while True:
                try:
                    result = self.evaluate(node.body, env)
                except BreakException:
                    break
                except ContinueException:
                    pass
                cond_val = self.evaluate(node.condition, env)
                if not cond_val.is_truthy():
                    break
            return result

        elif isinstance(node, ast_nodes.ForStatement):
            # Create a loop environment scope
            loop_env = Environment(outer=env, is_function_boundary=False)
            if node.initializer:
                self.evaluate(node.initializer, loop_env)

            result = values.UNDEFINED
            while True:
                if node.condition:
                    cond_val = self.evaluate(node.condition, loop_env)
                    if not cond_val.is_truthy():
                        break

                # Create fresh block iteration environment for closure state safety
                iter_env = Environment(outer=loop_env.outer, is_function_boundary=False)
                for k, v in loop_env.store.items():
                    iter_env.store[k] = v
                    if k in loop_env.consts:
                        iter_env.consts.add(k)

                try:
                    result = self.evaluate(node.body, iter_env)
                except BreakException:
                    break
                except ContinueException:
                    pass

                # Propagate changes back to loop env for update expressions
                for k in loop_env.store:
                    if k in iter_env.store:
                        loop_env.store[k] = iter_env.store[k]

                if node.increment:
                    self.evaluate(node.increment, loop_env)
            return result

        elif isinstance(node, ast_nodes.BreakStatement):
            raise BreakException()

        elif isinstance(node, ast_nodes.ContinueStatement):
            raise ContinueException()

        elif isinstance(node, ast_nodes.SwitchStatement):
            disc_val = self.evaluate(node.discriminant, env)
            
            # 1. Find matching case
            matched_idx = -1
            default_idx = -1
            for i, case in enumerate(node.cases):
                if case.test is None:
                    default_idx = i
                else:
                    test_val = self.evaluate(case.test, env)
                    if values.strict_equals(disc_val, test_val):
                        matched_idx = i
                        break
            
            start_idx = matched_idx if matched_idx != -1 else default_idx
            if start_idx == -1:
                return values.UNDEFINED

            # Run cases with fallthrough
            result = values.UNDEFINED
            try:
                for i in range(start_idx, len(node.cases)):
                    for stmt in node.cases[i].consequent:
                        result = self.evaluate(stmt, env)
            except BreakException:
                pass
            return result

        # --- Expressions ---

        elif isinstance(node, ast_nodes.Identifier):
            return env.get(node.value)

        elif isinstance(node, ast_nodes.Literal):
            if node.value_type == "number":
                return values.JSNumber(node.value)
            elif node.value_type == "string":
                return values.JSString(node.value)
            elif node.value_type == "boolean":
                return values.TRUE if node.value else values.FALSE
            elif node.value_type == "null":
                return values.NULL
            elif node.value_type == "undefined":
                return values.UNDEFINED

        elif isinstance(node, ast_nodes.ArrayLiteral):
            elements = []
            for elem in node.elements:
                if isinstance(elem, ast_nodes.SpreadExpression):
                    spread_val = self.evaluate(elem.expression, env)
                    if isinstance(spread_val, values.JSArray):
                        elements.extend(spread_val.elements)
                    elif isinstance(spread_val, values.JSString):
                        elements.extend(values.JSString(c) for c in spread_val.value)
                    else:
                        raise TypeError(f"TypeError: {spread_val.type_string()} is not iterable")
                else:
                    elements.append(self.evaluate(elem, env))
            return values.JSArray(elements)

        elif isinstance(node, ast_nodes.ObjectLiteral):
            obj = values.JSObject()
            for key, val_expr in node.properties:
                val = self.evaluate(val_expr, env)
                obj.set_member(key, val)
            return obj

        elif isinstance(node, ast_nodes.PrefixExpression):
            right_val = self.evaluate(node.right, env)
            if node.operator == "!":
                return values.FALSE if right_val.is_truthy() else values.TRUE
            elif node.operator == "-":
                return values.JSNumber(-right_val.to_number())
            elif node.operator == "+":
                return values.JSNumber(right_val.to_number())
            raise ValueError(f"Unknown prefix operator: {node.operator}")

        elif isinstance(node, ast_nodes.InfixExpression):
            # Assignment operators (Assignment requires left-side evaluation constraint)
            if node.operator in ["=", "+=", "-=", "*=", "/="]:
                right_val = self.evaluate(node.right, env)
                
                # Retrieve current value if self-assignment
                if node.operator != "=":
                    if isinstance(node.left, ast_nodes.Identifier):
                        current = env.get(node.left.value)
                    elif isinstance(node.left, ast_nodes.IndexExpression):
                        obj = self.evaluate(node.left.left, env)
                        idx = self.evaluate(node.left.index, env)
                        current = obj.get_member(idx.to_string())
                    elif isinstance(node.left, ast_nodes.MemberExpression):
                        obj = self.evaluate(node.left.left, env)
                        current = obj.get_member(node.left.member.value)
                    else:
                        raise ValueError("Invalid left-hand side assignment target")

                    # Apply arithmetic update
                    if node.operator == "+=":
                        prim_left = values.to_primitive(current)
                        prim_right = values.to_primitive(right_val)
                        if isinstance(prim_left, values.JSString) or isinstance(prim_right, values.JSString):
                            right_val = values.JSString(prim_left.to_string() + prim_right.to_string())
                        else:
                            right_val = values.JSNumber(prim_left.to_number() + prim_right.to_number())
                    elif node.operator == "-=":
                        right_val = values.JSNumber(current.to_number() - right_val.to_number())
                    elif node.operator == "*=":
                        right_val = values.JSNumber(current.to_number() * right_val.to_number())
                    elif node.operator == "/=":
                        right_val = values.JSNumber(current.to_number() / right_val.to_number())

                # Set result in environment or property
                if isinstance(node.left, ast_nodes.Identifier):
                    env.set(node.left.value, right_val)
                elif isinstance(node.left, ast_nodes.IndexExpression):
                    obj = self.evaluate(node.left.left, env)
                    idx = self.evaluate(node.left.index, env)
                    obj.set_member(idx.to_string(), right_val)
                elif isinstance(node.left, ast_nodes.MemberExpression):
                    obj = self.evaluate(node.left.left, env)
                    obj.set_member(node.left.member.value, right_val)
                else:
                    raise ValueError("Invalid left-hand side assignment target")
                
                return right_val

            # Logical operators (with short circuit)
            if node.operator == "&&":
                left_val = self.evaluate(node.left, env)
                if not left_val.is_truthy():
                    return left_val
                return self.evaluate(node.right, env)
            elif node.operator == "||":
                left_val = self.evaluate(node.left, env)
                if left_val.is_truthy():
                    return left_val
                return self.evaluate(node.right, env)

            # Standard binary operators
            left_val = self.evaluate(node.left, env)
            right_val = self.evaluate(node.right, env)

            if node.operator == "+":
                prim_left = values.to_primitive(left_val)
                prim_right = values.to_primitive(right_val)
                if isinstance(prim_left, values.JSString) or isinstance(prim_right, values.JSString):
                    return values.JSString(prim_left.to_string() + prim_right.to_string())
                return values.JSNumber(prim_left.to_number() + prim_right.to_number())

            elif node.operator == "-":
                return values.JSNumber(left_val.to_number() - right_val.to_number())
            elif node.operator == "*":
                return values.JSNumber(left_val.to_number() * right_val.to_number())
            elif node.operator == "/":
                r_num = right_val.to_number()
                l_num = left_val.to_number()
                if r_num == 0.0:
                    if l_num == 0.0: return values.JSNumber(float('nan'))
                    return values.JSNumber(float('inf') if l_num > 0 else float('-inf'))
                return values.JSNumber(l_num / r_num)
            elif node.operator == "%":
                r_num = right_val.to_number()
                if r_num == 0.0: return values.JSNumber(float('nan'))
                return values.JSNumber(math.fmod(left_val.to_number(), r_num))

            # Equality operations
            elif node.operator == "==":
                return values.JSBoolean(values.loose_equals(left_val, right_val))
            elif node.operator == "!=":
                return values.JSBoolean(not values.loose_equals(left_val, right_val))
            elif node.operator == "===":
                return values.JSBoolean(values.strict_equals(left_val, right_val))
            elif node.operator == "!==":
                return values.JSBoolean(not values.strict_equals(left_val, right_val))

            # Comparisons
            elif node.operator in ["<", ">", "<=", ">="]:
                # Lexicographical comparison if both are strings
                if isinstance(left_val, values.JSString) and isinstance(right_val, values.JSString):
                    if node.operator == "<": return values.JSBoolean(left_val.value < right_val.value)
                    elif node.operator == ">": return values.JSBoolean(left_val.value > right_val.value)
                    elif node.operator == "<=": return values.JSBoolean(left_val.value <= right_val.value)
                    elif node.operator == ">=": return values.JSBoolean(left_val.value >= right_val.value)
                else:
                    l_num = left_val.to_number()
                    r_num = right_val.to_number()
                    if math.isnan(l_num) or math.isnan(r_num):
                        return values.FALSE
                    if node.operator == "<": return values.JSBoolean(l_num < r_num)
                    elif node.operator == ">": return values.JSBoolean(l_num > r_num)
                    elif node.operator == "<=": return values.JSBoolean(l_num <= r_num)
                    elif node.operator == ">=": return values.JSBoolean(l_num >= r_num)

            raise ValueError(f"Unknown infix operator: {node.operator}")

        elif isinstance(node, ast_nodes.CallExpression):
            # Check if calling a member function (setting 'this')
            this_val = values.UNDEFINED
            if isinstance(node.function, ast_nodes.MemberExpression):
                obj_val = self.evaluate(node.function.left, env)
                func_val = obj_val.get_member(node.function.member.value)
                this_val = obj_val
            elif isinstance(node.function, ast_nodes.IndexExpression):
                obj_val = self.evaluate(node.function.left, env)
                idx_val = self.evaluate(node.function.index, env)
                func_val = obj_val.get_member(idx_val.to_string())
                this_val = obj_val
            else:
                func_val = self.evaluate(node.function, env)

            # Evaluate arguments with spread support
            args = []
            for arg_expr in node.arguments:
                if isinstance(arg_expr, ast_nodes.SpreadExpression):
                    spread_val = self.evaluate(arg_expr.expression, env)
                    if isinstance(spread_val, values.JSArray):
                        args.extend(spread_val.elements)
                    elif isinstance(spread_val, values.JSString):
                        args.extend(values.JSString(c) for c in spread_val.value)
                    else:
                        raise TypeError(f"TypeError: {spread_val.type_string()} is not iterable")
                else:
                    args.append(self.evaluate(arg_expr, env))

            return self.call_function(func_val, args, this_val)

        elif isinstance(node, ast_nodes.IndexExpression):
            left_val = self.evaluate(node.left, env)
            idx_val = self.evaluate(node.index, env)
            return left_val.get_member(idx_val.to_string())

        elif isinstance(node, ast_nodes.MemberExpression):
            left_val = self.evaluate(node.left, env)
            return left_val.get_member(node.member.value)

        elif isinstance(node, ast_nodes.NewExpression):
            constructor_val = self.evaluate(node.constructor, env)
            
            # Evaluate arguments
            args = [self.evaluate(arg, env) for arg in node.arguments]

            if isinstance(constructor_val, values.JSBuiltinFunction) and constructor_val.fn == values.date_constructor:
                # Date instance initialization
                instance = values.JSDate(datetime.now())
                return values.date_constructor(self, instance, args)
            
            raise TypeError("TypeError: constructor is not a constructor")

        elif isinstance(node, ast_nodes.FunctionExpression):
            return values.JSFunction(
                parameters=node.parameters,
                rest_parameter=node.rest_parameter,
                body=node.body,
                env=env,
                is_arrow=False
            )

        elif isinstance(node, ast_nodes.ArrowFunctionLiteral):
            return values.JSFunction(
                parameters=node.parameters,
                rest_parameter=node.rest_parameter,
                body=node.body,
                env=env,
                is_arrow=True
            )

        elif isinstance(node, ast_nodes.UpdateExpression):
            if isinstance(node.argument, ast_nodes.Identifier):
                name = node.argument.value
                current = env.get(name)
                num = current.to_number()
                new_num = num + 1 if node.operator == "++" else num - 1
                env.set(name, values.JSNumber(new_num))
                return values.JSNumber(new_num) if node.is_prefix else values.JSNumber(num)
            elif isinstance(node.argument, ast_nodes.IndexExpression):
                obj = self.evaluate(node.argument.left, env)
                idx = self.evaluate(node.argument.index, env)
                current = obj.get_member(idx.to_string())
                num = current.to_number()
                new_num = num + 1 if node.operator == "++" else num - 1
                obj.set_member(idx.to_string(), values.JSNumber(new_num))
                return values.JSNumber(new_num) if node.is_prefix else values.JSNumber(num)
            elif isinstance(node.argument, ast_nodes.MemberExpression):
                obj = self.evaluate(node.argument.left, env)
                current = obj.get_member(node.argument.member.value)
                num = current.to_number()
                new_num = num + 1 if node.operator == "++" else num - 1
                obj.set_member(node.argument.member.value, values.JSNumber(new_num))
                return values.JSNumber(new_num) if node.is_prefix else values.JSNumber(num)
            else:
                raise ValueError("Invalid target for update operator")

        raise ValueError(f"Unknown AST node type: {type(node)}")

    # --- Invocation ---

    def call_function(self, func_val: values.JSValue, args: list, this_val: values.JSValue) -> values.JSValue:
        if isinstance(func_val, values.JSFunction):
            # Create invocation frame scope
            call_env = Environment(outer=func_val.env, is_function_boundary=True)

            # Bind 'this' context lexically (arrow functions inherit closure 'this')
            if not func_val.is_arrow:
                call_env.declare_let("this", this_val)

            # Map positional arguments
            for i, param in enumerate(func_val.parameters):
                val = args[i] if i < len(args) else values.UNDEFINED
                call_env.declare_let(param.value, val)

            # Map rest parameters
            if func_val.rest_parameter:
                rest_args = args[len(func_val.parameters):]
                call_env.declare_let(func_val.rest_parameter.value, values.JSArray(rest_args))

            # Run function body
            if isinstance(func_val.body, ast_nodes.BlockStatement):
                # We hoist within the function body
                self.hoist_vars(func_val.body, call_env)
                self.hoist_functions(func_val.body, call_env)
                try:
                    self.evaluate(func_val.body, call_env)
                except ReturnException as ret:
                    return ret.value
                return values.UNDEFINED
            else:
                # Arrow function expression body
                return self.evaluate(func_val.body, call_env)

        elif isinstance(func_val, values.JSBuiltinFunction):
            return func_val.fn(self, this_val, args)

        raise TypeError(f"TypeError: {func_val.to_string()} is not a function")
