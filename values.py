# values.py

import math
import random
from datetime import datetime
import functools

# --- Value Wrappers ---

class JSValue:
    def type_string(self) -> str:
        raise NotImplementedError()

    def to_string(self) -> str:
        raise NotImplementedError()

    def to_number(self) -> float:
        raise NotImplementedError()

    def to_boolean(self) -> bool:
        raise NotImplementedError()

    def is_truthy(self) -> bool:
        return self.to_boolean()

    def get_member(self, name: str) -> 'JSValue':
        raise TypeError(f"TypeError: Cannot read properties of {self.type_string()} (reading '{name}')")

    def set_member(self, name: str, value: 'JSValue'):
        raise TypeError(f"TypeError: Cannot set properties of {self.type_string()} (setting '{name}')")


class JSUndefined(JSValue):
    def type_string(self) -> str:
        return "undefined"

    def to_string(self) -> str:
        return "undefined"

    def to_number(self) -> float:
        return float('nan')

    def to_boolean(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "undefined"


class JSNull(JSValue):
    def type_string(self) -> str:
        return "object"  # typeof null is "object" in JS

    def to_string(self) -> str:
        return "null"

    def to_number(self) -> float:
        return 0.0

    def to_boolean(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "null"


# Singletons
UNDEFINED = JSUndefined()
NULL = JSNull()


class JSBoolean(JSValue):
    def __init__(self, value: bool):
        self.value = value

    def type_string(self) -> str:
        return "boolean"

    def to_string(self) -> str:
        return "true" if self.value else "false"

    def to_number(self) -> float:
        return 1.0 if self.value else 0.0

    def to_boolean(self) -> bool:
        return self.value

    def __repr__(self) -> str:
        return "true" if self.value else "false"


# Singletons
TRUE = JSBoolean(True)
FALSE = JSBoolean(False)


class JSNumber(JSValue):
    def __init__(self, value: float):
        # We store as float but try to use int if it represents an integer value
        self.value = float(value)

    def type_string(self) -> str:
        return "number"

    def to_string(self) -> str:
        if math.isnan(self.value):
            return "NaN"
        if math.isinf(self.value):
            return "Infinity" if self.value > 0 else "-Infinity"
        if self.value.is_integer():
            return str(int(self.value))
        return str(self.value)

    def to_number(self) -> float:
        return self.value

    def to_boolean(self) -> bool:
        if math.isnan(self.value) or self.value == 0.0:
            return False
        return True

    def __repr__(self) -> str:
        return self.to_string()


class JSString(JSValue):
    def __init__(self, value: str):
        self.value = value

    def type_string(self) -> str:
        return "string"

    def to_string(self) -> str:
        return self.value

    def to_number(self) -> float:
        s = self.value.strip()
        if not s:
            return 0.0
        try:
            return float(s)
        except ValueError:
            return float('nan')

    def to_boolean(self) -> bool:
        return len(self.value) > 0

    def get_member(self, name: str) -> JSValue:
        if name == "length":
            return JSNumber(len(self.value))
        # Check string prototype methods
        if name in STRING_PROTOTYPE:
            return JSBuiltinFunction(name, STRING_PROTOTYPE[name], this_val=self)
        return UNDEFINED

    def __repr__(self) -> str:
        return f"'{self.value}'"


class JSObject(JSValue):
    def __init__(self):
        self.properties = {}

    def type_string(self) -> str:
        return "object"

    def to_string(self) -> str:
        return "[object Object]"

    def to_number(self) -> float:
        return float('nan')

    def to_boolean(self) -> bool:
        return True

    def get_member(self, name: str) -> JSValue:
        if name in self.properties:
            return self.properties[name]
        return UNDEFINED

    def set_member(self, name: str, value: JSValue):
        self.properties[name] = value

    def __repr__(self) -> str:
        items = [f"{k}: {repr(v)}" for k, v in self.properties.items()]
        return "{" + ", ".join(items) + "}"


class JSArray(JSObject):
    def __init__(self, elements=None):
        super().__init__()
        self.elements = list(elements) if elements is not None else []

    def to_string(self) -> str:
        return ",".join(e.to_string() if e not in (UNDEFINED, NULL) else "" for e in self.elements)

    def to_number(self) -> float:
        if not self.elements:
            return 0.0
        if len(self.elements) == 1:
            return self.elements[0].to_number()
        return float('nan')

    def get_member(self, name: str) -> JSValue:
        if name == "length":
            return JSNumber(len(self.elements))
        
        # Array index access
        if name.isdigit():
            idx = int(name)
            if 0 <= idx < len(self.elements):
                return self.elements[idx]
            return UNDEFINED

        # Prototype methods
        if name in ARRAY_PROTOTYPE:
            return JSBuiltinFunction(name, ARRAY_PROTOTYPE[name], this_val=self)

        return super().get_member(name)

    def set_member(self, name: str, value: JSValue):
        if name == "length":
            new_len = int(value.to_number())
            if new_len < 0 or math.isnan(new_len):
                raise ValueError("RangeError: Invalid array length")
            if new_len < len(self.elements):
                self.elements = self.elements[:new_len]
            else:
                self.elements.extend([UNDEFINED] * (new_len - len(self.elements)))
            return

        if name.isdigit():
            idx = int(name)
            if idx >= len(self.elements):
                # pad with undefined
                self.elements.extend([UNDEFINED] * (idx - len(self.elements) + 1))
            self.elements[idx] = value
            return

        super().set_member(name, value)

    def __repr__(self) -> str:
        return f"[{', '.join(repr(e) for e in self.elements)}]"


class JSFunction(JSValue):
    def __init__(self, parameters, rest_parameter, body, env, is_arrow: bool = False):
        self.parameters = parameters  # list of ast_nodes.Identifier
        self.rest_parameter = rest_parameter  # ast_nodes.Identifier or None
        self.body = body  # BlockStatement or Expression (for expression arrow bodies)
        self.env = env  # Captured environment (closure)
        self.is_arrow = is_arrow

    def type_string(self) -> str:
        return "function"

    def to_string(self) -> str:
        return f"function(...) {{ [code] }}"

    def to_number(self) -> float:
        return float('nan')

    def to_boolean(self) -> bool:
        return True

    def __repr__(self) -> str:
        return "[Function]"


class JSBuiltinFunction(JSValue):
    def __init__(self, name: str, fn, this_val=None):
        self.name = name
        self.fn = fn  # fn(evaluator, this_val, args)
        self.this_val = this_val

    def type_string(self) -> str:
        return "function"

    def to_string(self) -> str:
        return f"function {self.name}() {{ [native code] }}"

    def to_number(self) -> float:
        return float('nan')

    def to_boolean(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"[BuiltinFunction: {self.name}]"


class JSDate(JSObject):
    def __init__(self, dt: datetime):
        super().__init__()
        self.dt = dt

    def to_string(self) -> str:
        return self.dt.isoformat()

    def to_number(self) -> float:
        return self.dt.timestamp() * 1000.0

    def get_member(self, name: str) -> JSValue:
        if name in DATE_PROTOTYPE:
            return JSBuiltinFunction(name, DATE_PROTOTYPE[name], this_val=self)
        return super().get_member(name)

    def __repr__(self) -> str:
        return f"Date({self.dt.isoformat()})"


# --- Coercion Helpers ---

def to_primitive(val: JSValue) -> JSValue:
    if isinstance(val, (JSObject, JSArray)):
        return JSString(val.to_string())
    return val


def loose_equals(left: JSValue, right: JSValue) -> bool:
    lt = left.type_string()
    rt = right.type_string()

    if lt == rt:
        # Same type comparison
        if isinstance(left, JSNumber):
            if math.isnan(left.value) or math.isnan(right.value):
                return False
            return left.value == right.value
        if isinstance(left, (JSString, JSBoolean)):
            return left.value == right.value
        if isinstance(left, (JSUndefined, JSNull)):
            return True
        # Objects compared by reference in Python (identity check)
        return left is right

    # null and undefined are loosely equal
    if (isinstance(left, JSUndefined) and isinstance(right, JSNull)) or \
       (isinstance(left, JSNull) and isinstance(right, JSUndefined)):
        return True

    # number and string -> convert string to number
    if lt == "number" and rt == "string":
        return loose_equals(left, JSNumber(right.to_number()))
    if lt == "string" and rt == "number":
        return loose_equals(JSNumber(left.to_number()), right)

    # boolean and anything else -> convert boolean to number
    if lt == "boolean":
        return loose_equals(JSNumber(left.to_number()), right)
    if rt == "boolean":
        return loose_equals(left, JSNumber(right.to_number()))

    # object and primitive (string, number, boolean)
    if lt == "object" and rt in ["string", "number", "boolean"]:
        return loose_equals(to_primitive(left), right)
    if rt == "object" and lt in ["string", "number", "boolean"]:
        return loose_equals(left, to_primitive(right))

    return False


def strict_equals(left: JSValue, right: JSValue) -> bool:
    lt = left.type_string()
    rt = right.type_string()

    if lt != rt:
        return False

    if isinstance(left, JSNumber):
        if math.isnan(left.value) or math.isnan(right.value):
            return False
        return left.value == right.value
    if isinstance(left, (JSString, JSBoolean)):
        return left.value == right.value
    if isinstance(left, (JSUndefined, JSNull)):
        return True
    return left is right


# --- String Prototype Methods ---

def str_split(evaluator, this_val, args):
    s = this_val.value
    if not args:
        return JSArray([JSString(s)])
    sep = args[0].to_string()
    parts = s.split(sep) if sep != "" else list(s)
    return JSArray([JSString(p) for p in parts])

def str_slice(evaluator, this_val, args):
    s = this_val.value
    start = int(args[0].to_number()) if len(args) > 0 else 0
    end = int(args[1].to_number()) if len(args) > 1 else len(s)
    
    # Resolve negative indices
    if start < 0: start = max(len(s) + start, 0)
    if end < 0: end = max(len(s) + end, 0)
    
    return JSString(s[start:end])

def str_substring(evaluator, this_val, args):
    s = this_val.value
    start = int(args[0].to_number()) if len(args) > 0 else 0
    end = int(args[1].to_number()) if len(args) > 1 else len(s)
    
    # NaN becomes 0, negative becomes 0
    if start < 0 or math.isnan(start): start = 0
    if end < 0 or math.isnan(end): end = 0
    
    start = min(start, len(s))
    end = min(end, len(s))
    
    # Swap if start > end
    if start > end:
        start, end = end, start
        
    return JSString(s[start:end])

def str_trim(evaluator, this_val, args):
    return JSString(this_val.value.strip())

def str_toUpperCase(evaluator, this_val, args):
    return JSString(this_val.value.upper())

def str_toLowerCase(evaluator, this_val, args):
    return JSString(this_val.value.lower())

def str_includes(evaluator, this_val, args):
    search = args[0].to_string() if args else "undefined"
    pos = int(args[1].to_number()) if len(args) > 1 else 0
    pos = max(pos, 0)
    return JSBoolean(search in this_val.value[pos:])

def str_startsWith(evaluator, this_val, args):
    search = args[0].to_string() if args else "undefined"
    pos = int(args[1].to_number()) if len(args) > 1 else 0
    pos = max(pos, 0)
    return JSBoolean(this_val.value.startswith(search, pos))

def str_endsWith(evaluator, this_val, args):
    s = this_val.value
    search = args[0].to_string() if args else "undefined"
    length = int(args[1].to_number()) if len(args) > 1 else len(s)
    length = min(max(length, 0), len(s))
    return JSBoolean(s[:length].endswith(search))

def str_indexOf(evaluator, this_val, args):
    search = args[0].to_string() if args else "undefined"
    pos = int(args[1].to_number()) if len(args) > 1 else 0
    pos = max(pos, 0)
    idx = this_val.value.find(search, pos)
    return JSNumber(idx)

def str_replace(evaluator, this_val, args):
    search = args[0].to_string() if len(args) > 0 else "undefined"
    replacement = args[1].to_string() if len(args) > 1 else "undefined"
    return JSString(this_val.value.replace(search, replacement, 1))

def str_replaceAll(evaluator, this_val, args):
    search = args[0].to_string() if len(args) > 0 else "undefined"
    replacement = args[1].to_string() if len(args) > 1 else "undefined"
    return JSString(this_val.value.replace(search, replacement))

STRING_PROTOTYPE = {
    "split": str_split,
    "slice": str_slice,
    "substring": str_substring,
    "trim": str_trim,
    "toUpperCase": str_toUpperCase,
    "toLowerCase": str_toLowerCase,
    "includes": str_includes,
    "startsWith": str_startsWith,
    "endsWith": str_endsWith,
    "indexOf": str_indexOf,
    "replace": str_replace,
    "replaceAll": str_replaceAll,
}


# --- Array Prototype Methods ---

def arr_push(evaluator, this_val, args):
    for arg in args:
        this_val.elements.append(arg)
    return JSNumber(len(this_val.elements))

def arr_pop(evaluator, this_val, args):
    if not this_val.elements:
        return UNDEFINED
    return this_val.elements.pop()

def arr_shift(evaluator, this_val, args):
    if not this_val.elements:
        return UNDEFINED
    return this_val.elements.pop(0)

def arr_unshift(evaluator, this_val, args):
    for arg in reversed(args):
        this_val.elements.insert(0, arg)
    return JSNumber(len(this_val.elements))

def arr_slice(evaluator, this_val, args):
    arr = this_val.elements
    start = int(args[0].to_number()) if len(args) > 0 else 0
    end = int(args[1].to_number()) if len(args) > 1 else len(arr)
    
    if start < 0: start = max(len(arr) + start, 0)
    if end < 0: end = max(len(arr) + end, 0)
    
    return JSArray(arr[start:end])

def arr_splice(evaluator, this_val, args):
    arr = this_val.elements
    if not args:
        return JSArray()
        
    start = int(args[0].to_number())
    if start < 0: start = max(len(arr) + start, 0)
    start = min(start, len(arr))

    delete_count = len(arr) - start
    if len(args) > 1:
        delete_count = int(args[1].to_number())
        delete_count = min(max(delete_count, 0), len(arr) - start)

    insert_items = args[2:]
    deleted = arr[start:start+delete_count]
    
    # In-place modification of Python list
    arr[start:start+delete_count] = insert_items
    return JSArray(deleted)

def arr_concat(evaluator, this_val, args):
    new_elements = list(this_val.elements)
    for arg in args:
        if isinstance(arg, JSArray):
            new_elements.extend(arg.elements)
        else:
            new_elements.append(arg)
    return JSArray(new_elements)

def arr_includes(evaluator, this_val, args):
    search = args[0] if args else UNDEFINED
    from_idx = int(args[1].to_number()) if len(args) > 1 else 0
    if from_idx < 0: from_idx = max(len(this_val.elements) + from_idx, 0)
    
    # SameValueZero comparison (NaN === NaN is true)
    for e in this_val.elements[from_idx:]:
        if isinstance(e, JSNumber) and isinstance(search, JSNumber):
            if math.isnan(e.value) and math.isnan(search.value):
                return TRUE
        if strict_equals(e, search):
            return TRUE
    return FALSE

def arr_indexOf(evaluator, this_val, args):
    search = args[0] if args else UNDEFINED
    from_idx = int(args[1].to_number()) if len(args) > 1 else 0
    if from_idx < 0: from_idx = max(len(this_val.elements) + from_idx, 0)
    
    for i in range(from_idx, len(this_val.elements)):
        if strict_equals(this_val.elements[i], search):
            return JSNumber(i)
    return JSNumber(-1)

def arr_join(evaluator, this_val, args):
    sep = args[0].to_string() if args else ","
    return JSString(sep.join(e.to_string() if e not in (UNDEFINED, NULL) else "" for e in this_val.elements))

def arr_reverse(evaluator, this_val, args):
    this_val.elements.reverse()
    return this_val

def arr_sort(evaluator, this_val, args):
    compare_fn = args[0] if args else None
    
    if compare_fn is None:
        # Sort by JS string representations
        def fallback_cmp(a, b):
            sa = a.to_string()
            sb = b.to_string()
            if sa < sb: return -1
            if sa > sb: return 1
            return 0
        this_val.elements.sort(key=functools.cmp_to_key(fallback_cmp))
    else:
        def custom_cmp(a, b):
            # Call user JS function. Needs evaluator.
            # In evaluator, call_function(func, args, this_val)
            res = evaluator.call_function(compare_fn, [a, b], UNDEFINED)
            val = res.to_number()
            if math.isnan(val) or val == 0.0:
                return 0
            return -1 if val < 0 else 1
        this_val.elements.sort(key=functools.cmp_to_key(custom_cmp))
        
    return this_val

def arr_map(evaluator, this_val, args):
    if not args:
        raise TypeError("TypeError: undefined is not a function")
    callback = args[0]
    result = []
    for i, e in enumerate(this_val.elements):
        res = evaluator.call_function(callback, [e, JSNumber(i), this_val], UNDEFINED)
        result.append(res)
    return JSArray(result)

def arr_filter(evaluator, this_val, args):
    if not args:
        raise TypeError("TypeError: undefined is not a function")
    callback = args[0]
    result = []
    for i, e in enumerate(this_val.elements):
        res = evaluator.call_function(callback, [e, JSNumber(i), this_val], UNDEFINED)
        if res.is_truthy():
            result.append(e)
    return JSArray(result)

def arr_reduce(evaluator, this_val, args):
    if not args:
        raise TypeError("TypeError: undefined is not a function")
    callback = args[0]
    arr = this_val.elements
    
    if not arr and len(args) < 2:
        raise TypeError("TypeError: Reduce of empty array with no initial value")
        
    if len(args) >= 2:
        acc = args[1]
        start_idx = 0
    else:
        acc = arr[0]
        start_idx = 1
        
    for i in range(start_idx, len(arr)):
        acc = evaluator.call_function(callback, [acc, arr[i], JSNumber(i), this_val], UNDEFINED)
        
    return acc

def arr_find(evaluator, this_val, args):
    if not args:
        raise TypeError("TypeError: undefined is not a function")
    callback = args[0]
    for i, e in enumerate(this_val.elements):
        res = evaluator.call_function(callback, [e, JSNumber(i), this_val], UNDEFINED)
        if res.is_truthy():
            return e
    return UNDEFINED

def arr_some(evaluator, this_val, args):
    if not args:
        raise TypeError("TypeError: undefined is not a function")
    callback = args[0]
    for i, e in enumerate(this_val.elements):
        res = evaluator.call_function(callback, [e, JSNumber(i), this_val], UNDEFINED)
        if res.is_truthy():
            return TRUE
    return FALSE

def arr_every(evaluator, this_val, args):
    if not args:
        raise TypeError("TypeError: undefined is not a function")
    callback = args[0]
    for i, e in enumerate(this_val.elements):
        res = evaluator.call_function(callback, [e, JSNumber(i), this_val], UNDEFINED)
        if not res.is_truthy():
            return FALSE
    return TRUE

ARRAY_PROTOTYPE = {
    "push": arr_push,
    "pop": arr_pop,
    "shift": arr_shift,
    "unshift": arr_unshift,
    "slice": arr_slice,
    "splice": arr_splice,
    "concat": arr_concat,
    "includes": arr_includes,
    "indexOf": arr_indexOf,
    "join": arr_join,
    "sort": arr_sort,
    "reverse": arr_reverse,
    "map": arr_map,
    "filter": arr_filter,
    "reduce": arr_reduce,
    "find": arr_find,
    "some": arr_some,
    "every": arr_every,
}


# --- Date Prototype Methods ---

def date_getTime(evaluator, this_val, args):
    return JSNumber(this_val.to_number())

def date_getFullYear(evaluator, this_val, args):
    return JSNumber(this_val.dt.year)

def date_getMonth(evaluator, this_val, args):
    # JS months are 0-11
    return JSNumber(this_val.dt.month - 1)

def date_getDate(evaluator, this_val, args):
    # day of month (1-31)
    return JSNumber(this_val.dt.day)

def date_getDay(evaluator, this_val, args):
    # day of week (0 = Sunday, ..., 6 = Saturday)
    # python weekday is 0 = Monday, ..., 6 = Sunday
    # convert python to JS: (py_day + 1) % 7
    return JSNumber((this_val.dt.weekday() + 1) % 7)

def date_getHours(evaluator, this_val, args):
    return JSNumber(this_val.dt.hour)

def date_getMinutes(evaluator, this_val, args):
    return JSNumber(this_val.dt.minute)

def date_getSeconds(evaluator, this_val, args):
    return JSNumber(this_val.dt.second)

DATE_PROTOTYPE = {
    "getTime": date_getTime,
    "getFullYear": date_getFullYear,
    "getMonth": date_getMonth,
    "getDate": date_getDate,
    "getDay": date_getDay,
    "getHours": date_getHours,
    "getMinutes": date_getMinutes,
    "getSeconds": date_getSeconds,
}


# --- Date Constructor Function ---

def date_constructor(evaluator, this_val, args):
    # If not called as 'new Date(...)', JS returns current date as string
    # How does the evaluator distinguish? We can check if `this_val` is passed as a new instance.
    # In parser, `new Date(...)` runs NewExpression.
    # Evaluator's evaluate_new_expression creates a new empty JSDate with dummy datetime.
    # If we pass that instance as `this_val`, we can configure it!
    # Let's see:
    if this_val is None or not isinstance(this_val, JSDate):
        # Called as normal function Date(), return formatted date string
        return JSString(datetime.now().isoformat()) # Simplified string
        
    # Configure the JSDate instance `this_val`
    if not args:
        this_val.dt = datetime.now()
    elif len(args) == 1:
        arg = args[0]
        if isinstance(arg, JSNumber):
            # timestamp in milliseconds
            this_val.dt = datetime.fromtimestamp(arg.value / 1000.0)
        else:
            # parse string
            try:
                # support ISO parsing
                this_val.dt = datetime.fromisoformat(arg.to_string())
            except ValueError:
                # Fallback
                this_val.dt = datetime.now()
    else:
        # multiple args: year, month, day=1, hours=0, minutes=0, seconds=0, ms=0
        year = int(args[0].to_number())
        month = int(args[1].to_number()) + 1 # Convert JS 0-11 to Python 1-12
        day = int(args[2].to_number()) if len(args) > 2 else 1
        hours = int(args[3].to_number()) if len(args) > 3 else 0
        minutes = int(args[4].to_number()) if len(args) > 4 else 0
        seconds = int(args[5].to_number()) if len(args) > 5 else 0
        this_val.dt = datetime(year, month, day, hours, minutes, seconds)
        
    return this_val
