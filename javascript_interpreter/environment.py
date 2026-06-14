# environment.py

class Environment:
    def __init__(self, outer=None, is_function_boundary: bool = False):
        self.store = {}
        self.consts = set()
        self.outer = outer
        self.is_function_boundary = is_function_boundary

    def get(self, name: str):
        if name in self.store:
            return self.store[name]
        if self.outer:
            return self.outer.get(name)
        raise NameError(f"ReferenceError: {name} is not defined")

    def set(self, name: str, value):
        if name in self.store:
            if name in self.consts:
                raise TypeError(f"TypeError: Assignment to constant variable '{name}'")
            self.store[name] = value
            return value
        
        if self.outer:
            return self.outer.set(name, value)
            
        # In non-strict JavaScript, setting a previously undeclared variable
        # implicitly creates it as a global property.
        self.store[name] = value
        return value

    def declare_let(self, name: str, value):
        if name in self.store:
            raise NameError(f"SyntaxError: Identifier '{name}' has already been declared")
        self.store[name] = value
        return value

    def declare_const(self, name: str, value):
        if name in self.store:
            raise NameError(f"SyntaxError: Identifier '{name}' has already been declared")
        self.store[name] = value
        self.consts.add(name)
        return value

    def declare_var(self, name: str, value):
        # Walk up to the nearest function boundary or global scope
        env = self
        while env.outer and not env.is_function_boundary:
            env = env.outer
        
        # If it's a non-undefined value, or not already in store, set it
        if type(value).__name__ != 'JSUndefined' or name not in env.store:
            env.store[name] = value
        return env.store[name]
